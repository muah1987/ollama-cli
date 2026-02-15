/**
 * ☕ Arabic Coffee (Qahwa) theme - Progress as preparing traditional coffee.
 */

import type { ThemeMap } from "../types/theme.js";

export const QAHWA_THEME: ThemeMap = {
  analyzing: {
    emoji: "🫘",
    messageEn: "Selecting the finest beans",
    messageAr: "اختيار أجود الحبوب",
  },
  planning: {
    emoji: "⚗️",
    messageEn: "Measuring cardamom and saffron",
    messageAr: "قياس الهيل والزعفران",
  },
  implementing: {
    emoji: "☕",
    messageEn: "Brewing in the dallah",
    messageAr: "التحضير في الدلّة",
  },
  testing: {
    emoji: "👃",
    messageEn: "Testing the aroma",
    messageAr: "اختبار الرائحة",
  },
  reviewing: {
    emoji: "🫖",
    messageEn: "Pouring with care",
    messageAr: "الصب بعناية",
  },
  complete: {
    emoji: "🏆",
    messageEn: "Qahwa is ready! تفضّل",
    messageAr: "!القهوة جاهزة! تفضّل",
  },
  error: {
    emoji: "🔥",
    messageEn: "Overheated! Adjusting flame",
    messageAr: "!سخنت كثيراً! تعديل اللهب",
  },
};
