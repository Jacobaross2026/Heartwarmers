"""Download a story's own videos and photos from the links Grok provides.

Each item in the story's "story_media" list is a link to:
  - a video post (YouTube, X, Facebook, Instagram, TikTok, news video...) -> yt-dlp
  - a direct image (.jpg/.png/.webp)                                    -> plain download
  - an article page                                                       -> try its video, else its main photos

Files land in assets/footage/<story-id>/real-<n>.mp4 / .jpg, with a record of where
each came from (for credits). Permission is handled by the channel owner outside this
pipeline, so anything Grok hands over is treated as cleared to use.
"""
import re
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

from .config import ASSETS, env

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")
RIGHTS_NOTE = "Permission handled by the channel owner outside the pipeline"


def _platform(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.").removeprefix("m.")
    for key, name in (("youtube", "YouTube"), ("youtu.be", "YouTube"), ("x.com", "X"), ("twitter", "X"),
                      ("facebook", "Facebook"), ("fb.watch", "Facebook"), ("instagram", "Instagram"),
                      ("tiktok", "TikTok"), ("reddit", "Reddit")):
        if key in host:
            return name
    return host or "web"


def _record(file: Path, item: dict, kind: str, url: str) -> dict:
    return {
        "file": file.relative_to(ASSETS.parent).as_posix(),
        "kind": kind,  # video | image
        "source": item.get("creator") or _platform(url),
        "creator": item.get("creator", ""),
        "platform": _platform(url),
        "url": url,
        "is_original": bool(item.get("is_original", False)),
        "description": item.get("description", ""),
        "license": "Used with permission",
        "rights_status": "permission_granted",
        "rights_note": RIGHTS_NOTE,
        "ai_generated": False,
        "real": True,
    }


def _download_video(url: str, dest_stem: Path) -> Path | None:
    import yt_dlp
    opts = {
        "outtmpl": str(dest_stem) + ".%(ext)s",
        "format": "bv*[height<=1920][ext=mp4]+ba[ext=m4a]/b[height<=1920][ext=mp4]/bv*+ba/b",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "max_filesize": 400 * 1024 * 1024,
        "socket_timeout": 30,
        "noprogress": True,
    }
    browser = env("YTDLP_COOKIES_BROWSER")  # e.g. chrome / edge / firefox: lets yt-dlp use your logins
    if browser:
        opts["cookiesfrombrowser"] = (browser,)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception as e:  # noqa: BLE001  (any site error -> try the next method)
        print(f"      (no video via yt-dlp: {str(e).splitlines()[0][:120]})")
        return None
    hits = sorted(dest_stem.parent.glob(dest_stem.name + ".*"))
    vids = [h for h in hits if h.suffix.lower() in (".mp4", ".mkv", ".webm", ".mov")]
    return vids[0] if vids else None


def _download_image(url: str, dest_stem: Path) -> Path | None:
    try:
        r = requests.get(url, headers=UA, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"      (image download failed: {e.__class__.__name__})")
        return None
    ctype = r.headers.get("content-type", "")
    if not ctype.startswith("image/") or len(r.content) < 15_000:  # skip icons, logos, tracking pixels
        return None
    ext = {"image/png": ".png", "image/webp": ".webp"}.get(ctype.split(";")[0], ".jpg")
    out = dest_stem.with_suffix(ext)
    out.write_bytes(r.content)
    return out


def _page_images(url: str, limit: int = 3) -> list[str]:
    """Main photos of an article: og:image / twitter:image first, then large in-article images."""
    try:
        html = requests.get(url, headers=UA, timeout=30).text
    except requests.RequestException:
        return []
    found = []
    for prop in ("og:image", "twitter:image", "og:image:url"):
        for m in re.finditer(rf'<meta[^>]+(?:property|name)=["\']{prop}["\'][^>]*>', html, re.I):
            c = re.search(r'content=["\']([^"\']+)', m.group(0))
            if c:
                found.append(unescape(c.group(1)))
    body = re.search(r"<article.*?</article>", html, re.S | re.I)
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', body.group(0) if body else html, re.I):
        src = unescape(m.group(1))
        if any(bad in src.lower() for bad in ("logo", "icon", "avatar", "sprite", "pixel", ".svg", "ad.")):
            continue
        found.append(src)
    out = []
    for f in found:
        full = urljoin(url, f)
        if full not in out:
            out.append(full)
    return out[:limit]


def fetch(items: list[dict], story_id: str) -> tuple[list[dict], list[str]]:
    """Download every story_media item. Returns (records, plain-English problems)."""
    folder = ASSETS / "footage" / story_id
    folder.mkdir(parents=True, exist_ok=True)
    records, problems, n = [], [], 0
    for item in items:
        url = (item.get("url") or "").strip()
        if not url or item.get("file"):  # no link, or already supplied as a local file
            continue
        kind = (item.get("type") or "").lower()
        print(f"   media: {url[:90]}")
        got: list[tuple[Path, str]] = []
        is_image_url = urlparse(url).path.lower().endswith(IMAGE_EXT)
        if kind == "image" or is_image_url:
            n += 1
            f = _download_image(url, folder / f"real-{n}")
            if f:
                got.append((f, "image"))
        else:
            n += 1
            f = _download_video(url, folder / f"real-{n}")
            if f:
                got.append((f, "video"))
            elif kind != "video":  # an article page without a video: take its photos
                for img in _page_images(url):
                    n += 1
                    f = _download_image(img, folder / f"real-{n}")
                    if f:
                        got.append((f, "image"))
        if not got:
            problems.append(f"Couldn't download anything from {url} (the site blocks automatic "
                            f"downloads or needs a login). Open it in your browser and save the video/photo "
                            f"into assets/footage/{story_id}/ as real-<number>.mp4 or .jpg, then run "
                            f"import again. For Facebook/Instagram posts, setting YTDLP_COOKIES_BROWSER "
                            f"in .env lets the downloader use your own login.")
        for f, k in got:
            print(f"      saved {f.name} ({k})")
            records.append(_record(f, item, k, url))
    return records, problems


VIDEO_EXT = (".mp4", ".mov", ".m4v", ".webm", ".mkv")


def use_local(files: list[Path], items: list[dict], story_id: str, fallback_creator: str) -> list[dict]:
    """Media files uploaded next to the script (e.g. by the Grok bot into Drive).
    Credit comes from the story_media entry whose "file" matches, else the story's source."""
    import shutil
    folder = ASSETS / "footage" / story_id
    folder.mkdir(parents=True, exist_ok=True)
    by_name = {Path(i["file"]).name.lower(): i for i in items if i.get("file")}
    records = []
    for n, f in enumerate(sorted(files), 1):
        ext = f.suffix.lower()
        kind = "video" if ext in VIDEO_EXT else "image"
        dest = folder / f"local-{n}{ext}"
        shutil.copyfile(f, dest)
        item = dict(by_name.get(f.name.lower(), {}))
        item.setdefault("creator", fallback_creator)
        item.setdefault("is_original", True)
        rec = _record(dest, item, kind, item.get("url", ""))
        if not item.get("url"):
            rec["platform"] = item.get("platform", "")
        print(f"   media: {f.name} ({kind}, credit: {rec['creator'] or 'story source'})")
        records.append(rec)
    return records
