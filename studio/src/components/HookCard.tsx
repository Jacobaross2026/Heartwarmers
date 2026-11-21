import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { brand } from "../brand";
import { Heart } from "./Heart";

/** Branded card in the first ~2 seconds: states the stakes. */
export const HookCard: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = brand.hookCard.seconds * fps;
  const enter = spring({ frame, fps, config: { damping: 13, stiffness: 160 } });
  const exit = interpolate(frame, [total - 8, total], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const beat = 1 + 0.08 * Math.max(0, Math.sin((frame / fps) * Math.PI * 2.4));

  return (
    <AbsoluteFill style={{ alignItems: "center", opacity: exit }}>
      <div
        style={{
          marginTop: brand.hookCard.top,
          width: 900,
          padding: "46px 56px 54px",
          borderRadius: 48,
          background: brand.colors.plum,
          boxShadow: "0 24px 60px rgba(0,0,0,0.45)",
          border: `5px solid ${brand.colors.gold}`,
          transform: `translateY(${interpolate(enter, [0, 1], [-120, 0])}px) scale(${interpolate(enter, [0, 1], [0.8, 1])})`,
          textAlign: "center",
        }}
      >
        <div style={{ transform: `scale(${beat})`, marginBottom: 14 }}>
          <Heart size={84} />
        </div>
        <div
          style={{
            fontFamily: brand.font.family,
            fontWeight: brand.font.weight,
            fontSize: brand.hookCard.fontSize,
            lineHeight: 1.08,
            color: brand.colors.cream,
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};
