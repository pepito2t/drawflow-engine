# Prompt de démarrage — Claude Code

> À coller dans Claude Code, à la racine d'un repo vide (déjà créé sur GitHub et cloné).
> Pré-requis côté machine : `gh` CLI authentifié (`gh auth status`), `uv`, `pnpm`, Rust (`rustup`).

---

Tu es le développeur principal d'une application desktop Windows destinée à un **dessinateur en façade**. Il travaille avec AutoCAD (plans DWG), des plans PDF, et produit des listes de pièces (XLSX), des rapports (DOCX) et des soumissions (XLSX ou PDF contenant un XLSX en pièce jointe). L'application automatise ces tâches. Elle doit être **performante et fiable avant d'être jolie**, et **évolutive** : de nouvelles fonctionnalités seront ajoutées régulièrement.

Le développeur travaille sous **macOS** ; l'utilisateur final est sous **Windows**. Les builds Windows se font exclusivement via **GitHub Actions**.

## Objectifs fonctionnels (v1)

1. **Liste de pièces depuis DWG** : à partir d'un ou plusieurs fichiers/dossiers DWG, extraire les blocs et leurs attributs, agréger les quantités, exporter un XLSX selon un template.
2. **Rapport automatique** : extraire des données de plans PDF (cartouche, cotes, références, textes) et générer un DOCX à partir d'un template Word à balises.
3. **Soumission** : lire une soumission XLSX, ou un PDF qui contient un ou plusieurs XLSX en pièce jointe, potentiellement répartis dans **plusieurs dossiers** ; normaliser et exporter les données.
4. **Interface** : pour chaque fonctionnalité, des champs d'entrée (fichier, dossier, liste de chemins, template, dossier de sortie) avec bouton « Parcourir » et glisser-déposer, un bouton Lancer, une barre de progression, un journal d'erreurs lisible.
5. **Mise à jour automatique** : l'app vérifie au démarrage si une nouvelle version existe et s'installe sans retéléchargement manuel.

## Stack imposée

- **Shell desktop** : Tauri 2 (Rust minimal) + plugins officiels `dialog`, `shell` (sidecar), `updater`, `process`, `fs`.
- **UI** : React + TypeScript strict + Vite, pnpm. Pas de bibliothèque UI lourde ; CSS simple. Interface générée dynamiquement à partir des manifestes de modules.
- **Moteur** : Python 3.12, géré avec `uv`, packagé en exécutable unique avec PyInstaller et embarqué comme **sidecar** Tauri.
  - DWG : ODA File Converter (externe, chemin configurable) pour DWG → DXF, puis `ezdxf`.
  - PDF : `PyMuPDF` (texte, blocs, fichiers intégrés) ; `pdfplumber` si besoin de tableaux.
  - DOCX : `docxtpl`. XLSX : `openpyxl`.
  - Validation et contrats : `pydantic` v2.
- **Qualité** : `ruff` (lint + format), `mypy --strict`, `pytest` ; ESLint + Prettier + `tsc --noEmit` ; `cargo fmt` + `cargo clippy -D warnings`.
- **CI/CD** : GitHub Actions. CI sur chaque PR (macOS + Windows). Release sur tag `v*` via `tauri-apps/tauri-action` sur `windows-latest` : build du sidecar PyInstaller, installeur NSIS, publication dans GitHub Releases avec `latest.json` signé pour l'updater.

## Architecture imposée

- Le moteur Python est une **CLI** sans état :
  - `engine list-modules` → JSON : manifestes de tous les modules.
  - `engine run <module_id> --input <fichier.json>` → émet sur stdout un flux **NDJSON** d'événements typés (`progress`, `log`, `warning`, `result`, `error`).
- Chaque fonctionnalité est un **module** isolé dans `engine/src/engine/modules/<id>/` qui implémente un contrat commun (manifeste + schéma d'entrée pydantic + `run()`). Ajouter une fonctionnalité = ajouter un dossier, **sans modifier le cœur ni l'UI**.
- L'UI ne contient **aucune logique métier** : elle lit les manifestes, génère les formulaires, appelle le sidecar, affiche les événements.
- Rust ne fait que le pont (lancer le sidecar, relayer les événements, updater). Pas de logique métier en Rust.
- Performance : traitement par lots en parallèle (`ProcessPoolExecutor`) ; cache des conversions DWG → DXF par hash de fichier ; lecture PDF page par page ; jamais de fichier entier chargé en mémoire quand un flux suffit.

Le détail des règles est dans `CLAUDE.md`, que tu dois créer en premier (contenu fourni ci-dessous par l'utilisateur — reprends-le tel quel, puis complète les commandes réelles une fois le scaffolding fait).

## Déroulé attendu — respecte cet ordre

### Phase 0 — Questions
Avant d'écrire du code, pose-moi en une seule fois les questions bloquantes. Au minimum :
- nom du repo GitHub (owner/repo) ;
- noms des attributs de blocs AutoCAD utilisés pour les pièces (si je ne sais pas, prévois une config de mapping) ;
- champs attendus dans le rapport et dans la soumission ;
- présence de fixtures (vrais fichiers anonymisés) dans `fixtures/`.

### Phase 1 — Fondations
1. Crée `CLAUDE.md`.
2. Scaffold le monorepo (structure ci-dessous), les configs de lint/format/typecheck/tests, un module d'exemple `hello` qui traverse toute la chaîne UI → Rust → sidecar → événements.
3. CI GitHub Actions pour les PR.
4. Commit sur une branche `chore/bootstrap`, ouvre la PR avec `gh pr create`.

### Phase 2 — Backlog GitHub
Avec `gh`, crée :
- **Labels** : `type:feature`, `type:chore`, `type:bug`, `type:test`, `type:docs`, `area:ui`, `area:engine`, `area:tauri`, `area:ci`, `module:dwg-parts`, `module:pdf-report`, `module:soumission`, `priority:high`, `priority:low`.
- **Milestones** (via `gh api repos/{owner}/{repo}/milestones`) : `M0 Fondations`, `M1 Liste de pièces DWG`, `M2 Rapport PDF → DOCX`, `M3 Soumission`, `M4 Distribution & mises à jour`.
- **Issues** : une issue par unité livrable en une PR (≤ ~400 lignes modifiées). Chaque issue suit ce gabarit, écrit dans un fichier temporaire puis passé via `gh issue create --body-file` :

```
## Contexte
## Objectif
## Critères d'acceptation
- [ ] ...
## Tâches techniques
- [ ] ...
## Tests attendus
## Dépendances
Bloquée par #...
```

Ordonne les dépendances. Montre-moi la liste des issues (titre, milestone, labels) **avant** de les créer, attends ma validation, puis crée-les.

### Phase 3 — Implémentation, issue par issue
Pour chaque issue, dans l'ordre des dépendances :
1. Branche `feat/<n°>-<slug>` (ou `fix/`, `chore/`).
2. Écris d'abord les tests (fixtures → sortie attendue), puis le code.
3. Lance lint + typecheck + tests ; tout doit passer.
4. Commits conventionnels (`feat(dwg-parts): ...`), PR avec `Closes #<n°>` et un résumé court.
5. Ne passe à l'issue suivante qu'après mon accord ou si je t'ai demandé d'enchaîner.

## Actions humaines à me signaler (ne les simule pas)
- Génération de la clé de signature updater (`pnpm tauri signer generate`) et ajout des secrets GitHub `TAURI_SIGNING_PRIVATE_KEY` / `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`.
- Installation d'ODA File Converter sur le poste Windows.
- Éventuel certificat de signature de code Windows (Azure Trusted Signing).
- Fourniture de fixtures réelles.

Commence par la Phase 0.
