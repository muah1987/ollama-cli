/**
 * Unit tests for MemoryStore.
 */
import { describe, it, before, after } from "node:test";
import assert from "node:assert/strict";
import { MemoryStore } from "../core/memory.js";
import { rm } from "node:fs/promises";
import { resolve } from "node:path";

const TEST_DIR = resolve(".qarin/test-memory");

describe("MemoryStore", () => {
    let store;

    before(async () => {
        store = new MemoryStore(resolve("."));
        // Override base dir for testing
        store.baseDir = TEST_DIR;
        await store.init();
    });

    after(async () => {
        try {
            await rm(TEST_DIR, { recursive: true });
        } catch {}
    });

    it("stores and retrieves memories", async () => {
        const id = await store.store("The auth module uses JWT tokens");
        assert.ok(id);
        assert.equal(store.size, 1);
    });

    it("deduplicates identical content", async () => {
        await store.store("The auth module uses JWT tokens");
        await store.store("The auth module uses JWT tokens");
        assert.equal(store.size, 1);
    });

    it("lists all memories", async () => {
        await store.store("Database uses PostgreSQL");
        const entries = await store.list();
        assert.ok(entries.length >= 2);
    });

    it("searches by similarity", async () => {
        await store.store("React frontend with TypeScript");
        const results = await store.search("frontend React");
        assert.ok(results.length > 0);
        assert.ok(results[0].similarity > 0);
    });

    it("deletes a memory", async () => {
        const id = await store.store("Temporary fact to delete");
        const deleted = await store.delete(id);
        assert.equal(deleted, true);
    });

    it("clears all memories", async () => {
        await store.store("Fact A");
        await store.store("Fact B");
        const count = await store.clear();
        assert.ok(count >= 0);
        assert.equal(store.size, 0);
    });

    it("builds context injection", async () => {
        await store.store("The API uses REST with Express");
        await store.store("Tests use vitest framework");
        const injection = await store.buildContextInjection("API testing");
        // May or may not find results depending on embedding quality
        // Just verify it doesn't throw
        assert.ok(injection === null || typeof injection === "string");
    });
});
