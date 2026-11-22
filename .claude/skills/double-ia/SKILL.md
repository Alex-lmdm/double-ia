---
name: double-ia
description: >-
  Génère la vidéo face-cam de l'utilisateur avec son double HeyGen, depuis un AUDIO de sa vraie
  voix (par défaut) ou depuis un TEXTE lu par sa voix clonée (option « zéro micro »), puis enchaîne
  sur le montage Monteur IA, ou rend la vidéo prête à monter quand Ton Double IA est installé seul.
  Use when the user provides an AUDIO file (dictaphone, mp3, m4a, wav) and says « utilise mon
  double », « génère avec mon avatar », « ma vidéo avec le double IA », or gives a TEXT and says
  « avec ma voix clonée », « sans micro », « fais parler mon double ». Ne s'applique PAS si
  l'utilisateur fournit une VIDÉO de lui. Si `double-ia.config.json` n'existe pas → router vers
  `setup-double-ia`. JAMAIS de génération sans confirmation explicite du coût.
---

# Double IA : voix → vidéo face-cam → montage

L'utilisateur a un double HeyGen (configuré par `/setup-double-ia`, config dans
`double-ia.config.json`). Deux façons de le faire parler :

- **Sa vraie voix (par défaut, la plus naturelle)** : il écrit son script (ou tu l'écris avec lui),
  le lit au dictaphone de son téléphone et t'envoie l'audio. **L'audio envoyé EST la piste son
  finale** : c'est ce qui rend le résultat naturel. Étapes 1 à 3, puis 4.
- **Sa voix clonée (zéro micro)**, seulement s'il la demande ou ne peut pas enregistrer : il te
  donne le texte, sa voix clonée le lit (§ Voix clonée), puis étape 4. Plus pratique, un peu moins
  naturel : dis-le-lui une fois, sans le décourager.

**Deux installations possibles** (`python3 tools/double_ia.py check` dit laquelle, ligne « Dossier ») :

- **Dans Monteur IA** : travaille dans le dossier du Reel (`reels/<nom>/`, un projet par Reel) : les
  chemins `derush/…` et `tools/…` de ce skill partent de là. Pas encore de Reel : crée-le d'abord,
  comme pour une vidéo filmée, avec `tools/nouveau_reel.py "<sujet>"` du dossier Monteur IA (depuis
  l'accueil de l'app : `../tools/nouveau_reel.py`), puis travaille dans son dossier. La config du
  double reste dans le dossier Monteur IA, partagée par tous les Reels. (Ancienne installation sans
  `reels/` : tout se passe à la racine, comme avant.) Script : skill `reel-script`.
- **Seul** (dossier « Ton Double IA », sans `templates/AGENT.md.tpl`) : tout se passe à la racine du
  dossier, aucun Reel à créer. La vidéo finie sort dans `videos/<slug>.mp4` ; il n'y a pas de montage
  derrière (étape 6). Script : écris-le avec lui (30 à 45 s, phrases courtes, l'accroche dans la
  première phrase), fais-le valider avant qu'il le lise.

**Quand ce skill ne s'active pas :** l'utilisateur t'envoie une **vidéo** de lui → dans Monteur IA,
pipeline normal (`derush` puis `motion-design`), le double n'intervient pas ; installé seul, dis-lui
simplement que ce dossier fabrique des vidéos avec son double et ne monte pas une vidéo filmée.

## ⛔ Règles d'argent

- Chaque génération débite le portefeuille HeyGen de l'utilisateur (le script affiche le coût
  exact avant chaque génération : environ 3 $ le Reel de 30 s en Avatar 6, 1,50 $ en Avatar 6
  Turbo). **Jamais de génération sans son accord explicite sur le coût affiché** par le
  script. Ne passe `--yes` que s'il vient de dire oui dans la conversation.
- **On ne génère jamais l'enregistrement brut.** Un script lu au dictaphone contient des
  blancs, des faux départs et des phrases reprises (mesuré : 94 s de brut pour 44 s utiles,
  soit le double du prix pour rien). On coupe l'audio D'ABORD (étape 1), on génère ensuite.
- Un raté (mot mal prononcé, geste bizarre) → on corrige la cause, on regénère UNE fois,
  après nouvel accord. Pas d'itérations en rafale.
- Solde insuffisant → le script le dit ; guide vers l'Espace API HeyGen pour recharger
  (app.heygen.com → API → billing). Ne jamais réessayer en boucle.

## L'ordre, verrouillé (ne pas inverser) : sa vraie voix

| # | Étape | Qui | Barrière « terminé quand » |
|---|---|---|---|
| 1 | **Dérush de l'audio** | toi | `derush/<slug>_voice.mp3` : lecture = script, zéro doublon, zéro mot coupé, souffles ≈ 0,10 s |
| 2 | **Validation à l'oreille** | l'utilisateur | il a écouté le MP3 et dit OK (contenu + rythme) |
| 3 | **Nettoyage audio** | Adobe Podcast Enhance (l'utilisateur glisse le MP3, toi le reste) | `derush/<slug>_voice_enhanced.mp3`, **même durée** que le cut |
| 4 | **Génération** | toi, après accord sur le coût | Monteur IA : `derush/<slug>_enhanced.mp4` + `<slug>_cuts.json` ; seul : `videos/<slug>.mp4` |
| 5 | **Vérification du rendu** | toi | pas d'artefact, lip sync OK, 1080x1920 @ 29,97 |
| 6 | **Montage normal**, ou livraison (seul) | `motion-design`, ou toi | comme avec un vrai rush |

Pourquoi cet ordre : HeyGen cale la vidéo sur l'audio reçu et cet audio devient la piste
son finale. Couper ou nettoyer **après** la génération = recouper une vidéo payée en trop, ou
remplacer la piste sur laquelle le lip sync a été calculé (désynchro). Et nettoyer **après**
le cut plutôt qu'avant : le nettoyage uniformise le fond sonore sur l'ensemble, ce qui
masque les jump-cuts au lieu de les souligner.

## Voix clonée (zéro micro) : à la place des étapes 1 à 3

Seulement s'il la demande. `python3 tools/double_ia.py check` dit s'il a une voix clonée ; sinon,
crée-la une fois (gratuit, quelques secondes) : il enregistre **environ 1 minute** de sa voix au
dictaphone, dans une pièce calme, en parlant normalement (le clone garde le son de la pièce), puis

```bash
python3 tools/double_ia.py cloner-voix "<enregistrement>"
```

Ensuite, à chaque vidéo : fais-lui valider le texte, puis

```bash
python3 tools/double_ia.py voix-clonee "<texte, ou fichier .txt>" --slug <slug>
```

Il écrit `derush/<slug>_voix_clonee.mp3` (déjà propre : ni dérush ni Adobe Podcast) et les bornes
de chaque phrase (`<slug>_audio_timeline.json`). **Fais-le écouter avant de générer** (même geste
que l'étape 2). Un mot mal dit : réécris-le comme il se prononce, ou reformule la phrase, et
relance (gratuit). Validé : étape 4 sur `derush/<slug>_voix_clonee.mp3`.

## Étape 1 : dérusher l'audio

Même méthode que le skill `derush`, mais sur l'audio seul (pas de vidéo, donc pas de
détection de changement de plan). Outils et modèle Whisper : `brand.config.json` → `env`
(`ffmpegPath`, `whisperCli`, `whisperModel`), langue : `derush.whisperLanguage`.

1. Convertir en WAV 16 kHz mono (`work/a16.wav`) et repérer les îlots de parole :
   `ffmpeg -i work/a16.wav -af silencedetect=noise=-40dB:d=0.18 -f null -`
   (**jamais `-v error`** avec silencedetect : il logue en niveau info, tu ne verrais rien).
2. Transcrire le tout (`whisper-cli -m $MODEL -l <LANG> -oj`), puis **transcrire chaque îlot
   séparément** : Whisper segmente plus large que les îlots et attribue le texte au mauvais
   îlot, la transcription par îlot rend la sélection auto-vérifiante.
3. **Sélection : toujours la DERNIÈRE tentative complète de chaque phrase.** C'est la
   meilleure. Jeter les faux départs et les variantes intermédiaires. Le script connu sert de
   référence : une phrase jamais dite proprement → le signaler, proposer de la réenregistrer.
4. Deux pièges connus :
   - un **mot isolé** dans son propre îlot (« Tu », 0,24 s) suivi d'un blanc : presque toujours
     un faux départ, pas un début de phrase à recoller. **Zoomer mot-à-mot sur l'attaque de la
     prise suivante** (`-ml 1 -sow -wt 0.01` sur la slice) : si elle redit le mot, jeter
     l'orphelin, sinon on obtient « Tu, tu l'ajoutes », inaudible sur une transcription
     normale (Whisper lisse les bafouillages).
   - une **micro-pause** (< 0,25 s) au milieu d'une phrase = respiration à garder : fusionner
     les deux îlots avec `"gap": "breath"`.
5. Écrire `derush/<slug>_segments.json` (une entrée par prise gardée, dans l'ordre final,
   bornes = îlots silencedetect, jamais les timestamps Whisper) puis construire le cut :

```bash
python3 tools/build_audio_cut.py "<audio brut>" --segments derush/<slug>_segments.json --slug <slug>
```

   Il applique `derush.padStart` / `padEnd` (0,04 / 0,02 par défaut : on resserre les fins,
   jamais les débuts ; un 0 réglé par l'utilisateur est respecté, aucune marge), insère un
   souffle régulier entre les prises (0,10 s ; 0,05 en liaison intra-phrase ; 0,15 sur une
   respiration), et sort `derush/<slug>_voice.mp3` (320k mono
   48 kHz) + `derush/<slug>_audio_timeline.json`.
6. Vérifier : re-transcrire le cut (lecture = script, zéro doublon, zéro mot coupé) et mesurer
   les souffles (`silencedetect=noise=-40dB:d=0.05` → moyenne ≈ 0,10 s, max < 0,21 s).

## Étape 2 : faire valider à l'oreille

Révèle le MP3 (`open -R derush/<slug>_voice.mp3` sur macOS, `explorer /select,…` sur
Windows) et demande à l'utilisateur de l'écouter. **Rien ne part sur HeyGen avant son OK.**
S'il entend un doublon ou un mot coupé : zoom mot-à-mot sur la zone, corriger le segment,
rebuild, re-vérifier.

## Étape 3 : nettoyer l'audio (toujours, pas seulement « si ça grésille »)

Une seule méthode, **toujours la même** : Adobe Podcast Enhance (gratuit, compte Adobe). Ne
propose jamais d'alternative (pas de filtre ffmpeg, pas de « je le fais moi-même »). C'est le
même geste que le skill `derush` §7 :

1. Donne à l'utilisateur, en un seul message, exactement ces consignes puis attends :
   > « Ouvre https://podcast.adobe.com/enhance (connecté à ton compte Adobe), glisse le fichier
   > `<slug>_voice.mp3` que je viens de te montrer sur la zone « Optimiser », attends la fin du
   > traitement, clique « Télécharger », puis dis-moi "c'est téléchargé". »
   ⚠️ L'upload passe par le sélecteur de fichiers natif de l'OS : **tu ne peux pas le faire à sa
   place**, n'essaie pas.
2. Quand il dit que c'est téléchargé : prends le fichier le plus récent du dossier de
   téléchargements dont le nom commence par `<slug>_voice` (Adobe le renomme), copie-le en
   `derush/<slug>_voice_enhanced.mp3`. S'il n'y en a aucun, redonne la consigne, sans improviser.

**Vérifier que la durée est identique** au cut (`ffprobe … format=duration`, écart < 0,1 s)
avant de générer. **C'est ce fichier nettoyé, et lui seul, qui part en génération.**

## Étape 4 : générer

```bash
python3 tools/double_ia.py generate derush/<slug>_voice_enhanced.mp3     # sa vraie voix
python3 tools/double_ia.py generate derush/<slug>_voix_clonee.mp3        # sa voix clonée
```

Le script refuse un `_voice.mp3` non nettoyé et un audio sans `_audio_timeline.json` (garde-fou
contre la génération du brut ; `--allow-raw` seulement si l'utilisateur fournit un audio déjà
propre et lu d'une traite). Il affiche durée, moteur, coût estimé et solde ; lancé par l'agent, il
s'arrête là sans rien débiter (annonce ce coût, attends son oui, relance avec `--yes`). Avec
`--yes`, il génère avec le moteur de la config, puis conforme : 25 → 29,97 fps, crf 14, et remet
l'audio d'origine. Sorties : dans Monteur IA, `derush/<slug>_enhanced.mp4` (le même nom qu'un
dérush filmé) et `derush/<slug>_cuts.json` (frontières des prises, dérivées du cut audio : le
double ne saute pas à l'image, pas de scene-change à mesurer) ; installé seul, `videos/<slug>.mp4`.
Limites : 10 min / 50 Mo. Un rendu prend 1 à 3 minutes pour 30 s.

**Le moteur** (`python3 tools/double_ia.py moteur` les liste avec leur prix, `moteur <nom>` en
change pour les vidéos suivantes) :
- **Avatar 6** (`heygen-avatar-6`), celui d'un nouveau double : les gestes suivent ce qu'il dit,
  environ 3 $ le Reel de 30 s.
- **Avatar 6 Turbo** (`heygen-avatar-6-turbo`) : moitié prix, rendu plus rapide, un peu moins
  fin. À proposer pour un essai ou s'il veut dépenser moins.
- **Avatar IV** et **Avatar V** : les anciens moteurs (environ 2,20 $). Un double configuré avant
  Avatar 6 garde le sien : `check` signale qu'Avatar 6 est disponible ; propose-le une fois, avec
  son prix, et ne change de moteur que sur son oui. Ne propose jamais Avatar III.

**Sa gestuelle** (Avatar 6, et Avatar V pour la direction) : `--direction "<consigne>"` décrit
le jeu voulu en une phrase claire, de préférence en anglais (« smile warmly, small open-handed
gestures »), et `--calme` donne des gestes plus rares et plus petits. Seulement s'il le demande ou
si un rendu précédent bougeait trop : par défaut, Avatar 6 cale déjà les gestes sur le texte.

## Étape 5 : vérifier avant de montrer

1. Extraire 3-4 frames + un zoom visage : pas d'artefact, mains correctes.
2. Contrôler le lip sync sur un passage rapide (mots en b/p/m).
3. `ffprobe` : 1080x1920, 29,97 fps, durée = durée de l'audio.

Un mot mal prononcé ne se corrige pas côté HeyGen : l'utilisateur réenregistre la phrase,
tu la recolles dans les segments, rebuild du cut, re-nettoyage, regénération après accord (voix
clonée : corrige le texte, relance `voix-clonee`, regénère après accord).

## Étape 6 : livrer (installé seul)

Révèle la vidéo (`open -R videos/<slug>.mp4` sur macOS, `explorer /select,…` sur Windows) et
dis-lui qu'elle est prête à monter dans l'outil de son choix (CapCut, Premiere, InShot…) ou à
publier telle quelle. Ce dossier ne fait pas le montage : ne promets ni sous-titres ni coupes. S'il
demande le montage, dis une fois, simplement, que c'est ce que fait Monteur IA
(https://www.lemondedumarketing.fr/monteur-ia), qui reprend ce double tel quel, sans insister.

## Étape 6 : enchaîner sur le montage normal (dans Monteur IA)

Produire `derush/<slug>_words.json` avec `tools/build_words.py` (pointer `CUT` sur
`derush/<slug>_enhanced.mp4` et `tools/sections.py` → `CUTS_PATH` sur `<slug>_cuts.json`),
puis reprendre le pipeline Monteur IA à l'étape 4 (`motion-design` : sections, split-screens,
sous-titres, review, SFX/musique, export). Rien de spécifique au double au-delà de cette ligne :
la vidéo générée remplace le rush filmé, à l'identique.

## Dépannage

- « Pas de double configuré » → `/setup-double-ia` (double déjà créé sur HeyGen : étape 4 bis,
  `python3 tools/double_ia.py lier`).
- Consentement pas accepté → `python3 tools/double_ia.py consent` (lien webcam 24 h).
- Génération `failed` → lire le `failure_message` du script ; le plus courant : audio
  trop long (> 10 min) ou solde à zéro.
- Un moteur refusé par son double (« n'est pas disponible pour ce look ») → le script passe au
  meilleur moteur disponible et le dit ; `moteur` liste ceux que son double accepte.
- Voix clonée qui échoue (`FAILED`) → réenregistrer 1 minute de parole claire, sans musique ni
  bruit, puis `cloner-voix … --force`.
- Vérifier l'état général à tout moment : `python3 tools/double_ia.py check`.
