# Historique des versions

Les numéros entre parenthèses renvoient aux pull requests GitHub.

## Non publié

## 0.9.2 — 2026-10-06

- **Journal de diagnostic** : chaque échec du moteur est enregistré dans `logs\engine.log` avec sa cause exacte (réponse du serveur de modèle, erreur système, trace interne) ; bouton **Journaux** dans Paramètres → Installation pour ouvrir le dossier (#157).

## 0.9.1 — 2026-10-06

- Correctif : quand le serveur du modèle refuse une demande, l'assistant affiche le message du serveur ; un modèle trop gros pour la mémoire du poste est signalé comme tel, avec le conseil de choisir le modèle recommandé. Le modèle par défaut est celui qui tient dans la mémoire du poste (plus `qwen3.5:9b` en dur). Un lancement depuis le Stream Dock ou l'assistant avec un champ obligatoire vide pré-remplit le formulaire au lieu d'échouer (#155).

## 0.9.0 — 2026-10-06

- Écran Installation plus lisible : boutons sous le texte quand la fenêtre est étroite, aide par icône, libellés sans redite, accent bleu-cyan propre à Drawflow ; l'onglet Intégrations devient **API locale** (en bas des Paramètres) ; l'indicateur de mise à jour n'apparaît plus quand l'updater n'est pas configuré (#152).
- **Plugin Drawflow pour Stream Dock sans configuration** : Installer le plugin active l'API locale, et le plugin lit lui-même le port et le jeton de Drawflow sur ce poste. Plus rien à copier dans les touches (#148).
- **Plugin AutoCAD pour Stream Dock** installable en un clic depuis Paramètres → Installation (dernière version publiée du projet streamdock_autocad). L'écran Installation signale les mises à jour disponibles des deux plugins Stream Dock (**Mettre à jour**) et affiche un badge vert quand un prérequis est prêt (#146).

## 0.8.2 — 2026-10-05

- Correctifs issus de l'audit (suite) : deux traitements lancés en même temps ne peuvent plus écrire le même fichier de sortie ; un échec d'export ne laisse plus de fichier vide ; les blocs imbriqués au-delà de 8 niveaux sont signalés par un avertissement au lieu d'être ignorés en silence ; erreurs disque lisibles pendant le téléchargement d'un installeur (#143).
- Assistant plus réactif : le raisonnement interne des modèles « pensants » (Qwen 3.x) est désactivé, et les rubriques du guide sont connues d'avance, ce qui évite un aller-retour avec le modèle pour chaque question d'aide (#144).
- Correctifs issus de l'audit : conversion DWG fiable quand plusieurs plans identiques sont traités en parallèle ; signature de l'éditeur vérifiée avant d'exécuter les installeurs ODA et Ollama ; seuls les fichiers produits par Drawflow peuvent être ouverts depuis l'app ; le jeton de l'API locale n'est plus lisible app verrouillée ; plus d'avertissement React au changement d'onglet ni d'erreur non gérée quand le modèle local ne répond pas (#141).

## 0.8.1 — 2026-10-05

- Correctif : **Installer ODA** télécharge l'installeur directement sur le site de l'éditeur (toujours la dernière version) au lieu de winget, dont le lien renvoyait une erreur 404. L'aide donne les liens de téléchargement d'ODA, d'Ollama et de Stream Dock (#114).
- Correctif : démarrage et ouverture des Paramètres nettement plus rapides. Le moteur n'est plus décompressé à chaque appel et ne charge les bibliothèques DWG, PDF et Excel qu'au lancement d'un traitement (#116).
- Correctif : **Installer Ollama** (Windows) télécharge l'installeur officiel avec sa progression au lieu de winget. La progression des installations et des téléchargements de modèles reste visible après avoir quitté puis rouvert l'écran (#119).

## 0.8.0 — 2026-10-05

- **Aide intégrée** : icône **?** qui affiche le guide, section **Premiers pas** (marche à suivre complète), liens **Marche à suivre** sur l'écran Installation, commande `help.open`. L'assistant lit le même guide (outils `list_help_topics` / `read_help`) pour expliquer comment faire (#112).

## 0.7.0 — 2026-10-05

- **Plugin Stream Dock (Mirabox)** à la place du plugin Elgato Stream Deck, qui ne correspondait pas à l'appareil de l'utilisateur. Installation automatique depuis **Paramètres → Installation** : Drawflow installe le plugin dans Stream Dock, il suffit de redémarrer Stream Dock (#109).

## 0.6.0 — 2026-10-05

- **Paramètres → Modèles d'IA** : recherche, téléchargement avec progression, utilisation et suppression des modèles ; « Choisir un modèle » depuis l'écran Installation ; commande `models.open` (#106).
- Modèle conseillé selon la mémoire du poste (famille Qwen 3.5), modèle par défaut `qwen3.5:9b` ; téléchargement et suppression de modèles par le moteur (#105).
- La conversation de l'assistant est conservée sur le poste entre deux lancements ; **+** l'efface (#102).

## 0.5.0 — 2026-10-05

- L'assistant peut **proposer** de lancer un préréglage ou une fonctionnalité ; rien ne démarre sans confirmation (#95).
- Carte de confirmation dans le chat : **Lancer** / **Ignorer** ; nouvelle commande `feature.run` (#96).
- Correctif : un téléchargement winget impossible (fichier retiré par l'éditeur, comme ODA 27.1) affiche un message clair qui renvoie vers la page officielle ; les accents de la sortie de winget sont lisibles (#99).

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
