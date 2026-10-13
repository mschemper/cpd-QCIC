import unittest

from src.qcic.sources import council as c

T = [
    "Settlement agreement regarding case of Lorenzo Williams v. City of Chicago, et al., cited as 2026 L 007227",
    "Settlement agreement regarding case of Jose Gonzalez, as Special Administrator of the Estate of Jose Almanza-Martinez, Deceased v. City of Chicago, Officer Ashton Smiley, and Officer Michael Carreon, cited as 24 L 14052",
    "Settlement agreement regarding case of Arturo DeLeon-Reyes v. Reynaldo Guevara, et al., cited as 18 CV 1028",
    "Settlement agreement regarding case of In Re: Guevara",
    "Judgment and Settlement Report for month of September 2026",
]


class CouncilTests(unittest.TestCase):
    def test_police_signal(self):
        self.assertEqual(c.police_signal(T[1]), (True, "Officer"))
        self.assertEqual(c.police_signal("Order re Chicago Police Department overtime")[0], True)
        self.assertEqual(c.police_signal(T[0]), (False, None))
        self.assertEqual(c.police_signal(T[2]), (False, None))
        self.assertEqual(c.police_signal(None), (False, None))

    def test_cover_report(self):
        self.assertTrue(c.is_cover_report(T[4]))
        self.assertTrue(c.is_cover_report("x", "LAWSUITS/SETTLEMENTS | Report of Settlements"))
        self.assertFalse(c.is_cover_report(T[0], "LAWSUITS/SETTLEMENTS | Lawsuits"))

    def test_amount(self):
        self.assertEqual(c.parse_amount("pay $1,250,000.50 to"), 1250000.5)
        self.assertEqual(c.parse_amount("approx $2 million"), 2_000_000)
        self.assertEqual(c.parse_amount("$75,000"), 75000)
        self.assertIsNone(c.parse_amount(T[0]))
        self.assertIsNone(c.parse_amount(None))

    def test_redaction(self):
        self.assertEqual(c.redact_title(T[0]), "Settlement agreement regarding case of [plaintiff] v. City of Chicago, et al., cited as 2026 L 007227")
        self.assertTrue(c.redact_title(T[1]).startswith("Settlement agreement regarding case of [plaintiff] v. City of Chicago, Officer"))
        self.assertNotIn("Gonzalez", c.redact_title(T[1]))
        self.assertEqual(c.redact_title(T[3]), T[3])
        self.assertEqual(c.redact_title("Doe vs. City of Chicago"), "[plaintiff] vs. City of Chicago")

    def test_record(self):
        r = c.record({"matterId": "ID1", "recordNumber": "Or2026-1", "title": T[2], "introductionDate": "2026-09-14T15:00:00+00:00",
                      "finalActionDate": "2026-09-23T15:00:00+00:00", "status": "90-Final", "matterCategory": "LAWSUITS/SETTLEMENTS | Lawsuits"})
        self.assertEqual((r["date"], r["date_kind"], r["case_keys"]), ("2026-09-23", "final_action", ["18-1028"]))
        self.assertTrue(r["url"].endswith("matterId=ID1"))


if __name__ == "__main__":
    unittest.main()
