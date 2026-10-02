# API locale (protocole v1)

API WebSocket qui permet de piloter Drawflow depuis un autre programme sur le même ordinateur (plugin Stream Deck, futur assistant local).

## Activation

Paramètres → **Intégrations** : activer l'API, choisir le port (défaut `51717`), copier le jeton.

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
| `runs.cancel-all` | — | Annule tous les traitements en cours |
| `result.open-last` | — | Ouvre le dernier fichier produit |
| `settings.open` | — | Ouvre les paramètres |
| `update.install` | — | Installe la mise à jour disponible |

## Événements diffusés

```json
{ "type": "event", "event": { "type": "runProgress", "moduleId": "dwg-parts", "current": 3, "total": 10 } }
{ "type": "locked", "locked": false }
```

Types d'événements : `runStarted`, `runProgress`, `runFinished` (`outcome` = `succeeded` | `failed` | `cancelled`, `outputs`), `presetRunRequested`, `updateAvailable`, `updateDeferred`, `settingsSaved`, `presetSaved`, `templateImported`, `settingsExported`, `accessCodeChanged`.
