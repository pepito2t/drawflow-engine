# Architecture

Comment les pièces s'assemblent et pourquoi. Les conventions de code et les commandes sont dans [CLAUDE.md](../CLAUDE.md) ; le détail de chaque composant est dans son code et ses tests.

## Vue d'ensemble

```
┌──────────────── Fenêtre Tauri ────────────────┐         ┌────────── Moteur Python (sidecar) ──────────┐
│ UI React (ui/) : formulaires générés, runs,    │ invoke  │ cli.py : une commande = un processus        │
│ toasts, chat, écran Installation               │ ──────▶ │ core/      contrat, registre, réglages      │
│ Pont Rust (src-tauri/) : lance le moteur,      │ NDJSON  │ modules/   une fonctionnalité par dossier   │
│ relaie sa sortie, verrou, updater, API locale  │ ◀────── │ assistant/ serveur MCP, client du modèle    │
└────────────────────────────────────────────────┘         │ setup/     analyse du poste, installations  │
        ▲ WebSocket 127.0.0.1 + jeton                       └─────────────────────────────────────────────┘
 Plugin Stream Dock (streamdock/)
```

| Couche | Rôle | Ne fait pas |
|---|---|---|
| UI | Affiche, valide (zod) ce qu'elle reçoit, déclare les commandes nommées | Logique métier ; appels Tauri hors de `ui/src/lib/tauri/` |
| Rust | Lance le moteur et relaie sa sortie telle quelle ; code d'accès, mises à jour, API locale, ouverture de fichiers et de pages | Interpréter les données du moteur |
| Moteur | Toute la logique métier | Écrire autre chose que le protocole sur stdout |

Liste des commandes du moteur : `engine --help`.

## Flux principaux

**Lancer une fonctionnalité.** L'UI génère le formulaire depuis le JSON Schema du module. Au lancement, Rust démarre `engine run <id>` et relaie chaque ligne NDJSON (`progress`, `log`, `warning`, `result`, `error`). L'UI les valide, met à jour le registre des traitements et publie les événements notables dans le centre de notifications.

**Ajouter une fonctionnalité.** Il suffit d'ajouter un dossier `engine/src/engine/modules/<id>/` qui expose `MODULE = EngineModule(...)`, puis de le tester. Le registre le découvre automatiquement. L'onglet, le formulaire, les paramètres, les préréglages, l'outil de l'assistant et le Stream Dock suivent sans aucune modification de l'UI, de Rust ou du cœur.

**Piloter de l'extérieur.** Chaque action pilotable est une commande nommée (`ui/src/lib/commands.ts`), utilisée à la fois par l'interface, le Stream Dock (via l'API locale, voir [api-locale.md](api-locale.md)) et plus tard l'assistant. Les événements notables passent par le centre de notifications : toasts, notifications système et API locale s'y abonnent.

**Assistant.**

```
chat ─▶ Rust assistant_chat ─▶ engine assistant chat ─┬─ HTTP ─▶ modèle local (API OpenAI : Ollama, LM Studio…)
                                                      └─ stdio ─▶ engine mcp (outils Drawflow, lecture seule)
```

Un tour envoie la conversation au modèle et exécute les outils demandés, puis recommence. Le nombre d'appels, l'historique, la taille des réponses d'outils et la durée des requêtes sont bornés. Les outils `propose_*` ne lancent rien : ils valident la demande et la boucle émet un événement `proposal`, que l'utilisateur confirme dans le chat.

**Installation du poste.** `engine setup scan` produit la liste des prérequis et les actions possibles. `engine setup run <action>` exécute une action de la liste blanche, partagée avec Rust.

## Décisions

| Décision | Raison | Réf. |
|---|---|---|
| Moteur Python en sidecar, Rust réduit au rôle de pont | Bibliothèques CAO/PDF/Office en Python ; un seul endroit pour la logique | #1 |
| Un processus par commande, NDJSON sur stdout | Isolement des pannes, annulation par simple arrêt du processus | #1 |
| Formulaires et paramètres générés depuis pydantic | Ajouter une fonctionnalité sans toucher l'UI | #1, #27 |
| pdfplumber + pypdf, pas PyMuPDF | Licence AGPL de PyMuPDF incompatible avec la diffusion | #43 |
| ODA File Converter externe | Seul convertisseur DWG gratuit ; configuré ou installé par l'écran Installation | #37, #88 |
| Cache DWG → DXF par SHA-256 | Ne reconvertir que les plans modifiés | #36 |
| Lots en `ProcessPoolExecutor` | Parallélisme réel ; workers picklables, `freeze_support` dans le binaire figé | #35 |
| `settings.json` écrit de façon atomique, jamais écrasé s'il est illisible | Ne jamais perdre une norme de l'utilisateur | #27 |
| Code d'accès en argon2id vérifié par Rust, désactivé en développement | Pas de crypto maison ; le moteur ne voit jamais le code | #34 |
| Commandes nommées + centre de notifications | Toute l'application pilotable de l'extérieur par un seul registre | #70 |
| API locale en WebSocket sur 127.0.0.1 avec jeton | Stream Dock et outils tiers, sans exposition réseau | #71 |
| Assistant via MCP (SDK officiel), modèle local par API compatible OpenAI | Fonctionne avec Ollama, LM Studio, llama.cpp ; outils générés depuis le registre | #78, #79 |
| `docs/guide.md` est la seule source d'aide : embarqué dans le sidecar, affiché par l'app, lu par l'assistant via MCP | L'aide de l'app et les réponses de l'assistant ne peuvent pas se contredire | #112 |
| L'assistant propose, l'utilisateur lance | Aucun traitement sans confirmation ; le lancement suit le même circuit que l'interface | #95 |
| Catalogue de modèles choisi + téléchargement par nom, pas de recherche dans la bibliothèque | Ollama n'a pas d'API de recherche publique ; recommandation selon la mémoire du poste | #105 |
| Adresse du modèle limitée au loopback | Aucune donnée ne quitte le poste | #79 |
| SDK MCP importé à la demande | ~200 ms de démarrage évités pour les autres commandes | #78 |
| Modules importés avant la boucle stdio MCP | Sous Windows, un import pendant une lecture bloquante de stdin figeait le serveur | #82 |
| Sidecar PyInstaller en dossier (`--onedir`), `_internal` livré en ressource à côté de l'exécutable ; pipelines importés à la demande | Un `--onefile` se décompresse à chaque appel (lent sous Windows, Defender) ; lister ou lire les réglages n'a pas besoin d'ezdxf/openpyxl/pdfplumber | #116 |
| Actions GitHub épinglées par SHA de commit, `permissions: contents: read` sur la CI | Un tag d'action peut être déplacé ; le workflow de release manipule la clé de signature de l'updater | #142 |
| Installations via winget / Homebrew, commandes en liste d'arguments | Sources officielles et intégrité vérifiée, pas d'injection shell | #88 |
| ODA et Ollama installés depuis l'installeur officiel (lien sans version), pas par winget | winget pointe vers des versions retirées (404) et n'affiche aucune progression ; le lien sans version suit toujours la dernière | #114, #119 |
| État des installations et téléchargements de modèles au niveau de l'application | Un traitement de plusieurs minutes survit au changement d'écran | #119 |
| Pages de téléchargement en liste blanche côté Rust | L'UI ne peut pas ouvrir une URL arbitraire | #90 |
| Plugin pour Stream Dock (Mirabox), installé par Drawflow dans `%APPDATA%\HotSpot\StreamDock\plugins` | C'est l'appareil de l'utilisateur ; même protocole que le SDK Stream Deck, sans fichier d'installation à double-cliquer | #109 |
| Délais maximum en CI, tests et requêtes MCP | Un blocage échoue vite au lieu de figer la CI ou l'application | #82 |
| Updater activé seulement par la configuration de release | Aucune mise à jour en développement ; clé publique injectée par la CI | #52 |

## CI/CD

- **`ci.yml`** : moteur, UI, Tauri + sidecar sur macOS et Windows, plugin Stream Dock. Le smoke test exécute le binaire figé de bout en bout : modules, handshake MCP, erreur de l'assistant.
- **`release.yml`**, sur un tag `v*` : installeur NSIS, `latest.json` signé et plugin Stream Dock joint (`ch.drawflow.sdPlugin.zip`). Procédure dans le [README](../README.md#publier-une-version).
- **`scripts/version.py`** garde toutes les versions alignées (UI, Tauri, Cargo, moteur, plugin).
