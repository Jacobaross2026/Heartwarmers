import React from "react";
import { Composition } from "remotion";
import { Short, ShortProps } from "./Short";

const preview: ShortProps = {
  durationInFrames: 150,
  audio: "",
  shots: [],
  words: [
    { word: "This", start: 0.3, end: 0.5 },
    { word: "is", start: 0.5, end: 0.7 },
    { word: "a", start: 0.7, end: 0.8 },
    { word: "preview", start: 0.8, end: 1.3 },
    { word: "of", start: 1.3, end: 1.4 },
    { word: "the", start: 1.4, end: 1.5 },
    { word: "captions.", start: 1.5, end: 2.2 },
  ],
  question: "Would you have shown up?",
  voiceEnd: 3,
};

export const Root: React.FC = () => (
  <Composition
    id="Short"
    component={Short}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={preview.durationInFrames}
    defaultProps={preview}
    calculateMetadata={({ props }) => ({ durationInFrames: props.durationInFrames })}
  />
);
