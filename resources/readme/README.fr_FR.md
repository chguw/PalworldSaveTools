<div align="center">

![PalworldSaveTools Logo](../assets/branding/PalworldSaveTools_Blue.png)

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
<div align="center">

## Aperçu

<img src="https://readme-typing-svg.demolab.com?lines=Qu%27est-ce%20que%2Bexactement%2Bc%27est%2Bcette%2Bchose%C2%A0%3F%3B%C3%80%20votre%2Bsauvegarde%2B%C3%A0%2Bvotre%2Bfa%C3%A7on%3BUn%2Boutil%2Bpour%2Bles%2Bgouverner%2Btous&center=true&width=490&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Palworld Save Tools (PST) est une application de bureau rapide tout-en-un permettant d'inspecter et de modifier les fichiers de sauvegarde Palworld. Construit avec Python et PySide6, il lit et écrit directement le format de sauvegarde compressé du jeu – aucun module de jeu n'est requis.

Que vous ayez besoin de gérer un serveur dédié, de migrer entre des serveurs coopératifs et dédiés, de nettoyer des données abandonnées ou d'affiner un Pals individuel, PST fournit une interface unifiée unique pour tout cela.

### Faits saillants

- **Multiplateforme** : binaires prédéfinis pour **Windows**, **Linux** et **macOS**.
- **Analyse native rapide** — L'un des lecteurs de fichiers de sauvegarde les plus rapides disponibles, alimenté par le moteur [`palsav`](src/palsav).
- **Carte visuelle** — Carte du monde interactive avec marqueurs de base/joueur, zones d'exclusion et étalonnage des coordonnées.
- **Édition approfondie de Pal** — Contrôle total sur les statistiques, IVs, les âmes, les compétences, passives, les aptitudes au travail, le rang et les drapeaux d'apparence.
- **Outils de qualité serveur** — Suppression, nettoyage, conversion et transfert de caractères en masse conçus pour les administrateurs.
- **Sauvegardes automatiques** — Chaque opération de sauvegarde crée une sauvegarde avant l'écriture.
- **8 langues** — Interface utilisateur localisée, guides intégrés à l'application et documentation.





---





## Table des matières

- [Aperçu](#aperçu)
- [Fonctionnalités](#fonctionnalités)
- [Installation](#installation)
- [Démarrage rapide](#démarrage-rapide)
- [Guides](#guides)
- [Dépannage](#dépannage)
- [Construire à partir de la source](#construire-à-partir-de-la-source)
- [Contribuer](#contribuer)
- [Licence](#licence)
- [L'équipe Palworld](#léquipe-palworld)

- [Assistance](#assistance)
- [Licence](#licence)
- [Remerciements](#reconnaissances)





---




<div align="center">

## Fonctionnalités

<img src="https://readme-typing-svg.demolab.com?lines=Les%20%2Bbonnes%2Btrucs%3BV%C3%A9rifiez%2Ble%2Bout%3BEmball%C3%A9%2Bavec%2Bdes%2Boutils&center=true&width=290&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Gestion des joueurs

- Affichez et recherchez tous les joueurs par nom, niveau, nombre pal, UID, guilde et heure de dernière visite.
- Modifiez les noms des joueurs, les niveaux, les statistiques et les points technologiques.
- **Opérations groupées** sur plusieurs joueurs : gestion des objets, gestion pal et déverrouillages technologiques.
- Supprimer les joueurs inactifs par seuil de temps ; supprimer les doublons.

### Pal Editor

Une interface d'édition approfondie pour n'importe quel Pal appartenant à n'importe quel joueur. Pals sont organisés par **Party** (équipe active) et **Palbox** (stockage).

- **Statistiques et IVs** — HP, attaque, défense (IV 0-100), niveau (1-80), rang de confiance (0-10).
- **Âmes** — HP, Attaque, Défense, Vitesse d'artisanat (0–20).
- **Compétences** — Sélecteur de compétences actif ; apprendre tous les mouvements ; compétences de synchronisation en masse sur Pals.
- **Traits passifs** — Sélecteur passif avec données de jeu complètes.
- **Aptitude au travail** — Définissez les niveaux individuels d'aptitude au travail (0 à 10).
- **Drapeaux d'apparence** — Basculez entre Boss/Alpha, Chanceux/Brillant, Éveillé et Importé/ADN.
- **Rank & Lock** — Définissez le classement et le niveau de verrouillage des favoris (0 à 3).
- Ajoutez un nouveau Pals ou supprimez-le rapidement avec un double-clic.

### Gestion de guilde

Vue à deux panneaux : liste des guildes en haut, liste des membres en bas.

- Renommer les guildes, changer de chef, définir le niveau de guilde, le niveau de guilde maximum.
- Débloquez toutes les recherches de laboratoire ; reconstruisez toutes les guildes.
- Déplacez les joueurs entre les guildes ; supprimer les guildes vides ou inactives.

### Outils du camp de base

- Voir tous les camps de base avec association de guilde.
- **Exporter** les plans de base vers `.json` ; **importer** (un ou plusieurs fichiers) dans n'importe quelle guilde.
- **Cloner** des bases vers d'autres guildes avec un positionnement décalé.
- **Ajuster le rayon de base** (50 % à 1 000 %).
- Supprimer les bases inactives et les objets cartographiques non-base.

### Visionneuse de cartes

Visualisation interactive de votre monde entier.

- Marqueurs de base (icône de maison) et marqueurs de joueur (icône de personne) avec panneaux de détails.
- Basculer les superpositions : bases, joueurs, anneaux de rayon, zones d'exclusion.
- **Dessin de zone** — Dessinez des zones d'exclusion rectangulaires ou polygonales directement sur la carte.
- **Mode de calibrage** — Alignez avec précision la carte avec les coordonnées du jeu.
- Vues de la carte du monde et de la carte des arbres ; filtrer par guilde ou nom de joueur.
- Zoom (1,0x – 30,0x), panoramique, double-clic pour voler vers un marqueur.
- Cliquez avec le bouton droit sur les marqueurs et l'espace vide pour les actions de gestion.

### Gestion des stocks

**Inventaire des joueurs** — Trois sous-onglets :
- *Inventaire* — Tous les articles et équipements contenus dans le sac principal ; modifier la quantité, ajouter, supprimer.
- *Objets clés* — Objets de quête, effigies et technologie ; ajoutez en masse toutes les effigies/éléments clés.
- *Statistiques* — Niveau, HP, Endurance, Attaque, Défense, Vitesse de travail, Poids.
- Panneau d'équipement pour les emplacements d'armes, d'accessoires, de nourriture, d'armure, de bouclier, de planeur et de module.
- Débloquez toutes les cartes + points de déplacement rapide en un clic.

**Inventaire de base** – Parcourez et gérez les articles et travaillez Pals dans toutes les bases :
- Afficher/modifier les éléments dans les conteneurs ; conteneurs transparents; modifier les emplacements des conteneurs.
- Opérations d'objets entre guildes (trouver/supprimer des objets dans toutes les guildes).
- Suppression de la structure inter-guilde.
- Sous-onglet **Base Pals** — Gérez les Pals de travail attribués à chaque base avec les menus contextuels complets de l'éditeur pal.

### Exclusions

Listes de protection qui protègent les joueurs, les guildes et les bases des opérations de nettoyage.

- Trois panneaux côte à côte : exclus les UID des joueurs, les ID de guilde et les ID de base.
- Ajoutez des entrées via les menus contextuels du clic droit dans les onglets Joueurs, Guildes ou Bases.
- Enregistrez et chargez les listes d'exclusion de manière persistante.
- Construisez votre liste **avant** d'exécuter un nettoyage en masse.

### Enregistrer les outils

Accessible depuis l'onglet **Outils** sous forme de cartes cliquables :

| Outil | Descriptif |
|------|-------------|
| **Convertir les sauvegardes** | Convertir entre les formats SAV et JSON |
| **Convertir GamePass → Steam** | Convertir les sauvegardes Xbox/GamePass au format Steam |
| **Convertir SteamID** | Convertir les identifiants Steam en UID Palworld |
| **Restaurer la carte** | Appliquer la progression de la carte entièrement déverrouillée à tous les mondes/serveurs |
| **Injecteur à fente** | Augmenter les emplacements palbox par joueur |
| **Modifier Enregistrer** | Ouvrir et modifier les données de sauvegarde brutes |
| **Transfert de personnage** | Transférer des personnages entre différents mondes/serveurs (sauvegarde croisée) |
| **Correction de la sauvegarde de l'hôte** | Échanger les UID entre deux joueurs (échange d'hôte, migration de plateforme) |

### Fonctions de nettoyage et utilitaires

Accessibles via **Menu → Fonctions**, ces opérations de niveau serveur incluent :

- **Suppression** — Supprimez les guildes vides, les bases/joueurs inactifs, les joueurs en double, les données non référencées.
- **Nettoyage** — Supprimez les éléments invalides/modifiés, pals et passives invalides, les structures invalides ; correction du pals illégal (plafond au maximum légal) ; réinitialiser les tourelles anti-aériennes ; débloquer private chests ; réparer toutes les structures.
- **Réinitialisations** — Réinitialisez les missions, les donjons, la plate-forme pétrolière, l'envahisseur, les baisses de ravitaillement.
- **Horodatage** — Correction des horodatages négatifs ; réinitialiser les temps des joueurs.
- **PalDefender** — Génère des commandes `killnearestbase`.





---




<div align="center">

## Installation

<img src="https://readme-typing-svg.demolab.com?lines=Obtenez%2Ble%2Bfonctionnement%2Ben%2Bminutes%3BT%C3%A9l%C3%A9chargez%2Bet%2Bpartez%3BNon%2Bconfiguration%2Bobligatoire&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Builds autonomes (recommandées)

Des binaires prédéfinis sont disponibles pour les trois principales plates-formes à partir de [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest) :

| Plateforme | Télécharger | Exigences |
|--------------|----------|--------------|
| **Windows** | `PalworldSaveTools-*.exe` | Windows 10/11, [VC++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015-2022) |
| **Linux** | `PalworldSaveTools-*-linux` | Toute distribution moderne |
| **macOS** | `PalworldSaveTools-*-macos.dmg` | macOS 12+ (Monterey ou version ultérieure) |

Également disponible sur [Nexus Mods](https://www.nexusmods.com/palworld/mods/3190).

1. Téléchargez la version appropriée pour votre plateforme.
2. Extrayez (si archivé) et exécutez l'exécutable.
3. C'est tout – aucun Python ni dépendance n'est nécessaire.

> **Windows :** Si vous voyez « VCRUNTIME140.dll n'a pas été trouvé », installez [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170).

> **Linux :** Vous devrez peut-être marquer le fichier comme exécutable : `chmod +x PalworldSaveTools-*-linux`

> **macOS :** Si Gatekeeper bloque l'application, cliquez avec le bouton droit → **Ouvrir** pour la première fois ou exécutez `xattr -d com.apple.quarantine /path/to/app`.

### Depuis la source (toutes les plateformes)

PST utilise [`uv`](https://docs.astral.sh/uv/) pour la gestion des dépendances. Le script de démarrage crée automatiquement un environnement virtuel et installe tout.

**Prérequis :** [Python 3.11+](https://www.python.org/) et [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv run start.py
```

**Windows** (lanceur double-clic) :
```
start.cmd
```

Le lanceur crée un `.venv`, installe les dépendances via `uv sync` et démarre l'application. Il nettoie le fichier de verrouillage à la sortie afin que chaque exécution soit reproductible.





---




<div align="center">

## Démarrage rapide

<img src="https://readme-typing-svg.demolab.com?lines=Charger.%2BModifier.%2BEnregistrer.%2B%C3%87a%2Bsimple.%3BTrois%2B%C3%A9tapes%2Bvers%2Bla%2Bgloire%3BC%27est%2Bc%27est%2Bfacile&center=true&width=450&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

1. **Chargez votre sauvegarde**
   - Cliquez sur **Menu → Load Save** ou faites glisser et déposez un fichier `.sav` sur la fenêtre.
   - Accédez à votre dossier de sauvegarde Palworld et sélectionnez `Level.sav`.

2. **Explorez vos données**
   - Utilisez les onglets — **Carte**, **Outils**, **Joueurs**, **Guildes**, **Bases**, **Inventaire des joueurs**, **Inventaire de base**, **Pal Editor**, **Exclusions** — pour explorer votre sauvegarde.
   - La barre de statistiques affiche les décomptes en direct ; les icônes de navigation rapide passent à chaque section.

3. **Apporter des modifications**
   - Faites un clic gauche pour sélectionner ; faites un clic droit sur presque n'importe quoi pour des actions contextuelles.
   - Double-cliquez pour effectuer une modification ou une suppression rapide (voir les guides intégrés à l'application pour plus de détails).

4. **Enregistrez vos modifications**
   - Cliquez sur **Menu → Enregistrer les modifications**. Les sauvegardes sont créées automatiquement.

> **Conseil :** Chaque onglet dispose d'un guide intégré : cliquez sur l'icône d'aide dans n'importe quel onglet pour voir exactement ce qu'il peut faire. Pour en savoir plus, **passez la souris sur n'importe quel bouton, champ ou contrôle** pour afficher des info-bulles détaillées dans l'en-tête. Le système d'aide par info-bulles intégré à l'application est votre meilleure référence pour comprendre exactement ce que fait chaque fonctionnalité et comment l'utiliser.





---




<div align="center">

## Guides

<img src="https://readme-typing-svg.demolab.com?lines=Proc%C3%A9dures%20pas%20%C3%A0%20pas%20%2B%20pas%20%C3%A0%20pas%3BSuivez%2Ble%2Bguide%3BNous%20allons%2Bvous%2Bmontrer%2Bcomment&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### Enregistrer les emplacements des fichiers

**Hôte/Coop (Windows) :**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**Serveur dédié :**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### Déverrouillage de la carte

PST peut déverrouiller la carte complète (tous les points de déplacement rapide) pour votre sauvegarde :

1. Chargez votre sauvegarde dans PST.
2. Ouvrez l'onglet **Inventaire du joueur** et cliquez sur **Déverrouiller toutes les cartes + Voyage rapide** pour un seul joueur, **ou**
3. Utilisez l'outil **Restaurer la carte** dans l'onglet Outils pour appliquer la progression de la carte déverrouillée sur **tous** vos mondes/serveurs à la fois.
4. Enregistrez les modifications. Des sauvegardes automatiques sont créées.

### Hôte → Transfert de serveur

<details>
<summary>Cliquez pour agrandir</summary>

1. Copiez `Level.sav` et le dossier `Players` de votre sauvegarde hôte.
2. Collez-les dans le dossier de sauvegarde du serveur dédié.
3. Démarrez le serveur, créez un nouveau personnage et attendez une sauvegarde automatique.
4. Fermez le serveur.
5. Utilisez **Fix Host Save** dans PST pour migrer le GUID de l'ancien personnage vers le nouveau.
6. Copiez les fichiers et lancez le serveur.

</details>

### Échange d'hôte (changement d'hôte)

<details>
<summary>Cliquez pour agrandir</summary>

**Contexte :** L'hôte utilise toujours l'emplacement `0001.sav` – le même UID pour celui qui héberge. Chaque client obtient une sauvegarde régulière unique (par exemple, `123xxx.sav`).

**Prérequis :** L'ancien et le nouvel hôte doivent avoir une sauvegarde régulière générée en rejoignant et en créant un personnage.

**Étapes :**

1. Utilisez **Fix Host Save** pour échanger le `0001.sav` de l'ancien hôte → sa sauvegarde habituelle (par exemple, `123xxx.sav`). Cela déplace leur progression hors de l'emplacement hôte.
2. Utilisez **Fix Host Save** pour échanger la sauvegarde régulière du nouvel hôte (par exemple, `987xxx.sav`) → `0001.sav`. Cela déplace leur progression vers l’emplacement hôte.

**Résultat :** Le nouvel hôte occupe désormais `0001.sav` avec son propre personnage et Pals ; l'ancien hôte devient client avec sa progression d'origine intacte.

</details>

### Transfert de personnage (sauvegarde croisée)

<details>
<summary>Cliquez pour agrandir</summary>

Transférez des personnages entre différents mondes ou serveurs tout en préservant les personnages, Pals, l'inventaire et la technologie :

1. Ouvrez l'outil **Transfert de personnage** depuis l'onglet Outils.
2. Sélectionnez la sauvegarde source et la sauvegarde cible.
3. Transférez un seul joueur ou tous les joueurs.
4. Utile pour migrer entre des serveurs coopératifs et dédiés.

</details>

### Base Export / Import / Clone

<details>
<summary>Cliquez pour agrandir</summary>

**Exportation d'une base :**
1. Accédez à l'onglet **Bases** (ou utilisez la visionneuse de carte).
2. Cliquez avec le bouton droit sur une base → **Exporter la base**.
3. Enregistrez en tant que fichier de plan `.json`.

**Importation d'une base :**
1. Faites un clic droit sur la guilde cible (dans l'onglet Bases, Visionneuse de carte ou Guildes).
2. Sélectionnez **Importer une base** (fichier unique) ou **Importer des bases (multi-fichiers)**.
3. Sélectionnez votre ou vos fichiers `.json` exportés.

**Clonage d'une base :**
1. Cliquez avec le bouton droit sur une base → **Cloner la base**.
2. Sélectionnez la guilde cible.
3. La base est clonée avec un positionnement décalé.

**Ajustement du rayon de base :**
1. Cliquez avec le bouton droit sur une base → **Ajuster le rayon**.
2. Entrez un nouveau rayon (50 % à 1 000 %).
3. Enregistrez et rechargez la sauvegarde dans le jeu pour les structures à réaffecter.

</details>





---




<div align="center">

## Dépannage

<img src="https://readme-typing-svg.demolab.com?lines=Quand%2Bles%2Bchoses%2Bva%2Bde%20c%C3%B4t%C3%A9%3BNe%2Bpaniquez%20pas%3BNous%20avons%2Bvu%2Btout%2B&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

### "VCRUNTIME140.dll est introuvable" (Windows)

Installez le [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) (2015-2022).

### `struct.error` lors de l'analyse d'une sauvegarde

Le format du fichier de sauvegarde est obsolète. Chargez la sauvegarde dans le jeu (Solo, Co-op ou Serveur dédié) une fois pour déclencher une mise à jour automatique de la structure, puis réessayez. Assurez-vous que la sauvegarde a été mise à jour avec ou après le dernier patch du jeu.

### Le convertisseur GamePass ne fonctionne pas

1. Fermez complètement la version GamePass de Palworld.
2. Attendez quelques minutes que les descripteurs de fichiers soient libérés.
3. Exécutez le convertisseur GamePass → Steam.
4. Lancez Palworld sur GamePass pour vérifier.

### Le binaire Linux / macOS ne se lance pas

- **Linux :** `chmod +x PalworldSaveTools-*-linux` pour le marquer comme exécutable.
- **macOS :** Si bloqué par Gatekeeper, cliquez avec le bouton droit → **Ouvrir** ou exécutez `xattr -d com.apple.quarantine /path/to/app`.





---




<div align="center">

## Construire à partir de la source

<img src="https://readme-typing-svg.demolab.com?lines=Compilez-le%20vous-m%C3%AAme%3BConstruisez%2Ble%2Bvotre%2Bpropre%3BDe%2Bsource%2B%C3%A0%2Bbinaire&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

PST prend en charge deux chemins de construction. Le pipeline CI/CD utilise Nuitka pour les versions binaires multiplateformes ; cx_Freeze est utilisé pour le programme d'installation Windows local.

### Nuitka (Multiplateforme — Utilisé par CI/Releases)

Nécessite Python 3.11+ et `uv`. Nuitka est installé automatiquement.

```bash
# One-file build (Windows / Linux)
uv run python build/nuitka/build_nuitka.py --onefile

# One-directory build (macOS .app)
uv run python build/nuitka/build_nuitka.py --onedir
```

Les sorties vont à `dist/` :
-Windows → `dist/PalworldSaveTools-*.exe`
-Linux → `dist/PalworldSaveTools-*-linux`
- macOS → `dist/PalworldSaveTools.app` → conditionné sous la forme `.dmg`

### cx_Freeze (Windows Installer)

Pour un package Windows `.7z` local :

```
scripts\build_cx.cmd
```

Cela crée `PST_standalone_v{version}.7z` à la racine du projet.

### Constructeur interactif

Un menu interactif pour choisir un mode de construction :

```bash
uv run python build/build_interactively.py
```





---




<div align="center">

## Contribuer

<img src="https://readme-typing-svg.demolab.com?lines=Voulez-vous%2Baider%C2%A0%3F%2BVoici%2Bcomment%3BRejoignez%2Bla%2B%C3%A9quipe%3BChaque%2Bcontribution%2Bcompte&center=true&width=440&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Les contributions sont les bienvenues ! N'hésitez pas à soumettre une Pull Request.

1. Forkez le référentiel.
2. Créez votre branche de fonctionnalités (`git checkout -b feature/AmazingFeature`).
3. Validez vos modifications (`git commit -m 'Add some AmazingFeature'`).
4. Poussez vers la branche (`git push origin feature/AmazingFeature`).
5. Ouvrez une demande de tirage.





---




<div align="center">

## Avertissement

<img src="https://readme-typing-svg.demolab.com?lines=Lisez%2Bceci%2Bavant%2Bde%2Bpause%2Bquelque%20chose%3BVous%20avez%2B%C3%A9t%C3%A9%2Bpr%C3%A9venu%3BSauvegarde%2Bd%27abord%C2%A0%21%3BAvec%20%2Bune%2Bgrande%2Bpuissance...&center=true&width=520&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>
**Utilisez cet outil à vos propres risques. Sauvegardez toujours vos fichiers de sauvegarde avant d'apporter des modifications.**

Les développeurs ne sont pas responsables de toute perte de données de sauvegarde ou des problèmes pouvant résulter de l'utilisation de cet outil.





---




<div align="center">

## Assistance

<img src="https://readme-typing-svg.demolab.com?lines=Nous%20avons%2Bvotre%2Bdos%3BBesoin%2Bd%27aide%C2%A0%3F%3BNous%20sommes%2Bl%C3%A0%2Bpour%2Bvous&center=true&width=340&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

-**Discord :** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub Problèmes :** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Mods Nexus :** [Download & discuss](https://www.nexusmods.com/palworld/mods/3190)





---




<div align="center">

## Licence

<img src="https://readme-typing-svg.demolab.com?lines=MIT%2B%E2%80%94%2Bfaites%2Bce%20que%2Btu%2Bveux%3BGratuit%2Bcomme%2Bdans%2Bla%2Bbi%C3%A8re%3BOpen%2Bsource%2C%2Bouvert%2Besprit&center=true&width=430&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Ce projet est sous licence MIT – voir le fichier [license](license) pour plus de détails.





---




<div align="center">

## L'équipe Palworld

<img src="https://readme-typing-svg.demolab.com?lines=Les%2Bgens%2Bderri%C3%A8re%2Bla%2Bmagie%3BRencontrer%2Bl%27%C3%A9quipe%3BConstruit%2Bavec%2Bpassion&center=true&width=420&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Ce projet n'existerait pas sans les personnes qui le soutiennent.

**[Pylar](https://github.com/deafdudecomputers)** — L'homme qui a tout déclenché. Chaque ligne de cet outil remonte à sa vision et à son travail acharné sur le moteur de sauvegarde, l'interface graphique et les fonctionnalités que vous utilisez quotidiennement.

**[cyrix](https://github.com/CyrixJD115)** — Refactoriste et sous-responsable. Axé sur la qualité du code, la simplification et les améliorations structurelles, en gardant la base de code propre, plus petite et plus facile à maintenir à mesure que le projet se développe.

**[dkoz](https://github.com/dkoz)** — L'homme derrière les pièces d'identité. Fournit des identifiants de données de jeu, un aperçu structurel des codes d'identification et une connaissance approfondie de la manière dont les données de Palworld sont reliées entre elles, ce qui garantit la précision de l'outil à chaque mise à jour du jeu.

**[oMaN-Rod](https://github.com/oMaN-Rod)** — Fourni l'analyseur de sauvegarde d'origine à partir duquel ce projet est issu. Sans son travail fondamental sur le piratage du format de sauvegarde Palworld, rien de tout cela n’existerait. Le fork a rationalisé et simplifié son analyseur pour en faire ce qu'est PST aujourd'hui.


**[Okaetsu](https://github.com/Okaetsu)** — Modding insights that made base import/export possible. His understanding of how Palworld structures base data from the modding side bridged the gap between modding and save editing, making this feature a reality.




---




<div align="center">

## Remerciements

<img src="https://readme-typing-svg.demolab.com?lines=O%C3%B9%2Ble%2Bcr%C3%A9dit%2Best%2Bd%C3%BB%3BMerci%2B%C3%A0%2Btous%3BNous%20%2B%20nous%20tenons%20%2B%20sur%20%2B%20les%20%C3%A9paules&center=true&width=390&height=28&font=monospace&size=22&color=7DD3FC&vCenter=true" alt="" />

</div>

Un immense merci à :

- **Palworld** développé par Pocketpair, Inc. — pour le jeu qui nous a tous réunis.
- **Les rapporteurs de bogues** — chaque problème déposé, chaque cas limite trouvé, chaque journal collé dans Discord. Vous rendez cet outil plus robuste à chaque rapport.
- **La communauté de modding Palworld** : d'autres moddeurs, développeurs d'outils et bricoleurs qui partagent leurs connaissances, effectuent de l'ingénierie inverse des formats et font avancer l'écosystème. Ce projet repose sur les épaules de cet effort collectif.
- **Tous les contributeurs et membres de la communauté** — que vous ayez soumis un PR, répondu à une question dans Discord ou simplement parlé de PST à un ami — merci.

---

<div align="center">

![Divider](../assets/branding/PalworldSaveTools_readme_divider.png)

**Réalisé avec ❤️ pour la communauté Palworld**

[⬆ Back to Top](#palworld-save-tools)

</div>