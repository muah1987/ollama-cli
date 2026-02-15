/**
 * Long-term memory system.
 *
 * Persists facts, decisions, and project knowledge across sessions
 * in .qarin/memory/. Uses LLM-based embedding via the active provider
 * for similarity search and top-K retrieval.
 *
 * Storage format: one JSON file per memory entry in .qarin/memory/
 * Each entry: { id, content, embedding, tags, timestamp, sessionId }
 *
 * Supports /memory list, /memory search <query>, /memory clear commands.
 */
import { readdir, readFile, writeFile, mkdir, rm } from "node:fs/promises";
import { resolve, join } from "node:path";
import { createHash } from "node:crypto";
const MEMORY_DIR = ".qarin/memory";
/**
 * Generate a content hash as a stable ID.
 */
function memoryId(content) {
    return createHash("sha256").update(content).digest("hex").slice(0, 16);
}
/**
 * Simple cosine similarity between two vectors.
 */
function cosineSimilarity(a, b) {
    if (a.length !== b.length || a.length === 0)
        return 0;
    let dotProduct = 0;
    let normA = 0;
    let normB = 0;
    for (let i = 0; i < a.length; i++) {
        dotProduct += a[i] * b[i];
        normA += a[i] * a[i];
        normB += b[i] * b[i];
    }
    const denominator = Math.sqrt(normA) * Math.sqrt(normB);
    return denominator === 0 ? 0 : dotProduct / denominator;
}
/**
 * Lightweight bag-of-words embedding for fallback when no LLM
 * embedding endpoint is available.
 *
 * Creates a 256-dimensional vector from character trigram hashes.
 */
function localEmbed(text) {
    const dims = 256;
    const vec = new Float64Array(dims);
    const lower = text.toLowerCase().replace(/[^a-z0-9 ]/g, "");
    const words = lower.split(/\s+/).filter(Boolean);
    // Word-level features
    for (const word of words) {
        const hash = createHash("md5").update(word).digest();
        for (let i = 0; i < Math.min(hash.length, dims); i++) {
            vec[i % dims] += hash[i] / 255;
        }
    }
    // Trigram features
    for (let i = 0; i < lower.length - 2; i++) {
        const trigram = lower.slice(i, i + 3);
        const hash = createHash("md5").update(trigram).digest();
        const idx = (hash[0] * 256 + hash[1]) % dims;
        vec[idx] += 1;
    }
    // L2 normalize
    let norm = 0;
    for (let i = 0; i < dims; i++) {
        norm += vec[i] * vec[i];
    }
    norm = Math.sqrt(norm);
    if (norm > 0) {
        for (let i = 0; i < dims; i++) {
            vec[i] /= norm;
        }
    }
    return Array.from(vec);
}
/**
 * Memory store for persisting and retrieving facts across sessions.
 */
export class MemoryStore {
    baseDir;
    entries = new Map();
    loaded = false;
    constructor(projectDir) {
        this.baseDir = resolve(projectDir ?? process.env.QARIN_PROJECT_DIR ?? process.cwd(), MEMORY_DIR);
    }
    /** Ensure the memory directory exists */
    async init() {
        await mkdir(this.baseDir, { recursive: true });
    }
    /** Load all memory entries from disk */
    async load() {
        await this.init();
        try {
            const files = await readdir(this.baseDir);
            const jsonFiles = files.filter((f) => f.endsWith(".json"));
            for (const file of jsonFiles) {
                try {
                    const content = await readFile(join(this.baseDir, file), "utf-8");
                    const entry = JSON.parse(content);
                    if (entry.id && entry.content) {
                        this.entries.set(entry.id, entry);
                    }
                }
                catch {
                    // Skip corrupted files
                }
            }
            this.loaded = true;
        }
        catch {
            this.loaded = true;
        }
    }
    /** Store a new memory entry */
    async store(content, options) {
        if (!this.loaded)
            await this.load();
        const id = memoryId(content);
        // Don't duplicate
        if (this.entries.has(id))
            return id;
        const embedding = localEmbed(content);
        const entry = {
            id,
            content,
            embedding,
            tags: options?.tags ?? [],
            timestamp: new Date().toISOString(),
            sessionId: options?.sessionId ?? null,
            source: options?.source ?? "user",
        };
        this.entries.set(id, entry);
        await this.init();
        await writeFile(join(this.baseDir, `${id}.json`), JSON.stringify(entry, null, 2));
        return id;
    }
    /** Search memories by semantic similarity */
    async search(query, topK = 5) {
        if (!this.loaded)
            await this.load();
        const queryEmbedding = localEmbed(query);
        const scored = [];
        for (const entry of this.entries.values()) {
            const similarity = cosineSimilarity(queryEmbedding, entry.embedding);
            scored.push({ entry, similarity });
        }
        scored.sort((a, b) => b.similarity - a.similarity);
        return scored.slice(0, topK).map((s) => ({
            id: s.entry.id,
            content: s.entry.content,
            similarity: s.similarity,
            tags: s.entry.tags,
            timestamp: s.entry.timestamp,
        }));
    }
    /** List all memories */
    async list() {
        if (!this.loaded)
            await this.load();
        return Array.from(this.entries.values()).map((e) => ({
            id: e.id,
            content: e.content.slice(0, 100),
            tags: e.tags,
            timestamp: e.timestamp,
        }));
    }
    /** Delete a memory by ID */
    async delete(id) {
        if (!this.loaded)
            await this.load();
        if (!this.entries.has(id))
            return false;
        this.entries.delete(id);
        try {
            const { unlink } = await import("node:fs/promises");
            await unlink(join(this.baseDir, `${id}.json`));
        }
        catch { }
        return true;
    }
    /** Clear all memories */
    async clear() {
        if (!this.loaded)
            await this.load();
        const ids = [...this.entries.keys()];
        for (const id of ids) {
            await this.delete(id);
        }
        return ids.length;
    }
    /** Get memory count */
    get size() {
        return this.entries.size;
    }
    /**
     * Build a context injection string from top-K relevant memories.
     *
     * Used to inject into the system message for long-term awareness.
     */
    async buildContextInjection(query, topK = 3) {
        const results = await this.search(query, topK);
        if (results.length === 0)
            return null;
        const relevantResults = results.filter((r) => r.similarity > 0.1);
        if (relevantResults.length === 0)
            return null;
        const lines = relevantResults.map((r) => `- ${r.content} [${r.tags.join(", ")}]`);
        return `[Long-term memory - ${relevantResults.length} relevant entries]\n${lines.join("\n")}`;
    }
}
//# sourceMappingURL=memory.js.map
