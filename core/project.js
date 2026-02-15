/**
 * Project context evolution module.
 *
 * Manages QARIN.md: reads structured sections, injects relevant
 * context based on intent, and appends session summaries at session
 * end (opt-in via settings).
 */
import { readFile, writeFile, access } from "node:fs/promises";
import { resolve } from "node:path";
const QARIN_MD = "QARIN.md";
/**
 * Parse QARIN.md into structured sections.
 *
 * Sections are delimited by ## headings.
 */
function parseSections(content) {
    const sections = new Map();
    const lines = content.split("\n");
    let currentSection = "preamble";
    let currentContent = [];
    for (const line of lines) {
        const headingMatch = line.match(/^##\s+(.+)/);
        if (headingMatch) {
            // Save previous section
            if (currentContent.length > 0) {
                sections.set(currentSection, currentContent.join("\n").trim());
            }
            currentSection = headingMatch[1].trim().toLowerCase();
            currentContent = [];
        }
        else {
            currentContent.push(line);
        }
    }
    // Save last section
    if (currentContent.length > 0) {
        sections.set(currentSection, currentContent.join("\n").trim());
    }
    return sections;
}
/**
 * Determine which sections are relevant for a given intent.
 */
function relevantSections(intent) {
    const mapping = {
        code: ["architecture", "conventions", "patterns", "dependencies", "structure"],
        debug: ["known issues", "debugging", "common errors", "architecture"],
        test: ["testing", "test patterns", "conventions"],
        review: ["conventions", "patterns", "architecture", "security"],
        plan: ["architecture", "roadmap", "goals", "decisions"],
        docs: ["documentation", "conventions", "api"],
        research: ["architecture", "decisions", "goals"],
        orchestrator: ["architecture", "workflows", "deployment"],
        team: ["team", "roles", "conventions"],
    };
    return mapping[intent] ?? ["architecture", "conventions"];
}
/**
 * Project context manager for QARIN.md.
 */
export class ProjectContext {
    projectDir;
    filePath;
    sections = null;
    rawContent = null;
    constructor(projectDir) {
        this.projectDir = projectDir ?? process.env.QARIN_PROJECT_DIR ?? process.cwd();
        this.filePath = resolve(this.projectDir, QARIN_MD);
    }
    /** Check if QARIN.md exists */
    async exists() {
        try {
            await access(this.filePath);
            return true;
        }
        catch {
            return false;
        }
    }
    /** Load and parse QARIN.md */
    async load() {
        try {
            this.rawContent = await readFile(this.filePath, "utf-8");
            this.sections = parseSections(this.rawContent);
        }
        catch {
            this.rawContent = null;
            this.sections = null;
        }
    }
    /**
     * Build a selective context injection based on intent.
     *
     * Only includes sections relevant to the current task type.
     */
    async buildInjection(intentType) {
        if (!this.sections)
            await this.load();
        if (!this.sections || this.sections.size === 0)
            return null;
        const relevant = relevantSections(intentType);
        const included = [];
        for (const sectionName of relevant) {
            // Fuzzy match section names
            for (const [key, value] of this.sections) {
                if (key.includes(sectionName) || sectionName.includes(key)) {
                    if (value.length > 0) {
                        included.push(`## ${key}\n${value}`);
                    }
                }
            }
        }
        if (included.length === 0) {
            // Fall back to preamble if no sections matched
            const preamble = this.sections.get("preamble");
            if (preamble)
                return `[Project context from QARIN.md]\n${preamble}`;
            return null;
        }
        return `[Project context from QARIN.md]\n${included.join("\n\n")}`;
    }
    /**
     * Append a session summary to QARIN.md.
     *
     * Adds a new entry under the ## Session History section.
     */
    async appendSessionSummary(summary) {
        if (!this.rawContent)
            await this.load();
        const timestamp = new Date().toISOString().split("T")[0];
        const entry = `\n### ${timestamp} - Session Summary\n\n${summary}\n`;
        if (this.rawContent) {
            // Check if Session History section exists
            if (this.rawContent.includes("## Session History")) {
                // Append to existing section
                const updated = this.rawContent.replace(/(## Session History\n)/, `$1${entry}`);
                await writeFile(this.filePath, updated);
                this.rawContent = updated;
            }
            else {
                // Add new section at the end
                const updated = this.rawContent + `\n## Session History\n${entry}`;
                await writeFile(this.filePath, updated);
                this.rawContent = updated;
            }
        }
        else {
            // Create new QARIN.md
            const content = `# QARIN Project Context\n\n## Session History\n${entry}`;
            await writeFile(this.filePath, content);
            this.rawContent = content;
        }
        this.sections = parseSections(this.rawContent);
    }
    /** Get all sections */
    getSections() {
        return this.sections ? new Map(this.sections) : new Map();
    }
    /** Get full raw content */
    getRawContent() {
        return this.rawContent;
    }
}
//# sourceMappingURL=project.js.map
