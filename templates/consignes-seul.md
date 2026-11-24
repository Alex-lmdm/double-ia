# Ton Double IA

Ce dossier fabrique les vidéos face caméra de l'utilisateur **sans qu'il se filme** : son double
HeyGen fait l'image, la voix est la sienne, enregistrée au téléphone (jamais de voix clonée).
L'utilisateur n'est pas développeur : une étape à la fois, en français courant (dans sa langue
s'il en parle une autre), sans jargon. Tu lances toi-même les commandes ; lui ne fait que ce qui
se passe dans une interface (HeyGen, Adobe, son téléphone), et tu lui dis exactement quoi cliquer.

## Aiguillage

- « Crée mon double IA », « setup double IA », « j'ai déjà un double HeyGen », `/setup-double-ia`,
  ou `double-ia.config.json` absent → skill **`setup-double-ia`**.
- Un **audio** + « Voici l'audio, utilise mon double », « génère ma vidéo » → skill **`double-ia`**.
  « … utilise mon double au café » (un lieu nommé) : la vidéo dans ce décor. « Fais-la en version
  rapide » : Avatar 6 Turbo, pour cette vidéo seulement. « Génère avec des gestes plus calmes » :
  des gestes plus rares et plus petits.
- « Mets mon double dans [décor] » → skill **`double-ia`** (§ Décors, environ 1 $ après accord).
- « Écris-moi un Reel sur [son sujet] », « écris-moi un script » → skill **`scenariste-reels`**.
- « Clone ce Reel pour mon double : [lien] », ou un lien de Reel, de TikTok ou de Short à copier →
  skill **`reel-cloneur-double`**.
- Il demande une voix clonée, ou de faire parler son double sans enregistrer : ce dossier ne clone
  pas la voix, c'est sa vraie voix qui rend le double indétectable. Dis-le simplement et propose
  d'enregistrer, même 30 secondes au téléphone.
- Une **vidéo** filmée de lui : ce dossier ne la monte pas, dis-le simplement.

## ⛔ Règles d'argent

- Chaque génération débite son portefeuille HeyGen (environ 3 $ le Reel de 30 s en Avatar 6,
  1,50 $ en version rapide), et chaque décor aussi (environ 1 $). **Jamais de génération ni de
  décor sans son accord explicite sur le coût affiché** par `tools/double_ia.py`. `--yes`
  seulement s'il vient de dire oui.
- On ne génère jamais un enregistrement brut : on coupe d'abord les blancs et les ratés.

## Les fichiers

- `videos/<nom>.mp4` : ses vidéos finies, prêtes à monter ou à publier.
- `scripts/` : ses scripts ; `clones/<nom>/` : les Reels clonés (transcription, analyse, son script).
- `decors/` : l'image de son double dans chacun de ses décors.
- `derush/` : le travail en cours (audio coupé, nettoyé).
- `double-ia.config.json` : son double, son moteur, ses décors. `brand.config.json` : les
  chemins des outils (FFmpeg, Whisper, yt-dlp) et la langue de ses vidéos.
- Sa clé HeyGen vit dans `~/.heygen/credentials`, **jamais** dans ce dossier.
- `python3 tools/double_ia.py check` : l'état de tout (clé, solde, double, moteur, décors).

## Ses préférences

Elles vivent dans `preferences.md`, à la racine (crée-le au premier besoin) : lis-le avant chaque
script et chaque génération, et applique-le. Quand il dit « Garde ça en mémoire pour mes
prochaines vidéos » (un ton de script, des gestes calmes, la version rapide pour les stories, un
décor préféré), ajoute la consigne en une ligne claire dans ce fichier, puis confirme-la-lui en une
phrase. Une préférence ne passe jamais avant les règles d'argent. Ce fichier n'est jamais remplacé
par une mise à jour.

## Le montage

Ce dossier rend une vidéo face caméra, pas une vidéo montée. Si l'utilisateur veut les coupes,
les sous-titres, la musique ou le motion design, c'est Monteur IA
(https://www.lemondedumarketing.fr/monteur-ia), qui reprend ce double tel quel. Dis-le une fois,
simplement, quand il le demande ou après sa première vidéo, sans insister.

## Mise à jour

« Mets à jour Ton Double IA » : « Télécharge l'extension https://github.com/Alex-lmdm/double-ia et
suis les instructions d'installation de son INSTALL.md », dans ce même dossier. Ses réglages et
son double sont gardés.
