# Guide utilisateur

Drawflow automatise trois tâches du dessinateur en façade : la **liste de pièces** (plans DWG/DXF → Excel), le **rapport** (plans PDF → Word) et la **soumission** (XLSX ou PDF → tableau normalisé). Tout se fait sur le poste : aucun fichier ne quitte la machine.

Les réglages et leurs valeurs par défaut sont décrits directement dans l'application (Paramètres) ; ce guide explique comment s'en servir.

## Premiers pas

La marche à suivre complète, dans l'ordre. Chaque étape renvoie à sa section.

1. **Installer Drawflow** et saisir le code d'accès (`0000` au départ) : [Installer Drawflow](#installer-drawflow).
2. **Ouvrir Paramètres → Installation** et régler chaque ligne marquée « À configurer » : [Installer les prérequis](#installer-les-prérequis).
   1. **ODA File Converter** (pour les DWG) : **Installer**, puis acceptez la demande d'autorisation de Windows. En cas d'échec, [téléchargez ODA](https://www.opendesign.com/guestfiles/oda_file_converter), installez-le, puis **Analyser à nouveau** et **Utiliser**.
   2. **Serveur du modèle** : **Installer** Ollama, puis **Démarrer** s'il ne répond pas.
   3. **Modèle** : **Choisir un modèle** ouvre Paramètres → Modèles d'IA ; téléchargez le modèle **Recommandé**, puis **Utiliser**.
3. **Adapter les fonctionnalités à votre norme** (blocs, champs, colonnes, noms de fichiers) dans Paramètres : [Adapter une fonctionnalité à votre norme](#adapter-une-fonctionnalité-à-votre-norme).
4. **Facultatif — Stream Dock** : [Piloter avec un Stream Dock](#piloter-avec-un-stream-dock).
5. **Lancer un premier traitement** depuis l'onglet d'une fonctionnalité : [Lancer une fonctionnalité](#lancer-une-fonctionnalité). Enregistrez-le comme préréglage pour le relancer en un clic.
6. **Poser une question à l'assistant** (icône bulle) : [Utiliser l'assistant](#utiliser-lassistant).

En cas de souci : [Dépannage](#dépannage).

### Langue

Paramètres → **Général** → **Langue** : `fr` ou `en`. L'interface change dès l'enregistrement ; la langue suit celle de Windows au premier lancement.

## L'écran Aujourd'hui

Drawflow s'ouvre sur **Aujourd'hui** : les prérequis manquants (bouton **Configurer**), les préréglages lançables en un clic, et les derniers traitements avec **Ouvrir le résultat** et **Relancer**. Commande `today.open` pour le Stream Dock ; l'assistant lit le même écran (« qu'est-ce qui m'attend ? »).

## Installer Drawflow

1. Téléchargez `Drawflow_X.Y.Z_x64-setup.exe` depuis la [dernière release](https://github.com/pepito2t/drawflow-engine/releases/latest) et lancez-le (installation pour l'utilisateur courant, sans droits administrateur).
2. Si Windows affiche « éditeur inconnu » (SmartScreen) : **Informations complémentaires → Exécuter quand même**. L'installeur n'est pas encore signé.
3. Saisissez le code d'accès (voir [Code d'accès](#code-daccès)).
4. Si un prérequis manque, le message **Configurer Drawflow** ouvre l'écran Installation.

## Installer les prérequis

**Paramètres → Installation** analyse le poste et propose pour chaque prérequis le bouton qui le règle : installer, démarrer, télécharger, ou ouvrir la page officielle.

| Prérequis | À quoi il sert | Téléchargement manuel |
|---|---|---|
| ODA File Converter | Lire les fichiers DWG (les DXF n'en ont pas besoin) | [Installeur Windows](https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_vc16_amd64dll.msi) · [Page officielle](https://www.opendesign.com/guestfiles/oda_file_converter) |
| Serveur du modèle local (Ollama ou LM Studio) et un modèle | Faire tourner l'assistant | [Ollama](https://ollama.com/download) |
| Logiciel Stream Dock *(facultatif)* | Piloter Drawflow, et AutoCAD, depuis un Stream Dock (Mirabox) | [Mirabox](https://mirabox.net/pages/download) · [Plugin AutoCAD](https://github.com/pepito2t/streamdock_autocad) |

- Sous Windows, **Installer** télécharge l'installeur officiel (dernière version) avec sa progression, puis l'installe ; Ollama fait environ 1,5 Go. Sous macOS, Ollama s'installe par Homebrew. Sinon, utilisez les liens ci-dessus.
- Vous pouvez quitter l'écran pendant une installation ou un téléchargement : la progression est toujours là en revenant.
- Drawflow demande confirmation avant d'installer un logiciel tiers (vous acceptez sa licence) et avant de télécharger un modèle (plusieurs Go).
- **Analyser à nouveau** après une installation manuelle.

## Lancer une fonctionnalité

1. Ouvrez l'onglet de la fonctionnalité ; son mode d'emploi est dans « Comment ça marche ».
2. Ajoutez les fichiers ou les dossiers (**Parcourir** ou glisser-déposer).
3. Renseignez le nom du projet et le dossier de sortie. Drawflow n'écrit **jamais** dans les fichiers d'origine.
4. Cliquez sur **Lancer**. Pour la liste de pièces et la soumission, l'**aperçu avant export** (coché par défaut) affiche d'abord le tableau : lignes à vérifier surlignées (cellule vide, montant illisible), filtre **Anomalies seulement**. **Exporter** écrit le fichier Excel ; **Annuler** n'écrit rien. Décochez l'aperçu dans un préréglage destiné au Stream Dock pour exporter directement.

À la fin, le bloc **avertissements à vérifier** liste, fichier par fichier, ce qui n'a pas pu être traité comme prévu : où (feuille, cartouche, bloc) et quoi faire. **Copier** met le rapport dans le presse-papiers pour l'envoyer. Les avertissements restent consultables dans l'Historique.

Vous pouvez changer d'onglet ou lancer une autre fonctionnalité pendant un traitement. L'icône **Traitements** (à côté de la roue) montre ceux en cours ; **Annuler** arrête un traitement. Un message signale la fin, et une notification Windows si le traitement a été long ou si Drawflow était en arrière-plan.

### Raccourcis clavier

| Raccourci | Effet |
|---|---|
| **Ctrl+Entrée** | Lance la fonctionnalité affichée, comme **Lancer** |
| **Ctrl+,** | Ouvre les paramètres |
| **F1** | Ouvre l'aide |

Dans la liste des onglets, les flèches **haut** et **bas** passent d'un onglet à l'autre, **Début** et **Fin** vont au premier et au dernier. Les raccourcis sont sans effet quand une fenêtre (Paramètres, Aide) est ouverte ; **Échap** la ferme.

### Historique

L'onglet **Historique** liste les derniers traitements (200 au plus) : date, durée, résultat ou erreur, nombre d'avertissements. **Ouvrir le résultat** ouvre le dernier fichier produit ; **Relancer** recharge les mêmes fichiers et relance ; **×** retire une ligne. Commandes `history.open` et `history.rerun` pour le Stream Dock et l'assistant.

### Plusieurs projets en une liste

Cochez **Un projet par dossier** dans la liste de pièces : chaque dossier de plans devient un projet (son nom), la liste reçoit une colonne **Projet**, et un onglet **Total** additionne les pièces identiques de tous les projets — pratique pour une commande fournisseur qui couvre plusieurs chantiers.

### Comparer deux indices de plans

L'onglet **Comparaison d'indices** prend les plans de l'indice précédent (A) et ceux du nouvel indice (B), établit les deux listes de pièces avec la norme de la liste de pièces, puis les compare : pièces **ajoutées**, **supprimées**, **quantités modifiées**, inchangées, et un onglet **Plans** (présent dans A, dans B, dans les deux). Les pièces sont rapprochées par les colonnes choisies dans Paramètres → Comparaison d'indices (par défaut « Référence »). Les plans numérotés (`01_facade-nord`, `facade-nord_02`) sont reconnus comme le même plan grâce au motif d'incrément, réglable au même endroit.

### Adapter une fonctionnalité à votre norme

Chaque fonctionnalité a sa catégorie dans les Paramètres :

- **Liste de pièces** : quels blocs retenir (jokers `*` et `?`), quel attribut AutoCAD remplit chaque colonne, comment compter et regrouper les pièces.
- **Rapport** : où se trouve le cartouche sur la page, quels champs y relever (libellé cherché, ou expression régulière avec le préfixe `re:`), format des références.
- **Soumission** : quels en-têtes reconnaître pour chaque colonne, quelles colonnes convertir en nombres.
- **Nom des fichiers exportés** : un modèle avec des variables (`{projet}`, `{date}`…), listées sous le champ.

**Exporter / Importer** dans chaque catégorie partage une norme entre postes.

### Modèles Excel et Word

**Paramètres → Modèles** : importez vos modèles et choisissez celui par défaut de chaque fonctionnalité. Un modèle choisi dans le formulaire est prioritaire. Les balises utilisables dans un modèle Word sont rappelées dans le mode d'emploi de l'onglet Rapport.

### Profil complet

Paramètres → **Profil** exporte en un zip toutes les normes, les modèles Excel et Word importés et les préréglages, sans le code d'accès ni le jeton de l'API locale. Sur un autre poste, **Importer un profil** affiche ce qui sera remplacé avant d'appliquer. Un profil venant d'une version plus récente de Drawflow est refusé : mettez d'abord l'application à jour.

### Préréglages

**Enregistrer comme préréglage** (en haut de l'onglet) mémorise le formulaire sous un nom, pour le recharger ou le lancer depuis le Stream Dock.

### Dossiers surveillés

Paramètres → **Automatisations** : choisissez un dossier et un préréglage. Dès qu'un plan, un PDF ou un fichier Excel y est déposé, le préréglage se lance avec ce fichier, une seule fois par fichier et une fois la copie terminée. L'application doit être ouverte et déverrouillée ; un dossier réseau est vérifié toutes les quelques secondes.

## Utiliser l'assistant

L'icône **bulle** ouvre le panneau de discussion. L'assistant répond aux questions sur Drawflow en consultant l'application.

Il peut aussi **proposer un lancement** (« lance la soumission sur C:\Chantier\Soumissions ») : une carte affiche la fonctionnalité et les entrées, et rien ne démarre tant que vous n'avez pas cliqué sur **Lancer**. Le traitement suit ensuite le circuit normal : progression dans Traitements, annulation, notification.

- Prérequis : un modèle local (voir [Installer les prérequis](#installer-les-prérequis)). L'adresse du serveur doit désigner ce poste : aucune donnée ne sort de la machine.
- **Paramètres → Modèles d'IA** recommande le modèle adapté à la mémoire du poste, et permet de chercher, télécharger, utiliser ou supprimer un modèle (ou d'en télécharger un autre de la bibliothèque Ollama par son nom).
- **Glissez un fichier dans le panneau** (plan, PDF, soumission, Word) : il apparaît comme pièce jointe du message ; l'assistant le lit sur le poste, dit ce qu'il contient et propose la fonctionnalité adaptée. Rien n'est copié ni envoyé.
- **Pourquoi cette pièce manque ?** L'assistant lit le traitement concerné (fichiers produits, avertissements avec fichier et endroit) et répond en citant la cause et le conseil.
- **Soumission non reconnue** : demandez à l'assistant d'associer les en-têtes du fichier aux colonnes ; il lit le fichier, propose les correspondances dans une carte, et **Appliquer** les enregistre dans Paramètres → Soumission. Rien n'est modifié sans ce clic.
- La liste en haut du panneau change de modèle. **Arrêter** interrompt une réponse, **+** démarre une nouvelle conversation. La conversation en cours est conservée sur le poste entre deux lancements (sans les cartes de lancement).

## Courriels (Exchange / Microsoft 365)

L'onglet **Courriels** conserve vos conversations sur ce poste, en lecture seule : Drawflow ne déplace, ne marque et ne supprime rien dans la boîte mail.

1. Paramètres → **Courriel** : collez l'identifiant d'application Entra ID (fourni par la personne qui administre Drawflow) ; le tenant reste `common` pour un compte professionnel.
2. Onglet Courriels → **Connecter la boîte mail** : ouvrez la page indiquée, saisissez le code affiché, connectez-vous avec le compte de la boîte. La session reste valable d'un lancement à l'autre.
3. **Récupérer les nouveaux messages** (ou la touche `mail.fetch` du Stream Dock) : les messages des derniers jours (réglable) sont rangés par conversation, pièces jointes comprises (sauf images et fichiers de plus de 25 Mo).
4. Ouvrez une conversation pour la lire ; **Exporter vers un dossier…** copie les messages lisibles et les pièces jointes dans un dossier de chantier ; **Retirer de Drawflow** efface la copie locale, jamais le courriel d'origine.

Les conversations sont dans `%APPDATA%\ch.drawflow.desktop\mail\` (dossier modifiable) ; au-delà du nombre réglé, les plus anciennes sont retirées.

## Piloter avec un Stream Dock

Drawflow fonctionne avec le **Stream Dock** de Mirabox (logiciel Stream Dock pour Windows).

1. **Paramètres → Installation → Plugin Drawflow pour Stream Dock → Installer le plugin** : Drawflow active son API locale et installe le plugin dans Stream Dock.
2. **Redémarrez Stream Dock** (il ne charge un nouveau plugin qu'au démarrage).
3. Dans Stream Dock, glissez une action de la catégorie **Drawflow** sur une touche ; pour une touche **Préréglage**, **Onglet** ou **Commande**, choisissez le préréglage, l'onglet ou la commande dans la liste.

Le plugin se connecte tout seul à Drawflow installé sur ce poste : il n'y a ni port ni jeton à saisir. Les champs de la touche ne servent que si Drawflow tourne sous un autre compte Windows (port et jeton dans Paramètres → API locale).

Les touches lancent un préréglage (progression, puis vert ou rouge ; un appui long sur un préréglage en cours annule ce traitement, la touche affiche « Annulation… »), ouvrent un onglet, annulent les traitements, ouvrent le dernier résultat ou comptent les traitements. La touche **Commande** envoie n'importe quelle commande sans argument de Drawflow (Aujourd'hui, Historique, Courriels, Relever les courriels, Assistant, Paramètres, Installation, Modèles d'IA, Aide, Mise à jour…) : la touche affiche le nom de la commande, une coche si Drawflow l'a exécutée, et la raison du refus sinon. Elles affichent « Verrouillé » tant que Drawflow est verrouillée, « Hors ligne » quand Drawflow est fermée ou que le port ne répond pas, et « Jeton invalide » quand Drawflow est ouverte mais que le jeton ou le port saisi dans la touche est incorrect : copiez le jeton depuis Paramètres → API locale. Après un appui refusé (préréglage supprimé, traitement déjà en cours…), la touche affiche la raison pendant trois secondes.

**Plugin AutoCAD** : la ligne **Plugin AutoCAD pour Stream Dock** installe de la même façon le plugin [streamdock_autocad](https://github.com/pepito2t/streamdock_autocad) : macros, calques, bascules (ORTHO, accrochages…) et état d'AutoCAD sur les touches. Il faut AutoCAD complet (pas LT), ouvert pendant l'utilisation.

**Mises à jour** : l'écran Installation affiche **Mise à jour** quand une version plus récente d'un plugin existe (après une mise à jour de Drawflow, ou une nouvelle version du plugin AutoCAD). Cliquez sur **Mettre à jour**, puis redémarrez Stream Dock.

## Code d'accès

Code initial : `0000`, à changer dans **Paramètres → Code d'accès**. Après plusieurs erreurs, un délai croissant est imposé.

**Code oublié** : fermez Drawflow et supprimez `access-code.json` dans `%APPDATA%\ch.drawflow.desktop\` ; le code redevient `0000`.

## Mises à jour

Au démarrage, Drawflow propose les nouvelles versions (**Mettre à jour** ou **Plus tard**). La mise à jour se télécharge pendant que vous travaillez ; elle ne s'installe que lorsqu'aucun traitement n'est en cours, arrête les processus du moteur encore ouverts (assistant, courriel), puis redémarre l'application. En cas d'échec du téléchargement, un nouveau clic relance la mise à jour.

## Ce que Drawflow vous a fait gagner

Paramètres → **À propos** compte les traitements terminés et les fichiers traités sur ce poste, par fonctionnalité, et en déduit un temps gagné (minutes par fichier réglables dans Général, compteurs désactivables). Rien n'est envoyé nulle part.

## Où sont les fichiers

| Contenu | Emplacement (Windows) |
|---|---|
| Paramètres, préréglages, historique des traitements, modèles importés, code d'accès, intégrations | `%APPDATA%\ch.drawflow.desktop\` |
| Compteurs d'utilisation (`stats.json`) | `%APPDATA%\ch.drawflow.desktop\` |
| Journaux de diagnostic (`engine.log`) | `%APPDATA%\ch.drawflow.desktop\logs\` |
| Cache des plans DWG convertis | `%LOCALAPPDATA%\drawflow\cache\` (modifiable dans Paramètres → Général) |

## Console et envoi des journaux au support

La **console** liste ce qui se passe dans Drawflow : messages des traitements, avertissements, erreurs, installations, assistant. Elle sert surtout à transmettre une erreur au support.

1. Cliquez sur **Console** en bas de la fenêtre. Un chiffre rouge indique les erreurs que vous n'avez pas encore vues.
2. Pour ne garder que l'essentiel, choisissez **Erreurs** ou **Avertissements et erreurs**, une source, ou tapez un mot dans **Rechercher**.
3. Sélectionnez les lignes utiles : clic sur une ligne, **Maj+clic** pour une plage, **Ctrl+clic** pour en ajouter. **Ctrl+A** sélectionne toutes les lignes affichées.
4. Cliquez sur **Copier la sélection** (ou **Ctrl+C**), ou sur **Tout copier** pour toutes les lignes correspondant aux filtres.
5. Collez (**Ctrl+V**) dans un courriel au support. La première ligne indique la version de Drawflow, le système et la date.

**Détacher** ouvre la console dans sa propre fenêtre, à garder à côté de l'application ; la fermer ne perd rien. **Effacer** vide la console. Les jetons et clés sont masqués avant d'apparaître ; le code d'accès n'y figure jamais. Sur un Stream Dock, une touche de commande `console.copy-errors` copie directement les dernières erreurs.

## Dépannage

| Problème | Solution |
|---|---|
| « ODA File Converter n'est pas configuré » | Paramètres → Installation → **Installer** ou **Utiliser** |
| L'installation d'ODA échoue | [Téléchargez l'installeur ODA](https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_vc16_amd64dll.msi), lancez-le, puis **Analyser à nouveau** et **Utiliser** |
| « Le modèle local ne répond pas » | Paramètres → Installation → **Démarrer**, ou lancez LM Studio |
| « Le modèle … est introuvable » | Paramètres → Installation → **Télécharger**, ou choisissez un modèle installé dans le panneau |
| « Le fichier de paramètres est illisible » | Il n'est jamais écrasé : restaurez une sauvegarde ou supprimez `settings.json` |
| Autre erreur, ou erreur qui se répète | **Console** → **Erreurs** → **Tout copier**, puis collez dans un courriel au support (voir [Console](#console-et-envoi-des-journaux-au-support)) ; au besoin, Paramètres → Installation → **Journaux** : envoyez `engine.log` (chaque échec y est noté avec la cause exacte, par exemple la réponse d'Ollama) |
| Touches Stream Dock « Hors ligne » | Lancez Drawflow et vérifiez que l'API locale est activée (Paramètres → API locale) |
| Touches Stream Dock « Jeton invalide » | Drawflow est ouverte mais refuse la touche : copiez le jeton depuis Paramètres → API locale dans les réglages de la touche, ou videz les champs si Drawflow tourne sous le même compte Windows |
