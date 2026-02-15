/**
 * Theme registry - Maps theme names to their stage definitions.
 */

import type { OperationPhase, ThemeMap, ThemeName, ThemeStage } from "../types/theme.js";
import { BASE_THEME } from "./base.js";
import { CARAVAN_THEME } from "./caravan.js";
import { QAHWA_THEME } from "./qahwa.js";
import { SCHOLARLY_THEME } from "./scholarly.js";
import { SHISHA_THEME } from "./shisha.js";

/** All available themes */
const THEMES: Record<ThemeName, ThemeMap> = {
  caravan: CARAVAN_THEME,
  shisha: SHISHA_THEME,
  qahwa: QAHWA_THEME,
  scholarly: SCHOLARLY_THEME,
};

/**
 * Get the themed stage for a given theme and phase.
 * Falls back to the base theme if the theme is unknown.
 */
export function getThemeStage(
  themeName: ThemeName,
  phase: OperationPhase,
): ThemeStage {
  const theme = THEMES[themeName];
  if (theme && theme[phase]) {
    return theme[phase];
  }
  return BASE_THEME[phase];
}

/**
 * Get all available theme names.
 */
export function getAvailableThemes(): ThemeName[] {
  return Object.keys(THEMES) as ThemeName[];
}

/**
 * Get the full theme map for a theme name.
 */
export function getTheme(themeName: ThemeName): ThemeMap {
  return THEMES[themeName] ?? BASE_THEME;
}

export { BASE_THEME, CARAVAN_THEME, QAHWA_THEME, SCHOLARLY_THEME, SHISHA_THEME };
