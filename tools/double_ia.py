#!/usr/bin/env python3
"""Ton Double IA : pilote HeyGen, seul ou dans le Monteur IA. Tout par API, zéro abonnement.

Sous-commandes :
    python3 tools/double_ia.py check              # clé, solde, état du double, moteur
    python3 tools/double_ia.py create <video>     # crée ton double depuis ta vidéo de 30 s
    python3 tools/double_ia.py lier               # double déjà créé sur HeyGen : liste tes doubles
    python3 tools/double_ia.py lier --avatar-id <look> [--group-id <groupe>] [--nom "…"]
                                                  # … et le relie (lecture seule, gratuit)
    python3 tools/double_ia.py consent            # lien webcam de consentement (10 s)
    python3 tools/double_ia.py moteur [<moteur>]  # moteurs de ton double et leur prix ; en choisir un
    python3 tools/double_ia.py generate <audio>   # audio de ta voix → vidéo de ton double
    python3 tools/double_ia.py cloner-voix <audio>        # clone ta voix (1 min d'enregistrement)
    python3 tools/double_ia.py voix-clonee <texte> --slug <nom>  # ton texte lu par ta voix clonée

Deux façons de faire parler le double :
- TA VRAIE VOIX (par défaut, la plus naturelle) : dérush de l'audio (tools/build_audio_cut.py) →
  validation à l'oreille → nettoyage audio → `generate` sur le fichier NETTOYÉ. Jamais sur le
  brut : chaque seconde générée est facturée, et l'audio envoyé devient la piste son finale (on ne
  peut plus le nettoyer après sans casser le lip sync).
- TA VOIX CLONÉE (zéro micro) : `voix-clonee` écrit `derush/<slug>_voix_clonee.mp3` (déjà propre,
  sans blanc) et ses bornes de phrases ; on l'écoute, puis `generate` dessus.

Deux dossiers possibles :
- dans le Monteur IA (extension) : `generate` écrit `derush/<slug>_enhanced.mp4` (le même livrable
  qu'un dérush filmé, pour que le montage enchaîne à l'identique) et le `derush/<slug>_cuts.json`
  que le montage exige ;
- seul (dossier « Ton Double IA », sans Monteur IA) : `generate` rend `videos/<slug>.mp4`, prête à
  monter dans n'importe quel outil.

La config du double vit dans `double-ia.config.json` à la racine du dossier (Monteur IA ou Ton
Double IA), écrite par `create` ou `lier` ; le dérush s'écrit dans le dossier du Reel (Monteur IA)
ou à la racine (seul). La clé API vient de $HEYGEN_API_KEY, sinon de ~/.heygen/credentials.

Moteurs : Avatar 6 par défaut (sorti le 17/11/2026 : gestes calés sur ce que tu dis, ~0,10 $/s),
Avatar 6 Turbo (plus rapide, moitié prix), Avatar IV et Avatar V (les anciens, ~0,07 $/s).
Avatar III volontairement absent : il rejoue les coupes de la vidéo d'entraînement.

HeyGen sort en 25 fps : `generate` conforme en 29,97 fps (le standard du Monteur IA)
et remet TON audio d'origine à la place de la piste ré-encodée par HeyGen.

Coût débité du portefeuille API pay-as-you-go. Le coût estimé et le solde sont TOUJOURS
affichés avant de générer, et rien ne part sans accord.
"""
import argparse
import json
import mimetypes
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
try:  # Monteur IA 2 : un Reel = un projet (reels/<nom>/), réglages dans le dossier Monteur IA
    from lieux import MAISON, REEL
except ImportError:  # Monteur IA 1 : tout vit à la racine du projet
    MAISON = REEL = ROOT
    # Windows : une sortie lue par l'agent (redirigée) est en cp1252, et un « → » y fait planter
    # l'outil. Monteur IA 2 règle ça dans lieux.py.
    for _flux in (sys.stdout, sys.stderr):
        try:
            _flux.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def dossier_reel():
    """Le Reel où écrire le dérush ; depuis la racine de Monteur IA 2, on demande d'en créer un."""
    if REEL is None:
        sys.exit("Lance cette commande depuis le dossier du Reel (reels/<nom>/). Pas encore de Reel : "
                 f"python3 \"{MAISON / 'tools' / 'nouveau_reel.py'}\" \"<sujet>\", puis entre dans son dossier.")
    return REEL
CONFIG = MAISON / "double-ia.config.json"


def autonome():
    """Vrai quand Ton Double IA est installé SEUL (dossier « Ton Double IA »), sans Monteur IA : pas de
    montage derrière, la vidéo générée est le livrable (videos/<slug>.mp4)."""
    return not (MAISON / "templates" / "AGENT.md.tpl").exists()


def brand_config():
    for name in ("brand.config.json", "brand.config.example.json"):
        p = MAISON / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return {}


def ffbin(name):
    """ffmpeg / ffprobe : brand.config.json → env.ffmpegPath, le dossier qui les contient (Monteur IA 2)
    ou le chemin de ffmpeg lui-même (Monteur IA 1, `which ffmpeg`) ; sinon le PATH."""
    v = (brand_config().get("env") or {}).get("ffmpegPath")
    if v:
        p = pathlib.Path(v).expanduser()
        d = p if p.is_dir() else p.parent
        for cand in (d / name, d / f"{name}.exe"):
            if cand.is_file():
                return str(cand)
    return shutil.which(name) or name


def slug_of(audio):
    """codes-chatgpt_voice_enhanced.mp3 → codes-chatgpt (on retire les suffixes du pipeline), et
    promo_voix_clonee.mp3 → promo."""
    return re.sub(r"(_voix_clonee|(_voice)?(_enhanced|_clean|_optimis[ée](-v\d+)?)*)$", "",
                  audio.stem) or audio.stem


def phrases_horodatees(texte, caracteres):
    """Bornes de chaque phrase dans l'audio de la voix clonée, au format des prises de
    build_audio_cut.py ({"i", "start", "end", "text"}), depuis les horodatages par caractère de
    HeyGen (`original_characters` : un {text, start_time, end_time} par caractère de `texte`, dans
    l'ordre). Une phrase finit sur . ! ? ou … suivi d'un blanc ou de la fin du texte."""
    if len(caracteres) != len(texte):
        return []
    prises, debut = [], 0
    for i, ch in enumerate(texte):
        fin_de_texte = i == len(texte) - 1
        if not (fin_de_texte or (ch in ".!?…" and texte[i + 1].isspace())):
            continue
        idx = [j for j in range(debut, i + 1) if not texte[j].isspace()]
        if idx:
            st = float(caracteres[idx[0]]["start_time"])
            en = float(caracteres[idx[-1]]["end_time"])
            if en > st:
                prises.append({"i": len(prises), "start": round(st, 3), "end": round(en, 3),
                               "text": texte[debut:i + 1].strip()})
        debut = i + 1
    return prises
BASE = "https://api.heygen.com"
FPS = "30000/1001"
CREDENTIALS = pathlib.Path.home() / ".heygen" / "credentials"
# Moteurs pris en charge, du préféré au moins bon. Avatar III volontairement absent (il rejoue les
# coupes de la vidéo d'entraînement).
MOTEURS = ("heygen-avatar-6", "heygen-avatar-6-turbo", "avatar_iv", "avatar_v")
MOTEUR_DEFAUT = MOTEURS[0]
NOMS_MOTEURS = {"heygen-avatar-6": "Avatar 6", "heygen-avatar-6-turbo": "Avatar 6 Turbo",
                "avatar_iv": "Avatar IV", "avatar_v": "Avatar V"}
# $/s constatés, arrondis au-dessus : Avatar 6 mesuré le 22/11/2026 (0,90 $ pour 9 s), Avatar IV
# le 02/09/2026 (tarif affiché 0,0667). Ils servent au coût annoncé AVANT de générer ; le coût
# réel (écart de solde) s'affiche après.
TARIFS = {"heygen-avatar-6": 0.10, "heygen-avatar-6-turbo": 0.05, "avatar_iv": 0.073, "avatar_v": 0.073}
# Le clone de voix et la lecture d'un texte par la voix clonée (HeyGen Voice 1) n'ont rien débité
# le 22/11/2026 : `voix-clonee` affiche quand même le coût réel après coup.
# Avatar 6 et Avatar V acceptent une direction de jeu (motion_prompt) ; Avatar IV la refuse.
MOTEURS_DIRECTION = ("heygen-avatar-6", "heygen-avatar-6-turbo", "avatar_v")
MOTEURS_CALME = ("heygen-avatar-6", "heygen-avatar-6-turbo")


def tarif(moteur):
    return TARIFS.get(moteur, max(TARIFS.values()))


def choisir_moteur(voulu, pris_en_charge):
    """(moteur retenu, remarque ou None). `pris_en_charge` : les moteurs que le look accepte selon
    HeyGen (vide = inconnu, on garde le voulu). Un moteur refusé par le look est remplacé par le
    premier de MOTEURS qu'il accepte ; aucun → (None, explication)."""
    voulu = voulu or MOTEUR_DEFAUT
    if not pris_en_charge or voulu in pris_en_charge:
        return voulu, None
    autre = next((m for m in MOTEURS if m in pris_en_charge), None)
    if not autre:
        return None, (f"Ce look ne prend aucun des moteurs de Ton Double IA (il prend : "
                      f"{', '.join(pris_en_charge)}). Avatar III rejoue les coupes de l'entraînement : "
                      "recrée ton double avec /setup-double-ia.")
    return autre, (f"{NOMS_MOTEURS.get(voulu, voulu)} n'est pas disponible pour ce look : "
                   f"{NOMS_MOTEURS[autre]} à la place.")


def api_key(obligatoire=True):
    k = os.environ.get("HEYGEN_API_KEY")
    if k and k.strip():
        return k.strip()
    if CREDENTIALS.exists():
        raw = CREDENTIALS.read_text(encoding="utf-8").strip()
        if raw:
            return json.loads(raw).get("api_key") if raw.startswith("{") else raw
    if not obligatoire:
        return None
    sys.exit("Pas de clé HeyGen. Colle ta clé dans ~/.heygen/credentials (fichier texte, "
             "juste la clé) ou exporte $HEYGEN_API_KEY. Elle se crée sur "
             "https://app.heygen.com/home?nav=API")


def req(path, method="GET", body=None, files=None, introuvable=False):
    """Appel à l'API HeyGen ; rend son champ `data`. introuvable : un id inconnu (HTTP 400, 404 ou
    422) rend None au lieu d'arrêter, pour l'expliquer à l'utilisateur."""
    headers = {"X-Api-Key": api_key()}
    if files:  # multipart minimal, zéro dépendance
        name, blob = files
        boundary = "----doubleiaboundary"
        ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
        data = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
                f"filename=\"{name}\"\r\nContent-Type: {ctype}\r\n\r\n").encode() + blob + \
               f"\r\n--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    else:
        data = json.dumps(body).encode() if body is not None else None
        if data:
            headers["Content-Type"] = "application/json"
    r = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return json.loads(resp.read())["data"]
    except urllib.error.HTTPError as e:
        if introuvable and e.code in (400, 404, 422):
            return None
        detail = e.read().decode(errors="replace")[:300]
        if e.code in (401, 403):
            sys.exit(f"HeyGen refuse la clé API (HTTP {e.code}) : vérifie ~/.heygen/credentials "
                     f"(la clé se crée sur https://app.heygen.com/home?nav=API).\n{detail}")
        sys.exit(f"HeyGen a répondu HTTP {e.code} sur {method} {path} :\n{detail}")
    except urllib.error.URLError as e:
        sys.exit(f"HeyGen injoignable ({e.reason}) : vérifie la connexion internet, puis relance.")


def config():
    return json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}


def save_config(c):
    CONFIG.write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def balance():
    return req("/v3/users/me")["wallet"]["remaining_balance"]


def duration(path):
    return float(subprocess.run(
        [ffbin("ffprobe"), "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, encoding="utf-8", errors="replace", check=True).stdout.strip())


def groupe_du_double(c):
    """Le groupe HeyGen du double. Un double lié hors ligne n'a que son look : le groupe se lit
    alors sur HeyGen et s'ajoute à la config."""
    if c.get("avatar_group_id"):
        return c["avatar_group_id"]
    look = req(f"/v3/avatars/looks/{c['avatar_id']}", introuvable=True)
    if not look:
        sys.exit(f"Le look {c['avatar_id']} de double-ia.config.json est inconnu de ce compte HeyGen : "
                 "relie ton double avec `python3 tools/double_ia.py lier` (il liste tes doubles).")
    if not look.get("group_id"):
        sys.exit("HeyGen ne donne pas le groupe de ce look : relance `lier` avec --group-id.")
    c["avatar_group_id"] = look["group_id"]
    save_config(c)
    return c["avatar_group_id"]


def moteurs_du_look(c):
    """Les moteurs que HeyGen accepte pour le look du double (lecture seule, gratuit) ; [] si
    HeyGen ne le dit pas."""
    look = req(f"/v3/avatars/looks/{c['avatar_id']}", introuvable=True) or {}
    return list(look.get("supported_api_engines") or [])


def cmd_check(_):
    b = balance()
    c = config()
    moteur = c.get("engine") or MOTEUR_DEFAUT
    print(f"Clé API   : ok")
    print(f"Solde     : {b:.2f} $ (~{int(b / (tarif(moteur) * 30))} reels de 30 s en "
          f"{NOMS_MOTEURS.get(moteur, moteur)})")
    print(f"Dossier   : {'Ton Double IA, seul' if autonome() else 'Monteur IA'}")
    if not c.get("avatar_id"):
        print("Double    : pas encore configuré → `create <video>`, ou `lier` s'il existe déjà sur "
              "HeyGen (ou lance /setup-double-ia)")
        return
    g = req(f"/v3/avatars/{groupe_du_double(c)}")
    print(f"Double    : {g['name']}, entraînement {g['status']}, consentement "
          f"{g.get('consent_status')}")
    print(f"Moteur    : {NOMS_MOTEURS.get(moteur, moteur)} (~{tarif(moteur) * 30:.2f} $ le reel de 30 s)")
    print(f"Voix clonée : {c['voice_name'] if c.get('voice_id') else 'aucune (option : `cloner-voix`)'}")
    if g.get("consent_status") != "accepted":
        print("→ consentement à faire : `python3 tools/double_ia.py consent`")
    elif moteur != MOTEUR_DEFAUT and MOTEUR_DEFAUT in moteurs_du_look(c):
        print(f"→ {NOMS_MOTEURS[MOTEUR_DEFAUT]} est disponible pour ton double : "
              "`python3 tools/double_ia.py moteur` compare les moteurs (à proposer, jamais imposer).")


def cmd_create(a):
    video = pathlib.Path(a.file)
    if not video.exists():
        sys.exit(f"Vidéo introuvable : {video}")
    if config().get("avatar_id") and not a.force:
        sys.exit("Un double est déjà configuré (double-ia.config.json). Le recréer coûte un "
                 "nouvel entraînement : relance avec --force si c'est voulu.")
    print("Upload de la vidéo d'entraînement…")
    asset = req("/v3/assets", "POST", files=(video.name, video.read_bytes()))
    print("Création du double (l'entraînement prend plusieurs minutes)…")
    r = req("/v3/avatars", "POST", {
        "type": "digital_twin", "name": a.name,
        "file": {"type": "asset_id", "asset_id": asset["asset_id"]}})
    item, group = r["avatar_item"], r["avatar_group"]
    # Avatar 6 d'office ; `generate` passe au meilleur moteur pris en charge si le look le refuse.
    save_config({**config(), "name": a.name, "avatar_id": item["id"], "avatar_group_id": group["id"],
                 "engine": MOTEUR_DEFAUT})
    print(f"Double créé : look {item['id']} (groupe {group['id']}) → double-ia.config.json")
    print("Prochaine étape, le consentement : `python3 tools/double_ia.py consent`")


def _ligne_look(l):
    moteurs = ", ".join(e for e in l.get("supported_api_engines") or [] if e in MOTEURS) or "?"
    return (f"  - {l.get('name') or '(sans nom)'} : --avatar-id {l['id']}  (groupe {l.get('group_id') or '?'}, "
            f"{l.get('status') or 'état ?'}, moteurs {moteurs})")


def lister_doubles():
    """Les doubles (jumeaux numériques) du compte HeyGen, en lecture seule."""
    looks = req("/v3/avatars/looks?ownership=private&avatar_type=digital_twin&limit=50") or []
    looks = [l for l in looks if l.get("avatar_type", "digital_twin") == "digital_twin"]
    if not looks:
        sys.exit("Aucun double (jumeau numérique) sur ce compte HeyGen : on le crée avec /setup-double-ia "
                 "(vidéo d'entraînement, puis `create`).")
    print("Tes doubles sur HeyGen (un look = une tenue, un lieu ; c'est l'id du look qui génère) :")
    for l in looks:
        print(_ligne_look(l))
    print("\nRelie celui que tu utilises : python3 tools/double_ia.py lier --avatar-id <id du look>")


def cmd_lier(a):
    """Relie au Monteur IA un double DÉJÀ créé sur HeyGen : vérifie les ids en lecture seule (aucune
    génération, rien de débité) puis écrit double-ia.config.json, comme `create`."""
    c = config()
    cle = api_key(obligatoire=False)
    if not (a.avatar_id or "").strip():
        if not cle:
            sys.exit("Donne l'id du look de ton double : `lier --avatar-id <id>`. Avec ta clé API dans "
                     "~/.heygen/credentials, `lier` seul liste tes doubles.")
        return lister_doubles()
    look_id, groupe_id = a.avatar_id.strip(), (a.group_id or "").strip() or None
    deja = c.get("avatar_id")
    if deja and deja != look_id and not a.force:
        sys.exit(f"Un autre double est déjà configuré : « {c.get('name')} », look {deja}, groupe "
                 f"{c.get('avatar_group_id')}. Pour le remplacer : relance avec --force (note ces ids "
                 "pour revenir en arrière).")
    base = c if deja == look_id else {}
    moteur = a.engine or base.get("engine") or MOTEUR_DEFAUT
    nom, consentement = a.nom, None
    if cle:
        groupe = None
        look = req(f"/v3/avatars/looks/{look_id}", introuvable=True)
        if look is None:
            # Erreur courante : l'id copié est celui du groupe (l'avatar), pas celui de son look.
            groupe = req(f"/v3/avatars/{look_id}", introuvable=True)
            if groupe is None:
                sys.exit(f"Aucun look « {look_id} » sur ce compte HeyGen (vérifie l'id, et la clé : celle "
                         "du compte où vit le double). `lier` sans --avatar-id liste tes doubles.")
            if groupe_id and groupe_id != look_id:
                sys.exit(f"« {look_id} » est l'id d'un groupe, différent de --group-id {groupe_id}.")
            looks = req(f"/v3/avatars/looks?group_id={look_id}&ownership=private&limit=50") or []
            looks = [l for l in looks if l.get("group_id") in (None, look_id)]
            if len(looks) != 1:
                print(f"« {look_id} » est l'id du groupe « {groupe.get('name')} », pas d'un look. Ses looks :")
                for l in looks:
                    print(_ligne_look(l))
                sys.exit("Relance avec --avatar-id <id du look> (celui de la tenue et du lieu de tes vidéos).")
            look, groupe_id = looks[0], look_id
            print(f"« {look_id} » est l'id du groupe « {groupe.get('name')} » : son look {look['id']} est pris.")
            look_id = look["id"]
        if groupe_id and look.get("group_id") and look["group_id"] != groupe_id:
            sys.exit(f"Le look {look_id} appartient au groupe {look['group_id']}, pas à {groupe_id} : "
                     "retire --group-id (il se lit sur HeyGen) ou corrige-le.")
        groupe_id = groupe_id or look.get("group_id")
        if not groupe_id:
            sys.exit("HeyGen ne donne pas le groupe de ce look : relance avec --group-id <id du groupe>.")
        groupe = groupe or req(f"/v3/avatars/{groupe_id}", introuvable=True)
        if groupe is None:
            sys.exit(f"Aucun groupe « {groupe_id} » sur ce compte HeyGen : vérifie --group-id.")
        if look.get("status") == "failed":
            erreur = (look.get("error") or {}).get("message") or "raison non précisée"
            sys.exit(f"Ce double a échoué à l'entraînement sur HeyGen ({erreur}) : il ne peut pas générer. "
                     "Recrée-le avec /setup-double-ia.")
        if look.get("avatar_type") not in (None, "digital_twin"):
            print(f"⚠️  Ce look est un « {look['avatar_type']} », pas un double filmé (digital_twin) : il "
                  "générera, avec le rendu de ce look.")
        moteur, remarque = choisir_moteur(moteur, look.get("supported_api_engines") or [])
        if moteur is None:
            sys.exit(remarque)
        if remarque:
            print(remarque)
        nom = nom or groupe.get("name") or look.get("name")
        consentement = groupe.get("consent_status")
        etat = look.get("status") or groupe.get("status")
    else:
        print("⚠️  Pas de clé HeyGen : ids écrits SANS vérification. Une fois la clé posée "
              "(~/.heygen/credentials), `python3 tools/double_ia.py check` les vérifie.")
        etat = None
    nom = nom or base.get("name") or "Mon double"
    # La voix clonée ne dépend pas du double : elle reste quand on en relie un autre.
    voix = {k: v for k, v in c.items() if k in ("voice_id", "voice_name")}
    nouveau = {**voix, **base, "name": nom, "avatar_id": look_id, "avatar_group_id": groupe_id,
               "engine": moteur}
    if not groupe_id:
        del nouveau["avatar_group_id"]
    save_config(nouveau)
    print(f"Double lié : « {nom} », look {look_id}" + (f" (groupe {groupe_id})" if groupe_id else "")
          + f", moteur {NOMS_MOTEURS.get(moteur, moteur)} → double-ia.config.json")
    print("Rien n'a été généré ni débité.")
    if etat == "processing":
        print("HeyGen entraîne encore ce double : patiente quelques minutes, puis `check`.")
    if cle and consentement != "accepted":
        print("Prochaine étape, le consentement : `python3 tools/double_ia.py consent`")
    elif cle:
        print("Consentement déjà accepté : le double est prêt à générer.")


def cmd_consent(_):
    c = config()
    if not c.get("avatar_id"):
        sys.exit("Pas de double configuré : lance d'abord `create <video>` (ou `lier` s'il existe déjà).")
    groupe = groupe_du_double(c)
    g = req(f"/v3/avatars/{groupe}")
    if g.get("consent_status") == "accepted":
        print("Consentement déjà accepté, tout est bon.")
        return
    r = req(f"/v3/avatars/{groupe}/consent", "POST", {})
    print("Ouvre ce lien (valable 24 h) et enregistre-toi 10 s à la webcam en lisant la "
          "phrase affichée :\n\n  " + r["url"] + "\n\nPuis relance `check` pour vérifier.")


def cmd_generate(a):
    audio = pathlib.Path(a.audio)
    if not audio.exists():
        sys.exit(f"Audio introuvable : {audio}")
    c = config()
    if not c.get("avatar_id"):
        sys.exit("Pas de double configuré : lance /setup-double-ia (ou `create <video>`, ou `lier`).")
    engine, remarque = choisir_moteur(a.engine or c.get("engine"), moteurs_du_look(c))
    if engine is None:
        sys.exit(remarque)
    if remarque:
        print(remarque)
    if a.direction and engine not in MOTEURS_DIRECTION:
        sys.exit(f"{NOMS_MOTEURS.get(engine, engine)} ne prend pas de direction de jeu : retire "
                 "--direction, ou passe à Avatar 6 (`moteur heygen-avatar-6`).")
    if a.calme and engine not in MOTEURS_CALME:
        sys.exit(f"--calme ne marche qu'avec Avatar 6 (moteur actuel : {NOMS_MOTEURS.get(engine, engine)}).")
    slug = a.slug or slug_of(audio)
    seul = autonome()
    reel = dossier_reel()
    if a.out:
        out = pathlib.Path(a.out)
    elif seul:  # Ton Double IA seul : la vidéo est le livrable, rangée à part du dérush
        out = MAISON / "videos" / f"{slug}.mp4"
    else:
        out = reel / "derush" / f"{slug}_enhanced.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    timeline_path = reel / "derush" / f"{slug}_audio_timeline.json"
    if "_voice." in audio.name and "enhanced" not in audio.name and not a.allow_raw:
        sys.exit(f"{audio.name} est le cut NON nettoyé. Nettoie-le d'abord avec Adobe Podcast "
                 f"Enhance (skill double-ia, étape 3) → derush/{slug}_voice_enhanced.mp3, puis génère sur "
                 f"celui-là. L'audio envoyé devient la piste son finale. (--allow-raw pour forcer.)")
    if not timeline_path.exists() and not a.allow_raw:
        sys.exit(f"Pas de derush/{slug}_audio_timeline.json : cet audio n'a pas été dérushé avec "
                 f"tools/build_audio_cut.py. Coupe d'abord les blancs et les ratés (chaque seconde "
                 f"générée est facturée). Audio déjà propre et lu d'une traite ? --allow-raw.")

    dur = duration(audio)
    if dur > 600:
        sys.exit("Audio trop long : maximum 10 minutes par génération.")
    b = balance()
    cout = dur * tarif(engine)
    print(f"Audio     : {audio.name} ({dur:.1f} s)")
    print(f"Moteur    : {NOMS_MOTEURS.get(engine, engine)}")
    if a.direction:
        print(f"Direction : {a.direction}")
    print(f"Coût est. : ~{cout:.2f} $  (solde {b:.2f} $)")
    if cout > b:
        sys.exit("Solde insuffisant : recharge le portefeuille API sur app.heygen.com "
                 "(Espace API → Billing).")
    if not a.yes:
        # Lancé par un agent, stdin n'est pas un terminal : input() planterait (EOFError).
        if not sys.stdin.isatty():
            sys.exit("Rien n'est lancé ni débité : annonce ce coût, attends l'accord, "
                     "puis relance la même commande avec --yes.")
        if input("Lancer la génération ? [o/N] ").strip().lower() not in ("o", "oui", "y"):
            sys.exit("Annulé : rien n'a été débité.")

    asset = req("/v3/assets", "POST", files=(audio.name, audio.read_bytes()))
    vid = req("/v3/videos", "POST", demande_video(c["avatar_id"], asset["asset_id"], engine,
                                                  f"double-ia {out.stem}", a.direction, a.calme))["video_id"]
    print(f"Génération en cours (1 à 3 min pour 30 s)", end="", flush=True)

    while True:
        v = req(f"/v3/videos/{vid}")
        if v["status"] == "completed":
            print(" ok")
            break
        if v["status"] == "failed":
            sys.exit(f"\nÉchec HeyGen : {v.get('failure_message')} ({v.get('failure_code')})")
        print(".", end="", flush=True)
        time.sleep(10)

    raw = out.with_name(out.stem + "_raw25.mp4")
    urllib.request.urlretrieve(v["video_url"], raw)
    # 25 → 29,97 fps + on remet TON audio (HeyGen ré-encode le sien, moins bon)
    subprocess.run([ffbin("ffmpeg"), "-v", "error", "-i", str(raw), "-i", str(audio),
                    "-map", "0:v:0", "-map", "1:a:0", "-vf", f"fps={FPS}",
                    "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-y", str(out)], check=True)
    raw.unlink()

    spent = b - balance()
    try:
        rel = out.relative_to(ROOT)
    except ValueError:
        rel = out
    print(f"\n{rel} : 1080x1920 @ 29,97 fps, {dur:.1f} s")
    print(f"Coût réel : {spent:.2f} $ (solde restant {b - spent:.2f} $)")
    if seul and not a.out:
        print("Vidéo prête à monter dans l'outil de ton choix (CapCut, Premiere, InShot…).")
        return
    cuts = write_cuts(slug, out, timeline_path if timeline_path.exists() else None)
    print(f"{cuts.relative_to(ROOT)} : frontières des prises pour le montage "
          f"(tools/sections.py → CUTS_PATH)")


def demande_video(avatar_id, asset_id, moteur, titre, direction=None, calme=False):
    """Le corps de POST /v3/videos. La direction de jeu (motion_prompt) et le jeu calme
    (engine.motion_expressiveness) ne partent que vers les moteurs qui les acceptent."""
    engine = {"type": moteur}
    if calme and moteur in MOTEURS_CALME:
        engine["motion_expressiveness"] = "less"
    corps = {"type": "avatar", "avatar_id": avatar_id, "audio_asset_id": asset_id, "title": titre,
             "aspect_ratio": "auto", "resolution": "1080p", "engine": engine}
    if direction and moteur in MOTEURS_DIRECTION:
        corps["motion_prompt"] = direction[:1200]
    return corps


def cmd_moteur(a):
    """Sans argument : les moteurs que le look accepte, avec leur prix pour 30 s (lecture seule,
    gratuit). Avec un moteur : l'écrit dans la config, s'il est pris en charge."""
    c = config()
    if not c.get("avatar_id"):
        sys.exit("Pas de double configuré : lance /setup-double-ia (ou `create <video>`, ou `lier`).")
    pris = moteurs_du_look(c)
    actuel = c.get("engine") or MOTEUR_DEFAUT
    if not a.moteur:
        print("Moteurs de ton double (prix estimé d'un reel de 30 s) :")
        for m in MOTEURS:
            if pris and m not in pris:
                continue
            note = {"heygen-avatar-6": "le plus récent, gestes calés sur ce que tu dis",
                    "heygen-avatar-6-turbo": "rendu plus rapide, moitié prix, un peu moins fin",
                    "avatar_iv": "l'ancien moteur, mouvements naturels",
                    "avatar_v": "l'ancien moteur, image un peu plus nette"}[m]
            print(f"  {'→' if m == actuel else ' '} {NOMS_MOTEURS[m]} ({m}) : ~{tarif(m) * 30:.2f} $, {note}")
        print(f"\nMoteur actuel : {NOMS_MOTEURS.get(actuel, actuel)}. "
              "En changer : python3 tools/double_ia.py moteur <moteur>")
        return
    if pris and a.moteur not in pris:
        sys.exit(f"{NOMS_MOTEURS[a.moteur]} n'est pas disponible pour ton double "
                 f"(il prend : {', '.join(m for m in pris if m in MOTEURS) or 'aucun de nos moteurs'}).")
    save_config({**c, "engine": a.moteur})
    print(f"Moteur : {NOMS_MOTEURS[a.moteur]} (~{tarif(a.moteur) * 30:.2f} $ le reel de 30 s). "
          "Rien n'a été généré ni débité.")


def cmd_cloner_voix(a):
    """Clone instantané de la voix (HeyGen Voice 1) depuis UN enregistrement : ~1 minute de parole
    claire, dans une pièce calme (le clone garde le son de la pièce). Rien d'autre à payer : aucun
    débit constaté le 22/11/2026."""
    audio = pathlib.Path(a.audio)
    if not audio.exists():
        sys.exit(f"Audio introuvable : {audio}")
    c = config()
    if c.get("voice_id") and not a.force:
        sys.exit(f"Une voix clonée existe déjà (« {c.get('voice_name')} ») : relance avec --force pour la "
                 "remplacer par une nouvelle.")
    dur = duration(audio)
    if dur < 20:
        sys.exit(f"Enregistrement trop court ({dur:.0f} s) : il faut environ 1 minute de parole claire.")
    if dur > 180:
        print(f"Enregistrement de {dur:.0f} s : HeyGen n'en garde que les 3 premières minutes.")
    ext = audio.suffix.lower()
    if ext not in (".mp3", ".wav"):  # HeyGen n'accepte que MP3 ou WAV en fichier envoyé
        conv = audio.with_name(audio.stem + "_pour-clone.mp3")
        subprocess.run([ffbin("ffmpeg"), "-v", "error", "-y", "-i", str(audio), "-c:a", "libmp3lame",
                        "-b:a", "320k", str(conv)], check=True)
        audio = conv
    langue = ((brand_config().get("derush") or {}).get("whisperLanguage") or "fr").split("-")[0].lower()
    nom = a.nom or f"Voix de {c.get('name') or 'mon double'}"
    print("Envoi de l'enregistrement…")
    asset = req("/v3/assets", "POST", files=(audio.name, audio.read_bytes()))
    v = req("/v3/models/audio/voices", "POST", {
        "mode": "instant", "name": nom[:64], "language": langue, "similarity": "max",
        "audio": [{"type": "asset_id", "asset_id": asset["asset_id"]}]})
    voice_id = v["voice_id"]
    print("Clonage", end="", flush=True)
    for _ in range(60):
        s = req(f"/v3/models/audio/voices/{voice_id}")
        if s.get("status") == "ACTIVE":
            print(" ok")
            break
        if s.get("status") == "FAILED":
            sys.exit(f"\nLe clonage a échoué ({s.get('failure_reason')}) : réenregistre 1 minute de parole "
                     "claire, dans une pièce calme, puis relance.")
        print(".", end="", flush=True)
        time.sleep(3)
    else:
        sys.exit("\nHeyGen n'a pas fini en 3 minutes : relance `check` dans un moment.")
    save_config({**config(), "voice_id": voice_id, "voice_name": nom})
    print(f"Voix clonée : « {nom} » → double-ia.config.json")
    print("Pour l'entendre : python3 tools/double_ia.py voix-clonee \"Une phrase de test.\" --slug test-voix")


def cmd_voix_clonee(a):
    """Ton texte lu par ta voix clonée : derush/<slug>_voix_clonee.mp3 + ses bornes de phrases
    (<slug>_audio_timeline.json, même format que le dérush), prêts pour `generate`."""
    c = config()
    if not c.get("voice_id"):
        sys.exit("Pas de voix clonée : `python3 tools/double_ia.py cloner-voix <enregistrement d'1 min>` d'abord.")
    source = pathlib.Path(a.texte)
    texte = source.read_text(encoding="utf-8") if source.suffix.lower() in (".txt", ".md") and source.exists() else a.texte
    texte = " ".join(texte.split())
    if not texte:
        sys.exit("Texte vide.")
    if len(texte) > 10000:
        sys.exit("Texte trop long : 10 000 caractères au maximum.")
    langue = ((brand_config().get("derush") or {}).get("whisperLanguage") or "fr").split("-")[0].lower()
    b = balance()
    t = req("/v3/models/audio/tts", "POST", {
        "model": "heygen-voice-1", "voice_id": c["voice_id"], "text": texte, "language": langue,
        "expressiveness_boost": 0.5, "with_timestamps": True})
    derush = dossier_reel() / "derush"
    derush.mkdir(parents=True, exist_ok=True)
    wav = derush / f"{a.slug}_voix_clonee.wav"
    mp3 = derush / f"{a.slug}_voix_clonee.mp3"
    urllib.request.urlretrieve(t["audio_url"], wav)
    subprocess.run([ffbin("ffmpeg"), "-v", "error", "-y", "-i", str(wav), "-ar", "48000", "-ac", "1",
                    "-c:a", "libmp3lame", "-b:a", "320k", str(mp3)], check=True)
    wav.unlink()
    dur = duration(mp3)
    prises = phrases_horodatees(texte, t.get("original_characters") or []) or \
        [{"i": 0, "start": 0.0, "end": round(dur, 3), "text": texte}]
    tl = derush / f"{a.slug}_audio_timeline.json"
    tl.write_text(json.dumps({"source": "voix clonée HeyGen", "duration": round(dur, 3), "takes": prises},
                             ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    spent = b - balance()
    try:
        rel = mp3.relative_to(ROOT)
    except ValueError:
        rel = mp3
    print(f"{rel} : {dur:.1f} s, {len(prises)} phrase(s), coût {spent:.2f} $")
    print("Fais-le écouter. Une phrase à reprendre : corrige le texte et relance. Validé : "
          f"python3 tools/double_ia.py generate {rel}")


def write_cuts(slug, video, timeline_path):
    """Le <slug>_cuts.json que le montage lit (tools/sections.py). Pas de scene-change ici :
    le double ne saute pas à l'image, les frontières sont celles du cut audio (chaque prise
    absorbe le souffle qui la suit, prises contiguës, dernière borne = durée du fichier)."""
    dur = round(duration(video), 3)
    takes = []
    if timeline_path:
        src = json.loads(timeline_path.read_text(encoding="utf-8"))["takes"]
        for i, t in enumerate(src):
            start = 0.0 if i == 0 else takes[-1]["end"]
            end = dur if i == len(src) - 1 else round(float(src[i + 1]["start"]), 3)
            takes.append({"i": i, "start": start, "end": end, "text": t.get("text", "")})
    else:
        takes.append({"i": 0, "start": 0.0, "end": dur, "text": ""})
    out = ROOT / "derush" / f"{slug}_cuts.json"
    out.write_text(json.dumps({"source": str(video.relative_to(ROOT)) if video.is_relative_to(ROOT) else str(video),
                               "duration": dur,
                               "method": "double IA : frontières du cut audio (build_audio_cut.py), pas de scene-change",
                               "takes": takes}, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="clé, solde, état du double, moteur, voix clonée")
    c = sub.add_parser("create", help="crée ton double depuis ta vidéo d'entraînement")
    c.add_argument("file", help="vidéo de ~30 s, sans aucune coupe")
    c.add_argument("--name", default="Mon double", help="nom du double")
    c.add_argument("--force", action="store_true", help="recréer même si un double existe")
    li = sub.add_parser("lier", help="relie un double déjà créé sur HeyGen (sans --avatar-id : liste tes doubles)")
    li.add_argument("--avatar-id", help="id du LOOK du double (celui qui génère)")
    li.add_argument("--group-id", help="id du groupe du double (défaut : lu sur HeyGen)")
    li.add_argument("--nom", help="nom du double (défaut : son nom sur HeyGen)")
    li.add_argument("--engine", choices=list(MOTEURS), help=f"défaut : {MOTEUR_DEFAUT}")
    li.add_argument("--force", action="store_true", help="remplacer le double déjà configuré")
    sub.add_parser("consent", help="lien webcam de consentement")
    m = sub.add_parser("moteur", help="moteurs de ton double et leur prix ; avec un nom : le choisir")
    m.add_argument("moteur", nargs="?", choices=list(MOTEURS), help="moteur à garder pour les prochaines vidéos")
    g = sub.add_parser("generate", help="audio → vidéo de ton double")
    g.add_argument("audio", help="le cut NETTOYÉ de ta voix (derush/<slug>_voice_enhanced.mp3) ou ta voix "
                                 "clonée (derush/<slug>_voix_clonee.mp3) ; max 10 min / 50 Mo")
    g.add_argument("-o", "--out", help="MP4 de sortie (défaut : derush/<slug>_enhanced.mp4, ou "
                                       "videos/<slug>.mp4 quand Ton Double IA est installé seul)")
    g.add_argument("--slug", help="nom du reel (défaut : déduit du nom de l'audio)")
    g.add_argument("--allow-raw", action="store_true",
                   help="générer un audio qui n'est pas passé par build_audio_cut.py (déjà propre, lu d'une traite)")
    g.add_argument("--engine", choices=list(MOTEURS),
                   help="défaut : celui de la config (Avatar 6 pour un nouveau double)")
    g.add_argument("--direction", help="Avatar 6 ou V : la gestuelle voulue, en clair (ex. « sourire, petits "
                                       "gestes ouverts »)")
    g.add_argument("--calme", action="store_true", help="Avatar 6 : gestes plus rares et plus petits")
    g.add_argument("--yes", action="store_true", help="ne pas demander confirmation du coût")
    cv = sub.add_parser("cloner-voix", help="clone ta voix depuis ~1 min d'enregistrement (option « zéro micro »)")
    cv.add_argument("audio", help="~1 minute de ta voix, claire, dans une pièce calme (mp3, wav, m4a…)")
    cv.add_argument("--nom", help="nom de la voix (défaut : « Voix de <nom du double> »)")
    cv.add_argument("--force", action="store_true", help="remplacer la voix clonée existante")
    vc = sub.add_parser("voix-clonee", help="ton texte lu par ta voix clonée, prêt pour `generate`")
    vc.add_argument("texte", help="le texte, ou le chemin d'un fichier .txt")
    vc.add_argument("--slug", required=True, help="nom court de la vidéo, ex. promo-noel")
    a = p.parse_args()
    {"check": cmd_check, "create": cmd_create, "lier": cmd_lier, "consent": cmd_consent,
     "moteur": cmd_moteur, "generate": cmd_generate, "cloner-voix": cmd_cloner_voix,
     "voix-clonee": cmd_voix_clonee}[a.cmd](a)


if __name__ == "__main__":
    main()
