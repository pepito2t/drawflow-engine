import { describe, expect, it, vi } from "vitest";
import { channelListener, type EngineMessage } from "./engine-message";

describe("channelListener", () => {
  it("forwards valid bridge messages", () => {
    const onMessage = vi.fn<(message: EngineMessage) => void>();
    const onInvalid = vi.fn();
    const listen = channelListener(onMessage, onInvalid);

    listen({ kind: "stdout", line: "{}" });
    listen({ kind: "exit", code: null });

    expect(onMessage.mock.calls.map(([message]) => message.kind)).toEqual(["stdout", "exit"]);
    expect(onInvalid).not.toHaveBeenCalled();
  });

  it("reports an unreadable message instead of throwing", () => {
    const onMessage = vi.fn();
    const onInvalid = vi.fn<(message: string) => void>();
    const listen = channelListener(onMessage, onInvalid);

    expect(() => {
      listen({ kind: "surprise" });
    }).not.toThrow();
    expect(onMessage).not.toHaveBeenCalled();
    expect(onInvalid).toHaveBeenCalledOnce();
    expect(onInvalid.mock.calls[0]?.[0]).not.toBe("");
  });
});
