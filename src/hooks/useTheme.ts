/**
 * React hook for managing theme state.
 */

import { useState, useCallback } from "react";
import type { ThemeName } from "../types/theme.js";
import { getAvailableThemes } from "../themes/index.js";

interface UseThemeReturn {
  /** Current theme name */
  theme: ThemeName;
  /** Set the theme */
  setTheme: (name: ThemeName) => void;
  /** Cycle to the next available theme */
  nextTheme: () => void;
  /** List available theme names */
  availableThemes: ThemeName[];
}

export function useTheme(initialTheme: ThemeName = "shisha"): UseThemeReturn {
  const [theme, setThemeState] = useState<ThemeName>(initialTheme);
  const availableThemes = getAvailableThemes();

  const setTheme = useCallback((name: ThemeName) => {
    if (availableThemes.includes(name)) {
      setThemeState(name);
    }
  }, [availableThemes]);

  const nextTheme = useCallback(() => {
    const currentIndex = availableThemes.indexOf(theme);
    const nextIndex = (currentIndex + 1) % availableThemes.length;
    setThemeState(availableThemes[nextIndex]);
  }, [theme, availableThemes]);

  return {
    theme,
    setTheme,
    nextTheme,
    availableThemes,
  };
}
