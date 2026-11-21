import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { brand } from "../brand";
import { Heart } from "./Heart";

/** Closing card: the comment question + channel identity. */
export const EndCard: React.FC<{ question: string }> = ({ question }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bg = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const pop = spring({ frame: frame - 3, fps, config: { damping: 12, stiffness: 150 } });
  const sub = spring({ frame: frame - 14, fps, config: { damping: 16 } });
  const text = { fontFamily: brand.font.family, fontWeight: brand.font.weight, color: brand.colors.cream };

  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <AbsoluteFill style={{ background: brand.colors.plum, opacity: 0.82 * bg }} />
      <div style={{ textAlign: "center", padding: "0 80px", marginTop: -160, transform: `scale(${pop})` }}>
        <Heart size={130} />
        <div style={{ ...text, fontSize: 96, lineHeight: 1.08, marginTop: 24 }}>{question}</div>
        <div style={{ ...text, fontSize: 50, color: brand.colors.coral, marginTop: 30, opacity: sub }}>
          {brand.endCard.cta} ↓
        </div>
      </div>
      <div style={{ ...text, position: "absolute", bottom: 520, textAlign: "center", opacity: sub }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 14, fontSize: 46 }}>
          <Heart size={44} color={brand.colors.coral} />
          {brand.channelName}
        </div>
        <div style={{ fontSize: 34, marginTop: 10, opacity: 0.85 }}>{brand.endCard.follow}</div>
      </div>
    </AbsoluteFill>
  );
};
