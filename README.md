# drawflow-engine

Application desktop Windows qui automatise les tâches d'un dessinateur en façade : listes de pièces (DWG → XLSX), rapports (PDF → DOCX) et soumissions (XLSX / PDF avec XLSX intégré).

Stack : Tauri 2 · React + TypeScript · moteur Python (sidecar PyInstaller).

Les règles de développement sont dans [CLAUDE.md](CLAUDE.md).

## Code d'accès

L'application installée demande un code au démarrage (pas en développement). Le code initial est `0000` ; il se change dans **Paramètres → Code d'accès**. Il est stocké uniquement haché (argon2id).

**Code oublié :** fermer l'application et supprimer `access-code.json` dans le dossier de configuration (`%APPDATA%\ch.drawflow.desktop\` sous Windows). Le code redevient `0000`.

## Publier une version

1. `python scripts/version.py bump X.Y.Z` (met à jour UI, Tauri, Rust et moteur), commit via PR.
2. Une fois mergé : `git tag vX.Y.Z && git push origin vX.Y.Z`.
3. Le workflow `Release` construit l'installeur Windows (NSIS) et publie la release avec `latest.json` signé.

Prérequis (une fois) : `pnpm tauri signer generate`, puis secrets `TAURI_SIGNING_PRIVATE_KEY` et `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`, et variable `UPDATER_PUBKEY` (clé publique). L'app installée vérifie les mises à jour au démarrage (barre d'état) ; en développement, l'updater est désactivé. Pour publier les releases dans un repo public séparé : variables `RELEASES_OWNER` / `RELEASES_REPO` et secret `RELEASES_TOKEN` (token avec droit `contents:write` sur ce repo).

## Stream Deck

1. Dans Drawflow : **Paramètres → Intégrations** → activer l'API locale, copier le jeton.
2. Double-cliquer sur `ch.drawflow.streamDeckPlugin` (fourni avec chaque release) pour l'installer dans Stream Deck.
3. Glisser une action « Drawflow » sur une touche, puis coller le jeton dans ses réglages (une seule fois : il est partagé par toutes les touches).

Actions : lancer un préréglage (progression en direct, vert/rouge à la fin), ouvrir un onglet, annuler les traitements, ouvrir le dernier résultat, compteur de traitements. Tant que Drawflow est verrouillée, les touches affichent « Verrouillé » et n'exécutent rien. Protocole : [docs/api-locale.md](docs/api-locale.md).
