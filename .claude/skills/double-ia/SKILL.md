---
name: double-ia
description: >-
  Génère la vidéo face-cam de l'utilisateur depuis un AUDIO de sa vraie voix, via son
  double HeyGen, puis enchaîne sur le montage Monteur IA normal. Use when the user
  provides an audio file and says « utilise mon double », « génère avec mon avatar »,
  « ma vidéo avec le double IA ». Entrée : MP3/WAV lu d'une traite. Sortie : MP4
  1080x1920 @29,97 fps dans derush/, puis pipeline de montage habituel. Si
  `double-ia.config.json` n'existe pas → router vers `setup-double-ia`. JAMAIS de
  génération sans confirmation explicite du coût par l'utilisateur.
---

# Double IA — audio → vidéo face-cam → montage

L'utilisateur a un double HeyGen (configuré par `/setup-double-ia`, config dans
`double-ia.config.json`). Il enregistre son script au dictaphone, d'une traite ; le
double fait l'image. **On ne clone jamais la voix : l'audio fourni EST la piste son
finale** — c'est ce qui rend le résultat naturel.

## ⛔ Règles d'argent

- Chaque génération débite le portefeuille HeyGen de l'utilisateur (~0,07 $/s, ~2 $ le
  reel de 30 s). **Jamais de génération sans son accord explicite sur le coût affiché**
  par le script. Ne passe `--yes` que s'il vient de dire oui dans la conversation.
- Un raté (mot mal prononcé, geste bizarre) → on corrige la cause, on regénère UNE
  fois, après nouvel accord. Pas d'itérations en rafale.
- Solde insuffisant → le script le dit ; guide vers l'Espace API HeyGen pour recharger
  (app.heygen.com → API → billing). Ne jamais réessayer en boucle.

## Étape 1 — Générer

Si l'audio semble brut (souffle, niveau faible), propose d'abord le nettoyage audio
habituel du Monteur IA — **avant** de générer : la vidéo sera calée sur l'audio envoyé,
on ne nettoie pas après coup.

```bash
python3 tools/double_ia.py generate <audio> [-o derush/<slug>_double.mp4]
```

Le script affiche durée, coût estimé et solde, attend la confirmation, génère
(moteur de la config, `avatar_iv` par défaut), puis conforme automatiquement :
25 → 29,97 fps, crf 14, et remet l'audio d'origine. Limites : 10 min / 50 Mo.

`--engine avatar_v` seulement si l'utilisateur le demande (image un peu plus nette,
même prix, mouvements moins naturels). Ne propose jamais Avatar III.

## Étape 2 — Vérifier avant de montrer

1. Extraire 3-4 frames + un zoom visage : pas d'artefact, mains correctes.
2. Contrôler le lip sync sur un passage rapide.
3. `ffprobe` : 1080x1920, 29,97 fps, durée = durée de l'audio.

Un mot mal prononcé ne se corrige pas côté HeyGen : l'utilisateur re-enregistre son
audio (ou juste la phrase, qu'on recolle en ffmpeg), puis regénération après accord.

## Étape 3 — Dérush léger (blancs uniquement)

L'audio est lu d'une traite : pas de doublons ni de ratés à chercher. Il reste les
**blancs** — début, fin, entre les sections.

1. `ffmpeg -af silencedetect=noise=-40dB:d=0.35` sur le MP4 généré (attention : jamais
   `-v error` avec silencedetect, il logue en niveau info).
2. Blanc > ~0,3 s → resserrer vers ~0,1 s de souffle : couper DANS les silences,
   resserrer les fins de segment, jamais les débuts (attaques de voyelle fragiles).
3. Aucun blanc > 0,3 s → ne rien couper, le fichier est déjà propre.
4. Re-transcrire le résultat (Whisper) et vérifier : lecture = script, zéro mot coupé.

## Étape 4 — Enchaîner sur le montage normal

À partir d'ici, la vidéo du double remplace le rush filmé, à l'identique : reprendre le
pipeline Monteur IA habituel (sections, motion, sous-titres, review, SFX/musique,
export). Rien de spécifique au double au-delà de cette ligne.

## Dépannage

- « Pas de double configuré » → `/setup-double-ia`.
- Consentement pas accepté → `python3 tools/double_ia.py consent` (lien webcam 24 h).
- Génération `failed` → lire le `failure_message` du script ; le plus courant : audio
  trop long (> 10 min) ou solde à zéro.
- Vérifier l'état général à tout moment : `python3 tools/double_ia.py check`.
