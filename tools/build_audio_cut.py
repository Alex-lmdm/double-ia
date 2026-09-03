#!/usr/bin/env python3
"""Dérush AUDIO d'un enregistrement dictaphone, AVANT la génération du double.

    python3 tools/build_audio_cut.py <audio brut> --segments derush/<slug>_segments.json --slug <slug>

Pourquoi ce fichier existe : le double est facturé à la seconde générée. Un script lu au
dictaphone contient toujours des blancs, des faux départs et des phrases reprises (mesuré sur
un vrai enregistrement : 93,7 s de brut pour 44,2 s utiles). Générer le brut, c'est payer le
double et devoir recouper ensuite. On coupe donc l'AUDIO d'abord, avec la même méthode que le
skill `derush` (îlots silencedetect, pads asymétriques, souffle régulier), puis on génère.

Entrée : `derush/<slug>_segments.json`, écrit par l'agent après sélection des prises :
    [ {"start": 1.08, "end": 4.31, "text": "Première phrase"},
      {"start": 9.66, "end": 13.60, "text": "Deuxième phrase", "gap": "sentence"}, ... ]
  - `start` / `end` : bornes de l'îlot de parole gardé, dans l'AUDIO BRUT (secondes).
  - `gap` (optionnel) : souffle inséré AVANT ce segment — "sentence" (défaut, 0,10 s),
    "link" (liaison intra-phrase, 0,05 s), "breath" (respiration conservée, 0,15 s), "none".

Sorties (dans derush/) :
  - `<slug>_voice.mp3`            : le cut, MP3 320k mono 48 kHz → à nettoyer, puis à générer.
  - `<slug>_audio_timeline.json`  : bornes de chaque prise SUR LE CUT (start, end, text) ;
    `double_ia.py generate` s'en sert pour écrire le `<slug>_cuts.json` du montage.

Réglages : lus dans brand.config.json → derush.padStart / derush.padEnd (défauts 0.04 / 0.02).
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAPS = {"sentence": 0.10, "link": 0.05, "breath": 0.15, "none": 0.0}


def brand_config():
    for name in ("brand.config.json", "brand.config.example.json"):
        p = ROOT / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return {}


def ffmpeg_bin(name):
    env = brand_config().get("env") or {}
    d = env.get("ffmpegPath")
    if d:
        cand = pathlib.Path(d) / name
        if cand.exists():
            return str(cand)
        if cand.with_suffix(".exe").exists():
            return str(cand.with_suffix(".exe"))
    return shutil.which(name) or name


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="l'enregistrement brut (m4a, mp3, wav…)")
    ap.add_argument("--segments", required=True, help="JSON des prises gardées (voir en-tête)")
    ap.add_argument("--slug", required=True, help="nom du reel, ex. codes-chatgpt")
    a = ap.parse_args()

    src = pathlib.Path(a.source).expanduser()
    if not src.exists():
        sys.exit(f"Audio introuvable : {src}")
    segs = json.loads(pathlib.Path(a.segments).read_text(encoding="utf-8"))
    if not segs:
        sys.exit("Aucun segment : rien à couper.")

    derush_cfg = brand_config().get("derush") or {}
    pad_start = float(derush_cfg.get("padStart") or 0.04)
    pad_end = float(derush_cfg.get("padEnd") or 0.02)
    if pad_start < 0:
        sys.exit("derush.padStart doit rester positif (attaques de voyelle fragiles).")

    out_dir = ROOT / "derush"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{a.slug}_voice.mp3"

    parts, labels, timeline, cursor = [], [], [], 0.0
    prev_end = None
    for i, s in enumerate(segs):
        st, en = float(s["start"]), float(s["end"])
        if en <= st:
            sys.exit(f"Segment {i} : end <= start.")
        if prev_end is not None and st < prev_end:
            sys.exit(f"Segment {i} : les prises doivent être dans l'ordre du cut (start < fin "
                     f"du segment précédent). Chevauchement volontaire ? Retire-le.")
        gap = GAPS.get(s.get("gap", "sentence"))
        if gap is None:
            sys.exit(f"Segment {i} : gap inconnu « {s['gap']} » (sentence, link, breath, none).")
        if i == 0:
            gap = 0.0
        if gap > 0:
            parts.append(f"aevalsrc=0:d={gap}:s=48000:c=mono[g{i}]")
            labels.append(f"[g{i}]")
            cursor += gap
        a0, b0 = max(0.0, st - pad_start), en + pad_end
        parts.append(f"[0:a]atrim=start={a0:.3f}:end={b0:.3f},asetpts=PTS-STARTPTS[s{i}]")
        labels.append(f"[s{i}]")
        timeline.append({"i": i, "start": round(cursor, 3), "end": round(cursor + (b0 - a0), 3),
                         "text": s.get("text", "")})
        cursor += b0 - a0
        prev_end = en

    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1[out]"
    subprocess.run([ffmpeg_bin("ffmpeg"), "-y", "-v", "error", "-i", str(src),
                    "-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-ac", "1",
                    "-c:a", "libmp3lame", "-b:a", "320k", str(out)], check=True)

    tl_path = out_dir / f"{a.slug}_audio_timeline.json"
    tl_path.write_text(json.dumps({"source": str(src), "duration": round(cursor, 3),
                                   "padStart": pad_start, "padEnd": pad_end,
                                   "takes": timeline}, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    print(f"{out.relative_to(ROOT)}  —  {cursor:.2f} s  ({len(segs)} prises)")
    print(f"{tl_path.relative_to(ROOT)}  —  bornes des prises sur le cut")
    print("Prochaine étape : fais écouter le MP3 pour validation, PUIS nettoyage audio, PUIS génération.")


if __name__ == "__main__":
    main()
