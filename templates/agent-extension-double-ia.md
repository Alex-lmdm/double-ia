<!-- BEGIN EXTENSION: double-ia (ajouté par l'installation de Ton Double IA ; ne pas dupliquer) -->

## 🎭 Extension installée : Ton Double IA

Ce projet sait AUSSI générer la vidéo face-cam de l'utilisateur **sans qu'il se filme** :
il fournit un audio de sa vraie voix, son double HeyGen fait l'image, et le montage
reprend ensuite le pipeline Reel habituel à l'identique. La voix n'est **jamais** clonée.

| L'utilisateur dit… | Route |
|---|---|
| un audio + « utilise mon double », « génère avec mon avatar » | charge le skill **`double-ia`** |
| `/setup-double-ia`, « crée mon double », « configure HeyGen », ou `double-ia.config.json` absent | charge le skill **`setup-double-ia`** |
| « écris le script d'abord » puis lecture au dictaphone | skill de script habituel, PUIS `double-ia` avec l'audio |

Rappels (le détail vit dans les skills) : ⛔ **jamais de génération sans accord explicite
sur le coût** (~2 $ le reel de 30 s, débité du portefeuille HeyGen de l'utilisateur) ;
moteur `avatar_iv` ; la sortie de `tools/double_ia.py` est déjà conformée 29,97 fps avec
l'audio d'origine ; après génération : dérush léger (blancs uniquement) puis montage
normal, comme avec un vrai rush.

<!-- END EXTENSION: double-ia -->
