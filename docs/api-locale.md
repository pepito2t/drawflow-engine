# API locale (protocole v1)

API WebSocket qui permet de piloter Drawflow depuis un autre programme sur le même ordinateur (plugin Stream Dock, outils tiers).

Les tableaux de commandes et d'événements sont tenus à jour par un test (`ui/src/lib/api-doc.test.ts`) qui compare ce fichier aux registres `ui/src/lib/commands.ts` et `ui/src/lib/app-events.ts`.

## Activation

Paramètres → **API locale** : activer l'API, choisir le port (défaut `51717`, minimum `1024`), copier le jeton. Le plugin Stream Dock lit ces réglages tout seul ; la copie du jeton ne concerne que les outils tiers.

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

Jeton ou version invalide : `{ "type": "error", "code": "invalidToken", "message": "…" }` puis la connexion est **abandonnée sans trame `Close`** (fin de flux TCP). Un client qui reçoit `error` avant `welcome` doit considérer son jeton comme refusé et ne pas se reconnecter en boucle avec le même.

### Refus et limites

| Situation | Comportement du serveur |
|---|---|
| Poignée de main avec un en-tête `Origin` (page web dans un navigateur) | Refusée avec HTTP `403` : seuls les programmes locaux, qui n'envoient pas cet en-tête, peuvent se connecter |
| Plus de 8 connexions simultanées (authentifiées ou non) | La connexion TCP en trop est fermée sans poignée de main |
| Message ou trame de plus de 64 Kio reçu | Connexion fermée |
| Aucun message ni `Pong` reçu pendant 60 s | Connexion fermée ; le serveur envoie un `Ping` toutes les 30 s, un client standard y répond automatiquement |
| Hello absent après 5 s | Connexion fermée |

## Commandes

```json
{ "type": "command", "id": "42", "command": "preset.run", "args": { "presetId": "a1b2c3d4" } }
```

Réponse (même `id`) :

```json
{ "type": "result", "id": "42", "ok": true, "data": { } }
{ "type": "result", "id": "42", "ok": false, "error": "Ce préréglage n'existe plus." }
{ "type": "result", "id": "42", "ok": false, "code": "locked", "error": "Drawflow is locked: enter the access code in the application." }
```

- **Délai de réponse : 15 s.** Au-delà, le serveur répond `ok: false` avec le code `noReply` ; la commande a pu être exécutée quand même.
- Les commandes sont traitées **en parallèle** : les réponses peuvent arriver dans un autre ordre que les envois, et les événements continuent d'être diffusés pendant qu'une commande attend. Le client associe chaque réponse à sa commande par `id`.
- Message qui n'est ni `hello` ni `command` : `{ "type": "error", "code": "unknownMessage", "message": "…" }`, connexion conservée.
- Application verrouillée : `ok: false` avec le code `locked`.

### Codes d'erreur

Les erreurs produites par Drawflow lui-même portent un champ `code` stable, à traduire côté client. `message` (pour `error`) et `error` (pour `result`) restent présents : texte anglais de secours pour les clients qui ne connaissent pas le code. Un `result` en échec **sans** `code` vient d'une commande de l'application : son `error` est déjà rédigé dans la langue de l'application et s'affiche tel quel. Un client doit afficher le texte reçu pour tout code qu'il ne connaît pas.

| Code | Message | Signification |
|---|---|---|
| `invalidToken` | `error` | Jeton ou version de protocole refusés ; la connexion est abandonnée |
| `unknownMessage` | `error` | Message qui n'est ni `hello` ni `command` |
| `locked` | `result` | Application verrouillée : saisir le code d'accès dans Drawflow |
| `noReply` | `result` | L'application n'a pas répondu dans les 15 s |
| `statePoisoned`, `appError` | `result` | Erreur interne de Drawflow : redémarrer l'application |

| Commande | Arguments | Effet |
|---|---|---|
| `app.state` | — | État : fonctionnalités, préréglages, traitements (renvoyé dans `data`) |
| `tab.open` | `moduleId` | Ouvre l'onglet et met l'app au premier plan |
| `preset.run` | `presetId` | Ouvre l'onglet, remplit le formulaire et lance le traitement |
| `feature.run` | `moduleId`, `inputs` | Ouvre l'onglet, remplit le formulaire avec `inputs` et lance le traitement |
| `feature.run-current` | — | Lance la fonctionnalité affichée avec les valeurs de son formulaire (raccourci Ctrl+Entrée) |
| `runs.cancel-all` | — | Annule tous les traitements en cours |
| `runs.cancel` | `moduleId` | Annule le traitement en cours de cette fonctionnalité (sans effet si elle ne traite rien) |
| `result.open-last` | — | Ouvre le dernier fichier produit |
| `history.open` | — | Ouvre l'onglet Historique |
| `history.rerun` | `entryId` | Relance un traitement de l'historique avec les mêmes fichiers |
| `today.open` | — | Ouvre l'écran Aujourd'hui |
| `settings.open` | — | Ouvre les paramètres |
| `settings.add-synonyms` | `columns` (objet : nom de colonne → liste de synonymes) | Ajoute des synonymes de colonnes aux réglages et diffuse `settingsSaved` |
| `assistant.toggle` | — | Ouvre ou ferme le panneau de l'assistant |
| `setup.open` | — | Ouvre Paramètres → Installation |
| `models.open` | — | Ouvre Paramètres → Modèles d'IA |
| `help.open` | `topic` (facultatif) | Ouvre l'aide, sur une section du guide si `topic` est donné |
| `update.install` | — | Installe la mise à jour disponible |
| `mail.open` | — | Ouvre l'onglet Courriels |
| `mail.fetch` | — | Récupère les nouveaux messages de la boîte connectée (résultat dans `data`) |
| `console.toggle` | — | Ouvre ou ferme la console au pied de l'application et met l'app au premier plan |
| `console.detach` | — | Ouvre la console dans sa propre fenêtre (ou la ramène au premier plan) |
| `console.copy-errors` | — | Copie dans le presse-papiers les dernières erreurs de la console, prêtes à coller dans un courriel (`data.copied` : nombre d'erreurs) ; `ok: false` s'il n'y en a aucune |
| `automation.run` | `automationId`, `path` | Lance le préréglage d'un dossier surveillé avec ce fichier (émis par l'application elle-même) |

## Événements diffusés

```json
{ "type": "event", "event": { "type": "runProgress", "moduleId": "dwg-parts", "current": 3, "total": 10 } }
{ "type": "locked", "locked": false }
```

`locked` est envoyé à chaque verrouillage ou déverrouillage de l'application. Les autres événements sont enveloppés dans `event`, avec leur `type` et leurs champs :

| Événement | Champs | Quand |
|---|---|---|
| `runStarted` | `moduleId`, `moduleName` | Un traitement démarre |
| `runProgress` | `moduleId`, `current`, `total` | Progression d'un traitement |
| `runFinished` | `moduleId`, `moduleName`, `outcome` (`succeeded` \| `failed` \| `cancelled`), `message` (résumé ou erreur lisible), `durationMs`, `outputs` (chemins produits) | Un traitement se termine |
| `presetRunRequested` | `presetId`, `moduleId` | Un préréglage est lancé par commande |
| `featureRunRequested` | `moduleId`, `inputs` | Une fonctionnalité est lancée par commande |
| `formRunRequested` | `moduleId` | La fonctionnalité affichée est lancée avec son formulaire (`feature.run-current`) |
| `featureRunIncomplete` | `moduleId`, `moduleName`, `missing` (champs manquants) | `feature.run` ou `history.rerun` n'a pas pu lancer le traitement : le formulaire reste ouvert |
| `updateAvailable` | `version` | Une mise à jour est disponible |
| `updateDeferred` | — | L'utilisateur a remis la mise à jour à plus tard |
| `settingsSaved` | — | Les réglages ont été enregistrés |
| `presetSaved` | `name` | Un préréglage a été créé ou modifié |
| `templateImported` | `name` | Un modèle a été importé |
| `settingsExported` | `target` | Les réglages ont été exportés |
| `accessCodeChanged` | — | Le code d'accès a été modifié |
| `setupNeeded` | `missing` (nombre de prérequis manquants) | L'installation est incomplète |
| `mailFetched` | `added` (nombre de messages ajoutés) | Une récupération de courriels s'est terminée |
| `resync` | — | Le client a manqué des événements (voir ci-dessous) : il doit redemander `app.state` |

### Tampon d'événements

Chaque connexion dispose d'un tampon de **256 événements**. Si le client ne les lit pas assez vite (traitement par lots très rapide, client suspendu), les événements en trop sont perdus et le serveur envoie `{ "type": "event", "event": { "type": "resync" } }` à la place. Le client doit alors redemander `app.state` pour retrouver l'état exact des traitements.
