# Ton Double IA : tes vidéos face-cam, sans te filmer

Ton IA (Claude ou ChatGPT) génère ta vidéo face-cam à partir d'un simple **audio de ta vraie
voix**, grâce à ton double IA. Il marche **seul**, dans son propre dossier, ou comme extension du
système **Monteur IA**, qui enchaîne alors le montage.

Tu écris ton script (ou ton IA l'écrit avec toi). Tu le lis au dictaphone de ton
téléphone, d'une traite. Tu envoies l'audio, et ton double fait l'image : ton visage,
ton lieu, ta gestuelle, calés sur ta voix. Seul, tu récupères la vidéo prête à monter où tu
veux ; avec Monteur IA, le montage reprend exactement comme d'habitude : coupes, motion design,
sous-titres, SFX, musique.

**Par défaut, ta voix n'est pas clonée.** C'est le secret du naturel : l'audio, c'est toi, en
vrai. Seule l'image est générée, et personne ne le remarque. Pour les jours sans micro, tu peux
aussi cloner ta voix (gratuit) : tu donnes un texte, ton double le dit.

Depuis le 17 novembre 2026, ton double tourne sur **Avatar 6**, le dernier moteur de HeyGen : ses
gestes suivent ce que tu dis. Un double déjà créé y passe sans refilmer.

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

- **Claude Code ou Codex** (l'app Claude ou ChatGPT sur ton ordinateur suffit) ;
- un **compte HeyGen gratuit**, sans abonnement : tu paies à l'utilisation,
  **environ 3 $ pour un reel de 30 secondes** (1,50 $ en version rapide), et ton IA t'annonce le
  coût avant chaque génération ;
- Monteur IA si tu veux que la vidéo sorte montée (facultatif) ;
- ~30 secondes de vidéo de toi pour créer ton double (ton téléphone suffit).

## Installation (2 minutes)

Ouvre **Claude Code** (ou **Codex**) **dans ton dossier Monteur IA** si tu l'as (ou, dans l'app
HyperFrames, dans l'accueil de Monteur IA), sinon dans un dossier vide « Ton Double IA », et colle
le prompt d'installation : il est dans **[INSTALL.md](INSTALL.md)**. Puis tape :

```
/setup-double-ia
```

(sous Codex, dis-lui simplement « setup double IA »). Ton IA te guide de zéro, pas à pas : compte HeyGen, clé, ta vidéo d'entraînement,
le consentement (10 s à la webcam : personne ne peut cloner quelqu'un d'autre), et ta
première génération. ~20 minutes, une seule fois.

Tu as déjà un double sur HeyGen ? Dis-le-lui au setup : il le relie tel quel,
sans le recréer ni rien payer.

## Comment on s'en sert ensuite

Deux phrases à dire à ton IA :

1. **« Écris-moi un script de reel »**, comme d'habitude. Puis tu le lis au dictaphone de
   ton téléphone, comme au prompteur : phrase par phrase, tu peux te reprendre, il gardera la
   dernière version de chaque phrase.
2. **« Voici l'audio, utilise mon double »** : il déroule, dans cet ordre :
   - il **coupe l'audio** (blancs, faux départs, phrases reprises), comme il dérushe une
     vidéo filmée ;
   - tu **écoutes et tu valides** ;
   - il **nettoie le son** avec Adobe Podcast Enhance (tu glisses un fichier, il fait le reste) ;
   - il **génère la vidéo** avec ton double, après t'avoir annoncé le coût ;
   - avec Monteur IA, il **enchaîne le montage complet** comme si tu avais tourné ; seul, il te
     rend la vidéo dans `videos/`.

Pas de micro sous la main ? Dis-lui « avec ma voix clonée » et donne-lui ton texte : ta voix
clonée le lit, tu écoutes, il génère.

Avec Monteur IA, le jour où tu te filmes pour de vrai, rien ne change : tu lui donnes ta vidéo,
l'extension reste silencieuse et le montage habituel s'applique.

## FAQ

**Ça se voit que c'est une IA ?**
C'est ce qui surprend le plus : non, quasiment pas. Parce que la voix est la tienne,
enregistrée pour de vrai, et c'est la voix qui trahit les avatars, pas l'image.

**Et la voix clonée ?**
Elle est devenue bonne, et pratique les jours sans micro (ou pour une vidéo dans une autre
langue). Mais ta vraie voix reste plus naturelle, et lire ton script au dictaphone prend 30
secondes : c'est la méthode par défaut, le clone est l'option.

**Combien ça coûte à l'usage ?**
~0,10 $ par seconde générée en Avatar 6 (~0,05 $ en Avatar 6 Turbo), débité d'un portefeuille que
tu recharges quand tu veux (10 $ ≈ 3 reels de 30 s en Avatar 6). Pas d'abonnement. Le clone de ta
voix ne coûte rien. Le coût exact est annoncé avant chaque génération.

**Et si je change de tête, de lieu, de style ?**
Ton double est figé sur ta vidéo d'entraînement. Nouveau setup → tu refais une vidéo de
30 s et ton IA recrée le double.
