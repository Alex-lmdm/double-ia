# Installation

**Pour l'IA :** guide l'utilisateur dans sa langue (espagnol s'il te parle espagnol),
y compris les bilans et les exemples. Conserve les noms des fichiers et des commandes.
Les exemples français ci-dessous doivent être adaptés, pas récités. La langue des vidéos
reste celle demandée pour le contenu et celle de l'audio à transcrire.

Ton Double IA s'installe de deux façons, choisies toutes seules par ton agent :

- **Dans ton Monteur IA** (si tu l'as) : c'est une extension, ton monteur enchaîne le montage
  dès que ton double a parlé.
- **Seul**, dans son propre dossier « Ton Double IA » : tu récupères tes vidéos face caméra,
  prêtes à monter dans l'outil de ton choix, avec les bonus (ton scénariste de Reels, le Reel
  Cloneur de ton double, ton double partout).

Rien à configurer à la main : l'installation copie les fichiers (et, seul, installe les outils
qui manquent), puis ton agent te guide de zéro (compte HeyGen, clé, ton double) avec
`/setup-double-ia`.

---

## 🚀 Le prompt d'installation

> **Le plus simple :** ouvre ton agent (Claude Code ou Codex). Tu as Monteur IA ? Ouvre-le **dans
> ton dossier Monteur IA** (dans l'app HyperFrames : l'accueil ou un Reel de Monteur IA
> conviennent). Sinon, ouvre-le dans un **dossier vide nommé « Ton Double IA »** (dans ton dossier
> Vidéos, par exemple). Puis dis-lui : « Télécharge l'extension https://github.com/Alex-lmdm/double-ia
> et suis les instructions d'installation de son INSTALL.md. » Il fait tout.

**Pour l'IA, si on te demande de télécharger l'extension :** télécharge-la dans un dossier
temporaire, jamais dans le dossier où tu installes. Crée-le avec `mktemp -d` (macOS, Linux) ou, sous
Windows (PowerShell), `New-Item -ItemType Directory -Path (Join-Path $env:TEMP "double-ia-$(Get-Random)")`,
puis, dans ce dossier (PowerShell : `curl.exe`, et `;` au lieu de `&&`) :

```bash
cd "<dossier temporaire>" && curl -fL -o double-ia.tar.gz https://github.com/Alex-lmdm/double-ia/archive/refs/heads/main.tar.gz && tar -xzf double-ia.tar.gz
```

Le dossier de l'extension est alors `<dossier temporaire>/double-ia-main` : suis le bloc ci-dessous
avec ce chemin en première ligne.

**Mettre à jour** : même phrase, dans le même dossier. La nouvelle version remplace l'ancienne, tes
réglages et ton double sont gardés ; inutile de refaire le setup.

Sinon, télécharge le ZIP de ce repo, dézippe-le où tu veux, ouvre ton agent dans ton dossier
Monteur IA (ou dans un dossier vide « Ton Double IA »), et copie-colle exactement le bloc
ci-dessous comme premier message (remplace le chemin de la première ligne par l'endroit où tu as
dézippé) :

```text
Tu es mon assistant d'installation de « Ton Double IA ».
Le dossier de l'extension dézippé est ici : ~/Downloads/double-ia-main
Installe-le étape par étape, sans jamais rien casser. Suis ces règles :

1. CHOISIS LE MODE. Cherche mon dossier Monteur IA : le dossier courant s'il contient
   `templates/AGENT.md.tpl`, sinon le premier dossier parent qui le contient (dans l'app
   HyperFrames, la conversation est ouverte dans l'accueil ou dans un Reel, deux
   sous-dossiers de Monteur IA).
   - Trouvé : mode EXTENSION, étapes A. MAISON = ce dossier Monteur IA.
   - Pas trouvé : demande-moi d'abord « Tu as Monteur IA installé sur cet ordinateur ? ».
     Oui : dis-moi d'ouvrir mon agent dans mon dossier Monteur IA et ARRÊTE-TOI.
     Non : mode SEUL, étapes B.

A. MODE EXTENSION (dans Monteur IA)

A1. VÉRIFIE que MAISON contient aussi `tools/`, `.claude/skills/`, et `brand.config.json`
    ou `brand.config.example.json`. Sinon, ARRÊTE-TOI et dis-moi d'ouvrir mon agent dans
    mon dossier Monteur IA. Tous les chemins des étapes suivantes partent de MAISON,
    jamais d'un Reel ni de l'accueil.

A2. COPIE dans MAISON, depuis le dossier de l'extension (étapes idempotentes : si un
    fichier identique est déjà là, ne le copie pas deux fois ; s'il existe en version
    différente, remplace-le) :
    a) `.claude/skills/double-ia/` et `.claude/skills/setup-double-ia/`
       → dans `.claude/skills/` (pas `scenariste-reels` ni `reel-cloneur-double` : Monteur
       IA a déjà les siens, `reel-script` et `reel-cloneur`) ;
    b) `tools/double_ia.py` et `tools/build_audio_cut.py` → dans `tools/` ;
    c) AIGUILLAGE : si `templates/AGENT.md.tpl` ne contient PAS le marqueur
       « BEGIN EXTENSION: double-ia », ajoute le contenu INTÉGRAL du fichier
       `templates/agent-extension-double-ia.md` de l'extension À LA FIN de
       `templates/AGENT.md.tpl` (sans le modifier). S'il contient déjà le marqueur,
       REMPLACE tout le bloc, de « BEGIN EXTENSION: double-ia » à « END EXTENSION:
       double-ia » (marqueurs compris), par ce même fichier : c'est ainsi qu'une
       nouvelle version de l'extension met ses consignes à jour, jamais en double.
    d) GITIGNORE : si `.gitignore` ne contient pas `double-ia.config.json`, ajoute une
       ligne `double-ia.config.json` (ce fichier contiendra les identifiants du double
       de l'utilisateur ; il reste local).

A3. VÉRIFIE ffmpeg et Python : `ffmpeg -version` et `python3 --version` (déjà là si
    Monteur IA fonctionne).

A4. Lance `node "<MAISON>/scripts/sync.mjs"` (c'est `npm run sync` : il régénère CLAUDE.md /
    AGENTS.md avec l'aiguillage du double, duplique les nouveaux skills pour Codex dans
    `.agents/skills/` et, en Monteur IA 2, met à jour l'accueil et les outils de chaque Reel).

A5. Termine. Si `double-ia.config.json` existe déjà (mise à jour) : lance
    `python3 tools/double_ia.py check` ; s'il dit qu'Avatar 6 est disponible, propose-le-moi
    une fois avec son prix (`python3 tools/double_ia.py moteur`), et change de moteur
    seulement si je dis oui. Sinon, dis-moi : « Extension installée. Dis-moi "Crée mon double IA"
    et je te guide de zéro : compte HeyGen gratuit, ta clé, ton double, ta première vidéo. »

B. MODE SEUL (dossier « Ton Double IA », sans Monteur IA)

B1. DOSSIER. MAISON = le dossier courant s'il est vide, s'il s'appelle « Ton Double IA »,
    ou s'il contient déjà `tools/double_ia.py` (mise à jour). Sinon (dossier personnel,
    Bureau, dossier rempli d'autres choses), crée `Ton Double IA` dans le dossier Vidéos
    (macOS : `~/Movies` ; Windows : le dossier Vidéos de l'utilisateur) : MAISON = ce
    dossier, et retiens qu'il faudra me dire de rouvrir mon agent dedans (étape B6).
    Évite Documents, le Bureau, iCloud Drive et OneDrive : ils sont souvent synchronisés.

B2. COPIE dans MAISON, depuis le dossier de l'extension (idempotent, comme en A2) :
    a) `.claude/skills/double-ia/`, `.claude/skills/setup-double-ia/`,
       `.claude/skills/scenariste-reels/` et `.claude/skills/reel-cloneur-double/` → dans
       `.claude/skills/` ET dans `.agents/skills/` (le second sert à Codex) ;
    b) `tools/double_ia.py` et `tools/build_audio_cut.py` → dans `tools/` ;
    c) `templates/consignes-seul.md` → copié DEUX fois, en `CLAUDE.md` et en `AGENTS.md`
       à la racine de MAISON (ce sont les consignes du dossier ; une version plus ancienne
       est remplacée) ;
    d) crée les dossiers `videos/` et `derush/` s'ils manquent.

B3. OUTILS. Vérifie chacun, et annonce en une fois ce qui manque (avec la taille des
    téléchargements) avant d'installer :
    - **Python 3.9 minimum** : macOS `python3 --version` (s'il manque, le Mac propose
      d'installer les « outils de développement en ligne de commande » : c'est la bonne
      réponse). Windows : `python --version`, sinon `py --version` ; absent :
      `winget install -e --id Python.Python.3.12`, puis rouvrir l'agent. Sous Windows, les
      commandes `python3` des consignes s'écrivent `python` (ou `py`).
    - **FFmpeg** : `ffmpeg -version` et `ffprobe -version`. macOS : `brew install ffmpeg`
      (si Homebrew manque, explique-le et demande mon accord avant de l'installer).
      Windows : `winget install Gyan.FFmpeg`, puis rouvrir l'agent si le PATH n'est pas vu.
    - **Whisper** (il transcrit mon audio pour couper les blancs et les ratés) : cherche
      `whisper-cli` (macOS : `command -v whisper-cli` ; PowerShell : `Get-Command whisper-cli
      -ErrorAction SilentlyContinue`) et un modèle `ggml-*.bin` dans `~/.cache/monteur-ia/whisper/`,
      `~/.cache/hyperframes/whisper/models/`, `~/whisper-models/` et `~/.cache/whisper/`. Garde
      un binaire et un modèle qui marchent déjà. macOS : `brew install whisper.cpp` ; Windows :
      le binaire whisper.cpp compatible des releases officielles `ggml-org/whisper.cpp` (vérifie
      que l'archive existe vraiment). Modèle manquant : `ggml-large-v3-turbo.bin` (~1,6 Go),
      rangé dans `~/.cache/monteur-ia/whisper/` (Windows : sous `%USERPROFILE%`), là où Monteur
      IA le cherchera s'il est installé un jour. Connexion limitée : `ggml-small.bin` (~0,5 Go),
      un peu moins précis.
    - **yt-dlp** (gratuit, il télécharge les Reels à cloner) : `yt-dlp --version`, version
      2026.07.01 ou plus récente (en dessous, Instagram ne se télécharge plus). macOS :
      `brew install yt-dlp` (trop ancien : `brew upgrade yt-dlp`). Windows :
      `winget install -e --id yt-dlp.yt-dlp` (trop ancien : `winget upgrade -e --id
      yt-dlp.yt-dlp`). Quelques dizaines de Mo.

B4. RÉGLAGES. Crée `brand.config.json` à la racine de MAISON s'il manque (sinon, complète
    seulement ce qui manque), avec les chemins RÉELLEMENT trouvés :
    { "env": { "ffmpegPath": "<dossier qui contient ffmpeg>", "whisperCli": "<chemin de
      whisper-cli>", "whisperModel": "<chemin du modèle>", "ytDlp": "<chemin de yt-dlp>" },
      "derush": { "whisperLanguage": "<langue de mes vidéos, ex. fr>", "padStart": 0.04,
      "padEnd": 0.02 } }

B5. VÉRIFIE avant d'annoncer la réussite : `python3 tools/double_ia.py --help` sans erreur ;
    `ffprobe -version` ; `yt-dlp --version` (2026.07.01 ou plus) ; Whisper sur un petit son
    de test fabriqué avec FFmpeg (code de sortie 0 et modèle réellement chargé ; un son sans
    parole peut ne donner aucun mot, ce n'est pas un échec). Fais un bilan bref : **✅ Vérifié** seulement ce qui est testé, sinon
    **À terminer** avec la prochaine action. Supprime les fichiers de test.

B6. Termine en me disant : « Ton Double IA est installé. Dis-moi "Crée mon double IA" et je te
    guide de zéro : compte HeyGen gratuit, ta clé, ton double, ta première vidéo. » Si tu as
    créé MAISON ailleurs que dans le dossier courant (B1), dis-moi d'abord de rouvrir mon agent
    dans ce dossier, en me donnant son chemin.
```

---

## Après l'installation

Dis simplement à ton agent :

```
/setup-double-ia
```

(sous Codex : « setup double IA », ou simplement « Crée mon double IA »). Il te guide pas à pas :
compte HeyGen gratuit (aucun abonnement à prendre), ta clé API, quelques euros de crédit, ta vidéo
d'entraînement de 30 secondes, et ta première génération. Compte 20 minutes la première fois ;
ensuite, c'est configuré pour de bon. Tu as déjà un double sur HeyGen : dis « J'ai déjà un double
HeyGen », il le relie sans rien recréer.

Ensuite, les phrases à lui dire sont dans le [README](README.md) : « Voici l'audio, utilise mon
double. », « Écris-moi un Reel sur [ton sujet] », « Clone ce Reel pour mon double : [lien du
Reel] », « Mets mon double dans [décor] », « Fais-la en version rapide »…
