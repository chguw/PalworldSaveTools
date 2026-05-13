<div align="center">

![PalworldSaveTools Logo](../PalworldSaveTools_Blue.png)

# PalworldSaveTools

**Une boîte à outils complète pour l'édition de fichiers de sauvegarde Palworld**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)

---

### **Téléchargez la version autonome depuis [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** 

---

</div>

## Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Installation](#installation)
- [Démarrage rapide](#démarrage-rapide)
- [Outils Présentation](#outils-présentation)
- [Guides](#guides)
- [Dépannage](#dépannage)
- [Création d'un exécutable autonome (Windows uniquement)](#création-dun-exécutable-autonome-windows-uniquement)
- [Contribuer](#contribuer)
- [Licence](#licence)

---

## Fonctionnalités

### Fonctionnalité de base

| Fonctionnalité | Descriptif |
|---------|-------------|
| **Analyse de sauvegarde rapide** | L'un des lecteurs de fichiers de sauvegarde les plus rapides disponibles |
| **Gestion des joueurs** | Afficher, modifier, renommer, changer de niveau, débloquer des technologies et gérer les joueurs |
| **Gestion de guilde** | Créez, renommez, déplacez des joueurs, débloquez des recherches en laboratoire et gérez des guildes |
| **Pal Editor** | Éditeur complet pour les statistiques, les compétences, IVs, le rang, les âmes, le sexe, le boss/le bouton chanceux |
| **Outils du camp de base** | Exporter, importer, cloner, ajuster le rayon et gérer les bases |
| **Visionneuse de carte** | Base interactive et carte des joueurs avec coordonnées et détails |
| **Transfert de personnage** | Transférer des personnages entre différents mondes/serveurs (sauvegarde croisée) |
| **Enregistrer la conversion** | Convertir entre les formats Steam et GamePass |
| **Paramètres mondiaux** | Modifier les paramètres WorldOption et LevelMeta |
| **Outils d'horodatage** | Corrigez les horodatages négatifs et réinitialisez les temps des joueurs |

### Outils tout-en-un

La suite **All-in-One Tools** offre une gestion complète des sauvegardes :

- **Outils de suppression**
  - Supprimer des joueurs, des bases ou des guildes
  - Supprimer les joueurs inactifs en fonction de seuils de temps
  - Supprimez les joueurs en double et les guildes vides
  - Supprimer les données non référencées/orphelines

- **Outils de nettoyage**
  - Supprimer les éléments invalides/modifiés
  - Supprimer les pals et passives invalides
  - Correction du pals illégal (plafond aux statistiques maximales légales)
  - Supprimer les structures invalides
  - Réinitialiser les tourelles anti-aériennes
  - Débloquez private chests

- **Outils de guilde**
  - Reconstruire toutes les guildes
  - Déplacer les joueurs entre les guildes
  - Faire du joueur un chef de guilde
  - Renommer les guildes
  - Niveau de guilde maximum
  - Débloquez toutes les recherches en laboratoire

- **Outils du joueur**
  - Modifier les statistiques et les compétences du joueur pal
  - Débloquez toutes les technologies
  - Déverrouiller la cage de visualisation
  - Joueurs de niveau supérieur/vers le bas
  - Renommer les joueurs

- **Enregistrer les utilitaires**
  - Réinitialiser les missions
  - Réinitialiser les donjons
  - Correction des horodatages
  - Réduire les stocks surchargés
  - Générer des commandes PalDefender

### Outils supplémentaires

| Outil | Descriptif |
|------|-------------|
| **Modifier le joueur Pals** | pal editor complet avec statistiques, compétences, IVs, talents, âmes, rang et sexe |
| **SteamConvertisseur d'ID** | Convertir les identifiants Steam en UID Palworld |
| **Correction de la sauvegarde de l'hôte** | Échanger les UID entre deux joueurs (par exemple, pour l'échange d'hôte) |
| **Injecteur à fente** | Augmenter les emplacements palbox par joueur |
| **Restaurer la carte** | Appliquer la progression de la carte déverrouillée sur tous les mondes/serveurs |
| **Renommer le monde** | Changer le nom du monde dans LevelMeta |
| **Éditeur WorldOption** | Modifier les paramètres et la configuration du monde |
| **Éditeur LevelMeta** | Modifier les métadonnées du monde (nom, hôte, niveau) |

---

## Installation

### Prérequis

**Pour la version autonome (Windows) :**
- Windows 10/11
- [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version) (2015-2022)

**Pour une exécution à partir des sources (toutes les plateformes) :**
- Python 3.11 ou supérieur

### Autonome (Windows - Recommandé)

1. Téléchargez la dernière version de [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)
2. Extrayez le fichier zip
3. Exécutez `PalworldSaveTools.exe`

### Depuis la source (toutes les plateformes)

Les scripts de démarrage créent automatiquement un environnement virtuel et installent toutes les dépendances.

**En utilisant uv :**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv venv --python 3.12
uv run start.py
```

**Fenêtres :**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
start_win.cmd
```

**Linux :**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
chmod +x start_linux.sh
./start_linux.sh
```

### Succursales

- **Stable** (recommandé) : `git clone https://github.com/deafdudecomputers/PalworldSaveTools.git`
- **Bêta** (dernières fonctionnalités) : `git clone -b beta https://github.com/deafdudecomputers/PalworldSaveTools.git`

---

## Démarrage rapide

1. **Chargez votre sauvegarde**
   - Cliquez sur le bouton de menu dans l'en-tête
   - Sélectionnez **Charger Enregistrer**
   - Accédez à votre dossier de sauvegarde Palworld
   - Sélectionnez `Level.sav`

2. **Explorez vos données**
   - Utilisez les onglets pour afficher les joueurs, les guildes, les bases ou la carte
   - Rechercher et filtrer pour trouver des entrées spécifiques

3. **Apporter des modifications**
   - Sélectionnez les éléments à éditer, supprimer ou modifier
   - Cliquez avec le bouton droit pour les menus contextuels avec des options supplémentaires

4. **Enregistrez vos modifications**
   - Cliquez sur le bouton de menu → **Enregistrer les modifications**
   - Les sauvegardes sont créées automatiquement

---

## Outils Présentation

### Outils tout-en-un (AIO)

L'interface principale pour une gestion complète des sauvegardes avec cinq onglets :

**Onglet Inventaire des joueurs** - Affichez et gérez l'inventaire de tous les joueurs sur le serveur.
- Modifiez les statistiques des joueurs, l'inventaire et l'équipement équipé.
- Possibilité de modifier la qualité, d'ajouter, de supprimer n'importe quoi de l'inventaire et de l'équipement équipé.

**Onglet Inventaire de base** - Affichez et gérez les inventaires de toutes les bases sur le serveur.
- Modifier l'inventaire de base.
- Possibilité de vider les conteneurs, de modifier la qualité, d'ajouter, de supprimer quoi que ce soit des inventaires de base.
- Filtrage inclus pour toute possibilité de triche.

**Onglet Joueurs** - Affichez et gérez tous les joueurs sur le serveur
- Modifiez les noms des joueurs, les niveaux et les comptes pal
- Supprimer les joueurs inactifs
- Afficher les guildes de joueurs et la dernière fois en ligne

**Onglet Guildes** - Gérer les guildes et leurs bases
- Renommer les guildes, changer de chef
- Afficher les emplacements et les niveaux de base
- Supprimer les guildes vides ou inactives

**Onglet Bases** - Afficher tous les camps de base
- Exporter/importer des plans de base
- Cloner des bases vers d'autres guildes
- Ajuster le rayon de base

### Visionneuse de cartes

Visualisation interactive de votre monde :
- Afficher tous les emplacements de base et les positions des joueurs
- Filtrer par guilde ou nom de joueur
- Cliquez sur les marqueurs pour des informations détaillées
- Générer des commandes `killnearestbase` pour PalDefender

### Transfert de personnage

Transférer des personnages entre différents mondes/serveurs (sauvegarde croisée) :
- Transférer un seul ou tous les joueurs
- Préserve les personnages, pals, l'inventaire et la technologie
- Utile pour migrer entre des serveurs coopératifs et dédiés

### Correction de la sauvegarde de l'hôte

Échangez les UID entre deux joueurs :
- Transférer la progression d'un joueur à un autre
- Indispensable pour les transferts d'hôte/coopérative vers serveur
- Utile pour échanger le rôle d'hôte entre les joueurs
- Utile pour les échanges de plateformes (Xbox ↔ Steam)
- Résout les problèmes d'attribution d'UID hôte/serveur
- **Remarque :** Le joueur concerné doit d'abord avoir un personnage créé sur la sauvegarde cible.

---

## Guides

### Enregistrer les emplacements des fichiers

**Hôte/Coop :**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**Serveur dédié :**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### Déverrouillage de la carte

<details>
<summary>Cliquez pour développer les instructions de déverrouillage de la carte</summary>

1. Copiez `LocalData.sav` de `resources\`
2. Recherchez votre dossier de sauvegarde serveur/monde
3. Remplacez le `LocalData.sav` existant par le fichier copié
4. Lancez le jeu avec une carte entièrement déverrouillée

> **Remarque :** Utilisez l'outil **Restaurer la carte** dans l'onglet Outils pour appliquer la carte déverrouillée à TOUS vos mondes/serveurs à la fois avec des sauvegardes automatiques.

</details>

### Hôte → Transfert de serveur

<details>
<summary>Cliquez pour développer le guide de transfert d'hôte à serveur</summary>

1. Copiez les dossiers `Level.sav` et `Players` de la sauvegarde de l'hôte
2. Collez dans le dossier de sauvegarde du serveur dédié
3. Démarrez le serveur, créez un nouveau personnage
4. Attendez la sauvegarde automatique, puis fermez
5. Utilisez **Fix Host Save** pour migrer les GUID
6. Copiez les fichiers et lancez-les

**Utilisation de Fix Host Save :**
- Sélectionnez le `Level.sav` dans votre dossier temporaire
- Choisissez l'**ancien personnage** (depuis la sauvegarde d'origine)
- Choisissez le **nouveau personnage** (que vous venez de créer)
- Cliquez sur **Migrer**

</details>

### Échange d'hôte (changement d'hôte)

<details>
<summary>Cliquez pour développer le guide d'échange d'hôte</summary>

**Contexte :**
- L'hôte utilise toujours `0001.sav` — même UID pour celui qui héberge
- Chaque client utilise une sauvegarde UID régulière unique (par exemple, `123xxx.sav`, `987xxx.sav`)

**Prérequis :**
Les deux joueurs (ancien hôte et nouvel hôte) doivent avoir leurs sauvegardes régulières générées. Cela se produit en rejoignant le monde de l'hôte et en créant un nouveau personnage.

**Étapes :**

1. **Assurez-vous que des sauvegardes régulières existent**
   - Le joueur A (ancien hôte) devrait avoir une sauvegarde régulière (par exemple, `123xxx.sav`)
   - Le joueur B (nouvel hôte) devrait avoir une sauvegarde régulière (par exemple, `987xxx.sav`)

2. ** Remplacez la sauvegarde de l'hôte de l'ancien hôte par une sauvegarde régulière **
   - Utilisez PalworldSaveTools **Fix Host Save** pour échanger :
   - `0001.sav` de l'ancien hôte → `123xxx.sav`
   - (Cela déplace la progression de l'ancien hôte de l'emplacement d'hôte vers son emplacement de joueur habituel)

3. ** Échangez la sauvegarde régulière du nouvel hôte par la sauvegarde de l'hôte **
   - Utilisez PalworldSaveTools **Fix Host Save** pour échanger :
   - `987xxx.sav` du nouvel hôte → `0001.sav`
   - (Cela déplace la progression du nouvel hôte vers l'emplacement de l'hôte)

**Résultat :**
- Le joueur B est désormais l'hôte avec son propre personnage et pals dans `0001.sav`
- Le joueur A devient client avec sa progression initiale en `123xxx.sav`

</details>

### Exportation/Importation de base

<details>
<summary>Cliquez pour développer le guide d'exportation/importation de base</summary>

**Exportation d'une base :**
1. Chargez votre sauvegarde dans PST
2. Accédez à l'onglet Bases
3. Cliquez avec le bouton droit sur une base → Exporter la base
4. Enregistrer sous le fichier `.json`

**Importation d'une base :**
1. Accédez à l'onglet Bases ou à la visionneuse de carte de base.
2. Faites un clic droit sur la guilde dans laquelle vous souhaitez importer la base.
3. Sélectionnez Importer la base
4. Sélectionnez votre fichier `.json` exporté

**Clonage d'une base :**
1. Cliquez avec le bouton droit sur une base → Cloner la base
2. Sélectionnez la guilde cible
3. La base sera clonée avec un positionnement décalé

**Ajustement du rayon de base :**
1. Cliquez avec le bouton droit sur une base → Ajuster le rayon
2. Entrez un nouveau rayon (50% - 1000%)
3. Enregistrez et chargez la sauvegarde dans le jeu pour les structures à réaffecter

</details>

---

## Dépannage

### "VCRUNTIME140.dll est introuvable"

**Solution :** Installez [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version)

### `struct.error` lors de l'analyse de la sauvegarde

**Cause :** Format de fichier de sauvegarde obsolète

**Solution :**
1. Chargez la sauvegarde dans le jeu (mode Solo, Coop ou Serveur dédié)
2. Cela déclenche une mise à jour automatique de la structure
3. Assurez-vous que la sauvegarde a été mise à jour avec ou après le dernier patch du jeu.

### Le convertisseur GamePass ne fonctionne pas

**Solution :**
1. Fermez la version GamePass de Palworld
2. Attendez quelques minutes
3. Exécutez le convertisseur Steam → GamePass
4. Lancez Palworld sur GamePass pour vérifier

---

## Création d'un exécutable autonome (Windows uniquement)

Exécutez le script de build pour créer un exécutable autonome :

```bash
scripts\build.cmd
```

Cela crée `PST_standalone_v{version}.7z` à la racine du projet.

---

## Contribuer

Les contributions sont les bienvenues ! N'hésitez pas à soumettre une Pull Request.

1. Forkez le référentiel
2. Créez votre branche de fonctionnalités (`git checkout -b feature/AmazingFeature`)
3. Validez vos modifications (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la succursale (`git push origin feature/AmazingFeature`)
5. Ouvrez une demande de tirage

---

## Avertissement

**Utilisez cet outil à vos propres risques. Sauvegardez toujours vos fichiers de sauvegarde avant d'apporter des modifications.**

Les développeurs ne sont pas responsables de toute perte de données de sauvegarde ou des problèmes pouvant résulter de l'utilisation de cet outil.

---

## Assistance

-**Discord :** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub Problèmes :** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Documentation :** [Wiki](https://github.com/deafdudecomputers/PalworldSaveTools/wiki) *(Actuellement en développement)*

---

## Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## Remerciements

- **Palworld** développé par Pocketpair, Inc.
- Merci à tous les contributeurs et membres de la communauté qui ont contribué à améliorer cet outil

---

<div align="center">

**Réalisé avec ❤️ pour la communauté Palworld**

[⬆ Back to Top](#palworldsavetools)

</div>