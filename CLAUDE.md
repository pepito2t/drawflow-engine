# CLAUDE.md

## Projet
Application desktop Windows pour un dessinateur en façade : automatisation de listes de pièces (DWG → XLSX), de rapports (PDF → DOCX) et de soumissions (XLSX / PDF avec XLSX intégré). Priorité : **performance, fiabilité, évolutivité**. L'esthétique est secondaire.

Développement sous macOS, cible Windows. Les builds Windows se font uniquement en CI (GitHub Actions).

## Structure
```
<racine du repo>/
  ui/                     # React + TS + Vite — affichage uniquement
  src-tauri/              # Tauri 2 — pont sidecar, dialogues, updater
  engine/                 # Moteur Python (uv), packagé en sidecar PyInstaller
    src/engine/
      cli.py              # list-modules, run
      core/               # contrat de module, événements, registry, config, erreurs
      modules/<id>/       # une fonctionnalité = un dossier
        manifest.py       # id, nom, description, version
        schema.py         # entrées/sorties pydantic
        service.py        # logique métier pure
        adapters.py       # I/O fichiers, ODA, PDF, XLSX, DOCX
        tests/
  templates/              # modèles DOCX/XLSX
  fixtures/               # fichiers réels anonymisés + sorties attendues
  streamdeck/             # plugin Stream Deck (SDK Node.js Elgato) — client de l'API locale
  docs/api-locale.md      # protocole de l'API locale WebSocket
  .github/workflows/      # ci.yml, release.yml
```

## Commandes
- Installation : `pnpm install` · `(cd engine && uv sync)`
- Moteur (dans `engine/`) : `uv run pytest` · `uv run ruff check . && uv run ruff format --check .` · `uv run mypy --strict src`
- UI : `pnpm --filter ui lint` · `pnpm --filter ui typecheck` · `pnpm --filter ui test`
- Rust (dans `src-tauri/`) : `cargo fmt --check` · `cargo clippy --all-targets -- -D warnings` · `cargo test`
- Sidecar : `pnpm sidecar:build` (PyInstaller → `src-tauri/binaries/engine-<target-triple>[.exe]`) · smoke test : `uv run --project engine python scripts/smoke-sidecar.py src-tauri/binaries/engine-*`
- Assistant (dans `engine/`) : `uv run engine mcp --settings <fichier>` (serveur MCP stdio) · `uv run engine assistant models|chat --settings <fichier> [--input <conversation.json>]`
- Dev complet : `pnpm dev` (build du sidecar puis `tauri dev`)
- Plugin Stream Deck (dans `streamdeck/`) : `pnpm lint` · `pnpm typecheck` · `pnpm test` · `pnpm build` · `pnpm validate` · `pnpm run package` (→ `dist/ch.drawflow.streamDeckPlugin`)

Avant tout commit : lint + typecheck + tests de la zone touchée doivent passer.

## Contrat de module (non négociable)
- Un module expose un manifeste, un schéma d'entrée pydantic (qui sert à générer le formulaire UI : types `file`, `files`, `folder`, `folders`, `output_folder`, `template`, `text`, `bool`, `enum`) et une fonction `run(inputs, emit) -> Result`.
- `run` communique **uniquement** via `emit(event)` : `progress`, `log`, `warning`, `result`, `error`. Sortie CLI en NDJSON, un événement par ligne, rien d'autre sur stdout.
- Les modules ne s'importent pas entre eux. Le partage passe par `core/` ou par une lib interne dédiée.
- Ajouter un module ne doit nécessiter **aucune modification** de l'UI, de Rust ou du cœur (hormis l'enregistrement automatique par découverte).

## Pilotage externe (Stream Deck)
- Toute l'application doit rester pilotable depuis l'extérieur (Stream Deck, plus tard LLM local).
- Chaque action de l'UI passe par une **commande nommée** (registre unique), jamais par une logique propre à un composant.
- Chaque événement notable (début/fin de traitement, erreur, paramètres enregistrés, mise à jour…) passe par le **centre de notifications** ; toasts, notifications système et intégrations s'y abonnent.

## Règles de code — Clean Code
- Fonctions courtes à responsabilité unique ; noms explicites ; pas d'abréviations obscures.
- Séparation stricte : `service.py` = logique pure et testable sans fichiers réels ; `adapters.py` = I/O. Injection des adapters dans le service.
- Pas de valeurs magiques : constantes nommées ou config.
- Pas de code mort, pas de code commenté, pas de `TODO` sans numéro d'issue.
- Erreurs : exceptions métier typées dans `core/errors.py`, converties en événement `error` avec un message compréhensible par un non-développeur (quel fichier, quel problème, quoi faire). Jamais d'`except Exception: pass`.
- Commentaires pour le *pourquoi*, pas le *quoi*.
- DRY sans sur-abstraction : on factorise à la troisième répétition.

## Règles framework
**Python**
- Python 3.12, typage complet, `mypy --strict` sans `type: ignore` non justifié.
- pydantic v2 pour toute donnée qui traverse une frontière (CLI, fichiers, config).
- `pathlib.Path` partout ; chemins Windows (espaces, accents, chemins longs, UNC) gérés et testés.
- Pas d'état global ; logs via l'émetteur d'événements, pas de `print`.

**Tauri 2 / Rust**
- Rust = pont uniquement. Commandes Tauri fines, erreurs typées (`thiserror`), pas de `unwrap()` hors tests.
- Permissions/capabilities minimales dans `src-tauri/capabilities/`.
- Sidecar déclaré dans `bundle.externalBin`, lancé via `tauri-plugin-shell`.
- Updater : `tauri-plugin-updater`, endpoint `latest.json` des GitHub Releases, vérification au démarrage, installeur NSIS.

**React / TypeScript**
- TS `strict`, pas de `any`. Composants fonctionnels, hooks, pas de logique métier.
- Formulaires générés depuis les manifestes. Types des événements partagés et validés à la réception (zod).
- Appels Tauri isolés dans `ui/src/lib/tauri/`.

## Performance
- Traitements par lots parallélisés (`ProcessPoolExecutor`), taille configurable.
- Cache DWG → DXF par hash SHA-256 dans le dossier cache de l'app.
- PDF lu page par page ; XLSX en `read_only` quand possible.
- PDF : `pdfplumber` (texte + positions) et `pypdf` (fichiers intégrés). PyMuPDF est exclu (licence AGPL incompatible avec la diffusion de l'app).
- Progression émise au moins par fichier traité ; l'UI ne doit jamais geler.
- Tout traitement > 2 s sur les fixtures doit avoir un test de non-régression de durée raisonnable.

## Tests
- Chaque module : tests unitaires du service + tests d'intégration sur `fixtures/` comparant la sortie à un résultat attendu (golden files).
- Un bug corrigé = un test qui le reproduit.
- Pas de dépendance réseau dans les tests. ODA File Converter mocké dans les tests unitaires ; tests d'intégration DWG marqués `@pytest.mark.oda` (skippés si ODA absent).

## Git & GitHub
- Une issue = une branche = une PR (`feat/<n°>-<slug>`, `fix/…`, `chore/…`).
- Commits conventionnels : `feat(dwg-parts): …`, `fix(ui): …`, `chore(ci): …`.
- PR : `Closes #<n°>`, résumé court, comment tester.
- Ne jamais pousser sur `main` directement. Ne jamais forcer un push.
- Releases : tag `vX.Y.Z` (semver) → workflow `release.yml`.

## Interdits
- Logique métier dans l'UI ou dans Rust.
- Modifier les fichiers de l'utilisateur en place : toujours écrire dans le dossier de sortie.
- Committer des secrets, des clés ou des fichiers clients non anonymisés.
- Ajouter une dépendance lourde sans le justifier dans la PR.
