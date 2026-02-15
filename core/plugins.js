/**
 * Tool plugin system.
 *
 * Loads custom tools from .qarin/tools/ (JS modules).
 * Each plugin must export: { name, description, parameters, execute }
 * Schemas are validated at load time.
 */
import { readdir } from "node:fs/promises";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";
import { z } from "zod";
const PLUGINS_DIR = ".qarin/tools";
/** Schema for a valid plugin export */
const PluginSchema = z.object({
    name: z.string().min(1),
    description: z.string().min(1),
    parameters: z.object({
        type: z.literal("object"),
        properties: z.record(z.any()),
    }).passthrough(),
    execute: z.function(),
});
/**
 * Plugin registry -- loads and manages custom tool plugins.
 */
export class PluginRegistry {
    plugins = new Map();
    toolDefinitions = [];
    loadErrors = [];
    /** Load all plugins from .qarin/tools/ */
    async load(projectDir) {
        const dir = resolve(projectDir ?? process.env.QARIN_PROJECT_DIR ?? process.cwd(), PLUGINS_DIR);
        try {
            const files = await readdir(dir);
            const jsFiles = files.filter((f) => f.endsWith(".js") || f.endsWith(".mjs"));
            for (const file of jsFiles) {
                await this.loadPlugin(join(dir, file));
            }
        }
        catch {
            // No plugins directory, that's fine
        }
    }
    /** Load a single plugin file */
    async loadPlugin(filePath) {
        try {
            const fileUrl = pathToFileURL(resolve(filePath)).href;
            const mod = await import(fileUrl);
            const exported = mod.default ?? mod;
            // Validate schema
            const parsed = PluginSchema.safeParse(exported);
            if (!parsed.success) {
                this.loadErrors.push({
                    file: filePath,
                    error: `Schema validation failed: ${parsed.error.issues.map((i) => i.message).join(", ")}`,
                });
                return;
            }
            const plugin = parsed.data;
            // Wrap execute to catch errors
            const safePlugin = {
                name: plugin.name,
                description: plugin.description,
                parameters: plugin.parameters,
                execute: async (args) => {
                    try {
                        const result = await plugin.execute(args);
                        return {
                            success: true,
                            output: typeof result === "string" ? result : JSON.stringify(result),
                        };
                    }
                    catch (err) {
                        return {
                            success: false,
                            output: "",
                            error: `Plugin ${plugin.name} failed: ${err instanceof Error ? err.message : String(err)}`,
                        };
                    }
                },
            };
            this.plugins.set(plugin.name, safePlugin);
            this.toolDefinitions.push({
                name: plugin.name,
                description: plugin.description,
                parameters: plugin.parameters,
            });
        }
        catch (err) {
            this.loadErrors.push({
                file: filePath,
                error: err instanceof Error ? err.message : String(err),
            });
        }
    }
    /** Get a plugin by name */
    get(name) {
        return this.plugins.get(name);
    }
    /** Get tool definitions for API calls (to merge with built-ins) */
    getToolDefinitions() {
        return this.toolDefinitions;
    }
    /** Get all registered plugin names */
    getPluginNames() {
        return [...this.plugins.keys()];
    }
    /** Check if any plugins loaded with errors */
    hasErrors() {
        return this.loadErrors.length > 0;
    }
    /** Get load errors */
    getErrors() {
        return [...this.loadErrors];
    }
    /** Get total plugin count */
    get size() {
        return this.plugins.size;
    }
}
//# sourceMappingURL=plugins.js.map
