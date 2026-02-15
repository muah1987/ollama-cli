/**
 * Base theme interface and utility for Arabic-themed progress indicators.
 */

import type { OperationPhase, ThemeMap, ThemeStage } from "../types/theme.js";

/** Base theme with sensible defaults */
export const BASE_THEME: ThemeMap = {
  analyzing: {
    emoji: "🔍",
    messageEn: "Analyzing...",
    messageAr: "جارٍ التحليل...",
  },
  planning: {
    emoji: "💭",
    messageEn: "Planning...",
    messageAr: "جارٍ التخطيط...",
  },
  implementing: {
    emoji: "⚡",
    messageEn: "Implementing...",
    messageAr: "جارٍ التنفيذ...",
  },
  testing: {
    emoji: "🧪",
    messageEn: "Testing...",
    messageAr: "جارٍ الاختبار...",
  },
  reviewing: {
    emoji: "📝",
    messageEn: "Reviewing...",
    messageAr: "جارٍ المراجعة...",
  },
  complete: {
    emoji: "✅",
    messageEn: "Complete!",
    messageAr: "اكتمل!",
  },
  error: {
    emoji: "❌",
    messageEn: "Error occurred",
    messageAr: "حدث خطأ",
  },
};

/**
 * Get the themed stage for a given phase, falling back to base theme.
 */
export function getBaseStage(phase: OperationPhase): ThemeStage {
  return BASE_THEME[phase];
}
