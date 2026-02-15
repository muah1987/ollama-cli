/**
 * React hook for sub-agent orchestration state.
 */

import { useState, useCallback, useRef, useEffect } from "react";
import type { SharedState } from "../types/agent.js";
import type { SubagentWaveEvent } from "../types/theme.js";
import { OperationPhase } from "../types/theme.js";
import { ContextManager } from "../core/context.js";
import { ModelOrchestrator } from "../core/models.js";
import { SubagentOrchestrator } from "../core/subagents.js";

interface UseSubagentsReturn {
  /** Whether orchestration is in progress */
  isOrchestrating: boolean;
  /** Current wave number (1-4) */
  currentWave: number;
  /** Wave events for tracking progress */
  waveEvents: SubagentWaveEvent[];
  /** Final shared state result */
  result: SharedState | null;
  /** Error if any */
  error: Error | null;
  /** Start orchestrating a task */
  orchestrate: (task: string) => Promise<void>;
}

export function useSubagents(
  orchestrator: ModelOrchestrator,
  context: ContextManager,
): UseSubagentsReturn {
  const [isOrchestrating, setIsOrchestrating] = useState(false);
  const [currentWave, setCurrentWave] = useState(0);
  const [waveEvents, setWaveEvents] = useState<SubagentWaveEvent[]>([]);
  const [result, setResult] = useState<SharedState | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const subagentRef = useRef<SubagentOrchestrator | null>(null);

  useEffect(() => {
    const sub = new SubagentOrchestrator(orchestrator, context);
    subagentRef.current = sub;

    sub.on("subagent:wave", (event: SubagentWaveEvent) => {
      setWaveEvents((prev) => [...prev, event]);
      if (event.status === "started") {
        setCurrentWave(event.wave);
      }
    });

    sub.on("progress", ({ phase }: { phase: OperationPhase }) => {
      // Progress events handled by parent via useAgent
    });

    return () => {
      sub.removeAllListeners();
    };
  }, [orchestrator, context]);

  const orchestrate = useCallback(async (task: string) => {
    const sub = subagentRef.current;
    if (!sub) return;

    setIsOrchestrating(true);
    setCurrentWave(0);
    setWaveEvents([]);
    setResult(null);
    setError(null);

    try {
      const state = await sub.orchestrate(task);
      setResult(state);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setIsOrchestrating(false);
    }
  }, []);

  return {
    isOrchestrating,
    currentWave,
    waveEvents,
    result,
    error,
    orchestrate,
  };
}
