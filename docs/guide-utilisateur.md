# Guide utilisateur

Drawflow automatise trois tâches du dessinateur en façade : la **liste de pièces** depuis les plans DWG/DXF, le **rapport** Word depuis les plans PDF et la **soumission** normalisée depuis des fichiers XLSX ou PDF. Tout se fait sur le poste : aucun fichier ne quitte la machine.

## Installation

1. Téléchargez `Drawflow_X.Y.Z_x64-setup.exe` depuis la [dernière release](https://github.com/pepito2t/drawflow-engine/releases/latest) et lancez-le. L'installation se fait pour l'utilisateur courant, sans droits administrateur.
2. Windows peut afficher un avertissement SmartScreen (« éditeur inconnu ») : l'installeur n'est pas encore signé par un certificat de signature de code. Cliquez sur **Informations complémentaires → Exécuter quand même**.
3. Au premier lancement, saisissez le code d'accès (voir [Code d'accès](#code-daccès)).
4. Si un prérequis manque, un message **Configurer Drawflow** s'affiche : il ouvre l'écran [Installation](#écran-installation).

Les mises à jour suivantes s'installent depuis l'application (voir [Mises à jour](#mises-à-jour)).

## Écran Installation

**Paramètres → Installation** analyse le poste et propose, pour chaque prérequis, le bouton qui le règle.

| Prérequis | Utilité | Boutons possibles |
|---|---|---|
| ODA File Converter | Lire les fichiers DWG (les DXF n'en ont pas besoin) | **Installer** (winget), **Utiliser** (ODA déjà installé : son chemin est renseigné automatiquement), **Page de téléchargement** |
| Serveur du modèle local | Faire tourner l'assistant | **Installer** Ollama (winget sous Windows, Homebrew sous macOS), **Démarrer**, **Page de téléchargement** |
| Modèle | Le modèle choisi dans Paramètres → Assistant | **Télécharger** (Ollama uniquement, progression en %) |
| Plugin Stream Deck *(facultatif)* | Piloter Drawflow depuis un Stream Deck | **Installer le plugin**, **Page de téléchargement** du logiciel Elgato |

- Avant d'installer un logiciel tiers, Drawflow demande une confirmation : l'installation accepte la licence de l'éditeur. Le téléchargement d'un modèle (plusieurs Go) est aussi confirmé.
- Sans winget (anciennes versions de Windows 10), seuls les liens vers les pages officielles sont proposés.
- **Analyser à nouveau** relance l'analyse, par exemple après une installation manuelle.

## Utiliser une fonctionnalité

Chaque fonctionnalité a son onglet dans la barre latérale, avec son mode d'emploi (« Comment ça marche »).

1. Ajoutez les fichiers et/ou les dossiers : bouton **Parcourir** ou glisser-déposer sur le champ.
2. Renseignez le nom du projet : il sert à nommer le fichier produit.
3. Choisissez le dossier de sortie. Drawflow n'écrit **jamais** dans les fichiers d'origine.
4. Cliquez sur **Lancer**.

Pendant le traitement, vous pouvez changer d'onglet ou lancer une autre fonctionnalité. L'icône **Traitements** (à côté de la roue des paramètres) affiche ceux en cours et leur progression ; **Annuler** arrête un traitement. À la fin, un message s'affiche ; si le traitement a duré longtemps ou si Drawflow était en arrière-plan, une notification Windows est aussi envoyée.

### Liste de pièces (DWG/DXF → Excel)

Lit les blocs des plans et produit la liste des pièces avec leurs quantités.

- Les plans DWG sont convertis par ODA File Converter, puis mis en cache : un plan déjà converti et non modifié n'est pas reconverti.
- Les blocs imbriqués et les blocs dynamiques sont pris en compte.
- Réglages (**Paramètres → Liste de pièces**) :
  - **Blocs retenus** : noms séparés par `;`, jokers `*` et `?` (ex. `PANNEAU*;EQUERRE`). `*` = tous les blocs.
  - **Colonnes de la liste** : chaque colonne reprend un attribut AutoCAD (par défaut Référence ← `REF`, Désignation ← `DESIGNATION`, Longueur ← `LONGUEUR`, Matière ← `MATIERE`, Finition ← `FINITION`).
  - **Attribut de quantité** (vide : chaque bloc compte pour 1), colonne **Bloc**, **regroupement** des pièces identiques.
  - **Feuille** et **ligne d'en-tête** du modèle Excel.

### Rapport (PDF → Word)

Relève le cartouche et les références de chaque plan PDF et remplit un modèle Word.

- Réglages (**Paramètres → Rapport**) :
  - **Zone du cartouche** en % de la page (bords gauche, haut, droit, bas).
  - **Champs du cartouche** : nom du champ → libellé cherché ; la valeur est le texte qui suit le libellé (ou la ligne suivante). Préfixe `re:` pour une expression régulière, ex. `re:Ind\.?\s*(\w+)`.
  - **Format des références** relevées sur tout le plan (expression régulière).
- Balises du modèle Word : `{{ projet }}`, `{{ date }}`, boucle `{%p for plan in plans %}` … `{%p endfor %}` avec `{{ plan.fichier }}`, `{{ plan.references }}` et chaque champ (ex. `{{ plan.indice }}`).

### Soumission (XLSX / PDF → tableau normalisé)

Rassemble des soumissions de formats différents dans un seul tableau Excel.

- Accepte les fichiers XLSX et les PDF qui contiennent un fichier XLSX joint. Plusieurs dossiers sont possibles ; un fichier présent deux fois n'est compté qu'une fois.
- Réglages (**Paramètres → Soumission**) :
  - **Colonnes normalisées** : pour chaque colonne, les en-têtes reconnus (sans accents ni majuscules), ex. Quantité ← `quantité;qté;qte;qty`.
  - **Colonnes numériques** : converties en nombres (formats `1'234.50` et `1 234,50` acceptés).
  - Nombre de lignes parcourues pour trouver l'en-tête.

## Préréglages

Un préréglage enregistre les valeurs d'un formulaire (fichiers, dossiers, projet, modèle, sortie) sous un nom.

- **Enregistrer comme préréglage** en haut de l'onglet ; la liste permet de le recharger ou de le supprimer.
- Un préréglage peut être lancé en un clic depuis le Stream Deck.

## Modèles de sortie

**Paramètres → Modèles** : importez vos modèles Excel (`.xlsx`) et Word (`.docx`) et choisissez le modèle par défaut de chaque fonctionnalité. Un modèle choisi dans le formulaire remplace celui par défaut.

## Nom des fichiers produits

Chaque fonctionnalité a son **Nom des fichiers exportés** dans ses paramètres. Variables : `{projet}`, `{type}`, `{date}` (AAAAMMJJ), `{heure}` (HHMM), `{source}` (nom du fichier source), `{indice}`. Par défaut : `{projet}_liste-pieces_{date}`, `{projet}_rapport_{date}`, `{projet}_soumission_{date}`.

## Paramètres

La roue en bas de la barre latérale ouvre les paramètres, classés par catégorie :

| Catégorie | Contenu |
|---|---|
| Général | Chemin d'ODA File Converter, dossier de cache, fichiers traités en parallèle, délai avant notification |
| Liste de pièces · Rapport · Soumission | Réglages propres à chaque fonctionnalité ; **Exporter / Importer** pour partager une norme entre postes |
| Assistant | Adresse du serveur du modèle et nom du modèle |
| Installation | Analyse du poste et installations ([voir plus haut](#écran-installation)) |
| Modèles | Modèles Excel et Word |
| Intégrations | API locale pour le Stream Deck |
| Code d'accès | Changer le code |

## Assistant

L'icône **bulle** ouvre un panneau de discussion à droite. L'assistant répond aux questions sur Drawflow (fonctionnalités, préréglages, modèles) en consultant directement l'application.

- **Prérequis** : un serveur de modèle local, Ollama (recommandé) ou LM Studio, avec un modèle installé. L'écran Installation s'en charge.
- **Confidentialité** : l'adresse du serveur doit désigner ce poste (`localhost`, `127.0.0.1`) ; toute autre adresse est refusée. Aucune donnée ne sort de la machine.
- **Choix du modèle** : la liste en haut du panneau affiche les modèles installés ; en choisir un l'enregistre dans Paramètres → Assistant.
- **Arrêter** interrompt une réponse ; **+** démarre une nouvelle conversation. Fermer le panneau ne perd pas la conversation (elle est effacée à la fermeture de l'application).
- L'assistant ne lance pas encore de traitement : il explique comment le faire.

## Stream Deck

1. **Paramètres → Intégrations** : activez l'API locale et copiez le jeton.
2. Installez le plugin (**Paramètres → Installation → Installer le plugin**, ou double-clic sur `ch.drawflow.streamDeckPlugin` fourni avec chaque release).
3. Glissez une action « Drawflow » sur une touche et collez le jeton dans ses réglages (une seule fois : il est partagé par toutes les touches).

Actions : lancer un préréglage (progression en direct, vert/rouge à la fin), ouvrir un onglet, annuler les traitements, ouvrir le dernier résultat, compteur de traitements. Tant que Drawflow est verrouillée, les touches affichent « Verrouillé » ; quand Drawflow est fermée, « Hors ligne ».

## Code d'accès

L'application demande un code au démarrage. Le code initial est `0000` ; changez-le dans **Paramètres → Code d'accès**. Après plusieurs erreurs, un délai croissant est imposé.

**Code oublié** : fermez Drawflow et supprimez `access-code.json` dans `%APPDATA%\ch.drawflow.desktop\`. Le code redevient `0000`.

## Mises à jour

Au démarrage, Drawflow vérifie s'il existe une nouvelle version. Si oui, un message propose **Mettre à jour** ou **Plus tard**. La mise à jour attend la fin des traitements en cours, puis redémarre l'application. L'état est visible dans la barre en bas de la fenêtre.

## Où sont les fichiers

| Contenu | Emplacement (Windows) |
|---|---|
| Paramètres, préréglages, modèles importés, code d'accès, intégrations | `%APPDATA%\ch.drawflow.desktop\` |
| Cache des plans DWG convertis | `%LOCALAPPDATA%\drawflow\cache\` (modifiable dans Paramètres → Général) |
| Fichiers produits | Le dossier de sortie choisi dans chaque formulaire |

## Dépannage

| Problème | Solution |
|---|---|
| « ODA File Converter n'est pas configuré » | Paramètres → Installation → **Installer** ou **Utiliser** |
| « Le modèle local ne répond pas » | Paramètres → Installation → **Démarrer** (Ollama) ou lancez LM Studio ; vérifiez l'adresse dans Paramètres → Assistant |
| « Le modèle … est introuvable » | Paramètres → Installation → **Télécharger**, ou choisissez un modèle installé dans la liste du panneau |
| Le fichier de paramètres est illisible | Il n'est jamais écrasé : restaurez une sauvegarde ou supprimez `settings.json` pour revenir aux valeurs par défaut |
| Les touches Stream Deck affichent « Hors ligne » | Lancez Drawflow et vérifiez que l'API locale est activée et que le jeton est correct |
