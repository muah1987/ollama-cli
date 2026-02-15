/**
 * React hook for managing the QarinAgent lifecycle.
 *
 * Provides reactive state for agent phases, streaming output,
 * intent classification, token metrics, and session status.
 */
import { useState, useCallback, useEffect, useRef } from "react";
import { OperationPhase } from "../types/theme.js";
import { QarinAgent } from "../core/agent.js";
export function useAgent(options) {
    const agentRef = useRef(null);
    const [phase, setPhase] = useState(OperationPhase.ANALYZING);
    const [details, setDetails] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [streamOutput, setStreamOutput] = useState("");
    const [status, setStatus] = useState(null);
    const [intent, setIntent] = useState(null);
    const [tokenDisplay, setTokenDisplay] = useState("");
    const [error, setError] = useState(null);
    useEffect(() => {
        const agent = new QarinAgent(options);
        agentRef.current = agent;
        agent.on("progress", ({ phase: p, details: d }) => {
            setPhase(p);
            if (d)
                setDetails(d);
        });
        agent.on("stream", (chunk) => {
            setStreamOutput((prev) => prev + chunk);
        });
        agent.on("intent", (intentResult) => {
            setIntent(intentResult);
        });
        agent.on("error", ({ error: err }) => {
            setError(err);
            setIsProcessing(false);
        });
        agent.on("success", () => {
            setIsProcessing(false);
            setStatus(agent.getStatus());
            setTokenDisplay(agent.getTokenCounter().formatDisplay());
        });
        agent.start().catch((err) => setError(err));
        return () => {
            // Intentionally suppress cleanup errors — agent resources are best-effort released
            agent.end().catch(() => { });
        };
    }, []);
    // Note: empty deps is intentional — agent is created once on mount
    const sendMessage = useCallback(async (message) => {
        const agent = agentRef.current;
        if (!agent)
            return;
        setIsProcessing(true);
        setStreamOutput("");
        setError(null);
        try {
            if (options.chain) {
                await agent.executeWithChain(message);
            }
            else {
                await agent.executeWithTools(message);
            }
            setStatus(agent.getStatus());
            setTokenDisplay(agent.getTokenCounter().formatDisplay());
        }
        catch (err) {
            setError(err instanceof Error ? err : new Error(String(err)));
        }
        finally {
            setIsProcessing(false);
        }
    }, []);
    const runTool = useCallback(async (name, args) => {
        const agent = agentRef.current;
        if (!agent)
            return null;
        return agent.runTool(name, args);
    }, []);
    const endSession = useCallback(async () => {
        const agent = agentRef.current;
        if (!agent)
            return;
        const finalStatus = await agent.end();
        setStatus(finalStatus);
    }, []);
    return {
        phase,
        details,
        isProcessing,
        streamOutput,
        status,
        intent,
        tokenDisplay,
        error,
        sendMessage,
        runTool,
        endSession,
    };
}
//# sourceMappingURL=useAgent.js.map