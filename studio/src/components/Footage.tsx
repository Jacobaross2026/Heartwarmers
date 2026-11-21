import React from "react";
import { AbsoluteFill, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame } from "remotion";
import { brand } from "../brand";

export type Shot = { src: string; from: number; dur: number; credit?: string };

/** Small on-screen credit for the story's own footage (e.g. "Video: Smith family"). */
const Credit: React.FC<{ text: string }> = ({ text }) => (
  <div
    style={{
      position: "absolute",
      zIndex: 2,
      top: 218,
      left: 64,
      padding: "6px 16px",
      borderRadius: 999,
      background: "rgba(0,0,0,0.45)",
      color: brand.colors.cream,
      fontFamily: brand.font.family,
      fontWeight: 700,
      fontSize: 26,
      letterSpacing: 0.3,
    }}
  >
    {text}
  </div>
);

const ShotView: React.FC<{ shot: Shot; index: number }> = ({ shot, index }) => {
  const f = useCurrentFrame();
  const zoom = 1 + brand.slowZoom * (f / Math.max(shot.dur, 1));
  // alternate zoom origin so consecutive shots don't feel identical
  const origin = index % 2 === 0 ? "50% 45%" : "50% 55%";
  const fadeIn = index === 0 ? 1 : interpolate(f, [0, 5], [0.4, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: fadeIn }}>
      {shot.credit ? <Credit text={shot.credit} /> : null}
      <OffthreadVideo
        src={staticFile(shot.src)}
        muted
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${zoom})`,
          transformOrigin: origin,
          filter: brand.footageFilter,
        }}
      />
    </AbsoluteFill>
  );
};

export const Footage: React.FC<{ shots: Shot[] }> = ({ shots }) => (
  <AbsoluteFill style={{ backgroundColor: "black" }}>
    {shots.map((s, i) => (
      <Sequence key={i} from={s.from} durationInFrames={s.dur}>
        <ShotView shot={s} index={i} />
      </Sequence>
    ))}
    {/* soft vignette + darker bottom so captions always read */}
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%), " +
          "linear-gradient(180deg, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0) 18%, rgba(0,0,0,0) 50%, rgba(0,0,0,0.35) 100%)",
      }}
    />
  </AbsoluteFill>
);
