import { t } from "../i18n/shell";
import { Suspense, use, useState } from "react";
import { useLanguage } from "../hooks/use-language";
import { useRetryablePromise } from "../hooks/use-retryable-promise";
import { toReadableError } from "../lib/error-message";
import { parseGuide, sectionForAnchor, type GuideSection } from "../lib/guide";
import { engineRequest } from "../lib/tauri/engine";
import { openDownloadPage } from "../lib/tauri/setup";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorPanel } from "./ErrorPanel";
import { CloseIcon } from "./icons";
import { MarkdownText } from "./MarkdownText";
import { ModalDialog } from "./ModalDialog";
import { Loader } from "./Spinner";

const EXTERNAL_LINK = /^https:\/\//;

function loadGuide(): Promise<GuideSection[]> {
  return engineRequest("help.guide").then(parseGuide);
}

interface HelpDialogProps {
  topic: string | undefined;
  onClose: () => void;
}

export function HelpDialog({ topic, onClose }: HelpDialogProps) {
  useLanguage();
  const { id, promise, retry } = useRetryablePromise(loadGuide);
  return (
    <ModalDialog labelledBy="help-title" onCancel={onClose} onBackdropClick={onClose}>
      <header className="dialog-header">
        <h2 id="help-title">{t("helpDialog.title")}</h2>
        <button
          type="button"
          className="icon-button"
          aria-label={t("helpDialog.close")}
          onClick={onClose}
        >
          <CloseIcon />
        </button>
      </header>
      <ErrorBoundary
        key={id}
        fallback={(error) => {
          const { message, hint } = toReadableError(error);
          return (
            <div className="dialog-body centered">
              <ErrorPanel
                title={t("helpDialog.unavailable")}
                message={message}
                hint={hint}
                onRetry={retry}
              />
            </div>
          );
        }}
      >
        <Suspense
          fallback={
            <div className="dialog-body">
              <Loader label={t("helpDialog.loading")} />
            </div>
          }
        >
          <GuideView guidePromise={promise} topic={topic} />
        </Suspense>
      </ErrorBoundary>
    </ModalDialog>
  );
}

function GuideView({
  guidePromise,
  topic,
}: {
  guidePromise: Promise<GuideSection[]>;
  topic: string | undefined;
}) {
  const sections = use(guidePromise);
  const [current, setCurrent] = useState(
    () => (topic ? sectionForAnchor(sections, topic) : null) ?? sections[0],
  );

  const follow = (href: string) => {
    if (EXTERNAL_LINK.test(href)) {
      openDownloadPage(href).catch((error: unknown) => {
        console.error("Lien non ouvert :", error);
      });
      return;
    }
    const target = sectionForAnchor(sections, href);
    if (target) {
      setCurrent(target);
      requestAnimationFrame(() => {
        document.getElementById(href.replace(/^#/, ""))?.scrollIntoView();
      });
    }
  };

  return (
    <div className="dialog-body settings-layout">
      <nav
        className="side-tabs"
        role="tablist"
        aria-orientation="vertical"
        aria-label={t("helpDialog.sections")}
      >
        {sections.map((section) => (
          <button
            key={section.id}
            type="button"
            role="tab"
            aria-selected={section.id === current?.id}
            className={section.id === current?.id ? "side-tab selected" : "side-tab"}
            onClick={() => {
              setCurrent(section);
            }}
          >
            <span>{section.title}</span>
          </button>
        ))}
      </nav>
      {current && (
        <section className="settings-panel help-content" role="tabpanel">
          <h3>{current.title}</h3>
          <MarkdownText source={current.markdown} onLink={follow} />
        </section>
      )}
    </div>
  );
}
