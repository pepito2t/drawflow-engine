# drawflow-engine

Application desktop Windows qui automatise les tâches d'un dessinateur en façade :

- **Liste de pièces** : plans DWG/DXF → liste Excel des pièces et quantités.
- **Rapport** : plans PDF → rapport Word (cartouche, références).
- **Soumission** : soumissions XLSX ou PDF avec XLSX joint → tableau normalisé.

S'y ajoutent un **assistant local** (modèle d'IA sur le poste, rien ne sort de la machine), un **écran Installation** qui installe les prérequis en un clic, des **préréglages**, et le pilotage par **Stream Deck**.

Stack : Tauri 2 · React + TypeScript · moteur Python (sidecar PyInstaller).

## Documentation

| Document | Pour qui | Contenu |
|---|---|---|
| [Guide utilisateur](docs/guide.md) | Utilisateur | Installer, utiliser chaque fonctionnalité, assistant, Stream Deck, dépannage |
| [Architecture](docs/architecture.md) | Développeur | Vue d'ensemble, flux principaux, décisions et leurs raisons, CI/CD |
| [API locale](docs/api-locale.md) | Intégrations | Protocole WebSocket (Stream Deck, outils tiers) |
| [Historique des versions](CHANGELOG.md) | Tous | Contenu de chaque version |
| [CLAUDE.md](CLAUDE.md) | Développeur | Règles de développement et commandes |

Règles de la documentation :

1. Un fichier par public, et une information à un seul endroit ; ailleurs, un lien.
2. Pas de valeurs que le code connaît déjà (réglages par défaut, listes de champs, versions) : on renvoie à l'application ou au code.
3. Le pourquoi plutôt que le quoi : chaque choix structurant va dans « Décisions » de l'architecture (une ligne, la raison, la PR).
4. Taille maximum : README ~80 lignes, guide et architecture ~300 lignes chacun. Au-delà, on coupe ; on ne crée un nouveau fichier que pour un nouveau public ou un contrat externe.
5. Mise à jour dans la PR qui change le comportement : `CHANGELOG.md` toujours, les autres documents s'ils sont concernés.

## Démarrer en développement

Prérequis : Node 22 + pnpm, Python 3.12 + uv, Rust stable.

```bash
pnpm install
(cd engine && uv sync)
pnpm dev            # construit le sidecar puis lance l'application
```

Tests et vérifications : voir la section « Commandes » de [CLAUDE.md](CLAUDE.md). En développement, le code d'accès et l'updater sont désactivés.

## Publier une version

1. `python scripts/version.py bump X.Y.Z` (UI, Tauri, Rust, moteur, plugin Stream Deck), commit via PR.
2. Une fois mergé : `git tag vX.Y.Z && git push origin vX.Y.Z`.
3. Le workflow `Release` construit l'installeur Windows (NSIS), publie la release avec `latest.json` signé et y joint le plugin `ch.drawflow.streamDeckPlugin`.

Prérequis (une fois) :
- `pnpm tauri signer generate`, puis les secrets `TAURI_SIGNING_PRIVATE_KEY` et `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`, et la variable `UPDATER_PUBKEY` (clé publique).
- Pour publier les releases dans un autre dépôt public : variables `RELEASES_OWNER` et `RELEASES_REPO`, secret `RELEASES_TOKEN` (droit `contents:write` sur ce dépôt).

L'endpoint de mise à jour (`releases/latest/download/latest.json`) ignore les pré-releases.
