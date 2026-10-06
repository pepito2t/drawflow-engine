import { useCommands } from "../hooks/command-registry";
import { t } from "../i18n/panels";
import type { ProposalStatus, RunProposal } from "../lib/assistant-chat";
import type { CatalogModule } from "../lib/catalog";
import { COMMAND_ARGUMENTS, COMMANDS } from "../lib/commands";
import { describeInputs, describeSynonyms, proposalTitle } from "../lib/proposals";
import { Spinner } from "./Spinner";

interface ProposalCardProps {
  proposal: RunProposal;
  modules: CatalogModule[];
  onStatus: (status: ProposalStatus, error?: string) => void;
}

export function ProposalCard({ proposal, modules, onStatus }: ProposalCardProps) {
  const { execute } = useCommands();
  const fields = modules.find((module) => module.manifest.id === proposal.feature)?.fields ?? [];
  const isSettings = proposal.kind === "synonyms";
  const lines = isSettings
    ? describeSynonyms(proposal.inputs)
    : describeInputs(proposal.inputs, fields);

  const launch = () => {
    onStatus("launching");
    const request = isSettings
      ? execute(COMMANDS.addSynonyms, synonymsArguments(proposal.inputs))
      : proposal.kind === "preset" && proposal.presetId !== null
        ? execute(COMMANDS.runPreset, { presetId: proposal.presetId })
        : execute(COMMANDS.runFeature, { moduleId: proposal.feature, inputs: proposal.inputs });
    request
      .then((result) => {
        if (result.ok) {
          onStatus("launched");
        } else {
          onStatus("failed", result.error);
        }
      })
      .catch((error: unknown) => {
        onStatus("failed", error instanceof Error ? error.message : String(error));
      });
  };

  return (
    <div className={`proposal-card ${proposal.status}`}>
      <strong>
        {isSettings ? "" : t("proposal.launch_prefix")}
        {proposalTitle(proposal)}
      </strong>
      {lines.length > 0 && (
        <dl className="proposal-inputs">
          {lines.map((line) => (
            <div key={line.label}>
              <dt>{line.label}</dt>
              <dd>{line.value}</dd>
            </div>
          ))}
        </dl>
      )}
      <ProposalFooter
        proposal={proposal}
        onLaunch={launch}
        onDismiss={() => {
          onStatus("dismissed");
        }}
      />
    </div>
  );
}

interface ProposalFooterProps {
  proposal: RunProposal;
  onLaunch: () => void;
  onDismiss: () => void;
}

function ProposalFooter({ proposal, onLaunch, onDismiss }: ProposalFooterProps) {
  switch (proposal.status) {
    case "pending":
      return (
        <div className="proposal-actions">
          <button type="button" className="primary" onClick={onLaunch}>
            {proposal.kind === "synonyms" ? t("proposal.apply") : t("proposal.launch")}
          </button>
          <button type="button" onClick={onDismiss}>
            {t("proposal.dismiss")}
          </button>
        </div>
      );
    case "launching":
      return <Spinner label={t("proposal.launching")} />;
    case "launched":
      return (
        <span className="run-status succeeded">
          {proposal.kind === "synonyms" ? t("proposal.applied") : t("proposal.launched")}
        </span>
      );
    case "dismissed":
      return <span className="muted">{t("proposal.dismissed")}</span>;
    case "failed":
      return (
        <div className="proposal-actions">
          <span className="assistant-error">{proposal.error}</span>
          <button type="button" onClick={onLaunch}>
            {t("common.retry")}
          </button>
        </div>
      );
  }
}

function synonymsArguments(inputs: Record<string, unknown>): { columns: Record<string, string[]> } {
  const parsed = COMMAND_ARGUMENTS["settings.add-synonyms"].safeParse(inputs);
  return parsed.success ? parsed.data : { columns: {} };
}
