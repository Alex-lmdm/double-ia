---
name: setup-double-ia
description: >-
  Onboarding guidé de l'extension « Ton Double IA » : accompagne l'utilisateur de ZÉRO
  jusqu'à sa première vidéo générée par son double HeyGen. Use when the user says
  « /setup-double-ia », « installe mon double », « crée mon double IA », « configure
  HeyGen », ou au premier usage si `double-ia.config.json` n'existe pas. Guide pas à pas,
  une étape à la fois : compte HeyGen gratuit, clé API, portefeuille, vidéo
  d'entraînement, création du double, consentement, première génération.
---

# Setup — Ton Double IA (onboarding guidé)

> **L'utilisateur n'est pas développeur.** Une étape à la fois, zéro jargon, et à chaque
> étape d'interface : dis-lui exactement où aller et quoi cliquer, puis termine par
> « dis-moi quand c'est fait ». Tu vérifies toi-même que c'est fait (via `check`) avant
> de passer à la suite. Ne saute jamais d'étape, ne fais jamais deux étapes d'un coup.

Philosophie à annoncer d'entrée : « On configure HeyGen une seule fois. Ensuite tout se
passe ici : tu me donnes un audio, je te rends la vidéo. Pas d'abonnement HeyGen — tu
paies uniquement ce que tu génères, environ 2 $ pour un reel de 30 secondes. »

## Reprise

Avant de commencer, situe où en est l'utilisateur :
- `double-ia.config.json` existe + `python3 tools/double_ia.py check` dit consentement
  accepté → tout est déjà configuré, propose directement une génération (étape 7).
- La clé marche mais pas de config → reprendre à l'étape 4.
- Pas de clé → reprendre à l'étape 1.

## Étape 1 — Compte HeyGen gratuit (interface, ~1 min)

Envoie l'utilisateur sur https://app.heygen.com s'inscrire (email ou Google).
**Préviens-le** : HeyGen va lui proposer des abonnements — il n'en prend AUCUN. Le compte
gratuit suffit, tout passera par l'API. « Dis-moi quand ton compte est créé. »

## Étape 2 — Clé API (interface, ~2 min)

Envoie-le sur https://app.heygen.com/home?nav=API (« Espace API » / « API dashboard »)
générer sa clé. Explique en une phrase : « cette clé, c'est ton badge d'accès — elle a
son propre portefeuille, séparé du compte gratuit ». Demande-lui de te coller la clé,
puis écris-la dans `~/.heygen/credentials` (fichier texte contenant juste la clé,
`chmod 600`). Vérifie aussitôt : `python3 tools/double_ia.py check` doit afficher le
solde (0,00 $ à ce stade, c'est normal). Jamais la clé dans un fichier du projet (elle
finirait sur GitHub).

## Étape 3 — Charger le portefeuille (interface, ~1 min)

Dans le même Espace API, section facturation/billing : lui faire ajouter **10 $**
(≈ 4-5 reels, de quoi apprendre sans stress). Bien dire : pas d'abonnement, ce solde ne
se consomme que quand on génère, et **je t'annoncerai toujours le coût avant chaque
génération**. Vérifie avec `check` que le solde apparaît.

## Étape 4 — La vidéo d'entraînement (téléphone, le moment le plus important)

Explique l'enjeu : **cette vidéo de ~30 secondes fixe le rendu du double pour toujours**
— le lieu, la tenue, la lumière et le cadrage de cette vidéo seront ceux de toutes les
vidéos générées. Les consignes à lui donner telles quelles :

- Filme-toi dans **le setup exact de tes vidéos habituelles** (même endroit, même
  cadrage, même tenue type, micro si tu en utilises un).
- Regard caméra, gestuelle naturelle, parle en continu ~30 s (peu importe le texte —
  présente-toi, parle de ton activité).
- **Une seule prise, AUCUNE coupe dans le fichier.** Un raté au milieu → on refilme
  tout. C'est la règle n° 1 : les coupes d'un fichier d'entraînement peuvent ressortir
  en plein milieu des vidéos générées.
- Export en **résolution maximale** (pas de compression WhatsApp : AirDrop, câble ou
  Drive).

« Envoie-moi le fichier (glisse-le ici) quand tu l'as. »

## Étape 5 — Création du double (moi, ~1 min + entraînement)

Vérifie le fichier reçu (`ffprobe` : vertical, durée 20-120 s, une seule scène — si tu
détectes des coupes ou une résolution faible, dis-le et fais refilmer plutôt que de
créer un mauvais double). Puis :

```bash
python3 tools/double_ia.py create <video> --name "Double de <prénom>"
```

Explique pendant l'attente : « HeyGen apprend ton visage et tes mouvements. Il clone
aussi ta voix au passage — on ne s'en servira pas : notre méthode utilise TA vraie voix,
c'est ce qui rend le résultat indétectable. »

## Étape 6 — Consentement (webcam, ~2 min)

```bash
python3 tools/double_ia.py consent
```

Donne-lui le lien et explique : « HeyGen te demande de confirmer face caméra que c'est
bien toi et que tu es d'accord — 10 secondes à la webcam en lisant la phrase affichée.
C'est une protection : personne ne peut cloner quelqu'un d'autre. » Le lien vaut 24 h.
Quand il a fini : `check` jusqu'à « consentement accepted » (l'entraînement du double
peut prendre quelques minutes de plus — patiente avec lui).

## Étape 7 — Première génération (~5 min)

Propose les deux portes d'entrée :
1. « Tu as déjà un texte ? Lis-le au dictaphone de ton téléphone, d'une seule traite,
   et envoie-moi l'audio. »
2. « Tu n'as pas de texte ? On l'écrit ensemble » → charge le skill de script de reel
   du Monteur IA (`reel-script`), écris le script, fais-le valider, PUIS il le lit au
   dictaphone.

Règles à donner pour l'audio : dans un endroit calme, le téléphone près de la bouche, et
**comme au prompteur** : phrase par phrase, il peut se reprendre autant de fois qu'il veut,
la dernière version de chaque phrase sera gardée. Pas besoin de recommencer tout
l'enregistrement pour un raté : je coupe les blancs et les ratés avant de générer, exactement
comme je dérushe une vidéo filmée.

À réception de l'audio, passe la main au skill **`double-ia`** (c'est lui qui gère le dérush
de l'audio, la validation, le nettoyage, la génération et la suite du montage). Annonce
l'ordre à l'utilisateur pour qu'il sache ce qui vient : « je coupe ton audio, tu l'écoutes et
tu valides, on le nettoie, PUIS je génère la vidéo (je t'annonce le coût avant), puis on monte
comme d'habitude ».

## Étape 8 — Clôture de l'onboarding

Quand la première vidéo est là, explique le mode de croisière : « C'est configuré pour
de bon. La prochaine fois, envoie-moi juste un audio en me disant "utilise mon double",
et je te rends la vidéo montée. Tu peux aussi me demander d'écrire le script d'abord. Et
quand tu te filmes pour de vrai, rien ne change : tu m'envoies ta vidéo, on monte comme
avant. »
