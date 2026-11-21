import "@fontsource/nunito/700.css";
import "@fontsource/nunito/900.css";
import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { brand } from "./brand";
import { Captions, Word } from "./components/Captions";
import { EndCard } from "./components/EndCard";
import { Footage, Shot } from "./components/Footage";
import { Watermark } from "./components/Watermark";

export type ShortProps = {
  durationInFrames: number;
  audio: string;
  shots: Shot[];
  words: Word[];
  question: string;
  voiceEnd: number; // seconds
};

export const Short: React.FC<ShortProps> = ({ audio, shots, words, question, voiceEnd }) => {
  const { fps, durationInFrames } = useVideoConfig();
  const endFrom = Math.max(0, durationInFrames - Math.round(brand.endCard.seconds * fps));
  // The spoken question is shown by the end card, so captions stop where the question starts.
  const qWords = question.split(/\s+/).length;
  const qStart = words.length > qWords ? words[words.length - qWords].start : voiceEnd;
  const captionsEnd = Math.min(qStart, endFrom / fps);

  return (
    <AbsoluteFill style={{ backgroundColor: brand.colors.plum }}>
      <Footage shots={shots} />
      <Watermark />
      <Captions words={words} hideAfter={captionsEnd} />
      <Sequence from={Math.min(endFrom, Math.round(qStart * fps))}>
        <EndCard question={question} />
      </Sequence>
      {audio ? <Audio src={staticFile(audio)} /> : null}
    </AbsoluteFill>
  );
};
