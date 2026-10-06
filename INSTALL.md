# Installation

**Pour l'IA :** guide l'utilisateur dans sa langue (espagnol s'il te parle espagnol),
y compris les bilans et les exemples. Conserve les noms des fichiers et des commandes.
Les exemples français ci-dessous doivent être adaptés, pas récités. La langue des vidéos
reste celle demandée pour le contenu et celle de l'audio à transcrire.

Ton Double IA est une **extension** : elle s'installe **dans ton dossier Monteur IA**
existant. Rien à configurer à la main : l'installation copie les fichiers, puis ton
agent te guide de zéro (compte HeyGen, clé, ton double) avec `/setup-double-ia`.

> ⚠️ **Prérequis : Monteur IA installé et fonctionnel.** Si ce n'est pas encore fait,
> installe d'abord le système principal (son INSTALL.md), puis reviens ici.

---

## 🚀 Le prompt d'installation

> **Le plus simple :** ouvre ton agent (Claude Code ou Codex) **dans ton dossier
> Monteur IA** (dans l'app HyperFrames : l'accueil ou un Reel de Monteur IA conviennent) et
> dis-lui : « Télécharge l'extension https://github.com/Alex-lmdm/double-ia et suis les
> instructions d'installation de son INSTALL.md. » Il fait tout.

**Pour l'IA, si on te demande de télécharger l'extension :** télécharge-la dans un dossier
temporaire (celui de la mise à jour de Monteur IA convient), jamais dans le dossier Monteur IA. Crée-le avec
`node -p "require('fs').mkdtempSync(require('path').join(require('os').tmpdir(), 'double-ia-'))"`,
puis, dans ce dossier (PowerShell : `curl.exe`, et `;` au lieu de `&&`) :

```bash
cd "<dossier temporaire>" && curl -fL -o double-ia.tar.gz https://github.com/Alex-lmdm/double-ia/archive/refs/heads/main.tar.gz && tar -xzf double-ia.tar.gz
```

Le dossier de l'extension est alors `<dossier temporaire>/double-ia-main` : suis le bloc ci-dessous
avec ce chemin en première ligne.

**Mettre à jour l'extension** : même phrase. La nouvelle version remplace l'ancienne, tes réglages
sont gardés ; inutile de refaire le setup.

Sinon, télécharge le ZIP de ce repo, dézippe-le où tu veux, ouvre ton agent **dans ton
dossier Monteur IA**, et copie-colle exactement le bloc ci-dessous comme premier message
(remplace le chemin de la première ligne par l'endroit où tu as dézippé) :

```text
Tu es mon assistant d'installation pour l'extension « Ton Double IA » de mon Monteur IA.
Le dossier de l'extension dézippé est ici : ~/Downloads/double-ia-main
Installe l'extension étape par étape, sans jamais rien casser. Suis ces règles :

1. TROUVE mon dossier Monteur IA, appelé MAISON ci-dessous : le dossier courant s'il
   contient `templates/AGENT.md.tpl`, sinon le premier dossier parent qui le contient
   (dans l'app HyperFrames, la conversation est ouverte dans l'accueil ou dans un Reel,
   deux sous-dossiers de MAISON). VÉRIFIE que MAISON contient aussi `tools/`,
   `.claude/skills/`, et `brand.config.json` ou `brand.config.example.json`. Sinon,
   ARRÊTE-TOI et dis-moi d'ouvrir mon agent dans mon dossier Monteur IA. Tous les chemins
   des étapes suivantes partent de MAISON, jamais d'un Reel ni de l'accueil.

2. COPIE dans MAISON, depuis le dossier de l'extension (étapes idempotentes : si un
   fichier identique est déjà là, ne le copie pas deux fois ; s'il existe en version
   différente, remplace-le) :
   a) `.claude/skills/double-ia/` et `.claude/skills/setup-double-ia/`
      → dans `.claude/skills/` ;
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

3. VÉRIFIE ffmpeg et Python : `ffmpeg -version` et `python3 --version` (déjà là si
   Monteur IA fonctionne).

4. Lance `node "<MAISON>/scripts/sync.mjs"` (c'est `npm run sync` : il régénère CLAUDE.md /
   AGENTS.md avec l'aiguillage du double, duplique les nouveaux skills pour Codex dans
   `.agents/skills/` et, en Monteur IA 2, met à jour l'accueil et les outils de chaque Reel).

5. Termine en me disant : « Extension installée. Dis-moi "setup double IA" et je te
   guide de zéro : compte HeyGen gratuit, ta clé, ton double, ta première vidéo. »
```

---

## Après l'installation

Dis simplement à ton agent :

```
/setup-double-ia
```

Il te guide pas à pas : compte HeyGen gratuit (aucun abonnement à prendre), ta clé API,
quelques euros de crédit, ta vidéo d'entraînement de 30 secondes, et ta première
génération. Compte 20 minutes la première fois ; ensuite, c'est configuré pour de bon.
