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
4. Cliquez sur **Lancer**.

Vous pouvez changer d'onglet ou lancer une autre fonctionnalité pendant un traitement. L'icône **Traitements** (à côté de la roue) montre ceux en cours ; **Annuler** arrête un traitement. Un message signale la fin, et une notification Windows si le traitement a été long ou si Drawflow était en arrière-plan.

### Adapter une fonctionnalité à votre norme

Chaque fonctionnalité a sa catégorie dans les Paramètres :

- **Liste de pièces** : quels blocs retenir (jokers `*` et `?`), quel attribut AutoCAD remplit chaque colonne, comment compter et regrouper les pièces.
- **Rapport** : où se trouve le cartouche sur la page, quels champs y relever (libellé cherché, ou expression régulière avec le préfixe `re:`), format des références.
- **Soumission** : quels en-têtes reconnaître pour chaque colonne, quelles colonnes convertir en nombres.
- **Nom des fichiers exportés** : un modèle avec des variables (`{projet}`, `{date}`…), listées sous le champ.

**Exporter / Importer** dans chaque catégorie partage une norme entre postes.

### Modèles Excel et Word

**Paramètres → Modèles** : importez vos modèles et choisissez celui par défaut de chaque fonctionnalité. Un modèle choisi dans le formulaire est prioritaire. Les balises utilisables dans un modèle Word sont rappelées dans le mode d'emploi de l'onglet Rapport.

### Préréglages

**Enregistrer comme préréglage** (en haut de l'onglet) mémorise le formulaire sous un nom, pour le recharger ou le lancer depuis le Stream Dock.

## Utiliser l'assistant

L'icône **bulle** ouvre le panneau de discussion. L'assistant répond aux questions sur Drawflow en consultant l'application.

Il peut aussi **proposer un lancement** (« lance la soumission sur C:\Chantier\Soumissions ») : une carte affiche la fonctionnalité et les entrées, et rien ne démarre tant que vous n'avez pas cliqué sur **Lancer**. Le traitement suit ensuite le circuit normal : progression dans Traitements, annulation, notification.

- Prérequis : un modèle local (voir [Installer les prérequis](#installer-les-prérequis)). L'adresse du serveur doit désigner ce poste : aucune donnée ne sort de la machine.
- **Paramètres → Modèles d'IA** recommande le modèle adapté à la mémoire du poste, et permet de chercher, télécharger, utiliser ou supprimer un modèle (ou d'en télécharger un autre de la bibliothèque Ollama par son nom).
- La liste en haut du panneau change de modèle. **Arrêter** interrompt une réponse, **+** démarre une nouvelle conversation. La conversation en cours est conservée sur le poste entre deux lancements (sans les cartes de lancement).

## Piloter avec un Stream Dock

Drawflow fonctionne avec le **Stream Dock** de Mirabox (logiciel Stream Dock pour Windows).

1. **Paramètres → Intégrations** : activez l'API locale et copiez le jeton.
2. **Paramètres → Installation → Plugin Stream Dock → Installer le plugin** : Drawflow installe lui-même le plugin dans Stream Dock.
3. **Redémarrez Stream Dock** (il ne charge un nouveau plugin qu'au démarrage).
4. Dans Stream Dock, glissez une action de la catégorie **Drawflow** sur une touche.
5. Dans les réglages de la touche, saisissez le port (`51717` par défaut) et collez le jeton : une seule fois pour toutes les touches.
6. Pour une touche **Préréglage** ou **Onglet**, choisissez le préréglage ou l'onglet dans la liste.

Les touches lancent un préréglage (progression, puis vert ou rouge), ouvrent un onglet, annulent les traitements, ouvrent le dernier résultat ou comptent les traitements. Elles affichent « Verrouillé » tant que Drawflow est verrouillée et « Hors ligne » quand Drawflow est fermée ou que le jeton est faux.

**Plugin AutoCAD** : la ligne **Plugin AutoCAD pour Stream Dock** installe de la même façon le plugin [streamdock_autocad](https://github.com/pepito2t/streamdock_autocad) : macros, calques, bascules (ORTHO, accrochages…) et état d'AutoCAD sur les touches. Il faut AutoCAD complet (pas LT), ouvert pendant l'utilisation.

**Mises à jour** : l'écran Installation affiche **Mise à jour** quand une version plus récente d'un plugin existe (après une mise à jour de Drawflow, ou une nouvelle version du plugin AutoCAD). Cliquez sur **Mettre à jour**, puis redémarrez Stream Dock.

## Code d'accès

Code initial : `0000`, à changer dans **Paramètres → Code d'accès**. Après plusieurs erreurs, un délai croissant est imposé.

**Code oublié** : fermez Drawflow et supprimez `access-code.json` dans `%APPDATA%\ch.drawflow.desktop\` ; le code redevient `0000`.

## Mises à jour

Au démarrage, Drawflow propose les nouvelles versions (**Mettre à jour** ou **Plus tard**). La mise à jour attend la fin des traitements en cours puis redémarre l'application.

## Où sont les fichiers

| Contenu | Emplacement (Windows) |
|---|---|
| Paramètres, préréglages, modèles importés, code d'accès, intégrations | `%APPDATA%\ch.drawflow.desktop\` |
| Cache des plans DWG convertis | `%LOCALAPPDATA%\drawflow\cache\` (modifiable dans Paramètres → Général) |

## Dépannage

| Problème | Solution |
|---|---|
| « ODA File Converter n'est pas configuré » | Paramètres → Installation → **Installer** ou **Utiliser** |
| L'installation d'ODA échoue | [Téléchargez l'installeur ODA](https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_vc16_amd64dll.msi), lancez-le, puis **Analyser à nouveau** et **Utiliser** |
| « Le modèle local ne répond pas » | Paramètres → Installation → **Démarrer**, ou lancez LM Studio |
| « Le modèle … est introuvable » | Paramètres → Installation → **Télécharger**, ou choisissez un modèle installé dans le panneau |
| « Le fichier de paramètres est illisible » | Il n'est jamais écrasé : restaurez une sauvegarde ou supprimez `settings.json` |
| Touches Stream Dock « Hors ligne » | Lancez Drawflow, vérifiez l'API locale et le jeton |
