# Installation

Ton Double IA est une **extension** : elle s'installe **dans ton dossier Monteur IA**
existant. Rien à configurer à la main — l'installation copie les fichiers, puis ton
agent te guide de zéro (compte HeyGen, clé, ton double) avec `/setup-double-ia`.

> ⚠️ **Prérequis : Monteur IA installé et fonctionnel.** Si ce n'est pas encore fait,
> installe d'abord le système principal (son INSTALL.md), puis reviens ici.

---

## 🚀 Le prompt d'installation

> **Le plus simple :** ouvre ton agent (Claude Code ou Codex) **dans ton dossier
> Monteur IA** et dis-lui : « Télécharge l'extension
> https://github.com/Alex-lmdm/double-ia et suis les instructions d'installation de son
> INSTALL.md. » Il fait tout.

Sinon, télécharge le ZIP de ce repo, dézippe-le où tu veux, ouvre ton agent **dans ton
dossier Monteur IA**, et copie-colle exactement le bloc ci-dessous comme premier message
(remplace le chemin de la première ligne par l'endroit où tu as dézippé) :

```text
Tu es mon assistant d'installation pour l'extension « Ton Double IA » de mon Monteur IA.
Le dossier de l'extension dézippé est ici : ~/Downloads/double-ia-main
Installe l'extension étape par étape, sans jamais rien casser. Suis ces règles :

1. VÉRIFIE d'abord que le dossier courant est bien une installation Monteur IA : les
   dossiers `tools/` et `.claude/skills/` existent, et `brand.config.json` ou
   `brand.config.example.json` est présent. Si ce n'est pas le cas, ARRÊTE-TOI et
   dis-moi d'ouvrir mon agent dans mon dossier Monteur IA.

2. COPIE dans ce dossier, depuis le dossier de l'extension (étapes idempotentes : si un
   fichier identique est déjà là, ne le copie pas deux fois ; s'il existe en version
   différente, remplace-le) :
   a) `.claude/skills/double-ia/` et `.claude/skills/setup-double-ia/`
      → dans `.claude/skills/` ;
   b) `tools/double_ia.py` → dans `tools/` ;
   c) AIGUILLAGE : si `templates/AGENT.md.tpl` ne contient PAS le marqueur
      « BEGIN EXTENSION: double-ia », ajoute le contenu INTÉGRAL du fichier
      `templates/agent-extension-double-ia.md` de l'extension À LA FIN de
      `templates/AGENT.md.tpl` (sans le modifier). S'il contient déjà le marqueur,
      ne touche à rien.
   d) GITIGNORE : si `.gitignore` ne contient pas `double-ia.config.json`, ajoute une
      ligne `double-ia.config.json` (ce fichier contiendra les identifiants du double
      de l'utilisateur — il reste local).

3. VÉRIFIE ffmpeg et Python : `ffmpeg -version` et `python3 --version` (déjà là si
   Monteur IA fonctionne).

4. Lance `npm run sync` à la racine (il régénère CLAUDE.md / AGENTS.md avec
   l'aiguillage du double, et duplique les nouveaux skills pour Codex dans
   `.agents/skills/`).

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
génération. Compte 20 minutes la première fois — ensuite, c'est configuré pour de bon.
