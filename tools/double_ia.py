#!/usr/bin/env python3
"""Ton Double IA : pilote HeyGen pour le Monteur IA. Tout par API, zéro abonnement.

Sous-commandes :
    python3 tools/double_ia.py check              # clé, solde, état du double
    python3 tools/double_ia.py create <video>     # crée ton double depuis ta vidéo de 30 s
    python3 tools/double_ia.py lier               # double déjà créé sur HeyGen : liste tes doubles
    python3 tools/double_ia.py lier --avatar-id <look> [--group-id <groupe>] [--nom "…"]
                                                  # … et le relie au Monteur IA (lecture seule, gratuit)
    python3 tools/double_ia.py consent            # lien webcam de consentement (10 s)
    python3 tools/double_ia.py generate <audio>   # audio de ta voix → vidéo de ton double

Ordre du workflow (verrouillé) : dérush de l'audio (tools/build_audio_cut.py) → validation à
l'oreille → nettoyage audio → `generate` sur le fichier NETTOYÉ. Jamais sur le brut : chaque
seconde générée est facturée, et l'audio envoyé devient la piste son finale (on ne peut plus
le nettoyer après sans casser le lip sync).

`generate` écrit `derush/<slug>_enhanced.mp4` (le même livrable qu'un dérush filmé, pour que
le montage enchaîne à l'identique) et, si `derush/<slug>_audio_timeline.json` existe (produit
par build_audio_cut.py), le `derush/<slug>_cuts.json` que le montage exige.

La config du double vit dans `double-ia.config.json` à la racine du dossier Monteur IA (écrite
par `create`, ou par `lier` pour un double déjà créé sur HeyGen), partagée par tous les Reels ; le dérush s'écrit dans le dossier du Reel. La clé API vient de $HEYGEN_API_KEY, sinon de ~/.heygen/credentials.

Moteur par défaut : Avatar IV (mouvements les plus naturels). Avatar V dispo via
--engine avatar_v (image un peu plus nette, même prix). Avatar III volontairement
absent : il rejoue les coupes de la vidéo d'entraînement.

HeyGen sort en 25 fps : `generate` conforme en 29,97 fps (le standard du Monteur IA)
et remet TON audio d'origine à la place de la piste ré-encodée par HeyGen.

Coût : ~0,07 $/seconde générée (~2 $ le reel de 30 s), débité du portefeuille API
pay-as-you-go. Le coût estimé et le solde sont TOUJOURS affichés avant de générer.
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
    """codes-chatgpt_voice_enhanced.mp3 → codes-chatgpt (on retire les suffixes du pipeline)."""
    return re.sub(r"(_voice)?(_enhanced|_clean|_optimis[ée](-v\d+)?)*$", "", audio.stem) or audio.stem
BASE = "https://api.heygen.com"
FPS = "30000/1001"
RATE_PER_SEC = 0.073  # $/s constaté (tarif affiché 0,0667, HeyGen arrondit au-dessus)
CREDENTIALS = pathlib.Path.home() / ".heygen" / "credentials"
MOTEURS = ("avatar_iv", "avatar_v")   # Avatar III volontairement absent (il rejoue les coupes)


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


def cmd_check(_):
    b = balance()
    print(f"Clé API   : ok")
    print(f"Solde     : {b:.2f} $ (~{int(b / (RATE_PER_SEC * 30))} reels de 30 s)")
    c = config()
    if not c.get("avatar_id"):
        print("Double    : pas encore configuré → `create <video>`, ou `lier` s'il existe déjà sur "
              "HeyGen (ou lance /setup-double-ia)")
        return
    g = req(f"/v3/avatars/{groupe_du_double(c)}")
    print(f"Double    : {g['name']}, entraînement {g['status']}, consentement "
          f"{g.get('consent_status')}")
    if g.get("consent_status") != "accepted":
        print("→ consentement à faire : `python3 tools/double_ia.py consent`")


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
    save_config({"name": a.name, "avatar_id": item["id"], "avatar_group_id": group["id"],
                 "engine": "avatar_iv"})
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
    moteur = a.engine or base.get("engine") or "avatar_iv"
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
        moteurs = look.get("supported_api_engines") or []
        if moteurs and moteur not in moteurs:
            autre = next((m for m in MOTEURS if m in moteurs), None)
            if not autre:
                sys.exit(f"Ce look ne prend ni Avatar IV ni Avatar V (moteurs : {', '.join(moteurs)}) : "
                         "Ton Double IA ne s'en sert pas (Avatar III rejoue les coupes de l'entraînement).")
            print(f"Moteur {moteur} non pris en charge par ce look : {autre} à la place.")
            moteur = autre
        nom = nom or groupe.get("name") or look.get("name")
        consentement = groupe.get("consent_status")
        etat = look.get("status") or groupe.get("status")
    else:
        print("⚠️  Pas de clé HeyGen : ids écrits SANS vérification. Une fois la clé posée "
              "(~/.heygen/credentials), `python3 tools/double_ia.py check` les vérifie.")
        etat = None
    nom = nom or base.get("name") or "Mon double"
    nouveau = {**base, "name": nom, "avatar_id": look_id, "avatar_group_id": groupe_id, "engine": moteur}
    if not groupe_id:
        del nouveau["avatar_group_id"]
    save_config(nouveau)
    print(f"Double lié : « {nom} », look {look_id}" + (f" (groupe {groupe_id})" if groupe_id else "")
          + f", moteur {moteur} → double-ia.config.json")
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
    engine = a.engine or c.get("engine") or "avatar_iv"
    slug = a.slug or slug_of(audio)
    reel = dossier_reel()
    out = pathlib.Path(a.out) if a.out else reel / "derush" / f"{slug}_enhanced.mp4"
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
    print(f"Audio     : {audio.name} ({dur:.1f} s)")
    print(f"Moteur    : {engine}")
    print(f"Coût est. : ~{dur * RATE_PER_SEC:.2f} $  (solde {b:.2f} $)")
    if dur * RATE_PER_SEC > b:
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
    vid = req("/v3/videos", "POST", {
        "type": "avatar", "avatar_id": c["avatar_id"], "audio_asset_id": asset["asset_id"],
        "title": f"double-ia {out.stem}", "aspect_ratio": "auto", "resolution": "1080p",
        "engine": {"type": engine}})["video_id"]
    print(f"Génération en cours (2-3 min pour 30 s)", end="", flush=True)

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
    cuts = write_cuts(slug, out, timeline_path if timeline_path.exists() else None)
    print(f"{cuts.relative_to(ROOT)} : frontières des prises pour le montage "
          f"(tools/sections.py → CUTS_PATH)")


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
    sub.add_parser("check", help="clé, solde, état du double")
    c = sub.add_parser("create", help="crée ton double depuis ta vidéo d'entraînement")
    c.add_argument("file", help="vidéo de ~30 s, sans aucune coupe")
    c.add_argument("--name", default="Mon double", help="nom du double")
    c.add_argument("--force", action="store_true", help="recréer même si un double existe")
    li = sub.add_parser("lier", help="relie un double déjà créé sur HeyGen (sans --avatar-id : liste tes doubles)")
    li.add_argument("--avatar-id", help="id du LOOK du double (celui qui génère)")
    li.add_argument("--group-id", help="id du groupe du double (défaut : lu sur HeyGen)")
    li.add_argument("--nom", help="nom du double (défaut : son nom sur HeyGen)")
    li.add_argument("--engine", choices=list(MOTEURS), help="défaut : avatar_iv")
    li.add_argument("--force", action="store_true", help="remplacer le double déjà configuré")
    sub.add_parser("consent", help="lien webcam de consentement")
    g = sub.add_parser("generate", help="audio → vidéo de ton double")
    g.add_argument("audio", help="le cut NETTOYÉ de ta voix, derush/<slug>_voice_enhanced.mp3 (max 10 min / 50 Mo)")
    g.add_argument("-o", "--out", help="MP4 de sortie (défaut : derush/<slug>_enhanced.mp4)")
    g.add_argument("--slug", help="nom du reel (défaut : déduit du nom de l'audio)")
    g.add_argument("--allow-raw", action="store_true",
                   help="générer un audio qui n'est pas passé par build_audio_cut.py (déjà propre, lu d'une traite)")
    g.add_argument("--engine", choices=list(MOTEURS),
                   help="défaut : celui de la config (avatar_iv)")
    g.add_argument("--yes", action="store_true", help="ne pas demander confirmation du coût")
    a = p.parse_args()
    {"check": cmd_check, "create": cmd_create, "lier": cmd_lier,
     "consent": cmd_consent, "generate": cmd_generate}[a.cmd](a)


if __name__ == "__main__":
    main()
