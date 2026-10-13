import io
import unittest
from xml.sax.saxutils import escape
import zipfile

from src.qcic.sources import payments_dol as p

SS = ["junk preamble", "CASE # ", "PAYEE", "PAYMENT AMOUNT", "FEES & COSTS", "PRIMARY CAUSE",
      "CITY DEPARTMENT ", "DISPOSITION", "DATE TO COMPTROLLER", "18 C 1028", "Doe, John", "Excessive Force",
      "Police ", "Settlement", "19 L 5", "Roe", "Streets", "$1,234.50"]


def _xlsx():
    def s(r, c, i):
        return f'<c r="{c}{r}" t="s"><v>{i}</v></c>'
    rows = ['<row r="1">' + s(1, "A", 0) + "</row>",
            '<row r="5">' + "".join(s(5, c, i) for c, i in zip("ABCDEFGH", range(1, 9))) + "</row>"]
    rows.append('<row r="6">' + s(6, "A", 9) + s(6, "B", 10) + '<c r="C6"><v>5000</v></c><c r="D6"><v>250.5</v></c>'
                + s(6, "E", 11) + s(6, "F", 12) + s(6, "G", 13) + '<c r="H6"><v>46000</v></c></row>')
    rows.append('<row r="7">' + s(7, "A", 14) + s(7, "B", 15) + '<c r="C7"><v>9</v></c>' + s(7, "F", 16) + "</row>")
    rows.append('<row r="8">' + s(8, "A", 9) + s(8, "B", 10) + s(8, "C", 17)
                + '<c r="E8" t="inlineStr"><is><t>Other</t></is></c>' + s(8, "F", 12) + '<c r="H8"><v>46001</v></c></row>')
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("xl/sharedStrings.xml", f"<sst {ns}>" + "".join(f"<si><t>{t}</t></si>" for t in map(escape, SS)) + "</sst>")
        z.writestr("xl/workbook.xml", f'<workbook {ns} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                   '<sheets><sheet name="Summary" sheetId="1" r:id="rId1"/><sheet name="A" sheetId="2" r:id="rId2"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Target="worksheets/sheet2.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", f"<worksheet {ns}><sheetData/></worksheet>")
        z.writestr("xl/worksheets/sheet2.xml", f"<worksheet {ns}><sheetData>" + "".join(rows) + "</sheetData></worksheet>")
    return b.getvalue()


class T(unittest.TestCase):
    def test_parse(self):
        rows = p.parse_xlsx(_xlsx())
        self.assertEqual(len(rows), 2)
        a, b = rows
        self.assertEqual((a["case_no"], a["key"], a["payee"], a["amount"], a["fees"]), ("18 C 1028", "18-1028", "Doe, John", 5000.0, 250.5))
        self.assertEqual((a["date"], a["year"], a["cause"], a["disposition"]), ("2025-12-09", 2025, "Excessive Force", "Settlement"))
        self.assertEqual((b["amount"], b["fees"], b["date"], b["cause"]), (1234.5, None, "2025-12-10", "Other"))

    def test_helpers(self):
        self.assertEqual(p.money("$1,234.50"), 1234.5)
        self.assertEqual(p.to_date(46000), "2025-12-09")
        self.assertEqual(p.to_date("12/31/2025"), "2025-12-31")
        r = {"case_no": "x", "date": "d", "amount": 1.0, "fees": 0.0}
        self.assertEqual(len(p.dedupe([r, dict(r)])), 1)

    def test_links(self):
        h = ('<a href="/content/dam/x/2025/Finance%20Cmte%202025%20JS%20through%2012.31.25.xlsx">'
             '<a href="/content/dam/x/2026/Finance%20Cmte%202026%20JS%20through%208.31.26.xlsx">'
             '<a href="/content/dam/x/2026/Finance%20Cmte%202026%20JS%20through%207.31.26.xlsx">'
             '<a href="/content/dam/x/2023/Finance%20Cmte%202023%20JS%20through%2012.31.23.xlsx">')
        L = p.pick_links(h)
        self.assertEqual(len(L), 2)
        self.assertIn("8.31.26", L[1])


if __name__ == "__main__":
    unittest.main()
