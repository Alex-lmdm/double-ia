---
name: double-ia
description: >-
  Génère la vidéo face-cam de l'utilisateur depuis un AUDIO de sa vraie voix, via son
  double HeyGen, puis enchaîne sur le montage Monteur IA normal. Use when the user
  provides an AUDIO file (dictaphone, mp3, m4a, wav) and says « utilise mon double »,
  « génère avec mon avatar », « ma vidéo avec le double IA ». Ne s'applique PAS si
  l'utilisateur fournit une VIDÉO de lui : c'est le pipeline habituel (skill `derush`).
  Ordre verrouillé : dérush de l'audio → validation à l'oreille → nettoyage audio →
  génération → montage normal. Sortie : derush/<slug>_enhanced.mp4 + <slug>_cuts.json,
  les mêmes livrables qu'un dérush filmé. Si `double-ia.config.json` n'existe pas →
  router vers `setup-double-ia`. JAMAIS de génération sans confirmation explicite du coût.
---

# Double IA — audio → vidéo face-cam → montage

L'utilisateur a un double HeyGen (configuré par `/setup-double-ia`, config dans
`double-ia.config.json`). Il écrit son script (ou tu l'écris avec lui via `reel-script`), le lit
au dictaphone de son téléphone, et t'envoie l'audio. Le double fait l'image. **On ne clone
jamais la voix : l'audio envoyé EST la piste son finale du Reel.** C'est ce qui rend le
résultat naturel.

**Quand cette extension ne s'active pas :** l'utilisateur t'envoie une **vidéo** de lui →
pipeline Monteur IA normal (`derush` puis `motion-design`), le double n'intervient pas.

## ⛔ Règles d'argent

- Chaque génération débite le portefeuille HeyGen de l'utilisateur (~0,07 $/s, ~2 $ le reel
  de 30 s). **Jamais de génération sans son accord explicite sur le coût affiché** par le
  script. Ne passe `--yes` que s'il vient de dire oui dans la conversation.
- **On ne génère jamais l'enregistrement brut.** Un script lu au dictaphone contient des
  blancs, des faux départs et des phrases reprises (mesuré : 94 s de brut pour 44 s utiles,
  soit le double du prix pour rien). On coupe l'audio D'ABORD (étape 1), on génère ensuite.
- Un raté (mot mal prononcé, geste bizarre) → on corrige la cause, on regénère UNE fois,
  après nouvel accord. Pas d'itérations en rafale.
- Solde insuffisant → le script le dit ; guide vers l'Espace API HeyGen pour recharger
  (app.heygen.com → API → billing). Ne jamais réessayer en boucle.

## L'ordre, verrouillé (ne pas inverser)

| # | Étape | Qui | Barrière « terminé quand » |
|---|---|---|---|
| 1 | **Dérush de l'audio** | toi | `derush/<slug>_voice.mp3` : lecture = script, zéro doublon, zéro mot coupé, souffles ≈ 0,10 s |
| 2 | **Validation à l'oreille** | l'utilisateur | il a écouté le MP3 et dit OK (contenu + rythme) |
| 3 | **Nettoyage audio** | selon `audio.enhanceMethod` | `derush/<slug>_voice_enhanced.mp3`, **même durée** que le cut |
| 4 | **Génération** | toi, après accord sur le coût | `derush/<slug>_enhanced.mp4` + `<slug>_cuts.json` |
| 5 | **Vérification du rendu** | toi | pas d'artefact, lip sync OK, 1080x1920 @ 29,97 |
| 6 | **Montage normal** | `motion-design` | comme avec un vrai rush |

Pourquoi cet ordre : HeyGen cale la vidéo sur l'audio reçu et cet audio devient la piste
son finale. Couper ou nettoyer **après** la génération = recouper une vidéo payée en trop, ou
remplacer la piste sur laquelle le lip sync a été calculé (désynchro). Et nettoyer **après**
le cut plutôt qu'avant : le nettoyage uniformise le fond sonore sur l'ensemble, ce qui
masque les jump-cuts au lieu de les souligner.

## Étape 1 — Dérusher l'audio

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

   Il applique `derush.padStart` / `padEnd` (0,04 / 0,02 : on resserre les fins, jamais les
   débuts), insère un souffle régulier entre les prises (0,10 s ; 0,05 en liaison
   intra-phrase ; 0,15 sur une respiration), et sort `derush/<slug>_voice.mp3` (320k mono
   48 kHz) + `derush/<slug>_audio_timeline.json`.
6. Vérifier : re-transcrire le cut (lecture = script, zéro doublon, zéro mot coupé) et mesurer
   les souffles (`silencedetect=noise=-40dB:d=0.05` → moyenne ≈ 0,10 s, max < 0,21 s).

## Étape 2 — Faire valider à l'oreille

Révèle le MP3 (`open -R derush/<slug>_voice.mp3` sur macOS, `explorer /select,…` sur
Windows) et demande à l'utilisateur de l'écouter. **Rien ne part sur HeyGen avant son OK.**
S'il entend un doublon ou un mot coupé : zoom mot-à-mot sur la zone, corriger le segment,
rebuild, re-vérifier.

## Étape 3 — Nettoyer l'audio (toujours, pas seulement « si ça grésille »)

Le choix vient de `brand.config.json` → `audio.enhanceMethod` :

- **`adobe`** (recommandé, meilleure qualité) : ouvrir `https://podcast.adobe.com/enhance`,
  **l'utilisateur glisse lui-même** `<slug>_voice.mp3` (l'upload passe par le sélecteur natif
  de l'OS, tu ne peux pas le faire à sa place), il télécharge la version optimisée, tu la
  copies en `derush/<slug>_voice_enhanced.mp3`.
- **`ffmpeg`** (100 % local, zéro geste) :
  `ffmpeg -y -i derush/<slug>_voice.mp3 -af "highpass=f=90,afftdn=nf=-25,anlmdn=s=4:p=0.002:r=0.006,loudnorm=I=-16:TP=-1.5:LRA=11" -c:a libmp3lame -b:a 320k derush/<slug>_voice_enhanced.mp3`

Dans les deux cas, **vérifier que la durée est identique** au cut (`ffprobe … format=duration`)
avant de générer. **C'est ce fichier nettoyé, et lui seul, qui part en génération.**

## Étape 4 — Générer

```bash
python3 tools/double_ia.py generate derush/<slug>_voice_enhanced.mp3
```

Le script refuse un `_voice.mp3` non nettoyé et un audio sans `_audio_timeline.json` (garde-fou
contre la génération du brut ; `--allow-raw` seulement si l'utilisateur fournit un audio déjà
propre et lu d'une traite). Il affiche durée, coût estimé et solde, **attend la confirmation**,
génère (moteur `avatar_iv` de la config), puis conforme : 25 → 29,97 fps, crf 14, et remet
l'audio d'origine. Sorties : `derush/<slug>_enhanced.mp4` (le même nom qu'un dérush filmé)
et `derush/<slug>_cuts.json` (frontières des prises, dérivées du cut audio : le double ne
saute pas à l'image, pas de scene-change à mesurer). Limites : 10 min / 50 Mo.

`--engine avatar_v` seulement si l'utilisateur le demande (image un peu plus nette, même
prix, mouvements moins naturels). Ne propose jamais Avatar III.

## Étape 5 — Vérifier avant de montrer

1. Extraire 3-4 frames + un zoom visage : pas d'artefact, mains correctes.
2. Contrôler le lip sync sur un passage rapide (mots en b/p/m).
3. `ffprobe` : 1080x1920, 29,97 fps, durée = durée de l'audio.

Un mot mal prononcé ne se corrige pas côté HeyGen : l'utilisateur réenregistre la phrase,
tu la recolles dans les segments, rebuild du cut, re-nettoyage, regénération après accord.

## Étape 6 — Enchaîner sur le montage normal

Produire `derush/<slug>_words.json` avec `tools/build_words.py` (pointer `CUT` sur
`derush/<slug>_enhanced.mp4` et `tools/sections.py` → `CUTS_PATH` sur `<slug>_cuts.json`),
puis reprendre le pipeline Monteur IA à l'étape 4 (`motion-design` : sections, split-screens,
sous-titres, review, SFX/musique, export). Rien de spécifique au double au-delà de cette ligne :
la vidéo générée remplace le rush filmé, à l'identique.

## Dépannage

- « Pas de double configuré » → `/setup-double-ia`.
- Consentement pas accepté → `python3 tools/double_ia.py consent` (lien webcam 24 h).
- Génération `failed` → lire le `failure_message` du script ; le plus courant : audio
  trop long (> 10 min) ou solde à zéro.
- Vérifier l'état général à tout moment : `python3 tools/double_ia.py check`.
