import "@fontsource/nunito/900.css";
import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { brand } from "./brand";
import { Captions, Word } from "./components/Captions";
import { EndCard } from "./components/EndCard";
import { Footage, Shot } from "./components/Footage";
import { HookCard } from "./components/HookCard";
import { Watermark } from "./components/Watermark";

export type ShortProps = {
  durationInFrames: number;
  audio: string;
  shots: Shot[];
  words: Word[];
  hookCard: string;
  question: string;
  voiceEnd: number; // seconds
};

export const Short: React.FC<ShortProps> = ({ audio, shots, words, hookCard, question, voiceEnd }) => {
  const { fps, durationInFrames } = useVideoConfig();
  const endFrom = Math.max(0, durationInFrames - Math.round(brand.endCard.seconds * fps));
  // The spoken question is shown by the end card, so captions stop where the question starts.
  const qWords = question.split(/\s+/).length;
  const qStart = words.length > qWords ? words[words.length - qWords].start : voiceEnd;
  const captionsEnd = Math.min(qStart, endFrom / fps);
  // The hook card carries the first sentence, so captions begin with the second sentence.
  const hookEndIdx = words.findIndex((w) => /[.?!]["']?$/.test(w.word));
  const captionsStart = hookEndIdx >= 0 && hookEndIdx + 1 < words.length ? words[hookEndIdx + 1].start - 0.05 : 0;

  return (
    <AbsoluteFill style={{ backgroundColor: brand.colors.plum }}>
      <Footage shots={shots} />
      <Watermark />
      <Captions words={words} showFrom={captionsStart} hideAfter={captionsEnd} />
      <Sequence durationInFrames={Math.round(brand.hookCard.seconds * fps)}>
        <HookCard text={hookCard} />
      </Sequence>
      <Sequence from={Math.min(endFrom, Math.round(qStart * fps))}>
        <EndCard question={question} />
      </Sequence>
      {audio ? <Audio src={staticFile(audio)} /> : null}
    </AbsoluteFill>
  );
};
