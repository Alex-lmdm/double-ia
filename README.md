# Ton Double IA : tes vidéos face-cam, sans te filmer

Ton IA (Claude ou ChatGPT) génère ta vidéo face-cam à partir d'un simple **audio de ta vraie
voix**, grâce à ton double IA. Il marche **seul**, dans son propre dossier, ou comme extension du
système **Monteur IA**, qui enchaîne alors le montage.

Tu écris ton script (ou ton IA l'écrit avec toi). Tu le lis au dictaphone de ton
téléphone, d'une traite. Tu envoies l'audio, et ton double fait l'image : ton visage,
ton lieu, ta gestuelle, calés sur ta voix. Seul, tu récupères la vidéo prête à monter où tu
veux ; avec Monteur IA, le montage reprend exactement comme d'habitude : coupes, motion design,
sous-titres, SFX, musique.

**Ta voix n'est jamais clonée.** C'est le secret du naturel : l'audio, c'est toi, en vrai.
Seule l'image est générée, et personne ne le remarque.

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
le prompt d'installation : il est dans **[INSTALL.md](INSTALL.md)**. Puis dis-lui :

**« Crée mon double IA »** (ou tape `/setup-double-ia`).

Ton IA te guide de zéro, pas à pas : compte HeyGen, clé, ta vidéo d'entraînement, le consentement
(10 s à la webcam : personne ne peut cloner quelqu'un d'autre), et ta première génération.
~20 minutes, une seule fois.

Tu as déjà un double sur HeyGen ? Dis-lui **« J'ai déjà un double HeyGen »** : il le relie tel
quel, sans le recréer ni rien payer.

## Comment on s'en sert ensuite

Les phrases à dire à ton IA :

- **« Voici l'audio, utilise mon double. »** Il déroule, dans cet ordre :
  - il **coupe l'audio** (blancs, faux départs, phrases reprises), comme il dérushe une
    vidéo filmée ;
  - tu **écoutes et tu valides** ;
  - il **nettoie le son** avec Adobe Podcast Enhance (tu glisses un fichier, il fait le reste) ;
  - il **génère la vidéo** avec ton double, après t'avoir annoncé le coût ;
  - avec Monteur IA, il **enchaîne le montage complet** comme si tu avais tourné ; seul, il te
    rend la vidéo dans `videos/`.
- **« Fais-la en version rapide »** : cette vidéo sort en Avatar 6 Turbo, à moitié prix
  (~0,05 $ la seconde au lieu de 0,10 $). Les suivantes repartent en Avatar 6.
- **« Génère avec des gestes plus calmes »** : des gestes plus rares et plus petits.
- **« Garde ça en mémoire pour mes prochaines vidéos »** : un ton de script, des gestes calmes, la
  version rapide pour les stories… ton IA s'en souvient pour la suite.

Tu lis ton script comme au prompteur : phrase par phrase, tu peux te reprendre, il garde la
dernière version de chaque phrase.

Avec Monteur IA, le jour où tu te filmes pour de vrai, rien ne change : tu lui donnes ta vidéo,
l'extension reste silencieuse et le montage habituel s'applique.

## Les bonus

**Ton scénariste de Reels.** Dis **« Écris-moi un Reel sur [ton sujet] »** : il écrit un script de
30 à 45 secondes, en phrases courtes, avec des **accroches en 3 temps** (le sujet tout de suite, ce
qui donne envie d'en savoir plus, puis le retournement), un des **10 formats d'histoire** (ton
parcours, une leçon apprise, un avant / après, un défi…), des **relances qui retiennent** (une
toutes les 25 secondes environ, avant que l'attention retombe) et une **relecture avant
livraison** : il passe son script à une liste de contrôle avant de te le donner, avec trois
accroches au choix.

**Le Reel Cloneur de ton double.** Un Reel d'un autre créateur t'a plu ? Dis **« Clone ce Reel pour
mon double : [lien du Reel] »**. Il le télécharge, le transcrit, décortique sa structure
(accroche, verrouillage, relances, appel à l'action, durées) et t'écrit **ton** script, sur ton
sujet, avec la même mécanique, sans reprendre une seule de ses phrases. Tu valides, tu
l'enregistres au téléphone, et ton double le joue.

**Ton double partout.** Dis **« Mets mon double dans [décor] »** (un café, une plage, un bureau en
open space) : ton IA décrit le décor, t'annonce le prix (environ 1 $, une seule fois), crée ton
double dans ce lieu et te montre l'image. Ensuite, **« Voici l'audio, utilise mon double au
café »** : la vidéo se tourne dans ce décor, avec tes gestes, au prix normal. Ta tenue reste
celle de ta vidéo d'entraînement.

## FAQ

**Ça se voit que c'est une IA ?**
C'est ce qui surprend le plus : non, quasiment pas. Parce que la voix est la tienne,
enregistrée pour de vrai, et c'est la voix qui trahit les avatars, pas l'image. C'est pour ça
que Ton Double IA ne clone jamais ta voix.

**Combien ça coûte à l'usage ?**
~0,10 $ par seconde générée en Avatar 6 (~0,05 $ en version rapide), débité d'un portefeuille que
tu recharges quand tu veux (10 $ ≈ 3 reels de 30 s en Avatar 6). Un décor coûte environ 1 $, une
seule fois. Le Reel Cloneur et le scénariste ne coûtent rien. Pas d'abonnement. Le coût exact est
annoncé avant chaque génération et chaque décor, et rien ne part sans ton accord.

**Et si je change de tête, de lieu, de style ?**
Un autre lieu : un décor (bonus « Ton double partout »), sans refilmer. Une autre tête ou une autre
tenue : ton double est figé sur ta vidéo d'entraînement, tu refais une vidéo de 30 s et ton IA
recrée le double.
