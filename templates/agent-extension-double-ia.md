<!-- BEGIN EXTENSION: double-ia (ajouté par l'installation de Ton Double IA ; ne pas dupliquer) -->

## 🎭 Extension installée : Ton Double IA

Une vidéo face caméra **sans se filmer** : l'utilisateur fournit un **audio** de sa vraie voix
(jamais de voix clonée), son double HeyGen fait l'image, puis le montage Reel habituel reprend à
l'identique.

- Audio + « Voici l'audio, utilise mon double », « utiliza mi doble » → skill **`double-ia`**
  (remplace tournage + dérush), dans le dossier du Reel (le créer d'abord si besoin, comme une
  vidéo filmée : `nouveau_reel.py` du dossier Monteur IA). « … utilise mon double au café » : la
  vidéo dans ce décor ; « Fais-la en version rapide » : Avatar 6 Turbo pour cette vidéo ;
  « Génère avec des gestes plus calmes » : `--calme`.
- « Mets mon double dans [décor] » → skill **`double-ia`** (§ Décors, environ 1 $ après accord).
- « Clone ce Reel pour mon double : [lien] » → skill **`reel-cloneur`** (le script), puis l'audio
  passe par `double-ia`. « Écris-moi un Reel sur [sujet] » → skill **`reel-script`**, comme
  d'habitude.
- Vidéo filmée → pipeline normal : l'extension ne s'active pas.
- « crée mon double », « j'ai déjà un double HeyGen », « configura mi doble », `/setup-double-ia`, ou
  `double-ia.config.json` absent du dossier Monteur IA → skill **`setup-double-ia`** (un double existant
  se relie sans rien recréer ni payer : `double_ia.py lier`).
- ⛔ Ordre verrouillé : dérush de l'audio, validation à l'oreille, nettoyage, puis génération,
  **jamais sans accord explicite sur le coût** (environ 3 $ le Reel de 30 s, 1 $ un décor).

<!-- END EXTENSION: double-ia -->
