import { describe, expect, it } from "vitest";
import { checkNewAccessCode } from "./access-code";

describe("checkNewAccessCode", () => {
  it("accepts a confirmed new code", () => {
    expect(checkNewAccessCode("0000", "4829", "4829")).toBeNull();
  });

  it("rejects a confirmation mismatch", () => {
    expect(checkNewAccessCode("0000", "4829", "4828")).toBe("mismatch");
  });

  it("rejects an unchanged code", () => {
    expect(checkNewAccessCode("0000", "0000", "0000")).toBe("unchanged");
  });
});
