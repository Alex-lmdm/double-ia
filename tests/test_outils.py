"""Tests des outils de Ton Double IA (hors livraison : l'installation ne copie que tools/, les skills
et le bloc de consignes, jamais tests/).

    python3 -m unittest discover -s tests -v

Sans dépendance : bibliothèque standard seulement. Rien n'est écrit dans le dépôt (dossiers
temporaires), aucun appel à HeyGen.
"""
import base64
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


class Suite:
    """Réponses successives d'une même route (un look « processing » puis « completed », un solde
    avant puis après) ; la dernière se répète."""

    def __init__(self, *reponses):
        self.reponses = list(reponses)

    def suivante(self):
        return self.reponses.pop(0) if len(self.reponses) > 1 else self.reponses[0]


class FauxHeyGen:
    """L'API HeyGen simulée : un chemin connu rend son `data`, un inconnu un HTTP 404. Une route
    « POST /chemin » ne répond qu'à cette méthode ; chaque envoi est gardé (corps JSON, en-têtes)."""

    def __init__(self, routes):
        self.routes, self.appels, self.envois = routes, [], []

    def __call__(self, requete, *args, **kwargs):
        methode = requete.get_method()
        self.appels.append((methode, requete.full_url))
        chemin = requete.full_url.split("api.heygen.com", 1)[1]
        cle = f"{methode} {chemin}" if f"{methode} {chemin}" in self.routes else chemin
        if cle not in self.routes:
            raise urllib.error.HTTPError(requete.full_url, 404, "Not Found", {}, io.BytesIO(b'{"error": "not found"}'))
        json_envoye = requete.get_header("Content-type") == "application/json"
        self.envois.append({"methode": methode, "chemin": chemin, "entetes": dict(requete.header_items()),
                            "corps": json.loads(requete.data) if json_envoye else None})
        reponse = self.routes[cle]
        if isinstance(reponse, Suite):
            reponse = reponse.suivante()
        return io.BytesIO(json.dumps({"data": reponse}).encode("utf-8"))

    def envoi(self, methode, chemin):
        return next((e for e in self.envois if (e["methode"], e["chemin"]) == (methode, chemin)), None)


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
        # Hors ligne, les moteurs du look sont inconnus : Avatar 6 d'office, `generate` se replie au besoin.
        self.assertEqual(self.config(), {"name": "Mon double", "avatar_id": "look1", "engine": "heygen-avatar-6"})
        # La clé posée, `check` lit le groupe sur HeyGen et complète la config.
        code, sortie = self.lancer("check", routes={"/v3/users/me": {"wallet": {"remaining_balance": 12.5}},
                                                    "/v3/avatars/looks/look1": LOOK, "/v3/avatars/grp1": GROUPE})
        self.assertEqual(code, 0, sortie)
        self.assertIn("Double de Léa", sortie)
        self.assertEqual(self.config()["avatar_group_id"], "grp1")


LOOK6 = {**LOOK, "supported_api_engines": ["avatar_v", "avatar_iv", "avatar_iii", "heygen-avatar-6",
                                          "heygen-avatar-6-turbo"]}


class Avatar6(unittest.TestCase):
    """Avatar 6 (17/11/2026) : moteur par défaut quand le look le prend, repli sinon, options de jeu
    envoyées seulement aux moteurs qui les acceptent (Avatar IV refuse motion_prompt)."""

    def setUp(self):
        self.m = charger("double_ia")

    def test_choisir_moteur(self):
        c = self.m.choisir_moteur
        self.assertEqual(c(None, LOOK6["supported_api_engines"]), ("heygen-avatar-6", None))
        self.assertEqual(c("avatar_iv", LOOK6["supported_api_engines"]), ("avatar_iv", None))
        moteur, remarque = c(None, LOOK["supported_api_engines"])
        self.assertEqual(moteur, "avatar_iv")
        self.assertIn("Avatar 6 n'est pas disponible", remarque)
        self.assertEqual(c("heygen-avatar-6-turbo", []), ("heygen-avatar-6-turbo", None), "inconnu : on garde")
        moteur, remarque = c(None, ["avatar_iii"])
        self.assertIsNone(moteur)
        self.assertIn("Avatar III", remarque)

    def test_demande_video(self):
        decor = self.m.demande_video("lookcafe", "a1", "heygen-avatar-6", "t", reference_look_id="look1")
        self.assertEqual((decor["avatar_id"], decor["engine"]),
                         ("lookcafe", {"type": "heygen-avatar-6", "reference_look_id": "look1"}))
        d = self.m.demande_video("look1", "a1", "heygen-avatar-6", "t", "sourire", True)
        self.assertEqual(d["engine"], {"type": "heygen-avatar-6", "motion_expressiveness": "less"})
        self.assertEqual(d["motion_prompt"], "sourire")
        self.assertEqual((d["resolution"], d["aspect_ratio"], d["audio_asset_id"]), ("1080p", "auto", "a1"))
        iv = self.m.demande_video("look1", "a1", "avatar_iv", "t", "sourire", True)
        self.assertEqual(iv["engine"], {"type": "avatar_iv"})
        self.assertNotIn("motion_prompt", iv)
        v = self.m.demande_video("look1", "a1", "avatar_v", "t", "x" * 2000)
        self.assertEqual(len(v["motion_prompt"]), 1200)
        self.assertEqual(v["engine"], {"type": "avatar_v"})

    def test_tarifs(self):
        self.assertAlmostEqual(self.m.tarif("heygen-avatar-6") * 30, 3.0)
        self.assertAlmostEqual(self.m.tarif("heygen-avatar-6-turbo") * 30, 1.5)
        self.assertEqual(self.m.tarif("inconnu"), max(self.m.TARIFS.values()), "inconnu : le plus cher")


class NomsDeFichiers(unittest.TestCase):
    def setUp(self):
        self.m = charger("double_ia")

    def test_slug(self):
        self.assertEqual(self.m.slug_of(pathlib.Path("derush/codes_voice_enhanced.mp3")), "codes")
        self.assertEqual(self.m.slug_of(pathlib.Path("derush/promo-noel_voice.mp3")), "promo-noel")
        self.assertEqual(self.m.slugifier("Café de Flore !"), "cafe-de-flore")
        self.assertEqual(self.m.slugifier("Plage, été 2026"), "plage-ete-2026")


class Autonome(unittest.TestCase):
    """Ton Double IA installé seul (sans Monteur IA) : reconnu par l'absence de templates/AGENT.md.tpl ;
    `moteur` et `check` restent en lecture seule (aucune génération, rien de débité)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.maison = pathlib.Path(self.tmp.name) / "Ton Double IA"
        self.maison.mkdir()
        self.m = charger("double_ia")
        self.m.MAISON = self.maison
        self.m.CONFIG = self.maison / "double-ia.config.json"
        self.cle = mock.patch.dict(os.environ, {"HEYGEN_API_KEY": "cle-de-test"})
        self.cle.start()

    def tearDown(self):
        self.cle.stop()
        self.tmp.cleanup()

    def lancer(self, *args, routes):
        faux = FauxHeyGen(routes)
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

    def test_detection(self):
        self.assertTrue(self.m.autonome())
        (self.maison / "templates").mkdir()
        (self.maison / "templates" / "AGENT.md.tpl").write_text("", encoding="utf-8")
        self.assertFalse(self.m.autonome())

    def test_moteur_et_check(self):
        self.m.CONFIG.write_text(json.dumps({"name": "Léa", "avatar_id": "look1", "avatar_group_id": "grp1",
                                             "engine": "avatar_iv"}), encoding="utf-8")
        routes = {"/v3/avatars/looks/look1": LOOK6, "/v3/avatars/grp1": GROUPE,
                  "/v3/users/me": {"wallet": {"remaining_balance": 9.0}}}
        code, sortie = self.lancer("check", routes=routes)
        self.assertEqual(code, 0, sortie)
        self.assertIn("Ton Double IA, seul", sortie)
        self.assertIn("Avatar 6 est disponible", sortie)
        code, sortie = self.lancer("moteur", routes=routes)
        self.assertEqual(code, 0, sortie)
        self.assertIn("Avatar 6 Turbo", sortie)
        self.assertIn("~3.00 $", sortie)
        code, sortie = self.lancer("moteur", "heygen-avatar-6", routes=routes)
        self.assertEqual(code, 0, sortie)
        self.assertEqual(json.loads(self.m.CONFIG.read_text(encoding="utf-8"))["engine"], "heygen-avatar-6")
        code, sortie = self.lancer("moteur", "heygen-avatar-6", routes={**routes, "/v3/avatars/looks/look1": LOOK})
        self.assertNotEqual(code, 0)
        self.assertIn("pas disponible", sortie)


# Une image WebP de 1 × 1 pixel (sans perte), comme l'aperçu d'un décor chez HeyGen.
WEBP_1PX = base64.b64decode("UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4HAA==")


class DossierSeul(unittest.TestCase):
    """Base : un dossier « Ton Double IA » temporaire, une clé de test, l'API HeyGen simulée,
    stdin qui n'est pas un terminal (comme quand un agent lance l'outil) et aucune attente réelle."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.maison = pathlib.Path(self.tmp.name) / "Ton Double IA"
        self.maison.mkdir()
        self.m = charger("double_ia")
        self.m.MAISON = self.m.REEL = self.m.ROOT = self.maison
        self.m.CONFIG = self.maison / "double-ia.config.json"
        self.cle = mock.patch.dict(os.environ, {"HEYGEN_API_KEY": "cle-de-test"})
        self.cle.start()
        self.faux = None

    def tearDown(self):
        self.cle.stop()
        self.tmp.cleanup()

    def ecrire_config(self, **valeurs):
        cfg = {"name": "Double de Léa", "avatar_id": "look1", "avatar_group_id": "grp1",
               "engine": "heygen-avatar-6", **valeurs}
        self.m.CONFIG.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")

    def config(self):
        return json.loads(self.m.CONFIG.read_text(encoding="utf-8"))

    def lancer(self, *args, routes=None, executer=None, telecharger=None):
        """Lance l'outil. executer : remplace subprocess.run (FFmpeg, yt-dlp, Whisper) ; telecharger :
        remplace urlretrieve (les fichiers de HeyGen)."""
        self.faux = FauxHeyGen(routes or {})
        sortie, erreurs = io.StringIO(), io.StringIO()
        with contextlib.ExitStack() as pile:
            pile.enter_context(mock.patch.object(self.m.urllib.request, "urlopen", self.faux))
            pile.enter_context(mock.patch.object(self.m.time, "sleep", lambda s: None))
            pile.enter_context(mock.patch.object(sys, "argv", ["double_ia.py", *args]))
            pile.enter_context(mock.patch.object(sys, "stdin", io.StringIO()))
            pile.enter_context(contextlib.redirect_stdout(sortie))
            pile.enter_context(contextlib.redirect_stderr(erreurs))
            if executer:
                pile.enter_context(mock.patch.object(self.m.subprocess, "run", executer))
            if telecharger:
                pile.enter_context(mock.patch.object(self.m.urllib.request, "urlretrieve", telecharger))
            try:
                self.m.main()
                code = 0
            except SystemExit as e:
                code = e.code or 0
        return code, sortie.getvalue() + erreurs.getvalue() + (code if isinstance(code, str) else "")

    def methodes(self):
        return [m for m, _ in self.faux.appels]


def ffmpeg_simule(cmd, **kwargs):
    """FFmpeg simulé : écrit le fichier de sortie (dernier argument)."""
    pathlib.Path(str(cmd[-1])).write_bytes(b"\xff\xd8 faux")
    return subprocess.CompletedProcess(cmd, 0, "", "")


def ecrire_webp(url, chemin):
    pathlib.Path(chemin).write_bytes(WEBP_1PX)
    return chemin, None


DECOR_FINI = {"id": "lookcafe", "status": "completed", "avatar_type": "photo_avatar",
              "preview_image_url": "https://cdn.heygen.test/cafe.webp", "supported_api_engines": ["heygen-avatar-6"]}


class Decors(DossierSeul):
    """Bonus « Ton double partout » : `decor` crée un look photo du double dans un nouveau lieu
    (~1 $, seulement après accord), `decors` les liste, l'image arrive en JPEG dans decors/."""

    def routes_creation(self, look=DECOR_FINI):
        return {"/v3/users/me": Suite({"wallet": {"remaining_balance": 10.0}}, {"wallet": {"remaining_balance": 9.0}}),
                "POST /v3/avatars": {"avatar_item": {"id": "lookcafe"}, "avatar_group": {"id": "grp1"}},
                "/v3/avatars/looks/lookcafe": Suite({"id": "lookcafe", "status": "processing"}, look)}

    def test_rien_sans_accord(self):
        self.ecrire_config()
        code, sortie = self.lancer("decor", "Sitting in a cozy café", "--nom", "Café", routes=self.routes_creation())
        self.assertNotEqual(code, 0)
        self.assertIn("~1.00 $", sortie)
        self.assertIn("Rien n'est lancé ni débité", sortie)
        self.assertEqual(set(self.methodes()), {"GET"}, "aucune création sans --yes")
        self.assertNotIn("decors", self.config())

    def test_creer_un_decor(self):
        self.ecrire_config()
        code, sortie = self.lancer("decor", "  Sitting in a cozy café,\n warm light. ", "--nom", "Café", "--yes",
                                   routes=self.routes_creation(), executer=ffmpeg_simule, telecharger=ecrire_webp)
        self.assertEqual(code, 0, sortie)
        envoi = self.faux.envoi("POST", "/v3/avatars")
        self.assertEqual(envoi["corps"], {
            "type": "prompt", "name": "Double de Léa - décor cafe",
            "prompt": "Same person, same face and same outfit as the reference. Sitting in a cozy café, warm light.",
            "avatar_id": "look1", "aspect_ratio": "9:16"})
        cle = envoi["entetes"].get("Idempotency-key")
        self.assertTrue(cle and cle.startswith("double-ia-decor-"), envoi["entetes"])
        self.assertEqual(self.config()["decors"], {"cafe": "lookcafe"})
        self.assertEqual(self.config()["avatar_id"], "look1", "le double ne change pas")
        self.assertTrue((self.maison / "decors" / "cafe.jpg").exists())
        self.assertFalse((self.maison / "decors" / "cafe.webp").exists())
        self.assertIn("Coût réel : 1.00 $", sortie)
        self.assertIn("--decor cafe", sortie)
        # Le même nom : refusé sans --force (un nouveau décor se paie), puis une nouvelle demande.
        code, sortie = self.lancer("decor", "Sitting in a cozy café, warm light.", "--nom", "cafe", "--yes",
                                   routes=self.routes_creation())
        self.assertNotEqual(code, 0)
        self.assertIn("--force", sortie)
        self.assertNotIn("POST", self.methodes())
        code, sortie = self.lancer("decor", "Sitting in a cozy café, warm light.", "--nom", "cafe", "--yes", "--force",
                                   routes=self.routes_creation(), executer=ffmpeg_simule, telecharger=ecrire_webp)
        self.assertEqual(code, 0, sortie)
        self.assertNotEqual(self.faux.envoi("POST", "/v3/avatars")["entetes"]["Idempotency-key"], cle,
                            "refaire un décor est une nouvelle demande")

    def test_decor_echoue(self):
        self.ecrire_config()
        rate = {"id": "lookcafe", "status": "failed", "error": {"message": "prompt refusé"}}
        code, sortie = self.lancer("decor", "Somewhere", "--nom", "ailleurs", "--yes", routes=self.routes_creation(rate))
        self.assertNotEqual(code, 0)
        self.assertIn("prompt refusé", sortie)
        self.assertIn("Reformule", sortie)
        self.assertNotIn("decors", self.config())

    def test_lister_et_recuperer_une_image(self):
        self.ecrire_config(decors={"cafe": "lookcafe"})
        code, sortie = self.lancer("decors", routes={"/v3/avatars/looks/lookcafe": DECOR_FINI},
                                   executer=ffmpeg_simule, telecharger=ecrire_webp)
        self.assertEqual(code, 0, sortie)
        self.assertIn("decors/cafe.jpg", sortie)
        self.assertEqual(set(self.methodes()), {"GET"})
        code, sortie = self.lancer("decors")
        self.assertEqual(self.faux.appels, [], "image déjà là : rien à demander à HeyGen")

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg absent")
    def test_conversion_webp_en_jpeg(self):
        with mock.patch.object(self.m.urllib.request, "urlretrieve", ecrire_webp):
            image = self.m.telecharger_apercu("https://cdn.heygen.test/cafe.webp", "cafe")
        self.assertEqual(image, self.maison / "decors" / "cafe.jpg")
        self.assertEqual(image.read_bytes()[:2], b"\xff\xd8", "un vrai JPEG")


class GenererDansUnDecorOuEnRapide(DossierSeul):
    """`generate --decor` : la vidéo part du look du décor, avec le double en reference_look_id ;
    `generate --rapide` : Avatar 6 Turbo pour cette vidéo, le moteur gardé ne change pas."""

    def setUp(self):
        super().setUp()
        (self.maison / "derush").mkdir()
        self.audio = self.maison / "derush" / "promo_voice_enhanced.mp3"
        self.audio.write_bytes(b"audio")
        (self.maison / "derush" / "promo_audio_timeline.json").write_text('{"takes": []}', encoding="utf-8")
        self.duree = mock.patch.object(self.m, "duration", lambda p: 9.0)
        self.duree.start()

    def tearDown(self):
        self.duree.stop()
        super().tearDown()

    def routes(self, look_double=LOOK6, look_decor=None):
        r = {"/v3/users/me": Suite({"wallet": {"remaining_balance": 10.0}}, {"wallet": {"remaining_balance": 9.1}}),
             "/v3/avatars/looks/look1": look_double,
             "POST /v3/assets": {"asset_id": "a1"}, "POST /v3/videos": {"video_id": "v1"},
             "/v3/videos/v1": Suite({"status": "processing"},
                                    {"status": "completed", "video_url": "https://cdn.heygen.test/v1.mp4"})}
        if look_decor:
            r["/v3/avatars/looks/lookcafe"] = look_decor
        return r

    def generer(self, *options, **kw):
        return self.lancer("generate", str(self.audio), *options, executer=ffmpeg_simule,
                           telecharger=lambda url, chemin: pathlib.Path(chemin).write_bytes(b"mp4"), **kw)

    def test_dans_un_decor(self):
        self.ecrire_config(engine="avatar_iv", decors={"cafe": "lookcafe"})
        decor = {**DECOR_FINI, "supported_api_engines": ["heygen-avatar-6", "heygen-avatar-6-turbo"]}
        code, sortie = self.generer("--decor", "cafe", routes=self.routes(look_decor=decor))
        self.assertNotEqual(code, 0)
        self.assertIn("Rien n'est lancé ni débité", sortie)
        self.assertNotIn("POST", self.methodes())
        code, sortie = self.generer("--decor", "café", "--yes", routes=self.routes(look_decor=decor))
        self.assertEqual(code, 0, sortie)
        corps = self.faux.envoi("POST", "/v3/videos")["corps"]
        self.assertEqual(corps["avatar_id"], "lookcafe")
        self.assertEqual(corps["engine"], {"type": "heygen-avatar-6", "reference_look_id": "look1"})
        self.assertIn("Les décors se génèrent avec Avatar 6", sortie)
        self.assertIn("~0.90 $", sortie)
        self.assertIn("videos/promo-cafe.mp4", sortie)
        self.assertEqual(self.config()["engine"], "avatar_iv", "le moteur gardé ne change pas")

    def test_decor_inconnu(self):
        self.ecrire_config(decors={"cafe": "lookcafe"})
        code, sortie = self.generer("--decor", "plage", "--yes", routes=self.routes())
        self.assertNotEqual(code, 0)
        self.assertIn("Tes décors : cafe", sortie)
        self.assertNotIn("POST", self.methodes())

    def test_version_rapide(self):
        self.ecrire_config()
        code, sortie = self.generer("--rapide", "--yes", routes=self.routes())
        self.assertEqual(code, 0, sortie)
        self.assertEqual(self.faux.envoi("POST", "/v3/videos")["corps"]["engine"], {"type": "heygen-avatar-6-turbo"})
        self.assertIn("version rapide", sortie)
        self.assertIn("~0.45 $", sortie)
        self.assertIn("videos/promo.mp4", sortie)
        self.assertEqual(self.config()["engine"], "heygen-avatar-6", "le moteur par défaut ne change pas")
        # Un double sans Turbo : on le dit, rien ne part (pas de repli silencieux vers plus cher).
        code, sortie = self.generer("--rapide", "--yes", routes=self.routes(look_double=LOOK))
        self.assertNotEqual(code, 0)
        self.assertIn("version rapide (Avatar 6 Turbo) n'est pas disponible", sortie)
        self.assertNotIn("POST", self.methodes())
        code, sortie = self.generer("--rapide", "--engine", "avatar_iv", routes=self.routes())
        self.assertEqual(code, 2, "--rapide et --engine s'excluent")


class SansVoixClonee(DossierSeul):
    """La voix clonée est retirée : plus de commande, et une ancienne config qui en garde une trace
    marche toujours, sans jamais en parler."""

    def test_commandes_retirees(self):
        for commande in ("cloner-voix", "voix-clonee"):
            code, sortie = self.lancer(commande, "x")
            self.assertEqual(code, 2, sortie)

    def test_ancienne_config(self):
        self.ecrire_config(voice_id="v1", voice_name="Voix de Léa")
        routes = {"/v3/users/me": {"wallet": {"remaining_balance": 9.0}}, "/v3/avatars/looks/look1": LOOK6,
                  "/v3/avatars/grp1": GROUPE, "/v3/avatars/looks/look2": {**LOOK6, "id": "look2"}}
        code, sortie = self.lancer("check", routes=routes)
        self.assertEqual(code, 0, sortie)
        self.assertNotIn("oix", sortie)
        self.assertIn("Décors    : aucun", sortie)
        code, sortie = self.lancer("moteur", "heygen-avatar-6-turbo", routes=routes)
        self.assertEqual(code, 0, sortie)
        self.assertEqual(set(self.config()) & {"voice_id", "voice_name"}, set(), "plus jamais écrits")
        self.ecrire_config(voice_id="v1", decors={"cafe": "lookcafe"})
        code, sortie = self.lancer("lier", "--avatar-id", "look2", "--force", routes=routes)
        self.assertEqual(code, 0, sortie)
        self.assertNotIn("voice_id", self.config())
        self.assertNotIn("decors", self.config(), "un autre double repart sans les décors de l'ancien")
        for retiree in ("cloner-voix", "voix-clonee", "/v3/models/audio"):
            self.assertNotIn(retiree, pathlib.Path(self.m.__file__).read_text(encoding="utf-8"))


INFO_REEL = {"extractor_key": "Instagram", "uploader": "createur.test", "upload_date": "20261101",
             "description": "Commente VIRAL pour recevoir mon guide", "like_count": 1200, "comment_count": 300}
# Les mots horodatés de whisper-cli (-ml 1 -sow -oj), avec le jeton vide du début et un bruit.
MOTS_WHISPER = [("", 0, 0), (" Tu", 50, 110), (" veux", 110, 340), (" savoir", 340, 690), (" pourquoi", 690, 1190),
                (" tes", 1190, 1380), (" vidéos", 1380, 1730), (" ne", 1730, 1840), (" marchent", 1840, 2300),
                (" pas", 2300, 2470), (" ?", 2470, 2860), (" [Musique]", 2860, 3000), (" Je", 3000, 3180),
                (" vais", 3180, 3340), (" te", 3340, 3500), (" le", 3500, 3700), (" dire.", 3700, 4480)]


def whisper_json(mots=MOTS_WHISPER, langue="fr"):
    return {"result": {"language": langue},
            "transcription": [{"offsets": {"from": d, "to": f}, "text": t} for t, d, f in mots]}


class ReelCloneur(DossierSeul):
    """Bonus « Le Reel Cloneur de ton double » : `reel` télécharge (yt-dlp, sans cookies) ou lit un
    fichier, extrait l'audio et le transcrit (Whisper) ; `reel-verifier` repère une phrase reprise."""

    def setUp(self):
        super().setUp()
        outils = self.maison / "faux-outils"
        outils.mkdir()
        for nom in ("yt-dlp", "whisper-cli", "ggml-small.bin"):
            (outils / nom).write_text("", encoding="utf-8")
        env = {"ytDlp": str(outils / "yt-dlp"), "whisperCli": str(outils / "whisper-cli"),
               "whisperModel": str(outils / "ggml-small.bin")}
        (self.maison / "brand.config.json").write_text(json.dumps({"env": env}), encoding="utf-8")
        self.commandes, self.version_ytdlp, self.ytdlp_rate = [], "2026.08.19", None
        self.duree = mock.patch.object(self.m, "duration", lambda p: 14.0)
        self.duree.start()

    def tearDown(self):
        self.duree.stop()
        super().tearDown()

    def executer(self, cmd, **kwargs):
        cmd = [str(c) for c in cmd]
        self.commandes.append(cmd)
        outil = pathlib.Path(cmd[0]).name
        if outil == "yt-dlp":
            if "--version" in cmd:
                return subprocess.CompletedProcess(cmd, 0, self.version_ytdlp + "\n", "")
            if self.ytdlp_rate:
                return subprocess.CompletedProcess(cmd, 1, "", self.ytdlp_rate)
            dossier = pathlib.Path(cmd[cmd.index("-o") + 1]).parent
            (dossier / "media.mp4").write_bytes(b"video")
            (dossier / "media.info.json").write_text(json.dumps(INFO_REEL), encoding="utf-8")
        elif outil == "whisper-cli":
            prefixe = pathlib.Path(cmd[cmd.index("-of") + 1])
            prefixe.with_suffix(".json").write_text(json.dumps(whisper_json()), encoding="utf-8")
        elif "-vn" in cmd:
            pathlib.Path(cmd[-1]).write_bytes(b"wav")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def reel(self, *args):
        return self.lancer("reel", *args, executer=self.executer)

    def appels_de(self, outil):
        return [c for c in self.commandes if pathlib.Path(c[0]).name == outil]

    def test_lien_instagram(self):
        code, sortie = self.reel("https://www.instagram.com/reel/DfmjvZ4MN6e/?igsh=abc")
        self.assertEqual(code, 0, sortie)
        dossier = self.maison / "clones" / "instagram-dfmjvz4mn6e"
        telechargement = [c for c in self.appels_de("yt-dlp") if "--version" not in c][0]
        self.assertIn("--no-cookies", telechargement)
        self.assertFalse(any(c.startswith("--cookies") for c in telechargement))
        meta = json.loads((dossier / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual((meta["plateforme"], meta["compte"], meta["likes"], meta["duree"]),
                         ("instagram", "createur.test", 1200, 14.0))
        t = json.loads((dossier / "transcription.json").read_text(encoding="utf-8"))
        self.assertEqual(t["langue"], "fr")
        self.assertEqual([p["texte"] for p in t["phrases"]],
                         ["Tu veux savoir pourquoi tes vidéos ne marchent pas ?", "Je vais te le dire."])
        self.assertEqual((t["phrases"][0]["debut"], t["phrases"][0]["fin"]), (0.05, 2.86))
        self.assertEqual(t["mots"], 14)
        self.assertIn("0:00.1 → 0:02.9 · Tu veux savoir", (dossier / "transcription.txt").read_text(encoding="utf-8"))
        whisper = self.appels_de("whisper-cli")[0]
        self.assertEqual(whisper[whisper.index("-l") + 1], "auto", "le Reel peut être dans une autre langue")
        self.assertFalse((dossier / "_telechargement").exists())
        # Relancé sur le même lien : rien n'est refait.
        self.commandes.clear()
        code, sortie = self.reel("https://www.instagram.com/reel/DfmjvZ4MN6e/")
        self.assertEqual(code, 0, sortie)
        self.assertEqual(self.commandes, [])

    def test_fichier_glisse(self):
        video = self.maison / "Mon Reel préféré.mov"
        video.write_bytes(b"video")
        code, sortie = self.reel(str(video), "--langue", "en")
        self.assertEqual(code, 0, sortie)
        self.assertEqual(self.appels_de("yt-dlp"), [])
        self.assertTrue((self.maison / "clones" / "mon-reel-prefere" / "transcription.json").exists())
        whisper = self.appels_de("whisper-cli")[0]
        self.assertEqual(whisper[whisper.index("-l") + 1], "en")
        # Un autre fichier du même nom, ailleurs : il est retranscrit, pas confondu avec le premier.
        autre = self.maison / "ailleurs" / "Mon Reel préféré.mov"
        autre.parent.mkdir()
        autre.write_bytes(b"autre video")
        self.commandes.clear()
        code, sortie = self.reel(str(autre))
        self.assertEqual(code, 0, sortie)
        self.assertEqual(len(self.appels_de("whisper-cli")), 1)

    def test_telechargement_refuse(self):
        self.ytdlp_rate = "ERROR: [Instagram] DfmjvZ4MN6e: login required; please use --cookies-from-browser"
        code, sortie = self.reel("https://www.instagram.com/reel/DfmjvZ4MN6e/")
        self.assertNotEqual(code, 0)
        self.assertIn("glisse le fichier", sortie)
        self.assertNotIn("--cookies", sortie, "on ne conseille jamais de cookies")
        self.assertFalse((self.maison / "clones" / "instagram-dfmjvz4mn6e" / "media.mp4").exists())

    def test_ytdlp_absent_ou_trop_ancien(self):
        with mock.patch.object(self.m, "ytdlp", lambda: None):
            code, sortie = self.reel("https://www.tiktok.com/@x/video/7312345678901234567")
        self.assertNotEqual(code, 0)
        self.assertIn("brew install yt-dlp", sortie)
        self.version_ytdlp = "2025.01.15"
        code, sortie = self.reel("https://www.tiktok.com/@x/video/7312345678901234567")
        self.assertNotEqual(code, 0)
        self.assertIn("brew upgrade yt-dlp", sortie)

    def test_reel_verifier(self):
        self.reel("https://www.instagram.com/reel/DfmjvZ4MN6e/")
        dossier = self.maison / "clones" / "instagram-dfmjvz4mn6e"
        script = dossier / "script.md"
        script.write_text("# Mon script\nTu veux savoir POURQUOI tes videos ne marchent pas ?\nVoilà.\n", encoding="utf-8")
        code, sortie = self.lancer("reel-verifier", str(script))
        self.assertNotEqual(code, 0)
        self.assertIn("« Tu veux savoir POURQUOI tes videos ne marchent pas »", sortie)
        script.write_text("# Mon script\nTes Reels font 200 vues ? Regarde ta première phrase.\n"
                          "Commente GUIDE et je t'envoie ma méthode.\n", encoding="utf-8")
        code, sortie = self.lancer("reel-verifier", str(script))
        self.assertEqual(code, 0, sortie)
        self.assertIn("ok", sortie)

    def test_en_phrases(self):
        mots = [(0.0, 0.5, " Sans"), (0.5, 1.0, " point"), (13.0, 13.5, " fin"), (13.5, 14.0, " ici.")]
        phrases = self.m.en_phrases(mots, 13.8)
        self.assertEqual([p["texte"] for p in phrases], ["Sans point fin", "ici."], "coupée à 12 s")
        self.assertEqual(phrases[-1]["fin"], 13.8, "jamais au-delà de la durée")

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("whisper-cli"), "ffmpeg ou whisper-cli absent")
    def test_chaine_reelle_sur_un_fichier(self):
        """FFmpeg et Whisper pour de vrai, sur une vidéo de test de 2 s (sans parole)."""
        self.duree.stop()
        (self.maison / "brand.config.json").unlink()   # les vrais outils, pas les faux du setUp
        modele = self.m.modele_whisper()
        if not modele:
            self.duree.start()
            self.skipTest("aucun modèle Whisper")
        petit = pathlib.Path(modele).with_name("ggml-small.bin")
        env = {"whisperModel": str(petit if petit.exists() else modele)}
        (self.maison / "brand.config.json").write_text(json.dumps({"env": env}), encoding="utf-8")
        video = self.maison / "essai.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=180x320:rate=25:d=2",
                        "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-shortest", "-pix_fmt", "yuv420p",
                        str(video)], check=True)
        try:
            code, sortie = self.lancer("reel", str(video))
        finally:
            self.duree.start()
        self.assertEqual(code, 0, sortie)
        t = json.loads((self.maison / "clones" / "essai" / "transcription.json").read_text(encoding="utf-8"))
        self.assertAlmostEqual(t["duree"], 2.0, delta=0.1)


class Declencheurs(unittest.TestCase):
    """Chaque phrase que le README apprend au client mène au bon skill (sa description) ou aux
    consignes du dossier."""

    PHRASES = [
        ("Crée mon double IA", "setup-double-ia"),
        ("J'ai déjà un double HeyGen", "setup-double-ia"),
        ("Voici l'audio, utilise mon double.", "double-ia"),
        ("Voici l'audio, utilise mon double au café", "double-ia"),
        ("Mets mon double dans [décor]", "double-ia"),
        ("Fais-la en version rapide", "double-ia"),
        ("Génère avec des gestes plus calmes", "double-ia"),
        ("Écris-moi un Reel sur [ton sujet]", "scenariste-reels"),
        ("Clone ce Reel pour mon double : [lien du Reel]", "reel-cloneur-double"),
        ("Garde ça en mémoire pour mes prochaines vidéos", "consignes"),
    ]

    @staticmethod
    def normal(texte):
        return " ".join(texte.replace("’", "'").lower().split())

    def description(self, skill):
        if skill == "consignes":
            return (DEPOT / "templates" / "consignes-seul.md").read_text(encoding="utf-8")
        texte = (DEPOT / ".claude" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        return texte.split("---")[1]

    def test_phrases(self):
        readme = self.normal((DEPOT / "README.md").read_text(encoding="utf-8"))
        for phrase, skill in self.PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(self.normal(f"« {phrase} »"), readme)
                debut = self.normal(phrase.split("[")[0]).rstrip(" .:")
                self.assertIn(debut, self.normal(self.description(skill)))


class SansTiretLong(unittest.TestCase):
    """Rien de ce qui est livré (outils, skills, consignes, README, INSTALL) ne contient de tiret long
    ni de demi-cadratin."""

    def test_fichiers_livres(self):
        livres = [*OUTILS.glob("*.py"), *(DEPOT / ".claude" / "skills").rglob("*.*"),
                  *(DEPOT / "templates").rglob("*.md"), DEPOT / "README.md", DEPOT / "INSTALL.md"]
        fautifs = [f"{p.relative_to(DEPOT)}:{n}" for p in livres if p.is_file()
                   for n, ligne in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
                   if "\u2014" in ligne or "\u2013" in ligne]
        self.assertEqual(fautifs, [])


if __name__ == "__main__":
    unittest.main()
