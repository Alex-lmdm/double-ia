"""Tests des outils de Ton Double IA (hors livraison : l'installation ne copie que tools/, les skills
et le bloc de consignes, jamais tests/).

    python3 -m unittest discover -s tests -v

Sans dépendance : bibliothèque standard seulement. Rien n'est écrit dans le dépôt (dossiers
temporaires), aucun appel à HeyGen.
"""
import contextlib
import importlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

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


LOOK = {"id": "look1", "name": "Bureau", "avatar_type": "digital_twin", "group_id": "grp1", "status": "completed",
        "supported_api_engines": ["avatar_v", "avatar_iv", "avatar_iii"]}
GROUPE = {"id": "grp1", "name": "Double de Léa", "status": "completed", "consent_status": "accepted"}
LISTE = "/v3/avatars/looks?ownership=private&avatar_type=digital_twin&limit=50"


class FauxHeyGen:
    """L'API HeyGen simulée : un chemin connu rend son `data`, un inconnu un HTTP 404."""

    def __init__(self, routes):
        self.routes, self.appels = routes, []

    def __call__(self, requete, *args, **kwargs):
        self.appels.append((requete.get_method(), requete.full_url))
        chemin = requete.full_url.split("api.heygen.com", 1)[1]
        if chemin not in self.routes:
            raise urllib.error.HTTPError(requete.full_url, 404, "Not Found", {}, io.BytesIO(b'{"error": "not found"}'))
        return io.BytesIO(json.dumps({"data": self.routes[chemin]}).encode("utf-8"))


class LierUnDoubleExistant(unittest.TestCase):
    """`lier` : un double déjà créé sur HeyGen se relie au Monteur IA, ids vérifiés en lecture seule
    (aucune génération, rien de débité), ou écrits hors ligne sans clé, avec un avertissement."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.maison = pathlib.Path(self.tmp.name) / "Monteur IA"
        self.maison.mkdir()
        self.m = charger("double_ia")
        self.m.MAISON = self.maison
        self.m.CONFIG = self.maison / "double-ia.config.json"
        self.m.CREDENTIALS = pathlib.Path(self.tmp.name) / "pas-de-cle" / "credentials"
        self.cle = mock.patch.dict(os.environ, {"HEYGEN_API_KEY": "cle-de-test"})
        self.cle.start()

    def tearDown(self):
        self.cle.stop()
        self.tmp.cleanup()

    def lancer(self, *args, routes=None):
        faux = FauxHeyGen({"/v3/avatars/looks/look1": LOOK, "/v3/avatars/grp1": GROUPE} if routes is None else routes)
        sortie = io.StringIO()
        with mock.patch.object(self.m.urllib.request, "urlopen", faux), \
                mock.patch.object(sys, "argv", ["double_ia.py", *args]), contextlib.redirect_stdout(sortie):
            try:
                self.m.main()
                code = 0
            except SystemExit as e:
                code = e.code or 0
        self.assertTrue(all(methode == "GET" for methode, _ in faux.appels), faux.appels)
        return code, sortie.getvalue() + (code if isinstance(code, str) else "")

    def config(self):
        return json.loads(self.m.CONFIG.read_text(encoding="utf-8")) if self.m.CONFIG.exists() else None

    def test_lier_verifie_et_ecrit_la_config(self):
        code, sortie = self.lancer("lier", "--avatar-id", "look1")
        self.assertEqual(code, 0, sortie)
        self.assertEqual(self.config(), {"name": "Double de Léa", "avatar_id": "look1", "avatar_group_id": "grp1",
                                         "engine": "avatar_iv"})
        self.assertIn("Rien n'a été généré ni débité", sortie)
        self.assertIn("prêt à générer", sortie)

    def test_id_du_groupe_au_lieu_du_look(self):
        routes = {"/v3/avatars/grp1": GROUPE, "/v3/avatars/looks?group_id=grp1&ownership=private&limit=50": [LOOK]}
        code, sortie = self.lancer("lier", "--avatar-id", "grp1", "--nom", "Léa bureau", routes=routes)
        self.assertEqual(code, 0, sortie)
        self.assertEqual(self.config(), {"name": "Léa bureau", "avatar_id": "look1", "avatar_group_id": "grp1",
                                         "engine": "avatar_iv"})
        # Plusieurs looks : on les montre et on demande lequel, sans rien écrire.
        self.m.CONFIG.unlink()
        routes["/v3/avatars/looks?group_id=grp1&ownership=private&limit=50"] = [LOOK, {**LOOK, "id": "look2", "name": "Salon"}]
        code, sortie = self.lancer("lier", "--avatar-id", "grp1", routes=routes)
        self.assertNotEqual(code, 0)
        self.assertIn("--avatar-id look2", sortie)
        self.assertIsNone(self.config())

    def test_ids_refuses(self):
        code, sortie = self.lancer("lier", "--avatar-id", "inconnu")
        self.assertNotEqual(code, 0)
        self.assertIn("Aucun look « inconnu »", sortie)
        code, sortie = self.lancer("lier", "--avatar-id", "look1", "--group-id", "autre")
        self.assertNotEqual(code, 0)
        self.assertIn("appartient au groupe grp1", sortie)
        code, sortie = self.lancer("lier", "--avatar-id", "look1", routes={
            "/v3/avatars/looks/look1": {**LOOK, "status": "failed", "error": {"code": "x", "message": "vidéo coupée"}},
            "/v3/avatars/grp1": GROUPE})
        self.assertNotEqual(code, 0)
        self.assertIn("vidéo coupée", sortie)
        self.assertIsNone(self.config(), "rien n'est écrit quand les ids sont refusés")

    def test_moteurs_et_consentement(self):
        code, sortie = self.lancer("lier", "--avatar-id", "look1", routes={
            "/v3/avatars/looks/look1": {**LOOK, "supported_api_engines": ["avatar_v"]},
            "/v3/avatars/grp1": {**GROUPE, "consent_status": "pending"}})
        self.assertEqual(code, 0, sortie)
        self.assertEqual(self.config()["engine"], "avatar_v")
        self.assertIn("double_ia.py consent", sortie)
        self.m.CONFIG.unlink()
        code, sortie = self.lancer("lier", "--avatar-id", "look1", routes={
            "/v3/avatars/looks/look1": {**LOOK, "supported_api_engines": ["avatar_iii"]}, "/v3/avatars/grp1": GROUPE})
        self.assertNotEqual(code, 0)
        self.assertIsNone(self.config())

    def test_double_deja_configure(self):
        avant = {"name": "Ancien", "avatar_id": "vieux", "avatar_group_id": "gv", "engine": "avatar_iv"}
        self.m.CONFIG.write_text(json.dumps(avant), encoding="utf-8")
        code, sortie = self.lancer("lier", "--avatar-id", "look1")
        self.assertNotEqual(code, 0)
        self.assertIn("--force", sortie)
        self.assertIn("vieux", sortie, "les ids actuels sont donnés pour revenir en arrière")
        self.assertEqual(self.config(), avant)
        code, sortie = self.lancer("lier", "--avatar-id", "look1", "--force")
        self.assertEqual(code, 0, sortie)
        self.assertEqual(self.config()["avatar_id"], "look1")

    def test_lister_ses_doubles(self):
        routes = {LISTE: [LOOK, {"id": "pub", "name": "Studio", "avatar_type": "studio_avatar"}]}
        code, sortie = self.lancer("lier", routes=routes)
        self.assertEqual(code, 0, sortie)
        self.assertIn("--avatar-id look1", sortie)
        self.assertNotIn("Studio", sortie)
        self.assertIsNone(self.config())

    def test_hors_ligne_puis_check(self):
        with mock.patch.dict(os.environ, {"HEYGEN_API_KEY": ""}):
            code, sortie = self.lancer("lier", "--avatar-id", "look1", routes={})
        self.assertEqual(code, 0, sortie)
        self.assertIn("SANS vérification", sortie)
        self.assertEqual(self.config(), {"name": "Mon double", "avatar_id": "look1", "engine": "avatar_iv"})
        # La clé posée, `check` lit le groupe sur HeyGen et complète la config.
        code, sortie = self.lancer("check", routes={"/v3/users/me": {"wallet": {"remaining_balance": 12.5}},
                                                    "/v3/avatars/looks/look1": LOOK, "/v3/avatars/grp1": GROUPE})
        self.assertEqual(code, 0, sortie)
        self.assertIn("Double de Léa", sortie)
        self.assertEqual(self.config()["avatar_group_id"], "grp1")


class SansTiretLong(unittest.TestCase):
    """Rien de ce qui est livré (outils, skills, consignes, README, INSTALL) ne contient de tiret long."""

    def test_fichiers_livres(self):
        livres = [*OUTILS.glob("*.py"), *(DEPOT / ".claude" / "skills").rglob("*.*"),
                  *(DEPOT / "templates").glob("*.md"), DEPOT / "README.md", DEPOT / "INSTALL.md"]
        fautifs = [f"{p.relative_to(DEPOT)}:{n}" for p in livres if p.is_file()
                   for n, ligne in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if "\u2014" in ligne]
        self.assertEqual(fautifs, [])


if __name__ == "__main__":
    unittest.main()
