# Architecture

Les règles de code (nommage, tests, interdits) sont dans [CLAUDE.md](../CLAUDE.md). Ce document décrit comment les pièces s'assemblent.

```
┌──────────────── Fenêtre Tauri ────────────────┐        ┌─────────── Moteur Python (sidecar) ───────────┐
│ UI React (ui/)                                 │        │ engine/src/engine/                            │
│  formulaires générés · runs · toasts · chat    │ invoke │  cli.py ─ list-modules · run · settings ·     │
│        │                                       │ ─────▶ │           presets · templates · assistant ·   │
│        ▼                                       │        │           mcp · setup                         │
│ Pont Rust (src-tauri/) ─ lance le sidecar,     │ NDJSON │  core/      contrat, registre, réglages, lots │
│  relaie stdout, verrou, updater, API locale WS │ ◀───── │  modules/   dwg_parts · pdf_report · soumission│
└────────────────────────────────────────────────┘        │  assistant/ serveur MCP, client du modèle     │
        ▲ WebSocket 127.0.0.1                             │  setup/     analyse du poste, installations   │
 Stream Deck (streamdeck/)                                └───────────────────────────────────────────────┘
```

- **UI** : affichage uniquement. Tous les appels Tauri sont isolés dans `ui/src/lib/tauri/`.
- **Rust** : pont uniquement. Il lance le moteur, relaie sa sortie **sans l'interpréter** et gère ce qui doit rester natif : code d'accès, mises à jour, API locale, ouverture de fichiers et de pages.
- **Moteur** : toute la logique métier. Un processus par commande, et la sortie standard est réservée au protocole.

## Moteur

### Commandes CLI

| Commande | Sortie | Rôle |
|---|---|---|
| `list-modules` | JSON | Manifestes et schémas d'entrée des fonctionnalités |
| `run <id> --input --settings` | NDJSON | Exécute une fonctionnalité |
| `settings get\|set\|export\|read-import` | JSON | Paramètres par catégorie, export et import |
| `presets list\|save\|remove` | JSON | Préréglages |
| `templates list\|import\|remove\|set-default` | JSON | Bibliothèque de modèles de sortie |
| `assistant chat\|models` | NDJSON / JSON | Tour de conversation et modèles disponibles |
| `mcp --settings` | MCP stdio | Serveur MCP (outils de l'assistant) |
| `setup scan` / `setup run <action>` | JSON / NDJSON | Analyse du poste et installations |

### Événements NDJSON

Un événement par ligne, validé côté UI par zod :

- **Fonctionnalités et installations** : `progress`, `log`, `warning`, `result` et `error`. Une erreur contient le message, le fichier et un conseil.
- **Assistant** : `delta` (texte), `tool_call`, `tool_result`, `done` et `error`.

Chaque erreur métier est une `EngineError` typée, convertie en événement `error` compréhensible par un non-développeur. Les erreurs inattendues donnent un message générique, et le détail va sur stderr.

### Contrat de module

Une fonctionnalité correspond à un dossier `engine/src/engine/modules/<id>/`. Il expose un `MODULE = EngineModule(manifest, inputs_model, run, settings_model)`.

- **Manifeste** : `id`, nom, description, version, ordre de l'onglet, mode d'emploi, icône (`module|list|report|table|check`) et type de modèle (`xlsx|docx|None`).
- **Entrées** : un modèle pydantic dont chaque champ déclare son widget via `ui_field(kind, …)`. Les `kind` possibles sont `file`, `files`, `folder`, `folders`, `output_folder`, `template`, `text`, `number`, `bool`, `enum` et `mapping`. L'UI génère le formulaire depuis le JSON Schema.
- **Paramètres** (facultatif) : une sous-classe de `ModuleSettings`. Ils apparaissent dans leur propre catégorie des Paramètres.
- **`run(inputs, RunContext)`** : communique uniquement via `context.emit(...)` et renvoie un `ModuleResult`.

Le registre découvre les modules automatiquement. **Ajouter une fonctionnalité ne demande aucune modification de l'UI, de Rust ou du cœur** : l'onglet, le formulaire, les paramètres, les préréglages, l'outil de l'assistant et les commandes Stream Deck suivent.

### Briques partagées (`core/`)

- **Traitement par lots** : `batch.py`, un `ProcessPoolExecutor` dont la taille se règle dans Paramètres → Général. Les workers doivent être picklables.
- **Cache** : `cache.py`, indexé par le SHA-256 du fichier, pour les conversions DWG → DXF.
- **Collecte et nommage** : `collect.py` rassemble les fichiers et dossiers (sans doublons, sous-dossiers en option). `naming.py` applique la norme de nommage des fichiers produits.
- **Export Excel** : `xlsx.py`, avec une protection contre l'injection de formules.
- **Réglages** : `settings.py` et `settings_models.py`, dans un `settings.json` écrit de façon atomique. Un fichier corrompu n'est jamais écrasé.
- **Préréglages et modèles** : `presets.py` et `templates.py`.

### Bibliothèques

| Usage | Bibliothèque | Remarque |
|---|---|---|
| DXF | ezdxf | DWG converti au préalable par ODA File Converter (externe) |
| PDF | pdfplumber, pypdf | PyMuPDF exclu (licence AGPL) |
| Excel / Word | openpyxl, docxtpl | docxtpl en `StrictUndefined` |
| MCP | `mcp` (SDK officiel) | importé à la demande (~200 ms) |
| HTTP local | httpx | modèle local et API Ollama |

## Assistant local

```
Panneau de chat ─invoke─▶ Rust assistant_chat ─▶ engine assistant chat
                                                     │  ├─ HTTP ─▶ modèle local (API OpenAI : Ollama, LM Studio…)
                                                     │  └─ stdio ─▶ engine mcp (serveur MCP Drawflow)
                                                     ▼
                                     NDJSON : delta · tool_call · tool_result · done
```

- **Serveur MCP** (`assistant/mcp_server.py`) : il expose des outils en **lecture seule** générés depuis le registre (`list_features`, `list_presets`, `list_templates`). Les modules sont importés **avant** de démarrer la boucle stdio, sinon le serveur se bloque sous Windows (#81).
- **Boucle** (`assistant/agent.py`) : un tour envoie la conversation au modèle et exécute les appels d'outils demandés, puis recommence.
  - Au plus 6 séries d'appels par tour.
  - Historique limité à 40 messages.
  - Réponse d'outil tronquée à 20 000 caractères.
  - Délai de 60 s par requête MCP.
- **Confidentialité** : `AssistantSettings` refuse toute adresse qui ne désigne pas ce poste (loopback).
- **UI** :
  - reducer de conversation pur (`lib/assistant-chat.ts`) ;
  - Markdown léger rendu en éléments React, jamais en HTML injecté ;
  - une question à la fois, que Rust peut annuler.

## Installation du poste

- **Analyse** : `setup/scan.py` produit la liste des prérequis. Tous les accès au système passent par `setup/machine.py` (`Machine`), injectable, ce qui permet de tester sans dépendre du poste.
- **Actions** (`setup/actions.py`) :
  - liste blanche partagée avec Rust (`SetupAction`) ;
  - commandes passées en liste d'arguments, sans shell (`winget install --id ODA.ODAFileConverter|Ollama.Ollama`, `brew install --cask ollama`) ;
  - téléchargement d'un modèle via l'API Ollama `/api/pull`.
- **Pages de téléchargement** : la commande Rust `open_download_page` n'ouvre que les domaines officiels.

## UI

- **React 19** : `use()` + Suspense + ErrorBoundary pour les chargements, et `useRetryablePromise` pour réessayer.
- **Contextes** : `RunsProvider` (traitements en cours), `NotificationProvider` (centre de notifications et toasts), `CommandProvider` (commandes nommées), `PresetsProvider`, `UpdateProvider`.
- **Commandes nommées** (`lib/commands.ts`) : toute action pilotable de l'extérieur y est déclarée avec ses arguments (zod). L'interface, le Stream Deck et plus tard l'assistant passent par le même registre.

  `tab.open`, `preset.run`, `runs.cancel-all`, `result.open-last`, `settings.open`, `assistant.toggle`, `setup.open`, `update.install`, `app.state`.
- **Centre de notifications** : chaque événement notable y passe (traitement terminé, paramètres enregistrés, mise à jour, installation à faire…). Les toasts, les notifications système et l'API locale s'y abonnent.

## Rust (`src-tauri/`)

| Fichier | Rôle |
|---|---|
| `sidecar.rs` | Commandes ponctuelles (requêtes en liste blanche `EngineRequest`), traitements suivis (`start_streaming_run`), annulation |
| `runs.rs` | Registre des traitements : un traitement par fonctionnalité, arrêt de tous à la fermeture |
| `assistant.rs` | Un tour de conversation à la fois, annulable |
| `setup.rs` | Actions d'installation en liste blanche, pages de téléchargement autorisées |
| `access.rs` | Code d'accès (argon2id), délai croissant après échecs, désactivé en développement |
| `updates.rs` | Updater activé seulement si la configuration est injectée au build de release |
| `integrations/` | API locale WebSocket (`127.0.0.1`, jeton) — voir [api-locale.md](api-locale.md) |

Toutes les commandes qui touchent au moteur sont refusées tant que l'application est verrouillée.

## Stream Deck (`streamdeck/`)

Plugin Elgato SDK v3 (Node 20). C'est un client de l'API locale : connexion avec jeton, reconnexion progressive (2 → 15 s), touches dessinées en SVG (progression, vert/rouge, compteur). Protocole : [api-locale.md](api-locale.md).

## CI/CD

- **`ci.yml`**, sur chaque PR et chaque push sur `main` :
  - moteur, UI, Tauri + sidecar sur macOS et Windows, plugin Stream Deck ;
  - le smoke test exécute le sidecar figé de bout en bout : modules, handshake MCP, erreur de l'assistant ;
  - chaque job a un délai maximum.
- **`release.yml`**, sur un tag `v*` :
  - installeur NSIS signé pour l'updater et `latest.json` ;
  - plugin `.streamDeckPlugin` joint à la release.
- **Versions** : `scripts/version.py bump|check` garde alignées l'UI, Tauri, Cargo, le moteur et le plugin. Le manifeste Stream Deck utilise `X.Y.Z.0`.
