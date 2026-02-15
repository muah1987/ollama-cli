import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { getThemeStage, getAvailableThemes } from "./index.js";
import { OperationPhase } from "../types/theme.js";

describe("themes", () => {
  it("returns available theme names", () => {
    const themes = getAvailableThemes();
    assert.ok(themes.length >= 4);
    assert.ok(themes.includes("shisha"));
    assert.ok(themes.includes("caravan"));
    assert.ok(themes.includes("qahwa"));
    assert.ok(themes.includes("scholarly"));
  });

  it("returns stage for each phase in shisha theme", () => {
    const phases = [
      OperationPhase.ANALYZING,
      OperationPhase.PLANNING,
      OperationPhase.IMPLEMENTING,
      OperationPhase.TESTING,
      OperationPhase.REVIEWING,
      OperationPhase.COMPLETE,
    ];

    for (const phase of phases) {
      const stage = getThemeStage("shisha", phase);
      assert.ok(stage.emoji, `Missing emoji for ${phase}`);
      assert.ok(stage.messageEn, `Missing English message for ${phase}`);
    }
  });

  it("returns stage for each phase in caravan theme", () => {
    const stage = getThemeStage("caravan", OperationPhase.ANALYZING);
    assert.ok(stage.emoji);
    assert.ok(stage.messageEn);
  });

  it("returns stage for each phase in qahwa theme", () => {
    const stage = getThemeStage("qahwa", OperationPhase.IMPLEMENTING);
    assert.ok(stage.emoji);
    assert.ok(stage.messageEn);
  });

  it("returns stage for each phase in scholarly theme", () => {
    const stage = getThemeStage("scholarly", OperationPhase.COMPLETE);
    assert.ok(stage.emoji);
    assert.ok(stage.messageEn);
  });

  it("falls back to base theme for unknown theme", () => {
    const stage = getThemeStage("nonexistent" as any, OperationPhase.ANALYZING);
    assert.ok(stage.emoji);
    assert.ok(stage.messageEn);
  });

  it("includes Arabic messages", () => {
    const stage = getThemeStage("shisha", OperationPhase.ANALYZING);
    assert.ok(stage.messageAr, "Shisha theme should have Arabic messages");
  });
});
