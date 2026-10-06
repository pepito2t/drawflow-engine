# API locale (protocole v1)

API WebSocket qui permet de piloter Drawflow depuis un autre programme sur le même ordinateur (plugin Stream Dock, outils tiers).

## Activation

Paramètres → **API locale** : activer l'API, choisir le port (défaut `51717`), copier le jeton. Le plugin Stream Dock lit ces réglages tout seul ; la copie du jeton ne concerne que les outils tiers.

- Écoute **uniquement** sur `127.0.0.1` : jamais accessible depuis le réseau.
- Jeton obligatoire (48 caractères hexadécimaux), régénérable.
- Application verrouillée (code d'accès) : toutes les commandes sont refusées.

## Connexion

```
ws://127.0.0.1:51717
```

Premier message obligatoire (dans les 5 s) :

```json
{ "type": "hello", "token": "<jeton>", "version": 1 }
```

Réponse :

```json
{ "type": "welcome", "version": 1, "locked": false }
```

Jeton ou version invalide : `{ "type": "error", "message": "…" }` puis fermeture.

## Commandes

```json
{ "type": "command", "id": "42", "command": "preset.run", "args": { "presetId": "a1b2c3d4" } }
```

Réponse (même `id`) :

```json
{ "type": "result", "id": "42", "ok": true, "data": { } }
{ "type": "result", "id": "42", "ok": false, "error": "Ce préréglage n'existe plus." }
```

| Commande | Arguments | Effet |
|---|---|---|
| `app.state` | — | État : fonctionnalités, préréglages, traitements (renvoyé dans `data`) |
| `tab.open` | `moduleId` | Ouvre l'onglet et met l'app au premier plan |
| `preset.run` | `presetId` | Ouvre l'onglet, remplit le formulaire et lance le traitement |
| `feature.run` | `moduleId`, `inputs` | Ouvre l'onglet, remplit le formulaire avec `inputs` et lance le traitement |
| `runs.cancel-all` | — | Annule tous les traitements en cours |
| `result.open-last` | — | Ouvre le dernier fichier produit |
| `settings.open` | — | Ouvre les paramètres |
| `assistant.toggle` | — | Ouvre ou ferme le panneau de l'assistant |
| `setup.open` | — | Ouvre Paramètres → Installation |
| `models.open` | — | Ouvre Paramètres → Modèles d'IA |
| `help.open` | `topic` (facultatif) | Ouvre l'aide, sur une section du guide si `topic` est donné |
| `update.install` | — | Installe la mise à jour disponible |
| `mail.open` | — | Ouvre l'onglet Courriels |
| `mail.fetch` | — | Récupère les nouveaux messages de la boîte connectée (résultat dans `data`) |
| `automation.run` | `automationId`, `path` | Lance le préréglage d'un dossier surveillé avec ce fichier (émis par l'application elle-même) |

## Événements diffusés

```json
{ "type": "event", "event": { "type": "runProgress", "moduleId": "dwg-parts", "current": 3, "total": 10 } }
{ "type": "locked", "locked": false }
```

Types d'événements : `runStarted`, `runProgress`, `runFinished` (`outcome` = `succeeded` | `failed` | `cancelled`, `outputs`), `presetRunRequested`, `featureRunRequested`, `updateAvailable`, `updateDeferred`, `settingsSaved`, `presetSaved`, `templateImported`, `settingsExported`, `accessCodeChanged`.
