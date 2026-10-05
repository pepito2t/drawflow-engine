# Historique des versions

Les numéros entre parenthèses renvoient aux pull requests GitHub.

## Non publié

## 0.4.0 — 2026-10-05

- **Écran Installation** (Paramètres → Installation) : analyse du poste (système, ODA File Converter, serveur du modèle, modèle, Stream Deck) et installations en un clic. Il propose winget ou Homebrew, le démarrage d'Ollama, le téléchargement du modèle avec sa progression, le plugin Stream Deck et les pages officielles (#87, #88, #90).
- Message « Configurer Drawflow » au lancement s'il manque un prérequis ; commande `setup.open` (#90).
- Correctif : le bouton Enregistrer restait affiché sur les onglets Paramètres sans formulaire (#90).
- Documentation : guide utilisateur, architecture avec journal des décisions, historique des versions (#91).

## 0.3.0 — 2026-10-04

- **Assistant local** : panneau de discussion à droite, réponses en streaming, outils consultés visibles, choix du modèle installé en un clic (#80).
- Serveur MCP intégré au moteur : outils en lecture seule (fonctionnalités, préréglages, modèles) (#78).
- Connexion à un modèle local via une API compatible OpenAI (Ollama, LM Studio, llama.cpp), limitée à ce poste ; catégorie de paramètres Assistant (#79).
- Commande `assistant.toggle` pour le Stream Deck et l'API locale (#80).
- Correctif Windows : l'appel d'un outil de l'assistant bloquait indéfiniment ; délais maximum sur la CI, les tests et les requêtes MCP (#82).

## 0.2.0 — 2026-10-02

- **Préréglages** : enregistrer, recharger et lancer un jeu de paramètres (#69).
- **Commandes nommées** pour toute l'application, base du pilotage externe (#70).
- **API locale WebSocket** (127.0.0.1, jeton, refusée si l'app est verrouillée) (#71).
- **Plugin Stream Deck** : préréglages avec progression et résultat, onglets, annulation, dernier résultat, compteur (#72). Le plugin est joint à chaque release (#73).

## 0.1.0 — 2026-10-02

Première version.

- **Liste de pièces** (DWG/DXF → Excel) :
  - conversion DWG via ODA File Converter avec cache ;
  - blocs imbriqués et dynamiques ;
  - colonnes configurables, regroupement, modèle Excel (#37 à #42).
- **Rapport** (PDF → Word) :
  - cartouche et références relevés page par page ;
  - champs configurables ;
  - modèle Word à balises (#43 à #46).
- **Soumission** (XLSX / PDF avec XLSX joint → tableau normalisé) :
  - collecte multi-dossiers sans doublons ;
  - en-têtes reconnus configurables (#47 à #50).
- Paramètres par catégorie, export et import, normes de nommage des fichiers produits (#27 à #29).
- Traitements simultanés en arrière-plan, indicateur des traitements, notifications de fin (#30 à #32).
- Traitement par lots en parallèle, cache par hash SHA-256 (#35, #36).
- Code d'accès au démarrage (`0000` par défaut) (#34).
- Import de modèles Excel et Word (#61).
- Toasts, icônes de navigation, mise à jour automatique proposée au démarrage (#52, #54, #57).
- Installeur Windows (NSIS) et workflow de release (#51).
