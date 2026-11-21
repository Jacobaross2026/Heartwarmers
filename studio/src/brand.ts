/**
 * WARM HEARTS DAILY - BRAND SETTINGS
 * Change anything here and every future video follows. One place, whole channel.
 */
export const brand = {
  channelName: "Warm Hearts Daily",
  handle: "@WarmHeartsDailyTV",

  colors: {
    plum: "#2B1B3D", // hook card + end card background
    cream: "#FFF8F0", // main text
    coral: "#FF6B6B", // highlighted (currently spoken) word
    gold: "#FFC857", // heart icon / accents
  },

  font: {
    family: "Nunito",
    weight: 900,
  },

  captions: {
    wordsPerLine: 3, // how many words show at once
    fontSize: 78,
    centerY: 0.69, // 0 = top, 1 = bottom. Kept above the Shorts title and buttons.
    strokePx: 9, // dark outline around caption text
  },

  hook: {
    // The opening sentence: same caption style, shown in full from the first frame.
    scale: 1.25, // how much bigger than normal captions
  },

  endCard: {
    seconds: 1.2, // hold after the voice ends; must match END_CARD in pipeline/config.py
    cta: "Tell us in the comments",
    follow: "Follow for a little kindness every day",
  },

  // gentle "warm" color grade applied to all footage
  footageFilter: "saturate(1.08) contrast(1.04) sepia(0.10) brightness(1.02)",
  slowZoom: 0.07, // each shot slowly zooms in by 7%
};
