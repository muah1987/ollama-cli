/**
 * React hook for managing the QarinAgent lifecycle.
 */

import { useState, useCallback, useEffect, useRef } from "react";
import type { SessionStatus, ToolResult } from "../types/agent.js";
import type { CLIOptions } from "../types/agent.js";
import { OperationPhase } from "../types/theme.js";
import { QarinAgent } from "../core/agent.js";

interface UseAgentReturn {
  /** Current operation phase */
  phase: OperationPhase;
  /** Phase details message */
  details: string;
  /** Whether the agent is processing */
  isProcessing: boolean;
  /** Accumulated streaming output */
  streamOutput: string;
  /** Session status snapshot */
  status: SessionStatus | null;
  /** Error if any */
  error: Error | null;
  /** Send a message to the agent */
  sendMessage: (message: string) => Promise<void>;
  /** Execute a tool */
  runTool: (name: string, args: Record<string, unknown>) => Promise<ToolResult | null>;
  /** End the session */
  endSession: () => Promise<void>;
}

export function useAgent(options: CLIOptions): UseAgentReturn {
  const agentRef = useRef<QarinAgent | null>(null);
  const [phase, setPhase] = useState<OperationPhase>(OperationPhase.ANALYZING);
  const [details, setDetails] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [streamOutput, setStreamOutput] = useState("");
  const [status, setStatus] = useState<SessionStatus | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const agent = new QarinAgent(options);
    agentRef.current = agent;

    agent.on("progress", ({ phase: p, details: d }) => {
      setPhase(p);
      if (d) setDetails(d);
    });

    agent.on("stream", (chunk: string) => {
      setStreamOutput((prev) => prev + chunk);
    });

    agent.on("error", ({ error: err }: { error: Error }) => {
      setError(err);
      setIsProcessing(false);
    });

    agent.on("success", () => {
      setIsProcessing(false);
      setStatus(agent.getStatus());
    });

    agent.start().catch((err: Error) => setError(err));

    return () => {
      // Intentionally suppress cleanup errors — agent resources are best-effort released
      agent.end().catch(() => {});
    };
  }, []);
  // Note: empty deps is intentional — agent is created once on mount

  const sendMessage = useCallback(async (message: string) => {
    const agent = agentRef.current;
    if (!agent) return;

    setIsProcessing(true);
    setStreamOutput("");
    setError(null);

    try {
      await agent.executeTask(message);
      setStatus(agent.getStatus());
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const runTool = useCallback(
    async (name: string, args: Record<string, unknown>): Promise<ToolResult | null> => {
      const agent = agentRef.current;
      if (!agent) return null;
      return agent.runTool(name, args);
    },
    [],
  );

  const endSession = useCallback(async () => {
    const agent = agentRef.current;
    if (!agent) return;

    const finalStatus = await agent.end();
    setStatus(finalStatus);
  }, []);

  return {
    phase,
    details,
    isProcessing,
    streamOutput,
    status,
    error,
    sendMessage,
    runTool,
    endSession,
  };
}
