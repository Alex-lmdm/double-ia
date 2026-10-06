<!-- BEGIN EXTENSION: double-ia (ajouté par l'installation de Ton Double IA ; ne pas dupliquer) -->

## 🎭 Extension installée : Ton Double IA

Une vidéo face caméra **sans se filmer** : l'utilisateur fournit un **audio** de sa vraie voix, son
double HeyGen fait l'image, puis le montage Reel habituel reprend à l'identique (voix jamais clonée).

- Audio + « utilise mon double », « génère avec mon avatar », « utiliza mi doble » → skill
  **`double-ia`** (remplace tournage + dérush), dans le dossier du Reel (le créer d'abord avec
  `python3 tools/nouveau_reel.py "<sujet>"` si besoin).
- Vidéo filmée → pipeline normal : l'extension ne s'active pas.
- « crée mon double », « configura mi doble », `/setup-double-ia`, ou `double-ia.config.json` absent
  du dossier Monteur IA → skill **`setup-double-ia`**.
- ⛔ Ordre verrouillé : dérush de l'audio, validation à l'oreille, nettoyage, puis génération,
  **jamais sans accord explicite sur le coût** (environ 2 $ le Reel de 30 s).

<!-- END EXTENSION: double-ia -->
