interface ErrorPanelProps {
  title: string;
  message: string;
  hint?: string | null;
  file?: string | null;
  onRetry?: () => void;
}

export function ErrorPanel({ title, message, hint, file, onRetry }: ErrorPanelProps) {
  return (
    <div className="error-panel" role="alert">
      <span className="error-icon" aria-hidden="true">
        !
      </span>
      <div className="error-body">
        <strong>{title}</strong>
        <p>{message}</p>
        {file && (
          <p className="error-file">
            Fichier : <code>{file}</code>
          </p>
        )}
        {hint && <p className="error-hint">{hint}</p>}
        {onRetry && (
          <button type="button" onClick={onRetry}>
            Réessayer
          </button>
        )}
      </div>
    </div>
  );
}
