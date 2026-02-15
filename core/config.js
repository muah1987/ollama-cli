/**
 * Hierarchical configuration system.
 *
 * Priority (highest to lowest):
 * 1. CLI flags
 * 2. Project config: .qarin/config.json
 * 3. Global config: ~/.config/qarin/config.json
 * 4. Built-in defaults
 */
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { resolve, join, dirname } from "node:path";
import { homedir } from "node:os";
const GLOBAL_CONFIG_PATH = join(homedir(), ".config", "qarin", "config.json");
const PROJECT_CONFIG_PATH = ".qarin/config.json";
/** Built-in defaults */
const DEFAULTS = {
    model: "claude-sonnet-4-20250514",
    provider: "anthropic",
    theme: "shisha",
    outputFormat: "text",
    chain: false,
    maxRounds: 10,
    contextMax: 128_000,
    compactThreshold: 0.85,
    tokenBudget: null,
    tokenBudgetDistribution: {
        analysis: 0.10,
        plan_validate_optimize: 0.20,
        execution: 0.50,
        finalize: 0.20,
    },
    hooks: {},
    plugins: { enabled: true },
    logging: {
        level: "info",
        file: ".qarin/qarin.log",
        maxSize: 5_000_000,
    },
};
/**
 * Load a JSON config file, returning null if not found.
 */
async function loadJsonFile(path) {
    try {
        const content = await readFile(resolve(path), "utf-8");
        return JSON.parse(content);
    }
    catch {
        return null;
    }
}
/**
 * Deep merge two objects. Source values override target.
 */
function deepMerge(target, source) {
    const result = { ...target };
    for (const key of Object.keys(source)) {
        if (source[key] !== undefined &&
            source[key] !== null &&
            typeof source[key] === "object" &&
            !Array.isArray(source[key]) &&
            typeof result[key] === "object" &&
            !Array.isArray(result[key])) {
            result[key] = deepMerge(result[key], source[key]);
        }
        else {
            result[key] = source[key];
        }
    }
    return result;
}
/**
 * Configuration manager with hierarchical loading.
 */
export class Config {
    _resolved = null;
    _global = null;
    _project = null;
    _cli = {};
    /**
     * Load configuration from all sources.
     */
    async load(cliOverrides = {}) {
        this._cli = cliOverrides;
        // Load global config
        this._global = await loadJsonFile(GLOBAL_CONFIG_PATH);
        // Load project config
        const projectDir = process.env.QARIN_PROJECT_DIR ?? process.cwd();
        this._project = await loadJsonFile(join(projectDir, PROJECT_CONFIG_PATH));
        // Merge: defaults < global < project < cli
        let merged = { ...DEFAULTS };
        if (this._global)
            merged = deepMerge(merged, this._global);
        if (this._project)
            merged = deepMerge(merged, this._project);
        // CLI overrides (only non-undefined values)
        const cleanCli = {};
        for (const [key, value] of Object.entries(this._cli)) {
            if (value !== undefined)
                cleanCli[key] = value;
        }
        merged = deepMerge(merged, cleanCli);
        this._resolved = merged;
        return merged;
    }
    /** Get a config value by dot-notation key */
    get(key) {
        if (!this._resolved)
            return undefined;
        const parts = key.split(".");
        let current = this._resolved;
        for (const part of parts) {
            if (current == null || typeof current !== "object")
                return undefined;
            current = current[part];
        }
        return current;
    }
    /** Set a config value (writes to project config) */
    async set(key, value) {
        const projectDir = process.env.QARIN_PROJECT_DIR ?? process.cwd();
        const configPath = resolve(join(projectDir, PROJECT_CONFIG_PATH));
        // Load existing project config
        let config = (await loadJsonFile(configPath)) ?? {};
        // Set nested value
        const parts = key.split(".");
        let current = config;
        for (let i = 0; i < parts.length - 1; i++) {
            if (!current[parts[i]] || typeof current[parts[i]] !== "object") {
                current[parts[i]] = {};
            }
            current = current[parts[i]];
        }
        current[parts[parts.length - 1]] = value;
        // Write back
        await mkdir(dirname(configPath), { recursive: true });
        await writeFile(configPath, JSON.stringify(config, null, 2));
        // Reload
        await this.load(this._cli);
    }
    /** Get the full resolved config */
    getAll() {
        return this._resolved ? { ...this._resolved } : { ...DEFAULTS };
    }
    /** Get defaults */
    static getDefaults() {
        return { ...DEFAULTS };
    }
    /** Get the global config path */
    static get globalConfigPath() {
        return GLOBAL_CONFIG_PATH;
    }
    /** Get the project config path */
    static get projectConfigPath() {
        return PROJECT_CONFIG_PATH;
    }
}
//# sourceMappingURL=config.js.map
