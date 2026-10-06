import { describe, expect, it } from "vitest";
import {
  describeFetch,
  parseConversations,
  parseMailStatus,
  participantsSummary,
  type MailConversation,
} from "./mail";

const CONVERSATION: MailConversation = {
  id: "c1",
  subject: "Façade nord",
  participants: [
    { name: "Marc", address: "marc@chantier.ch" },
    { name: "", address: "lea@facades.ch" },
    { name: "Paul", address: "" },
    { name: "Ana", address: "ana@x.ch" },
  ],
  first_received_at: "2026-10-01T08:00:00Z",
  last_received_at: "2026-10-02T09:00:00Z",
  message_count: 2,
  attachment_count: 1,
  project: null,
  category: null,
};

describe("mail", () => {
  it("parses the engine payloads and refuses others", () => {
    const status = parseMailStatus(
      JSON.stringify({
        configured: true,
        account: "lea@facades.ch",
        last_fetch_at: null,
        conversations: 1,
        folder: "C:\\mail",
      }),
    );
    expect(status.account).toBe("lea@facades.ch");
    expect(parseConversations(JSON.stringify({ conversations: [CONVERSATION] }))).toHaveLength(1);
    expect(() => parseConversations("{}")).toThrow("invalide");
  });

  it("summarizes participants and fetch results", () => {
    expect(participantsSummary(CONVERSATION)).toBe("Marc, lea@facades.ch, Paul +1");
    expect(describeFetch({ fetched: 3, added: 0, conversations: 2, pruned: 0 })).toBe(
      "Aucun nouveau message.",
    );
    expect(describeFetch({ fetched: 3, added: 2, conversations: 2, pruned: 0 })).toBe(
      "2 nouveaux messages, 2 conversations.",
    );
  });
});
