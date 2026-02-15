/**
 * React hook for sub-agent orchestration state.
 */
import { useState, useCallback, useRef, useEffect } from "react";
import { SubagentOrchestrator } from "../core/subagents.js";
export function useSubagents(orchestrator, context) {
    const [isOrchestrating, setIsOrchestrating] = useState(false);
    const [currentWave, setCurrentWave] = useState(0);
    const [waveEvents, setWaveEvents] = useState([]);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const subagentRef = useRef(null);
    useEffect(() => {
        const sub = new SubagentOrchestrator(orchestrator, context);
        subagentRef.current = sub;
        sub.on("subagent:wave", (event) => {
            setWaveEvents((prev) => [...prev, event]);
            if (event.status === "started") {
                setCurrentWave(event.wave);
            }
        });
        sub.on("progress", ({ phase }) => {
            // Progress events handled by parent via useAgent
        });
        return () => {
            sub.removeAllListeners();
        };
    }, [orchestrator, context]);
    const orchestrate = useCallback(async (task) => {
        const sub = subagentRef.current;
        if (!sub)
            return;
        setIsOrchestrating(true);
        setCurrentWave(0);
        setWaveEvents([]);
        setResult(null);
        setError(null);
        try {
            const state = await sub.orchestrate(task);
            setResult(state);
        }
        catch (err) {
            setError(err instanceof Error ? err : new Error(String(err)));
        }
        finally {
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
//# sourceMappingURL=useSubagents.js.map