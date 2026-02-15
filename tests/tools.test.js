/**
 * Unit tests for tool functions.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { fileRead, fileWrite, fileEdit, grepSearch, isDestructiveCommand, getWorkingDir, setWorkingDir } from "../core/tools.js";
import { writeFile, unlink, mkdir } from "node:fs/promises";
import { resolve } from "node:path";

const TEST_DIR = resolve(".qarin/test-tmp");
const TEST_FILE = resolve(TEST_DIR, "test-file.txt");

describe("Tools", () => {
    it("fileRead reads existing files", async () => {
        await mkdir(TEST_DIR, { recursive: true });
        await writeFile(TEST_FILE, "hello world");
        const result = await fileRead(TEST_FILE);
        assert.equal(result.success, true);
        assert.equal(result.output, "hello world");
        await unlink(TEST_FILE);
    });

    it("fileRead fails on missing files", async () => {
        const result = await fileRead("/tmp/qarin-nonexistent-file.txt");
        assert.equal(result.success, false);
        assert.ok(result.error.includes("Failed to read"));
    });

    it("fileWrite creates files with directories", async () => {
        const path = resolve(TEST_DIR, "subdir", "new-file.txt");
        const result = await fileWrite(path, "test content");
        assert.equal(result.success, true);
        const read = await fileRead(path);
        assert.equal(read.output, "test content");
        await unlink(path);
    });

    it("fileEdit edits line ranges", async () => {
        await writeFile(TEST_FILE, "line1\nline2\nline3\nline4");
        const result = await fileEdit(TEST_FILE, 2, 3, "replaced");
        assert.equal(result.success, true);
        const read = await fileRead(TEST_FILE);
        assert.ok(read.output.includes("replaced"));
        assert.ok(!read.output.includes("line2"));
        await unlink(TEST_FILE);
    });

    it("fileEdit rejects invalid ranges", async () => {
        await writeFile(TEST_FILE, "line1\nline2");
        const result = await fileEdit(TEST_FILE, 5, 10, "nope");
        assert.equal(result.success, false);
        assert.ok(result.error.includes("Invalid line range"));
        await unlink(TEST_FILE);
    });

    it("isDestructiveCommand detects rm -rf", () => {
        assert.equal(isDestructiveCommand("rm -rf /tmp"), true);
        assert.equal(isDestructiveCommand("rm -rf /"), true);
    });

    it("isDestructiveCommand detects git push --force", () => {
        assert.equal(isDestructiveCommand("git push --force"), true);
    });

    it("isDestructiveCommand allows safe commands", () => {
        assert.equal(isDestructiveCommand("ls -la"), false);
        assert.equal(isDestructiveCommand("git status"), false);
        assert.equal(isDestructiveCommand("npm install"), false);
    });

    it("working directory tracker works", () => {
        const original = getWorkingDir();
        setWorkingDir("/tmp");
        assert.equal(getWorkingDir(), "/tmp");
        setWorkingDir(original);
    });
});
