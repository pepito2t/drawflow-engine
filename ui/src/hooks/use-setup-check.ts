import { useEffect } from "react";
import { missingCount, parseSetupReport } from "../lib/setup";
import { scanSetup } from "../lib/tauri/setup";
import { useNotificationCenter } from "./notification-center";

/** Once per launch: offers to finish the setup when a required tool is missing. */
export function useSetupCheck(): void {
  const { publish } = useNotificationCenter();
  useEffect(() => {
    let isActive = true;
    scanSetup()
      .then(parseSetupReport)
      .then((report) => {
        const missing = missingCount(report);
        if (isActive && missing > 0) {
          publish({ type: "setupNeeded", missing });
        }
      })
      .catch((error: unknown) => {
        console.error("Analyse de l'installation impossible :", error);
      });
    return () => {
      isActive = false;
    };
  }, [publish]);
}
