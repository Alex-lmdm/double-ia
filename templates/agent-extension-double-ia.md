<!-- BEGIN EXTENSION: double-ia (ajouté par l'installation de Ton Double IA ; ne pas dupliquer) -->

## 🎭 Extension installée : Ton Double IA

Une vidéo face caméra **sans se filmer** : l'utilisateur fournit un **audio** de sa vraie voix
(jamais clonée), son double HeyGen fait l'image, puis le montage Reel habituel reprend à l'identique.

- Audio + « utilise mon double », « utiliza mi doble », ou « mets mon double dans [décor] » → skill
  **`double-ia`** (décors, version rapide, gestes calmes : dans le skill), dans le dossier du Reel
  (le créer d'abord si besoin : `nouveau_reel.py` du dossier Monteur IA).
- « Clone ce Reel pour mon double » → skill **`reel-cloneur`**, puis l'audio passe par `double-ia`.
- Vidéo filmée → pipeline normal : l'extension ne s'active pas.
- « crée mon double », « j'ai déjà un double HeyGen », « configura mi doble », `/setup-double-ia`, ou
  `double-ia.config.json` absent → skill **`setup-double-ia`** (un double existant se relie sans rien
  recréer ni payer : `double_ia.py lier`).
- ⛔ Ordre verrouillé : dérush, validation à l'oreille, nettoyage, puis génération, **jamais sans
  accord explicite sur le coût** (environ 3 $ le Reel de 30 s, 1 $ un décor).

<!-- END EXTENSION: double-ia -->
