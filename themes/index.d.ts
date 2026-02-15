/**
 * Theme registry - Maps theme names to their stage definitions.
 */
import type { OperationPhase, ThemeMap, ThemeName, ThemeStage } from "../types/theme.js";
import { BASE_THEME } from "./base.js";
import { CARAVAN_THEME } from "./caravan.js";
import { QAHWA_THEME } from "./qahwa.js";
import { SCHOLARLY_THEME } from "./scholarly.js";
import { SHISHA_THEME } from "./shisha.js";
/**
 * Get the themed stage for a given theme and phase.
 * Falls back to the base theme if the theme is unknown.
 */
export declare function getThemeStage(themeName: ThemeName, phase: OperationPhase): ThemeStage;
/**
 * Get all available theme names.
 */
export declare function getAvailableThemes(): ThemeName[];
/**
 * Get the full theme map for a theme name.
 */
export declare function getTheme(themeName: ThemeName): ThemeMap;
export { BASE_THEME, CARAVAN_THEME, QAHWA_THEME, SCHOLARLY_THEME, SHISHA_THEME };
//# sourceMappingURL=index.d.ts.map