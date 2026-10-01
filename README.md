# drawflow-engine

Application desktop Windows qui automatise les tâches d'un dessinateur en façade : listes de pièces (DWG → XLSX), rapports (PDF → DOCX) et soumissions (XLSX / PDF avec XLSX intégré).

Stack : Tauri 2 · React + TypeScript · moteur Python (sidecar PyInstaller).

Les règles de développement sont dans [CLAUDE.md](CLAUDE.md).

## Code d'accès

L'application installée demande un code au démarrage (pas en développement). Le code initial est `0000` ; il se change dans **Paramètres → Code d'accès**. Il est stocké uniquement haché (argon2id).

**Code oublié :** fermer l'application et supprimer `access-code.json` dans le dossier de configuration (`%APPDATA%\ch.drawflow.desktop\` sous Windows). Le code redevient `0000`.
