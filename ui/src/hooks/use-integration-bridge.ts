import { useEffect } from "react";
import {
  listenToIntegrationCommands,
  publishToIntegrations,
  replyToIntegration,
} from "../lib/tauri/integrations";
import { useCommands } from "./command-registry";
import { useNotificationCenter } from "./notification-center";

/** Connects the local API (Stream Deck…) to named commands and to the event stream. */
export function useIntegrationBridge(): void {
  const { execute } = useCommands();
  const { subscribe } = useNotificationCenter();

  useEffect(
    () =>
      subscribe((event) => {
        publishToIntegrations(event).catch((error: unknown) => {
          console.error("Événement non transmis aux intégrations :", error);
        });
      }),
    [subscribe],
  );

  useEffect(() => {
    let stop: (() => void) | null = null;
    let disposed = false;
    listenToIntegrationCommands((command) => {
      execute(command.command, command.args)
        .then((result) =>
          replyToIntegration(
            result.ok
              ? { id: command.id, ok: true, data: result.data }
              : { id: command.id, ok: false, error: result.error },
          ),
        )
        .catch((error: unknown) => {
          console.error("Réponse non transmise aux intégrations :", error);
        });
    })
      .then((unlisten) => {
        if (disposed) {
          unlisten();
        } else {
          stop = unlisten;
        }
      })
      .catch((error: unknown) => {
        console.error("API locale indisponible :", error);
      });
    return () => {
      disposed = true;
      stop?.();
    };
  }, [execute]);
}
