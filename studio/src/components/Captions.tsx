import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { brand } from "../brand";

export type Word = { word: string; start: number; end: number };

/** Split each sentence into evenly sized lines (never a lonely last word). */
const toLines = (words: Word[]): Word[][] => {
  const max = brand.captions.wordsPerLine;
  const sentences: Word[][] = [];
  let cur: Word[] = [];
  for (const w of words) {
    cur.push(w);
    if (/[.?!]["']?$/.test(w.word)) {
      sentences.push(cur);
      cur = [];
    }
  }
  if (cur.length) sentences.push(cur);
  const lines: Word[][] = [];
  for (const sent of sentences) {
    const n = Math.ceil(sent.length / max);
    const size = sent.length / n;
    for (let i = 0; i < n; i++) lines.push(sent.slice(Math.round(i * size), Math.round((i + 1) * size)));
  }
  return lines;
};

export const Captions: React.FC<{ words: Word[]; showFrom: number; hideAfter: number }> = ({ words, showFrom, hideAfter }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const t = frame / fps;
  if (t >= hideAfter || t < showFrom) return null;
  const lines = toLines(words.filter((w) => w.end > showFrom));
  const line = lines.find((l, i) => {
    const next = lines[i + 1];
    const lastEnd = l[l.length - 1].end;
    // visible from its first word until the next line starts, but hidden during long pauses
    return t >= l[0].start - 0.05 && (!next || t < next[0].start - 0.05) && t < lastEnd + 0.4;
  });
  if (!line) return null;
  const lineStart = Math.round((line[0].start - 0.05) * fps);
  const pop = spring({ frame: frame - lineStart, fps, config: { damping: 14, stiffness: 220 } });
  const { fontSize, centerY, strokePx } = brand.captions;

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: height * centerY,
          left: 70,
          right: 70,
          transform: `translateY(-50%) scale(${interpolate(pop, [0, 1], [0.85, 1])})`,
          textAlign: "center",
          fontFamily: brand.font.family,
          fontWeight: brand.font.weight,
          fontSize,
          lineHeight: 1.1,
          textTransform: "uppercase",
        }}
      >
        {line.map((w, i) => {
          const active = t >= w.start - 0.03 && t < w.end + 0.08;
          const spoken = t >= w.start - 0.03;
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                margin: "0 20px",
                color: active ? brand.colors.coral : brand.colors.cream,
                opacity: spoken ? 1 : 0.9,
                transform: `scale(${active ? 1.08 : 1})`,
                WebkitTextStroke: `${strokePx}px ${brand.colors.plum}`,
                paintOrder: "stroke fill",
                textShadow: "0 6px 18px rgba(0,0,0,0.55)",
              }}
            >
              {w.word}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
