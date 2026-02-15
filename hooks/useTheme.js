/**
 * React hook for managing theme state.
 */
import { useState, useCallback } from "react";
import { getAvailableThemes } from "../themes/index.js";
export function useTheme(initialTheme = "shisha") {
    const [theme, setThemeState] = useState(initialTheme);
    const availableThemes = getAvailableThemes();
    const setTheme = useCallback((name) => {
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
//# sourceMappingURL=useTheme.js.map