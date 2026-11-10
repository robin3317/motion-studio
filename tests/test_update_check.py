#!/usr/bin/env python3
"""Tests for skills/motion-studio/scripts/update_check.py (stdlib only).

    python tests/test_update_check.py              # offline tests (fixtures)
    MS_LIVE_TESTS=1 python tests/test_update_check.py   # also hit the real endpoints

Run the live test from every place the skill runs (your machine AND a Claude Cowork cloud
session) before each release: it proves at least one update source is reachable from there.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "skills", "motion-studio", "scripts", "update_check.py")

CHANGELOG = """# Changelog

## 0.3.0 (2026-12-01): big one
- New thing A

## 0.2.1-beta (2026-11-10): reliability
- Fix B

## 0.2.0-beta (2026-11-09): older
- Old C
"""


class Case(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ms-update-test-")
        self.skill = os.path.join(self.tmp, "skills", "motion-studio")
        os.makedirs(os.path.join(self.skill, "scripts"))
        shutil.copy(SCRIPT, os.path.join(self.skill, "scripts", "update_check.py"))
        self.set_local("0.2.0-beta")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)
        self.missing = "file://" + os.path.join(self.tmp, "does-not-exist.json")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def set_local(self, version):
        with open(os.path.join(self.skill, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(f"---\nname: motion-studio\nmetadata:\n  version: {version}\n---\n")

    def fixture(self, name, content):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content if isinstance(content, str) else json.dumps(content))
        return "file://" + p

    def run_check(self, *args, releases=None, manifest=None, changelog=None, live=False):
        env = dict(os.environ, HOME=self.home, USERPROFILE=self.home)
        env.pop("MOTION_STUDIO_NO_UPDATE_CHECK", None)
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        if not live:
            env["MOTION_STUDIO_RELEASES_URL"] = releases or self.missing
            env["MOTION_STUDIO_MANIFEST_URL"] = manifest or self.missing
            env["MOTION_STUDIO_CHANGELOG_URL"] = changelog or self.missing
        p = subprocess.run([sys.executable, os.path.join(self.skill, "scripts", "update_check.py"), *args],
                           capture_output=True, text=True, env=env, timeout=30)
        return p.returncode, p.stdout.strip(), p.stderr.strip()

    def test_releases_source(self):
        rel = self.fixture("rel.json", [
            {"tag_name": "v0.2.0-beta", "html_url": "u1"},
            {"tag_name": "v0.3.0", "html_url": "u3", "draft": True},
            {"tag_name": "v0.2.1-beta", "html_url": "u2"}])
        code, out, _ = self.run_check("--json", releases=rel)
        d = json.loads(out)
        self.assertEqual((d["status"], d["latest"], d["source"]), ("UPDATE_AVAILABLE", "0.2.1-beta", "releases"))
        self.assertEqual(d["method"], "zip")

    def test_manifest_fallback_when_api_blocked(self):
        man = self.fixture("plugin.json", {"name": "motion-studio", "version": "0.2.1-beta"})
        code, out, _ = self.run_check(manifest=man)
        self.assertTrue(out.startswith("UPDATE_AVAILABLE 0.2.0-beta 0.2.1-beta zip"), out)
        self.assertIn("NOTES: https://github.com/robin3317/motion-studio/blob/main/CHANGELOG.md", out)
        code, out, _ = self.run_check("--json", manifest=man)
        self.assertEqual(json.loads(out)["source"], "manifest")

    def test_up_to_date(self):
        man = self.fixture("plugin.json", {"version": "0.2.0-beta"})
        self.assertEqual(self.run_check(manifest=man)[1], "UP_TO_DATE 0.2.0-beta")

    def test_all_blocked_is_silent_unless_forced(self):
        code, out, err = self.run_check()
        self.assertEqual((code, out, err), (0, "", ""))
        code, out, _ = self.run_check("--force")
        self.assertTrue(out.startswith("CHECK_FAILED releases:") and "manifest:" in out, out)
        code, out, _ = self.run_check("--json")
        self.assertEqual(json.loads(out)["status"], "CHECK_FAILED")

    def test_failure_is_not_cached(self):
        self.run_check()
        man = self.fixture("plugin.json", {"version": "0.2.1-beta"})
        self.assertTrue(self.run_check(manifest=man)[1].startswith("UPDATE_AVAILABLE"))

    def test_success_is_cached_for_a_day_and_force_skips_the_cache(self):
        man = self.fixture("plugin.json", {"version": "0.2.0-beta"})
        self.assertEqual(self.run_check(manifest=man)[1], "UP_TO_DATE 0.2.0-beta")
        man = self.fixture("plugin.json", {"version": "0.2.1-beta"})
        self.assertEqual(self.run_check(manifest=man)[1], "UP_TO_DATE 0.2.0-beta")  # cached
        self.assertTrue(self.run_check("--force", manifest=man)[1].startswith("UPDATE_AVAILABLE"))

    def test_snooze_never_reset(self):
        man = self.fixture("plugin.json", {"version": "0.2.1-beta"})
        self.run_check("--snooze", "1d")
        self.assertEqual(self.run_check(manifest=man)[1], "")
        self.run_check("--reset")
        self.run_check("--never")
        self.assertEqual(self.run_check(manifest=man)[1], "")
        self.run_check("--reset")
        self.assertTrue(self.run_check(manifest=man)[1].startswith("UPDATE_AVAILABLE"))

    def test_notes_only_newer_sections(self):
        cl = self.fixture("CHANGELOG.md", CHANGELOG)
        code, out, _ = self.run_check("--notes", changelog=cl)
        self.assertIn("New thing A", out)
        self.assertIn("Fix B", out)
        self.assertNotIn("Old C", out)
        self.assertNotIn("# Changelog", out)
        code, out, err = self.run_check("--notes")
        self.assertNotEqual(code, 0)
        self.assertIn("NOTES_UNAVAILABLE", err)

    def test_version_order(self):
        sys.path.insert(0, os.path.dirname(SCRIPT))
        try:
            import update_check as u
        finally:
            sys.path.pop(0)
        order = ["0.1.0-beta", "0.1.0-beta.2", "0.1.0", "0.2.0-beta", "0.2.1-beta", "0.2.1", "1.0.0"]
        for a, b in zip(order, order[1:]):
            self.assertTrue(u.newer(b, a), f"{b} should be newer than {a}")
            self.assertFalse(u.newer(a, b))
        self.assertFalse(u.newer("v0.2.0-beta", "0.2.0-beta"))

    @unittest.skipUnless(os.environ.get("MS_LIVE_TESTS"), "set MS_LIVE_TESTS=1 to hit the real endpoints")
    def test_live_at_least_one_source_answers(self):
        self.set_local("0.0.1")
        code, out, _ = self.run_check("--force", "--json", live=True)
        d = json.loads(out)
        print(f"\n  live check from this machine: status={d['status']} source={d.get('source')} "
              f"latest={d.get('latest')} errors={d.get('errors')}")
        self.assertEqual(d["status"], "UPDATE_AVAILABLE", d)
        code, out, err = self.run_check("--notes", live=True)
        self.assertEqual(code, 0, err)
        self.assertIn("##", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
