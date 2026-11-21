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
    fontSize: 92,
    centerY: 0.64, // 0 = top, 1 = bottom. Kept above the Shorts buttons.
    strokePx: 10, // dark outline around caption text
  },

  hookCard: {
    seconds: 2.0, // how long the hook card stays up at the start (captions start after it)
    top: 1000, // distance from the top in pixels; lower third keeps faces visible
    fontSize: 84,
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
