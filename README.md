# Ton Double IA — tes vidéos face-cam, sans te filmer

Extension du système **Monteur IA** : elle apprend à ton monteur à générer ta vidéo
face-cam à partir d'un simple **audio de ta vraie voix**, grâce à ton double IA.

Tu écris ton script (ou ton monteur l'écrit avec toi). Tu le lis au dictaphone de ton
téléphone, d'une traite. Tu envoies l'audio — et ton double fait l'image : ton visage,
ton lieu, ta gestuelle, calés sur ta voix. Le montage reprend ensuite exactement comme
d'habitude : coupes, motion design, sous-titres, SFX, musique.

**Ta voix n'est jamais clonée.** C'est le secret du naturel : l'audio, c'est toi, en
vrai. Seule l'image est générée — et personne ne le remarque.

---

## À quoi ça sert (et à quoi ça ne sert pas)

Le but n'est **pas** de ne plus jamais apparaître à l'écran. C'est d'avoir un plan B
chaque fois que te filmer est impossible ou pénible :

- tu es en vacances ou en déplacement, sans caméra ni trépied ;
- ton lieu de tournage n'est pas dispo, tu n'as pas le bon fond ni la bonne tenue ;
- t'es mal rasé, pas coiffé, pas l'envie, la tête dans le cul ;
- une actu tombe et tu veux publier aujourd'hui, pas dans trois jours.

Dans tous ces cas : script → dictaphone → audio → vidéo prête à monter.

## Ce qu'il te faut

- **Monteur IA installé et fonctionnel** (sinon : son INSTALL.md à lui, d'abord) ;
- un **compte HeyGen gratuit** — aucun abonnement : tu paies à l'utilisation,
  **environ 2 $ pour un reel de 30 secondes**, et ton monteur t'annonce le coût avant
  chaque génération ;
- ~30 secondes de vidéo de toi pour créer ton double (ton téléphone suffit).

## Installation — 2 minutes

Ouvre **Claude Code** (ou **Codex**) **dans ton dossier Monteur IA**, et colle le prompt
d'installation : il est dans **[INSTALL.md](INSTALL.md)**. Puis tape :

```
/setup-double-ia
```

Ton monteur te guide de zéro, pas à pas : compte HeyGen, clé, ta vidéo d'entraînement,
le consentement (10 s à la webcam — personne ne peut cloner quelqu'un d'autre), et ta
première génération. ~20 minutes, une seule fois.

## Comment on s'en sert ensuite

Deux phrases à dire à ton monteur :

1. **« Écris-moi un script de reel »** — comme d'habitude. Puis tu le lis au dictaphone,
   d'une seule traite.
2. **« Voici l'audio, utilise mon double »** — il génère la vidéo, coupe les éventuels
   blancs, et enchaîne le montage complet comme si tu avais tourné.

## FAQ

**Ça se voit que c'est une IA ?**
C'est ce qui surprend le plus : non, quasiment pas. Parce que la voix est la tienne,
enregistrée pour de vrai — et c'est la voix qui trahit les avatars, pas l'image.

**Pourquoi pas cloner aussi ma voix ?**
Tu peux (HeyGen le propose), mais c'est là que le naturel se perd — et lire ton script
au dictaphone prend 30 secondes. On garde ta vraie voix.

**Combien ça coûte à l'usage ?**
~0,07 $ par seconde générée, débité d'un portefeuille que tu recharges quand tu veux
(10 $ ≈ 4-5 reels). Pas d'abonnement. Le coût exact est annoncé avant chaque génération.

**Et si je change de tête, de lieu, de style ?**
Ton double est figé sur ta vidéo d'entraînement. Nouveau setup → tu refais une vidéo de
30 s et ton monteur recrée le double.
