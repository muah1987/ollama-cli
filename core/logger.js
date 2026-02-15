/**
 * Structured logging with performance metrics.
 *
 * Lightweight Pino-style logger with:
 * - Log levels: debug, info, warn, error
 * - JSON structured output to file
 * - Console output with colors
 * - Log rotation by size
 * - Performance metrics: per-wave latency, per-agent tokens, merge times
 */
import { appendFile, stat, rename, mkdir } from "node:fs/promises";
import { resolve, dirname } from "node:path";
const LOG_LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };
const LEVEL_NAMES = { 10: "DEBUG", 20: "INFO", 30: "WARN", 40: "ERROR" };
const LEVEL_COLORS = { 10: "\x1b[36m", 20: "\x1b[32m", 30: "\x1b[33m", 40: "\x1b[31m" };
const RESET = "\x1b[0m";
/**
 * Structured logger with file output and rotation.
 */
export class Logger {
    level;
    filePath;
    maxSize;
    consoleEnabled;
    rotateCount;
    constructor(options = {}) {
        this.level = LOG_LEVELS[options.level ?? "info"] ?? LOG_LEVELS.info;
        this.filePath = options.file
            ? resolve(options.file)
            : resolve(process.env.QARIN_PROJECT_DIR ?? process.cwd(), ".qarin", "qarin.log");
        this.maxSize = options.maxSize ?? 5_000_000;
        this.consoleEnabled = options.console ?? false;
        this.rotateCount = 0;
    }
    /** Log a debug message */
    debug(msg, data) {
        this.log(LOG_LEVELS.debug, msg, data);
    }
    /** Log an info message */
    info(msg, data) {
        this.log(LOG_LEVELS.info, msg, data);
    }
    /** Log a warning */
    warn(msg, data) {
        this.log(LOG_LEVELS.warn, msg, data);
    }
    /** Log an error */
    error(msg, data) {
        this.log(LOG_LEVELS.error, msg, data);
    }
    /** Core log method */
    log(level, msg, data) {
        if (level < this.level)
            return;
        const entry = {
            level: LEVEL_NAMES[level] ?? "INFO",
            ts: new Date().toISOString(),
            msg,
            ...data,
        };
        // Write to file (fire-and-forget)
        this.writeToFile(JSON.stringify(entry) + "\n").catch(() => { });
        // Console output
        if (this.consoleEnabled) {
            const color = LEVEL_COLORS[level] ?? "";
            const prefix = `${color}[${entry.level}]${RESET}`;
            const extra = data ? ` ${JSON.stringify(data)}` : "";
            process.stderr.write(`${prefix} ${msg}${extra}\n`);
        }
    }
    /** Write a line to the log file, rotating if needed */
    async writeToFile(line) {
        try {
            await mkdir(dirname(this.filePath), { recursive: true });
            // Check file size for rotation
            try {
                const st = await stat(this.filePath);
                if (st.size > this.maxSize) {
                    await this.rotate();
                }
            }
            catch {
                // File doesn't exist yet
            }
            await appendFile(this.filePath, line);
        }
        catch {
            // Best effort logging
        }
    }
    /** Rotate the log file */
    async rotate() {
        try {
            this.rotateCount++;
            const rotatedPath = `${this.filePath}.${this.rotateCount}`;
            await rename(this.filePath, rotatedPath);
        }
        catch {
            // Best effort rotation
        }
    }
    /**
     * Log a performance metric.
     */
    perf(operation, durationMs, data) {
        this.info(`perf:${operation}`, {
            duration_ms: Math.round(durationMs * 100) / 100,
            ...data,
        });
    }
    /**
     * Log a wave completion with metrics.
     */
    waveComplete(wave, durationMs, data) {
        this.info(`wave:${wave}:complete`, {
            duration_ms: Math.round(durationMs),
            ...data,
        });
    }
    /**
     * Log agent token usage.
     */
    agentTokens(role, tokens) {
        this.debug(`agent:${role}:tokens`, { tokens });
    }
    /**
     * Log merge timing.
     */
    mergeComplete(wave, durationMs, deduped, conflicts) {
        this.info(`merge:${wave}:complete`, {
            duration_ms: Math.round(durationMs),
            deduped,
            conflicts,
        });
    }
    /** Create a child logger with a prefix */
    child(prefix) {
        const parent = this;
        return {
            debug: (msg, data) => parent.debug(`[${prefix}] ${msg}`, data),
            info: (msg, data) => parent.info(`[${prefix}] ${msg}`, data),
            warn: (msg, data) => parent.warn(`[${prefix}] ${msg}`, data),
            error: (msg, data) => parent.error(`[${prefix}] ${msg}`, data),
            perf: (op, ms, data) => parent.perf(`${prefix}:${op}`, ms, data),
        };
    }
}
/** Global logger instance */
let _globalLogger = null;
export function getLogger(options) {
    if (!_globalLogger) {
        _globalLogger = new Logger(options);
    }
    return _globalLogger;
}
export function setLogger(logger) {
    _globalLogger = logger;
}
//# sourceMappingURL=logger.js.map
