/**
 * React hook for managing theme state.
 */
import type { ThemeName } from "../types/theme.js";
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
export declare function useTheme(initialTheme?: ThemeName): UseThemeReturn;
export {};
//# sourceMappingURL=useTheme.d.ts.map