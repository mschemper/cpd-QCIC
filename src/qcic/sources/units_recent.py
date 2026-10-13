"""Unit/district per active CPD member from the Nov-2023 FOIA roster (Invisible Institute repo).
fetch() -> data/raw/units_recent.json {key: {unit, unit_desc, as_of, source}}.
Keys: CPDP officer_id ("1234", unique name+birth_year match to final-profiles.csv) and "star:NNNN" (every active member).
Run: python3 -m src.qcic.sources.units_recent
"""
import csv, collections, gzip, io, json, os, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RAW = os.path.join(ROOT, "data", "raw")
NAME = "roster_1985-2023_2023-11_p891976"
URL = ("https://raw.githubusercontent.com/invinst/chicago-police-data/master/individual/"
       f"{NAME}/export/output/{NAME}.csv.gz")
AS_OF = "2023-11"
SOURCE = "invinst/chicago-police-data " + NAME


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "cpd-qcic"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def _unit(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def fetch(out=None):
    out = out or os.path.join(RAW, "units_recent.json")
    rows = list(csv.DictReader(io.StringIO(gzip.decompress(_get(URL)).decode("utf-8-sig"))))
    prof = collections.defaultdict(list)
    pp = os.path.join(RAW, "cpdp", "final-profiles.csv")
    if os.path.exists(pp):
        for p in csv.DictReader(open(pp, newline="", encoding="utf-8")):
            if p["current_status"] == "1":
                prof[(p["first_name"].upper(), p["last_name"].upper(), p["birth_year"][:4])].append(p["officer_id"])
    res, n_act, n_id, n_star = {}, 0, 0, 0
    for r in rows:
        if r["status"] != "Y" or _unit(r["unit"]) is None:
            continue
        n_act += 1
        rec = {"unit": _unit(r["unit"]), "unit_desc": r["unit_description"].title() if False else r["unit_description"],
               "as_of": AS_OF, "source": SOURCE}
        star = _unit(r["star1"])
        if star:
            res["star:%d" % star] = rec
            n_star += 1
        ids = prof.get((r["first_name"].upper(), r["last_name"].upper(), r["birth_year"][:4]), [])
        if len(ids) == 1:
            res[ids[0]] = rec
            n_id += 1
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=0)
    print("active with unit %d; keyed by officer_id %d; by star %d; -> %s" % (n_act, n_id, n_star, out))
    return res


if __name__ == "__main__":
    fetch()
