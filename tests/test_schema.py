"""Validate site/data.json (or any file) against docs/SCHEMA.md.

Tests: python3 -m unittest discover -s tests -t . -v
CLI:   python3 -m tests.test_schema [path]   (default: site/data.json; exit 1 on errors)
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXED_KEYS = ["total_pay", "overtime_pay", "overtime_ratio", "complaints_window",
              "sustained_total", "lawsuit_total"]
FLAG_KEYS = {"total", "ot", "otr", "cmp", "sus", "law"}
_MISSING = object()


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _str(x):
    return isinstance(x, str)


def _bool(x):
    return isinstance(x, bool)


def _dict(x):
    return isinstance(x, dict)


def _list(x):
    return isinstance(x, list)


def _opt(pred):
    return lambda x: x is None or pred(x)


class _Check:
    def __init__(self):
        self.errs = []

    def req(self, obj, key, where, pred, what):
        if not isinstance(obj, dict) or key not in obj:
            self.errs.append(f"{where}.{key}: missing")
            return None
        v = obj[key]
        if not pred(v):
            self.errs.append(f"{where}.{key}: expected {what}, got {repr(v)[:80]}")
        return v

    def fail(self, where, msg):
        self.errs.append(f"{where}: {msg}")


def validate(data):
    """Return a list of error strings; empty list means valid."""
    c = _Check()
    if not _dict(data):
        return ["root: expected object"]

    # meta
    meta = c.req(data, "meta", "root", _dict, "object") or {}
    c.req(meta, "generated", "meta", _str, "string")
    c.req(meta, "payroll_year", "meta", _int, "int")
    vint = c.req(meta, "vintage", "meta", _dict, "object") or {}
    for k in ("payroll", "complaints", "units", "lawsuits", "copa_bia"):
        c.req(vint, k, "meta.vintage", _str, "string")
    counts = c.req(meta, "counts", "meta", _dict, "object") or {}
    for k in ("employees", "sworn", "matched", "flagged_stat", "flagged_fixed"):
        c.req(counts, k, "meta.counts", _int, "int")
    # written by build.py, not yet in SCHEMA.md: optional
    for k in ("with_lawsuit_data",):
        if k in counts and not _int(counts[k]):
            c.fail("meta.counts." + k, "expected int")
    for k in ("pay_total", "ot_total"):
        if k in counts and not _num(counts[k]):
            c.fail("meta.counts." + k, "expected number")
    thr = c.req(meta, "thresholds", "meta", _dict, "object") or {}
    c.req(thr, "z_flag", "meta.thresholds", _num, "number")
    fixed = c.req(thr, "fixed", "meta.thresholds", _dict, "object") or {}
    for k in FIXED_KEYS:
        c.req(fixed, k, "meta.thresholds.fixed", _num, "number")
    sources = c.req(meta, "sources", "meta", _list, "array") or []
    for i, s in enumerate(sources):
        w = f"meta.sources[{i}]"
        for k in ("name", "url", "note"):
            c.req(s, k, w, _str, "string")

    # metrics
    metrics = c.req(data, "metrics", "root", _list, "array") or []
    if not all(_str(m) for m in metrics):
        c.fail("metrics", "all entries must be strings")
    n = len(metrics)
    labels = c.req(data, "metric_labels", "root", _dict, "object") or {}
    for m in metrics:
        c.req(labels, m, "metric_labels", _str, "string")

    # peers
    peers = c.req(data, "peers", "root", _dict, "object") or {}
    for g, st in peers.items():
        w = f"peers[{g!r}]"
        c.req(st, "n", w, _int, "int")
        for k in ("median", "p90", "p99"):
            arr = c.req(st, k, w, _list, "array") or []
            if len(arr) != n or not all(_num(x) for x in arr):
                c.fail(f"{w}.{k}", f"expected {n} numbers")

    # officers
    officers = c.req(data, "officers", "root", _list, "array") or []
    seen_ids = set()
    for i, o in enumerate(officers):
        w = f"officers[{i}]"
        if not _dict(o):
            c.fail(w, "expected object")
            continue
        oid = c.req(o, "id", w, _str, "string")
        if oid in seen_ids:
            c.fail(w + ".id", f"duplicate id {oid!r}")
        seen_ids.add(oid)
        for k in ("name", "title", "peer"):
            c.req(o, k, w, _str, "string")
        c.req(o, "sworn", w, _bool, "bool")
        for k in ("base", "ot", "other", "total"):
            c.req(o, k, w, _num, "number")
        c.req(o, "otr", w, _opt(_num), "number or null")
        cpdp = c.req(o, "cpdp", w, _opt(_int), "int or null")
        for k in ("cmp", "cmp_all", "sus"):
            c.req(o, k, w, _opt(_int), "int or null")
        c.req(o, "law", w, _opt(_num), "number or null")
        c.req(o, "law_n", w, _opt(_int), "int or null")
        for k in ("unit", "unit_desc", "dist", "badge"):
            c.req(o, k, w, _opt(_str), "string or null")
        z = c.req(o, "z", w, _list, "array") or []
        pct = c.req(o, "pct", w, _list, "array") or []
        for name, arr in (("z", z), ("pct", pct)):
            if len(arr) != n:
                c.fail(f"{w}.{name}", f"expected length {n}, got {len(arr)}")
            if not all(x is None or _num(x) for x in arr):
                c.fail(f"{w}.{name}", "entries must be number or null")
        fs = c.req(o, "fs", w, _list, "array") or []
        if not all(x in metrics for x in fs):
            c.fail(w + ".fs", f"entries must be in metrics {metrics}")
        ff = c.req(o, "ff", w, _list, "array") or []
        if not all(x in FLAG_KEYS for x in ff):
            c.fail(w + ".ff", f"entries must be in {sorted(FLAG_KEYS)}")
        # unmatched rule: CPDP-derived fields null (SCHEMA.md)
        if cpdp is None:
            for k in ("cmp", "cmp_all", "sus", "unit", "dist"):
                if o.get(k) is not None:
                    c.fail(f"{w}.{k}", "must be null when cpdp is null")
            for idx, m in enumerate(metrics):
                if m == "cmp" and idx < len(z) and z[idx] is not None:
                    c.fail(f"{w}.z[{idx}]", f"{m} z must be null when cpdp is null")
            if o.get("law_cpdp") is not None:
                c.fail(f"{w}.law_cpdp", "must be null when cpdp is null")

    # districts
    districts = c.req(data, "districts", "root", _list, "array") or []
    for i, d in enumerate(districts):
        w = f"districts[{i}]"
        c.req(d, "num", w, _str, "string")
        c.req(d, "label", w, _str, "string")
        c.req(d, "path", w, _str, "string")
        c.req(d, "lx", w, _num, "number")
        c.req(d, "ly", w, _num, "number")
        c.req(d, "members", w, _int, "int")
        c.req(d, "flagged", w, _int, "int")
        for k in ("copa", "bia"):
            arr = c.req(d, k, w, _list, "array") or []
            for j, pair in enumerate(arr):
                if not (_list(pair) and len(pair) == 2 and _int(pair[0]) and _int(pair[1])):
                    c.fail(f"{w}.{k}[{j}]", "expected [int year, int count]")
    return c.errs


class SchemaTests(unittest.TestCase):
    def test_validator_rejects_invalid(self):
        self.assertTrue(validate({}))
        self.assertTrue(validate({"meta": 1}))
        self.assertTrue(validate([]))

    def _check_file(self, path):
        if not path.exists():
            self.skipTest(f"{path.relative_to(ROOT)} not present")
        errs = validate(json.loads(path.read_text()))
        self.assertEqual(errs, [], "\n".join(errs[:20]))

    def test_sample_fixture(self):
        self._check_file(ROOT / "tests" / "fixtures" / "sample.json")

    def test_site_data(self):
        self._check_file(ROOT / "site" / "data.json")

    def test_mutated_sample_fails(self):
        p = ROOT / "tests" / "fixtures" / "sample.json"
        if not p.exists():
            self.skipTest("tests/fixtures/sample.json not present")
        d = json.loads(p.read_text())
        d["officers"][0]["z"] = d["officers"][0]["z"][:-1]
        self.assertTrue(validate(d))


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else ROOT / "site" / "data.json"
    errs = validate(json.loads(path.read_text()))
    for e in errs[:50]:
        print(e)
    if len(errs) > 50:
        print(f"... {len(errs) - 50} more")
    print(f"{path}: {'OK' if not errs else f'{len(errs)} error(s)'}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
