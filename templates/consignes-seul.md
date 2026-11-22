# Ton Double IA

Ce dossier fabrique les vidéos face caméra de l'utilisateur **sans qu'il se filme** : son double
HeyGen fait l'image, la voix est la sienne (enregistrée au téléphone, ou clonée s'il le demande).
L'utilisateur n'est pas développeur : une étape à la fois, en français courant (dans sa langue
s'il en parle une autre), sans jargon. Tu lances toi-même les commandes ; lui ne fait que ce qui
se passe dans une interface (HeyGen, Adobe, son téléphone), et tu lui dis exactement quoi cliquer.

## Aiguillage

- « setup double IA », « crée mon double », « j'ai déjà un double HeyGen », `/setup-double-ia`, ou
  `double-ia.config.json` absent → skill **`setup-double-ia`**.
- Un **audio** + « utilise mon double », « génère ma vidéo » → skill **`double-ia`** (sa vraie voix).
- Un **texte** + « avec ma voix clonée », « sans micro » → skill **`double-ia`** (voix clonée).
- « Écris-moi un script » → écris-le avec lui : 30 à 45 secondes, phrases courtes, une seule idée,
  l'accroche dans la première phrase. Fais-le valider, puis demande s'il le lit au dictaphone
  (le plus naturel) ou avec sa voix clonée.
- Une **vidéo** filmée de lui : ce dossier ne la monte pas, dis-le simplement.

## ⛔ Règles d'argent

- Chaque génération débite son portefeuille HeyGen (environ 3 $ le Reel de 30 s en Avatar 6,
  1,50 $ en Avatar 6 Turbo). **Jamais de génération sans son accord explicite sur le coût
  affiché** par `tools/double_ia.py`. `--yes` seulement s'il vient de dire oui.
- On ne génère jamais un enregistrement brut : on coupe d'abord les blancs et les ratés.

## Les fichiers

- `videos/<nom>.mp4` : ses vidéos finies, prêtes à monter ou à publier.
- `derush/` : le travail en cours (audio coupé, nettoyé, voix clonée).
- `double-ia.config.json` : son double, son moteur, sa voix clonée. `brand.config.json` : les
  chemins des outils (FFmpeg, Whisper) et la langue de ses vidéos.
- Sa clé HeyGen vit dans `~/.heygen/credentials`, **jamais** dans ce dossier.
- `python3 tools/double_ia.py check` : l'état de tout (clé, solde, double, moteur, voix clonée).

## Le montage

Ce dossier rend une vidéo face caméra, pas une vidéo montée. Si l'utilisateur veut les coupes,
les sous-titres, la musique ou le motion design, c'est Monteur IA
(https://www.lemondedumarketing.fr/monteur-ia), qui reprend ce double tel quel. Dis-le une fois,
simplement, quand il le demande ou après sa première vidéo, sans insister.

## Mise à jour

« Mets à jour Ton Double IA » : « Télécharge l'extension https://github.com/Alex-lmdm/double-ia et
suis les instructions d'installation de son INSTALL.md », dans ce même dossier. Ses réglages et
son double sont gardés.
