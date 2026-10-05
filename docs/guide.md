# Guide utilisateur

Drawflow automatise trois tâches du dessinateur en façade : la **liste de pièces** (plans DWG/DXF → Excel), le **rapport** (plans PDF → Word) et la **soumission** (XLSX ou PDF → tableau normalisé). Tout se fait sur le poste : aucun fichier ne quitte la machine.

Les réglages et leurs valeurs par défaut sont décrits directement dans l'application (Paramètres) ; ce guide explique comment s'en servir.

## Installer Drawflow

1. Téléchargez `Drawflow_X.Y.Z_x64-setup.exe` depuis la [dernière release](https://github.com/pepito2t/drawflow-engine/releases/latest) et lancez-le (installation pour l'utilisateur courant, sans droits administrateur).
2. Si Windows affiche « éditeur inconnu » (SmartScreen) : **Informations complémentaires → Exécuter quand même**. L'installeur n'est pas encore signé.
3. Saisissez le code d'accès (voir [Code d'accès](#code-daccès)).
4. Si un prérequis manque, le message **Configurer Drawflow** ouvre l'écran Installation.

## Installer les prérequis

**Paramètres → Installation** analyse le poste et propose pour chaque prérequis le bouton qui le règle : installer, démarrer, télécharger, ou ouvrir la page officielle.

| Prérequis | À quoi il sert |
|---|---|
| ODA File Converter | Lire les fichiers DWG (les DXF n'en ont pas besoin) |
| Serveur du modèle local (Ollama ou LM Studio) et un modèle | Faire tourner l'assistant |
| Plugin Stream Deck *(facultatif)* | Piloter Drawflow depuis un Stream Deck |

- Les installations passent par winget (Windows) ou Homebrew (macOS). Sans eux, seuls les liens vers les pages officielles sont proposés.
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

**Enregistrer comme préréglage** (en haut de l'onglet) mémorise le formulaire sous un nom, pour le recharger ou le lancer depuis le Stream Deck.

## Utiliser l'assistant

L'icône **bulle** ouvre le panneau de discussion. L'assistant répond aux questions sur Drawflow en consultant l'application.

Il peut aussi **proposer un lancement** (« lance la soumission sur C:\Chantier\Soumissions ») : une carte affiche la fonctionnalité et les entrées, et rien ne démarre tant que vous n'avez pas cliqué sur **Lancer**. Le traitement suit ensuite le circuit normal : progression dans Traitements, annulation, notification.

- Prérequis : un modèle local (voir [Installer les prérequis](#installer-les-prérequis)). L'adresse du serveur doit désigner ce poste : aucune donnée ne sort de la machine.
- La liste en haut du panneau change de modèle. **Arrêter** interrompt une réponse, **+** démarre une nouvelle conversation (effacée à la fermeture de l'application).

## Piloter avec un Stream Deck

1. **Paramètres → Intégrations** : activez l'API locale et copiez le jeton.
2. Installez le plugin (**Paramètres → Installation**, ou double-clic sur `ch.drawflow.streamDeckPlugin` joint à chaque release).
3. Glissez une action « Drawflow » sur une touche et collez le jeton (une fois pour toutes les touches).

Les touches lancent un préréglage (progression, puis vert ou rouge), ouvrent un onglet, annulent les traitements, ouvrent le dernier résultat ou comptent les traitements. Elles affichent « Verrouillé » tant que Drawflow est verrouillée et « Hors ligne » quand Drawflow est fermée.

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
| « Le modèle local ne répond pas » | Paramètres → Installation → **Démarrer**, ou lancez LM Studio |
| « Le modèle … est introuvable » | Paramètres → Installation → **Télécharger**, ou choisissez un modèle installé dans le panneau |
| « Le fichier de paramètres est illisible » | Il n'est jamais écrasé : restaurez une sauvegarde ou supprimez `settings.json` |
| Touches Stream Deck « Hors ligne » | Lancez Drawflow, vérifiez l'API locale et le jeton |
