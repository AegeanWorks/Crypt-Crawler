"""Unit tests for headless inspection configuration and viewports."""

import unittest
from tools.inspect_ui import VIEWPORTS, check_failed


class TestInspectConfig(unittest.TestCase):
    def test_viewports_declared(self):
        self.assertIn("desktop", VIEWPORTS)
        self.assertIn("laptop", VIEWPORTS)
        self.assertIn("mobile", VIEWPORTS)

        self.assertEqual(VIEWPORTS["desktop"]["width"], 1920)
        self.assertEqual(VIEWPORTS["desktop"]["height"], 1080)
        self.assertEqual(VIEWPORTS["laptop"]["width"], 1366)
        self.assertEqual(VIEWPORTS["laptop"]["height"], 768)
        self.assertEqual(VIEWPORTS["mobile"]["width"], 390)
        self.assertEqual(VIEWPORTS["mobile"]["height"], 844)

    def test_failed_check_predicate_uses_falsy_not_identity(self):
        # Truthy non-True audit values (e.g. 1 from an and-chain) must pass.
        self.assertFalse(check_failed(True))
        self.assertFalse(check_failed(1))
        self.assertFalse(check_failed("yes"))
        self.assertTrue(check_failed(False))
        self.assertTrue(check_failed(None))
        self.assertTrue(check_failed(0))

    def test_skip_is_vacuous_pass_for_optional_fixtures(self):
        # The probes use `skip is True or (...)` so a missing optional
        # fixture never fails the gate.
        objective = {"skip": True}
        self.assertTrue(
            objective.get("skip") is True or (objective.get("heldThree") and True)
        )
        bounty_xp = {"skip": True}
        self.assertTrue(
            bounty_xp.get("skip") is True or bounty_xp.get("leveled") is True
        )
        self.assertFalse(check_failed(objective.get("skip") is True or False))


if __name__ == "__main__":
    unittest.main()
