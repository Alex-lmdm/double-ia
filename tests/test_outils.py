"""Tests des outils de Ton Double IA (hors livraison : l'installation ne copie que tools/, les skills
et le bloc de consignes, jamais tests/).

    python3 -m unittest discover -s tests -v

Sans dépendance : bibliothèque standard seulement. Rien n'est écrit dans le dépôt (dossiers
temporaires), aucun appel à HeyGen.
"""
import importlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

DEPOT = pathlib.Path(__file__).resolve().parents[1]
OUTILS = DEPOT / "tools"


def charger(nom):
    """Importe un outil comme en Monteur IA 1 (pas de lieux.py à côté)."""
    if str(OUTILS) not in sys.path:
        sys.path.insert(0, str(OUTILS))
    if nom in sys.modules:
        return importlib.reload(sys.modules[nom])
    return importlib.import_module(nom)


class SortieWindows(unittest.TestCase):
    """Windows : la sortie lue par l'agent est en cp1252 ; un « → » ne doit pas faire planter l'outil
    (Monteur IA 1, sans lieux.py)."""

    def lancer(self, outil, *args):
        env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
        env.pop("PYTHONUTF8", None)
        return subprocess.run([sys.executable, str(OUTILS / outil), *args], capture_output=True, env=env,
                              cwd=tempfile.gettempdir())

    def test_aide_double_ia(self):
        r = self.lancer("double_ia.py", "--help")
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace")[-500:])
        self.assertIn("→".encode("utf-8"), r.stdout)

    def test_aide_build_audio_cut(self):
        r = self.lancer("build_audio_cut.py", "--help")
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace")[-500:])
        self.assertIn("→".encode("utf-8"), r.stdout)


class CheminFfmpeg(unittest.TestCase):
    """env.ffmpegPath : le dossier de ffmpeg (Monteur IA 2) ou ffmpeg lui-même (Monteur IA 1), même
    quand ffmpeg n'est pas dans le PATH."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        racine = pathlib.Path(self.tmp.name)
        self.maison = racine / "Monteur IA · Été"
        self.bin = racine / "ffmpeg é" / "bin"
        self.bin.mkdir(parents=True)
        self.maison.mkdir()
        for nom in ("ffmpeg", "ffprobe"):
            (self.bin / nom).write_text("", encoding="utf-8")
        self.vide = racine / "vide"
        self.vide.mkdir()
        self.path = os.environ.get("PATH", "")
        os.environ["PATH"] = str(self.vide)   # ffmpeg introuvable par le PATH

    def tearDown(self):
        os.environ["PATH"] = self.path
        self.tmp.cleanup()

    def regler(self, valeur):
        cfg = {"env": {"ffmpegPath": valeur}}
        (self.maison / "brand.config.json").write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")

    def verifier(self, module, fonction):
        m = charger(module)
        m.MAISON = self.maison
        trouve = getattr(m, fonction)
        for valeur in (str(self.bin), str(self.bin / "ffmpeg")):
            with self.subTest(module=module, ffmpegPath=valeur):
                self.regler(valeur)
                self.assertEqual(trouve("ffmpeg"), str(self.bin / "ffmpeg"))
                self.assertEqual(trouve("ffprobe"), str(self.bin / "ffprobe"))
        with self.subTest(module=module, ffmpegPath=None):
            self.regler(None)
            self.assertEqual(trouve("ffprobe"), "ffprobe")

    def test_double_ia(self):
        self.verifier("double_ia", "ffbin")

    def test_build_audio_cut(self):
        self.verifier("build_audio_cut", "ffmpeg_bin")


class MargesDuDerush(unittest.TestCase):
    """derush.padStart / padEnd à 0 = aucune marge, réglage voulu : jamais remplacé par le défaut."""

    def test_reglage(self):
        m = charger("build_audio_cut")
        self.assertEqual(m.reglage({"padEnd": 0}, "padEnd", 0.02), 0.0)
        self.assertEqual(m.reglage({"padStart": 0.0}, "padStart", 0.04), 0.0)
        self.assertEqual(m.reglage({}, "padEnd", 0.02), 0.02)
        self.assertEqual(m.reglage({"padEnd": None}, "padEnd", 0.02), 0.02)
        self.assertEqual(m.reglage({"padEnd": 0.05}, "padEnd", 0.02), 0.05)
        with self.assertRaises(SystemExit):
            m.reglage({"padEnd": "beaucoup"}, "padEnd", 0.02)

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg absent")
    def test_cut_sans_marge(self):
        with tempfile.TemporaryDirectory() as tmp:
            maison = pathlib.Path(tmp) / "Monteur IA"
            (maison / "tools").mkdir(parents=True)
            shutil.copy2(OUTILS / "build_audio_cut.py", maison / "tools")
            (maison / "brand.config.json").write_text(json.dumps({"derush": {"padStart": 0, "padEnd": 0}}),
                                                      encoding="utf-8")
            brut = maison / "brut.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=300:sample_rate=48000",
                            "-t", "3", str(brut)], check=True)
            segments = maison / "segments.json"
            segments.write_text(json.dumps([{"start": 0.5, "end": 1.0, "text": "un"},
                                            {"start": 1.5, "end": 2.0, "text": "deux", "gap": "none"}]),
                                encoding="utf-8")
            r = subprocess.run([sys.executable, str(maison / "tools" / "build_audio_cut.py"), str(brut),
                                "--segments", str(segments), "--slug", "essai"], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            tl = json.loads((maison / "derush" / "essai_audio_timeline.json").read_text(encoding="utf-8"))
            self.assertEqual((tl["padStart"], tl["padEnd"], tl["duration"]), (0.0, 0.0, 1.0))
            self.assertEqual([(x["start"], x["end"]) for x in tl["takes"]], [(0.0, 0.5), (0.5, 1.0)])



if __name__ == "__main__":
    unittest.main()
