<!-- BEGIN EXTENSION: double-ia (ajouté par l'installation de Ton Double IA ; ne pas dupliquer) -->

## 🎭 Extension installée : Ton Double IA

Ce projet sait AUSSI générer la vidéo face-cam de l'utilisateur **sans qu'il se filme** :
il fournit un **audio** de sa vraie voix (lu au dictaphone), son double HeyGen fait l'image,
et le montage reprend ensuite le pipeline Reel habituel à l'identique. La voix n'est
**jamais** clonée.

| L'utilisateur dit… | Route |
|---|---|
| un **audio** + « utilise mon double », « génère avec mon avatar » | charge le skill **`double-ia`** (remplace les étapes 2 tournage + 3 dérush) |
| une **vidéo** de lui (« voici la vidéo brute ») | **pipeline normal**, `derush` puis `motion-design` : l'extension ne s'active pas |
| `/setup-double-ia`, « crée mon double », « configure HeyGen », ou `double-ia.config.json` absent | charge le skill **`setup-double-ia`** |
| « écris le script d'abord » puis lecture au dictaphone | `reel-script`, PUIS `double-ia` avec l'audio |

**Ordre verrouillé quand un audio arrive** (le détail vit dans `double-ia`) :
**1. dérush de l'audio** (`tools/build_audio_cut.py` : blancs, faux départs, phrases reprises →
on garde la dernière tentative complète) → **2. l'utilisateur valide à l'oreille** →
**3. nettoyage audio avec Adobe Podcast Enhance** (toujours, aucune autre méthode) → **4. génération** (`tools/double_ia.py
generate` sur le fichier nettoyé, ⛔ **jamais sans accord explicite sur le coût**, ~2 $ le
reel de 30 s) → **5. montage normal** à partir de `derush/<slug>_enhanced.mp4` +
`<slug>_cuts.json`, les mêmes livrables qu'un dérush filmé. On ne génère jamais le brut
(facturé à la seconde) et on ne nettoie jamais après la génération (l'audio envoyé est la
piste son finale, la retoucher casserait le lip sync).

<!-- END EXTENSION: double-ia -->
