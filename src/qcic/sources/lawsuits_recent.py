"""City DOL CPD Annual Litigation Reports (consent decree par. 548), 2019-latest.
Appendix A (settled) + B (litigated) tables -> data/raw/lawsuits_recent.json.
Stdlib + lazy `pdfplumber` (not stdlib; system-installed; no pip done by this repo).
Run: python3 -m src.qcic.sources.lawsuits_recent [--keep-pdf]
"""
import json, os, re, sys, urllib.request, urllib.parse, ssl

INDEX = "https://www.chicago.gov/city/en/depts/dol/supp_info/CPDAnnLitReports.html"
BASE = "https://www.chicago.gov"
RAW = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "raw")
UA = {"User-Agent": "Mozilla/5.0 (cpd-qcic research)"}
NONOFFICER = re.compile(r"^(city of chicago|the city|chicago police department|cpd|unknown|unidentified|john doe|jane doe|doe|respondents?|et al|none|n/a|defendants dismissed)", re.I)


def _get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=120).read()


def pdf_links():
    """[(label, abs_url)] for report + appendix PDFs found on the index page."""
    html = _get(INDEX).decode("utf8", "replace")
    out = []
    for h in re.findall(r'href="([^"]*CPDLitigationReports[^"]*\.pdf)"', html):
        u = BASE + urllib.parse.quote(urllib.parse.unquote(h)) if h.startswith("/") else h
        out.append(u)
    return list(dict.fromkeys(out))


def money(s):
    m = re.sub(r"[^\d.]", "", s or "")
    try:
        return float(m)
    except ValueError:
        return None


RANK = r"(?:detective|officer|sergeant|sgt\.?|lieutenant|lt\.?|supervisor|commander|captain|police officer|po)"


def split_names(cell):
    """-> (names, badges). Handles 'A B, #123; C D. City of Chicago', 'A B, Detective, Star No. 5; ...', 'A, B and C'."""
    t = re.sub(r"\s+", " ", (cell or "").replace("\n", " ")).strip()
    badges = re.findall(r"(?:#|star no\.?\s*)(\d{1,6})", t, flags=re.I)
    t = re.sub(r"\(?\s*(?:#|star no\.?)\s*\d+\s*\)?,?", ";", t, flags=re.I)
    if ";" in t or re.search(RANK + r",", t, re.I):
        parts = re.split(r";\s*|\.\s+(?=[A-Z])", t)
        parts = [re.split(r",\s*(?:" + RANK + r"|#|star)", q, flags=re.I)[0] for q in parts]
    else:
        t = re.sub(r"\(#?\d+\)", "", t)
        parts = re.split(r",\s*(?:and\s+)?|\s+and\s+", t)
    names = []
    for q in parts:
        q = re.sub(r"^" + RANK + r"\s+", "", q.strip(), flags=re.I).strip(" .,")
        q = re.sub(r"^and\s+", "", q)
        q = re.sub(r"\s*\((?:ret|resigned|retired)[^)]*\)?", "", q, flags=re.I)
        q = re.sub(r"\s+(?:chicago police (?:officer|detective)|police officer|p\.?o\.?|sgt|det|officer|star|individually)\.?$", "", q, flags=re.I).strip(" .,/")
        if len(q) < 4 or q.lower() in ("individually", "star", "box", "sgt", "det"):
            continue
        if q and not NONOFFICER.match(q) and not q.startswith('"'):
            names.append(q.title() if q.isupper() else q)
    return names, badges


def parse_pdf(path, url):
    import pdfplumber  # lazy: only non-stdlib dependency
    recs = []
    hdr = None  # header persists across pages (continuation pages have none)
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for tb in page.extract_tables():
                for row in tb:
                    cells = [(c or "").replace("\n", " ") for c in row]
                    j = " ".join(cells).lower()
                    if "case number" in j and "defendants" in j:
                        hdr = [c.lower() for c in cells]
                        continue
                    if hdr is None or len(cells) != len(hdr):
                        continue

                    def col(*keys):
                        for i, h in enumerate(hdr):
                            if all(k in h for k in keys):
                                return cells[i]
                        return ""
                    case_no = re.sub(r"\s+", " ", col("case number")).strip()
                    if not case_no:
                        continue
                    amt = col("total amount") or col("settlement amount") or col("settlment amount")
                    settled = bool(amt) or any("settl" in h for h in hdr)
                    if settled:
                        pay = money(amt.split("(")[0])
                        date = (col("settlement date") or col("settlment date")
                                or col("date of stipulation") or col("date of final order"))
                    else:
                        pay = money(col("total of compensatory"))
                        if pay is None:
                            pay = (money(col("amount awarded")) or 0.0) + (money(col("amount of award")) or 0.0)
                        date = col("date of judgment") or col("date of final order")
                    my = re.search(r"(\d{4})-\d{2}-\d{2}|\d{1,2}/\d{1,2}/(\d{4})", date or "")
                    names, badges = split_names(col("defendants"))
                    recs.append({
                        "case_no": case_no,
                        "year": int(my.group(1) or my.group(2)) if my else None,
                        "payout": pay,
                        "officers": names,
                        "badges": badges,
                        "defendants_raw": re.sub(r"\s+", " ", col("defendants")).strip(),
                        "source_url": url,
                        "kind": "settled" if settled else "litigated",
                        "case_name": re.sub(r"\s+", " ", col("case name")).strip(),
                        "category": col("case category").strip(),
                        "incident_date": col("underlying").strip(),
                        "disposition": col("final disposition").strip(),
                    })
    return recs


def fetch(keep_pdf=False):
    os.makedirs(RAW, exist_ok=True)
    pdfdir = os.path.join(RAW, "dol_pdfs")
    os.makedirs(pdfdir, exist_ok=True)
    allrecs = []
    for u in pdf_links():
        name = urllib.parse.unquote(u.rsplit("/", 1)[1])
        if re.search(r"flyer|faq|updates to report|Watts", name, re.I):
            continue
        p = os.path.join(pdfdir, re.sub(r"[^\w.-]", "_", name))
        if not os.path.exists(p):
            open(p, "wb").write(_get(u))
        try:
            r = parse_pdf(p, u)
        except Exception as e:
            print("skip", name, e, file=sys.stderr)
            continue
        print(len(r), name)
        allrecs += r
    # dedupe: amended reports supersede; key = case_no+kind+year
    seen = {}
    for r in allrecs:
        seen[(r["case_no"], r["kind"], r["year"])] = r
    out = sorted(seen.values(), key=lambda r: (r["year"] or 0, r["case_no"]))
    json.dump(out, open(os.path.join(RAW, "lawsuits_recent.json"), "w"), indent=1)
    print("records", len(out))
    return out


if __name__ == "__main__":
    fetch("--keep-pdf" in sys.argv)
