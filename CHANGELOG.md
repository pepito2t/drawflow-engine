# Historique des versions

Les numéros entre parenthèses renvoient aux pull requests GitHub.

## Non publié

## 0.21.0 — 2026-10-07

- **Console de journal pour le support** : bouton **Console** dans la barre d'état, avec le nombre d'erreurs non vues ; panneau ancré, détachable dans sa propre fenêtre ; filtres par niveau et par source, recherche, sélection de lignes, **Copier la sélection** et **Tout copier** (avec version et système en en-tête) pour coller le journal dans un courriel ; jeton de l'API locale et autres secrets masqués. Commandes `console.toggle`, `console.detach`, `console.copy-errors` (#214).
- **Stream Dock : touche « Commande »** qui lance n'importe quelle commande sans argument de l'application (Paramètres, Console, Historique, Récupérer les courriels…) ; **appui long** sur un préréglage en cours pour l'annuler ; commande `runs.cancel` par fonctionnalité (#209).
- **Erreurs en français et en anglais partout** : les erreurs de l'application et de l'API locale suivent la langue réglée, avec un message qui dit quoi faire ; le plugin Stream Dock les traduit aussi (#212).
- **Stream Dock** : « Jeton invalide » distingué de « Hors ligne » ; la raison d'un refus s'affiche 3 s sur la touche ; plugin en français et en anglais ; panneau de réglage unique ; touche Annuler en orange ; état resynchronisé après des événements perdus ; plugin deux fois plus léger (#204).
- **Parcours d'un traitement** : **Lancer** désactivé tant qu'un champ obligatoire manque, avec la liste des champs ; bouton **Ouvrir** sur chaque fichier produit ; un traitement réussi n'est plus affiché en échec à cause d'une ligne parasite ; annulation prise en compte dès le démarrage ; confirmation avant de supprimer un préréglage ou de vider l'historique, et avant de fermer les Paramètres modifiés ; une case cochée dans un module ne modifie plus celle d'un autre (#205).
- **Raccourcis et accessibilité** : Ctrl+Entrée lance la fonctionnalité affichée, Ctrl+, ouvre les Paramètres, F1 l'aide ; navigation au clavier dans les onglets et les dialogues ; interface fluide pendant un gros lot (seul le module actif se redessine, journal limité aux 500 dernières lignes) (#213).
- **Changement de langue sans perte** : les saisies en cours sont conservées ; enregistrer les Paramètres n'écrase plus ce qu'un autre écran vient de changer (#199).
- **Annulation propre** : le moteur reçoit d'abord une demande d'arrêt et n'est tué qu'après 5 s ; aucun document tronqué n'est laissé sous le nom final et aucune conversion ODA ne survit à l'annulation (#206, #210).
- **Chemins Windows longs et partages réseau** (`\\serveur\partage`) pris en charge à l'écriture des résultats ; un chemin trop long est expliqué au lieu de « dossier inaccessible » (#211).
- **Fichiers abîmés expliqués** : une feuille Excel corrompue, un disque plein, un dossier courriel verrouillé ou un document illisible donné à l'assistant nomment le fichier et la marche à suivre ; un traitement interrompu par une erreur interne apparaît dans l'Historique (#206).
- **Soumission** : progression affichée dès la lecture des fichiers sur les gros lots ; dates exportées en JJ.MM.AAAA (#202, #206).
- **Rapport PDF → DOCX** : zone de cartouche incohérente refusée avec un message clair ; libellé précédé d'un « ß » extrait au bon endroit (#202).
- **API locale plus robuste** : les événements continuent d'arriver pendant une commande longue ; connexions depuis un navigateur refusées, taille des messages et nombre de connexions limités ; redémarrage de l'API sans erreur de port (#203).
- **Application (audit)** : requêtes au moteur limitées dans le temps et arrêtées à la fermeture ; mise à jour téléchargée avant l'arrêt du moteur, nouvelle tentative possible après un échec ; réglages illisibles signalés au lieu d'être remplacés ; seuls les documents s'ouvrent directement, les autres fichiers sont montrés dans leur dossier (#198).
- **Correctifs moteur (audit)** : un fichier d'un préréglage déplacé ou supprimé devient un avertissement qui le nomme (liste de pièces, comparaison d'indices, rapport, soumission) au lieu d'une erreur interne ; un historique illisible ou non inscriptible n'échoue plus un traitement réussi ; un profil endommagé est refusé lisiblement et un fichier de réglages illisible bloque l'import avant toute écriture ; `setup scan` ne modifie plus `settings.json` (le modèle recommandé est dans le rapport et enregistré au téléchargement) ; courriels : jeton de session renouvelé enregistré immédiatement, date de dernière récupération prise avant le téléchargement, pièces jointes des messages déjà rangés non retéléchargées, message endommagé ignoré, Microsoft injoignable expliqué, fichier de session restreint au compte Windows (`icacls`) ; quantités infinies ou NaN signalées ; installeur absent ou bloqué expliqué ; plugin Stream Dock : membres `\` et `:` rejetés ; écritures JSON atomiques à nom unique avec `fsync` ; démarrage plus léger (openpyxl, pypdf, ezdxf, pdfplumber chargés seulement par les commandes qui lisent des documents) (#187).
- **Maintenance** : SDK MCP de l'assistant en version 2 (#215) ; argon2, password-hash et sha2 à jour, codes d'accès existants toujours valides (#207) ; compteurs d'usage calculés sur les seuls fichiers traités, dépendances du moteur déclarées (#202).
- **Chaîne de publication** : installeur allégé (tests et outils de développement exclus), release publiée en une fois avec le plugin, notes de version tirées du changelog, installeur NSIS en français et en anglais ; audit des dépendances Rust, npm et Python en CI ; installeur construit sur chaque PR qui touche l'application ; une release n'est publiée que si la CI du commit tagué est verte (#188, #208).

## 0.20.0 — 2026-10-06

- **Moteur en français ou en anglais** : messages, avertissements, étiquettes de formulaires, noms des fonctionnalités, feuilles Excel, écran d'installation et assistant suivent la langue réglée ; aide intégrée servie depuis le guide traduit ; `engine --lang en` en ligne de commande (#121).

## 0.19.0 — 2026-10-06

- **Interface en français ou en anglais** : réglage Paramètres → Général → Langue, appliqué immédiatement ; catalogue de messages typé (mêmes clés dans les deux langues) ; guide utilisateur traduit (`docs/guide.en.md`) (#121).

## 0.18.0 — 2026-10-06

- **Courriels Exchange / Microsoft 365** : connexion par code (OAuth, sans mot de passe stocké), récupération des messages rangés par conversation avec pièces jointes, lecture, export vers un dossier de chantier, retrait local ; commandes `mail.open` et `mail.fetch` (#134).

## 0.17.0 — 2026-10-06

- **Profil complet** (Paramètres → Profil) : export en zip des normes, modèles importés et préréglages ; import avec aperçu de ce qui est remplacé ; profil d'une version plus récente refusé (#129).
- **Compteurs locaux** (Paramètres → À propos) : traitements, fichiers et temps estimé gagné par fonctionnalité, calculés sur ce poste et désactivables ; minutes par fichier réglables (#133).
- **Dossiers surveillés** (Paramètres → Automatisations) : un plan, un PDF ou un fichier Excel déposé dans un dossier lance le préréglage choisi, une seule fois par fichier, après la fin de la copie ; dossiers réseau scrutés périodiquement (#126).
- **Fichiers glissés dans l'assistant** : pièces jointes visibles dans le message ; outil `inspect_file` (blocs d'un plan, pages et texte d'un PDF, feuilles d'un XLSX, paragraphes d'un DOCX) et proposition de la fonctionnalité adaptée (#159).
- **L'assistant lit les traitements** : outils `list_runs` et `read_run` — résultat, fichiers produits, avertissements avec fichier, endroit et conseil ; il répond à « pourquoi la pièce P-12 manque ? » en citant la source (#171).

## 0.16.0 — 2026-10-06

- **Soumission : en-têtes inconnus associés par l'assistant** — quand un fichier n'est pas reconnu, l'avertissement cite les en-têtes trouvés ; l'assistant peut inspecter le fichier (`inspect_submission_headers`) et proposer d'ajouter ces en-têtes aux colonnes (`propose_column_synonyms`), appliqué d'un clic (#169).

## 0.15.0 — 2026-10-06

- **Liste de pièces multi-projets** : option « Un projet par dossier » — colonne Projet et onglet Total toutes origines confondues (#168).

## 0.14.0 — 2026-10-06

- **Comparaison d'indices** : nouvelle fonctionnalité qui compare deux indices d'un jeu de plans DWG/DXF (ajouts, suppressions, quantités modifiées, plans présents dans chaque indice), avec aperçu avant export et fichier Excel à onglets. Les noms de plans incrémentés (`01_`, `_02`) sont rapprochés automatiquement (#166).

## 0.13.0 — 2026-10-06

- **Écran Aujourd'hui** à l'ouverture : prérequis à configurer, préréglages lançables en un clic, derniers traitements (ouvrir, relancer). Commande `today.open` ; outil `read_today` pour l'assistant (#165).

## 0.12.0 — 2026-10-06

- **Aperçu avant export** (liste de pièces, soumission) : le tableau s'affiche avant l'écriture du fichier Excel, lignes à vérifier surlignées avec leur raison, filtre « Anomalies seulement », puis **Exporter** ou **Annuler**. Case « Aperçu avant export » dans le formulaire, mémorisée par les préréglages (#164).

## 0.11.0 — 2026-10-06

- **Avertissements lisibles** : à la fin d'un traitement, un rapport par fichier indique l'anomalie, l'endroit (feuille, cartouche, bloc) et le conseil pour la corriger ; bouton **Copier** ; détail conservé dans l'Historique. Les messages des trois fonctionnalités ont été réécrits dans ce sens (#162).

## 0.10.0 — 2026-10-06

- **Historique des traitements** : onglet Historique (date, durée, résultat, avertissements), **Ouvrir le résultat**, **Relancer**, retrait d'une ligne ou vidage ; conservé entre deux lancements (200 entrées), commandes `history.open` / `history.rerun` (#160).

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
