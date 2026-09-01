#!/usr/bin/env python3
"""Ton Double IA — pilote HeyGen pour le Monteur IA. Tout par API, zéro abonnement.

Sous-commandes :
    python3 tools/double_ia.py check              # clé, solde, état du double
    python3 tools/double_ia.py create <video>     # crée ton double depuis ta vidéo de 30 s
    python3 tools/double_ia.py consent            # lien webcam de consentement (10 s)
    python3 tools/double_ia.py generate <audio>   # audio de ta voix → vidéo de ton double

La config du double vit dans `double-ia.config.json` à la racine du projet (écrite par
`create`). La clé API vient de $HEYGEN_API_KEY, sinon de ~/.heygen/credentials.

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
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "double-ia.config.json"
BASE = "https://api.heygen.com"
FPS = "30000/1001"
RATE_PER_SEC = 0.073  # $/s constaté (tarif affiché 0,0667 — HeyGen arrondit au-dessus)


def api_key():
    k = os.environ.get("HEYGEN_API_KEY")
    if k:
        return k.strip()
    cred = pathlib.Path.home() / ".heygen/credentials"
    if cred.exists():
        raw = cred.read_text().strip()
        if raw:
            return json.loads(raw).get("api_key") if raw.startswith("{") else raw
    sys.exit("Pas de clé HeyGen. Colle ta clé dans ~/.heygen/credentials (fichier texte, "
             "juste la clé) ou exporte $HEYGEN_API_KEY. Elle se crée sur "
             "https://app.heygen.com/home?nav=API")


def req(path, method="GET", body=None, files=None):
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
        detail = e.read().decode(errors="replace")[:300]
        sys.exit(f"HeyGen a répondu HTTP {e.code} sur {method} {path} :\n{detail}")


def config():
    return json.loads(CONFIG.read_text()) if CONFIG.exists() else {}


def save_config(c):
    CONFIG.write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n")


def balance():
    return req("/v3/users/me")["wallet"]["remaining_balance"]


def duration(path):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True).stdout.strip())


def cmd_check(_):
    b = balance()
    print(f"Clé API   : ok")
    print(f"Solde     : {b:.2f} $ (~{int(b / (RATE_PER_SEC * 30))} reels de 30 s)")
    c = config()
    if not c.get("avatar_id"):
        print("Double    : pas encore créé → `create <video>` (ou lance /setup-double-ia)")
        return
    g = req(f"/v3/avatars/{c['avatar_group_id']}")
    print(f"Double    : {g['name']} — entraînement {g['status']}, consentement "
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
    print("Prochaine étape : le consentement — `python3 tools/double_ia.py consent`")


def cmd_consent(_):
    c = config()
    if not c.get("avatar_group_id"):
        sys.exit("Pas de double configuré : lance d'abord `create <video>`.")
    g = req(f"/v3/avatars/{c['avatar_group_id']}")
    if g.get("consent_status") == "accepted":
        print("Consentement déjà accepté, tout est bon.")
        return
    r = req(f"/v3/avatars/{c['avatar_group_id']}/consent", "POST", {})
    print("Ouvre ce lien (valable 24 h) et enregistre-toi 10 s à la webcam en lisant la "
          "phrase affichée :\n\n  " + r["url"] + "\n\nPuis relance `check` pour vérifier.")


def cmd_generate(a):
    audio = pathlib.Path(a.audio)
    if not audio.exists():
        sys.exit(f"Audio introuvable : {audio}")
    c = config()
    if not c.get("avatar_id"):
        sys.exit("Pas de double configuré : lance /setup-double-ia (ou `create <video>`).")
    engine = a.engine or c.get("engine", "avatar_iv")
    out = pathlib.Path(a.out) if a.out else ROOT / "derush" / f"{audio.stem}_double.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)

    dur = duration(audio)
    if dur > 600:
        sys.exit("Audio trop long : maximum 10 minutes par génération.")
    b = balance()
    print(f"Audio     : {audio.name} — {dur:.1f} s")
    print(f"Moteur    : {engine}")
    print(f"Coût est. : ~{dur * RATE_PER_SEC:.2f} $  (solde {b:.2f} $)")
    if dur * RATE_PER_SEC > b:
        sys.exit("Solde insuffisant : recharge le portefeuille API sur app.heygen.com "
                 "(Espace API → Billing).")
    if not a.yes and input("Lancer la génération ? [o/N] ").strip().lower() not in ("o", "oui", "y"):
        sys.exit("Annulé — rien n'a été débité.")

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
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(raw), "-i", str(audio),
                    "-map", "0:v:0", "-map", "1:a:0", "-vf", f"fps={FPS}",
                    "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-y", str(out)], check=True)
    raw.unlink()

    spent = b - balance()
    try:
        rel = out.relative_to(ROOT)
    except ValueError:
        rel = out
    print(f"\n{rel} — 1080x1920 @ 29,97 fps — {dur:.1f} s")
    print(f"Coût réel : {spent:.2f} $ — solde restant {b - spent:.2f} $")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="clé, solde, état du double")
    c = sub.add_parser("create", help="crée ton double depuis ta vidéo d'entraînement")
    c.add_argument("file", help="vidéo de ~30 s, sans aucune coupe")
    c.add_argument("--name", default="Mon double", help="nom du double")
    c.add_argument("--force", action="store_true", help="recréer même si un double existe")
    sub.add_parser("consent", help="lien webcam de consentement")
    g = sub.add_parser("generate", help="audio → vidéo de ton double")
    g.add_argument("audio", help="MP3 ou WAV de ta voix (max 10 min / 50 Mo)")
    g.add_argument("-o", "--out", help="MP4 de sortie (défaut : derush/<audio>_double.mp4)")
    g.add_argument("--engine", choices=["avatar_iv", "avatar_v"],
                   help="défaut : celui de la config (avatar_iv)")
    g.add_argument("--yes", action="store_true", help="ne pas demander confirmation du coût")
    a = p.parse_args()
    {"check": cmd_check, "create": cmd_create,
     "consent": cmd_consent, "generate": cmd_generate}[a.cmd](a)


if __name__ == "__main__":
    main()
