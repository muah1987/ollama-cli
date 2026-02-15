import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { writeFile, mkdir, rm } from "node:fs/promises";
import { join } from "node:path";
import { fileRead, fileWrite, fileEdit, shellExec, grepSearch, executeTool } from "./tools.js";

const TEST_DIR = "/tmp/qarin-test-tools";

describe("tools", () => {
  // Set up test directory
  it("setup", async () => {
    await mkdir(TEST_DIR, { recursive: true });
    await writeFile(join(TEST_DIR, "test.txt"), "line1\nline2\nline3\n");
  });

  describe("fileRead", () => {
    it("reads existing file", async () => {
      const result = await fileRead(join(TEST_DIR, "test.txt"));
      assert.equal(result.success, true);
      assert.ok(result.output.includes("line1"));
    });

    it("fails on missing file", async () => {
      const result = await fileRead(join(TEST_DIR, "nonexistent.txt"));
      assert.equal(result.success, false);
      assert.ok(result.error);
    });
  });

  describe("fileWrite", () => {
    it("writes new file", async () => {
      const result = await fileWrite(join(TEST_DIR, "written.txt"), "hello world");
      assert.equal(result.success, true);
      assert.ok(result.output.includes("11 bytes"));
    });

    it("creates directories as needed", async () => {
      const result = await fileWrite(join(TEST_DIR, "sub/dir/deep.txt"), "nested");
      assert.equal(result.success, true);
    });
  });

  describe("fileEdit", () => {
    it("edits line range", async () => {
      await writeFile(join(TEST_DIR, "edit.txt"), "a\nb\nc\nd\n");
      const result = await fileEdit(join(TEST_DIR, "edit.txt"), 2, 3, "X\nY");
      assert.equal(result.success, true);
    });

    it("fails on invalid line range", async () => {
      const result = await fileEdit(join(TEST_DIR, "edit.txt"), 99, 100, "X");
      assert.equal(result.success, false);
    });
  });

  describe("shellExec", () => {
    it("executes simple commands", async () => {
      const result = await shellExec("echo hello");
      assert.equal(result.success, true);
      assert.ok(result.output.includes("hello"));
    });

    it("captures failures", async () => {
      const result = await shellExec("false");
      assert.equal(result.success, false);
    });
  });

  describe("grepSearch", () => {
    it("finds pattern in files", async () => {
      const result = await grepSearch("line2", TEST_DIR);
      assert.equal(result.success, true);
      assert.ok(result.output.includes("line2"));
    });

    it("returns no matches gracefully", async () => {
      const result = await grepSearch("zzzznonexistent", TEST_DIR);
      assert.equal(result.success, true);
      assert.ok(result.output.includes("No matches"));
    });
  });

  describe("executeTool", () => {
    it("dispatches file_read", async () => {
      const result = await executeTool("file_read", { path: join(TEST_DIR, "test.txt") });
      assert.equal(result.success, true);
    });

    it("dispatches shell_exec", async () => {
      const result = await executeTool("shell_exec", { command: "echo dispatch" });
      assert.equal(result.success, true);
      assert.ok(result.output.includes("dispatch"));
    });

    it("returns error for unknown tool", async () => {
      const result = await executeTool("nonexistent_tool", {});
      assert.equal(result.success, false);
      assert.ok(result.error?.includes("Unknown tool"));
    });
  });

  // Clean up
  it("cleanup", async () => {
    await rm(TEST_DIR, { recursive: true, force: true });
  });
});
