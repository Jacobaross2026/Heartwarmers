import React from "react";
import { brand } from "../brand";
import { Heart } from "./Heart";

/** Small, constant channel mark so viewers start to recognise the channel. */
export const Watermark: React.FC = () => (
  <div
    style={{
      position: "absolute",
      top: 150,
      left: 60,
      display: "flex",
      alignItems: "center",
      gap: 12,
      padding: "12px 24px 12px 18px",
      borderRadius: 999,
      background: "rgba(43,27,61,0.72)",
      fontFamily: brand.font.family,
      fontWeight: brand.font.weight,
      fontSize: 34,
      color: brand.colors.cream,
    }}
  >
    <Heart size={36} color={brand.colors.coral} />
    {brand.channelName}
  </div>
);
