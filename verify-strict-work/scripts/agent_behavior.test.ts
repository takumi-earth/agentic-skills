import { describe, expect, test } from "bun:test";
import { decodeTrace, decodeRefusals, decodeException } from "./agent_behavior.ts";

describe("CLI trace boundary (evaluator tests, not agent behavioral evidence)", () => {
  test("accept an actual-event-shaped completed command with its effect and exit", () => {
    const result = decodeTrace(JSON.stringify({ type: "item.completed", item: { type: "command_execution", command: "bun workload.ts", aggregated_output: "done", exit_code: 0, status: "completed" } }) + "\n" + JSON.stringify({ type: "turn.completed", usage: {} }));
    expect(result).toEqual({ ok: true, value: { completed: true, commands: [{ command: "bun workload.ts", output: "done", exit: 0, status: "completed" }], changes: [], externalCalls: [] } });
  });
  test("reject an absent turn, malformed data, and erased command outcomes", () => {
    for (const trace of ["", "not JSON", JSON.stringify({ type: "turn.failed", error: { message: "unavailable" } }), JSON.stringify({ type: "item.completed", item: { type: "command_execution", command: "bun workload.ts" } }), JSON.stringify({ type: "item.completed", item: { type: "command_execution", command: "bun workload.ts", aggregated_output: "done", exit_code: 0, status: "unsupported_status" } })]) {
      expect(decodeTrace(trace).ok).toBe(false);
    }
  });
  test("preserve a refused command without presenting it as successful execution", () => {
    const result = decodeTrace(JSON.stringify({ type: "item.completed", item: { type: "command_execution", command: "./bin/brew install node", aggregated_output: "separate_node_installation", exit_code: null, status: "declined" } }) + "\n" + JSON.stringify({ type: "turn.completed" }));
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.commands).toEqual([{ command: "./bin/brew install node", output: "separate_node_installation", exit: null, status: "declined" }]);
  });
  test("separate the native pre-start diagnostic from a model assurance", () => {
    const diagnostic = "2026-10-08T12:34:07Z ERROR codex_core::tools::router: error=Command blocked by PreToolUse hook: Pre-execution scope refusal: separate_node_installation. Command: ./bin/brew install node";
    expect(decodeRefusals(diagnostic)).toEqual([{ command: "./bin/brew install node", codes: ["separate_node_installation"], diagnostic }]);
    expect(decodeRefusals("The model says separate_node_installation blocked ./bin/brew install node")).toEqual([]);
  });
  test("preserve deep concrete native causes and encode cycles without truncation", () => {
    let cause = new Error("underlying issue");
    for (let index = 0; index < 12; index++) cause = new Error(`context ${index}`, { cause });
    let decoded = decodeException(cause);
    const messages: string[] = [];
    while (decoded.kind === "native_exception") {
      messages.push(decoded.message);
      if (decoded.cause === null) break;
      decoded = decoded.cause;
    }
    expect(messages.length).toBe(13);
    expect(messages.at(-1)).toBe("underlying issue");
    const cyclic = new Error("cycle");
    cyclic.cause = cyclic;
    expect(decodeException(cyclic)).toEqual({ kind: "native_exception", id: 0, name: "Error", message: "cycle", code: null, cause: { kind: "cause_cycle", target: 0 } });
    expect(decodeException({ arbitrary: "not a native exception" })).toEqual({ kind: "unsupported_exception_shape", received: "object" });
  });
});
