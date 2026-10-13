"""Unit tests for src/qcic/build.py (names, matching, stats, districts, badges). stdlib unittest."""
import unittest

from src.qcic.build import (badge_of, district_of, match, median, pct_rank, quantile,
                            robust_scale, split_payroll_name)


def prof(uid, officer_id, first, last, mi=""):
    return {"UID": uid, "officer_id": officer_id, "first_name": first,
            "last_name": last, "middle_initial": mi}


class SplitPayrollNameTests(unittest.TestCase):
    def test_last_first_middle(self):
        self.assertEqual(split_payroll_name("AARON,  JEFFERY M"), ("AARON", "JEFFERY", "M"))

    def test_suffix_dropped_from_last(self):
        self.assertEqual(split_payroll_name("SMITH JR, JOHN")[0], "SMITH")

    def test_hyphen_and_spaces_squash(self):
        self.assertEqual(split_payroll_name("GARCIA-LOPEZ, ANA")[0], "GARCIALOPEZ")
        self.assertEqual(split_payroll_name("DE LA CRUZ, ANA")[0], "DELACRUZ")

    def test_no_middle_gives_blank_mi(self):
        self.assertEqual(split_payroll_name("DOE, JOHN"), ("DOE", "JOHN", ""))


class MatchTests(unittest.TestCase):
    def test_unique_three_key_match(self):
        people = {"p1": ("SMITH", "JOHN", "M")}
        out = match(people, [prof("u1", "1", "JOHN", "SMITH", "M"), prof("u2", "2", "JANE", "DOE")])
        self.assertEqual(out["p1"]["UID"], "u1")
        self.assertEqual(len(out), 1)

    def test_two_profiles_same_key_unmatched(self):
        people = {"p1": ("SMITH", "JOHN", "M")}
        out = match(people, [prof("u1", "1", "JOHN", "SMITH", "M"), prof("u2", "2", "JOHN", "SMITH", "M")])
        self.assertNotIn("p1", out)

    def test_two_payroll_same_key_unmatched(self):
        people = {"p1": ("SMITH", "JOHN", "M"), "p2": ("SMITH", "JOHN", "M")}
        out = match(people, [prof("u1", "1", "JOHN", "SMITH", "M")])
        self.assertEqual(out, {})

    def test_middle_initial_fallback_profile_blank(self):
        out = match({"p1": ("SMITH", "JOHN", "M")}, [prof("u1", "1", "JOHN", "SMITH", "")])
        self.assertEqual(out["p1"]["UID"], "u1")

    def test_middle_initial_fallback_payroll_blank(self):
        out = match({"p1": ("SMITH", "JOHN", "")}, [prof("u1", "1", "JOHN", "SMITH", "K")])
        self.assertEqual(out["p1"]["UID"], "u1")

    def test_conflicting_middle_initials_unmatched(self):
        out = match({"p1": ("SMITH", "JOHN", "M")}, [prof("u1", "1", "JOHN", "SMITH", "K")])
        self.assertEqual(out, {})

    def test_blank_first_or_last_never_matched(self):
        out = match({"p1": ("SMITH", "", "")}, [prof("u1", "1", "", "SMITH")])
        self.assertEqual(out, {})


class StatsTests(unittest.TestCase):
    def test_robust_scale_mad(self):
        med, scale = robust_scale([1, 2, 3, 4, 100])
        self.assertEqual(med, 3)
        # abs devs [2,1,0,1,97] -> MAD 1
        self.assertAlmostEqual(scale, 1 / 0.6745, places=9)

    def test_robust_scale_mad_zero_fallback(self):
        med, scale = robust_scale([0, 0, 0, 0, 5])
        self.assertEqual(med, 0)
        # MAD 0 -> 1.253314 * mean abs dev = 1.253314 * (5/5)
        self.assertAlmostEqual(scale, 1.253314, places=9)

    def test_robust_scale_all_equal_is_zero(self):
        self.assertEqual(robust_scale([2, 2, 2]), (2, 0.0))

    def test_median_odd_even_empty(self):
        self.assertEqual(median([3, 1, 2]), 2)
        self.assertEqual(median([1, 2, 3, 4]), 2.5)
        self.assertEqual(median([]), 0.0)

    def test_quantile_interpolates(self):
        self.assertEqual(quantile([1, 2, 3, 4, 5], 0.5), 3)
        self.assertAlmostEqual(quantile([1, 2, 3, 4, 5], 0.9), 4.6)
        self.assertEqual(quantile([10, 20], 0.5), 15)
        self.assertEqual(quantile([], 0.9), 0.0)

    def test_pct_rank_share_at_or_below(self):
        self.assertEqual(pct_rank([1, 2, 3, 4], 2), 50.0)
        self.assertEqual(pct_rank([1, 2, 3, 4], 4), 100.0)
        self.assertEqual(pct_rank([1, 2, 3, 4], 0), 0.0)
        self.assertEqual(pct_rank([], 1), 0.0)


class DistrictTests(unittest.TestCase):
    def test_valid_districts(self):
        self.assertEqual(district_of("1"), "1")
        self.assertEqual(district_of("25"), "25")

    def test_excluded_or_invalid_units(self):
        for u in ("13", "21", "23", "44", None):
            with self.subTest(unit=u):
                self.assertIsNone(district_of(u))


class BadgeTests(unittest.TestCase):
    def test_summary_badge_preferred(self):
        self.assertEqual(badge_of({"current_star": "17432"}, {"badge": "17000"}), "17000")

    def test_float_string_trimmed(self):
        self.assertEqual(badge_of(None, {"badge": "17432.0"}), "17432")

    def test_zero_or_empty_is_none(self):
        self.assertIsNone(badge_of(None, {"badge": "0"}))
        self.assertIsNone(badge_of(None, {"badge": ""}))
        self.assertIsNone(badge_of({"current_star": ""}, None))


if __name__ == "__main__":
    unittest.main()


class DefendantKeyTests(unittest.TestCase):
    def test_strips_rank_badge_paren_initial(self):
        from src.qcic.build import defendant_key
        self.assertEqual(defendant_key("Sgt. Clifford J. Martin #18859 (Defendant)"), ("MARTIN", "CLIFFORD"))
        self.assertEqual(defendant_key("Jennifer Dodge (Star 17504)"), ("DODGE", "JENNIFER"))

    def test_unusable(self):
        from src.qcic.build import defendant_key
        self.assertIsNone(defendant_key("Bond"))
        self.assertIsNone(defendant_key("Officer J."))
