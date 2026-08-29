"""Read a MacroFactor .xlsx export without assuming what is in it.

The repo carried this as a known gap for a reason: no export had ever been
seen, so an importer written in advance would have been guessing at column
names. This one discovers them — sheet names from the workbook, headers from
row 1, and date columns from the number formats in styles.xml rather than from
what the header happens to be called.

Standard library only. openpyxl is not installed and an .xlsx is a zip of XML,
so there is no reason to add a dependency for this.

Output goes to private/, which is gitignored. This repo is public: a series of
someone's daily energy expenditure is not something to publish by accident.

  python3 scripts/import_macrofactor.py <export.xlsx> [--person philipp]
"""

import datetime
import json
import os
import re
import sys
import zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.join(BASE, "..", "private", "macrofactor")
EPOCH = datetime.date(1899, 12, 30)          # Excel's, with its 1900 leap bug
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
BUILTIN_DATE_FMTS = set(range(14, 23)) | set(range(45, 48))


def strip_ns(tag):
    return tag.split("}")[-1]


def shared_strings(z):
    try:
        raw = z.read("xl/sharedStrings.xml").decode("utf-8")
    except KeyError:
        return []
    return [re.sub(r"<[^>]+>", "", si) for si in
            re.findall(r"<si>(.*?)</si>", raw, re.S)]


def date_styles(z):
    """Which cell-style indexes mean 'this is a date'."""
    try:
        raw = z.read("xl/styles.xml").decode("utf-8")
    except KeyError:
        return set()
    custom = set()
    for fid, code in re.findall(r'<numFmt numFmtId="(\d+)" formatCode="([^"]*)"', raw):
        if re.search(r"[yYdD]", code) and "General" not in code:
            custom.add(int(fid))
    m = re.search(r"<cellXfs[^>]*>(.*?)</cellXfs>", raw, re.S)
    if not m:
        return set()
    out = set()
    for i, xf in enumerate(re.findall(r"<xf\b[^>]*>", m.group(1))):
        fid = re.search(r'numFmtId="(\d+)"', xf)
        if fid and (int(fid.group(1)) in BUILTIN_DATE_FMTS or int(fid.group(1)) in custom):
            out.add(i)
    return out


def sheets(z):
    wb = z.read("xl/workbook.xml").decode("utf-8")
    rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    target = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
    found = []
    for rid, name in re.findall(r'<sheet name="([^"]+)" sheetId="\d+" r:id="([^"]+)"/>', wb):
        found.append((rid, name))
    if not found:                     # attribute order is not guaranteed
        for tag in re.findall(r"<sheet\b[^>]*/>", wb):
            n = re.search(r'name="([^"]+)"', tag)
            r = re.search(r'r:id="([^"]+)"', tag)
            if n and r:
                found.append((n.group(1), r.group(1)))
    out = []
    for name, rid in found:
        path = target.get(rid, "")
        if path and not path.startswith("xl/"):
            path = "xl/" + path.lstrip("/")
        if path in z.namelist():
            out.append((name, path))
    return out


def read_sheet(z, path, strings, datestyles):
    raw = z.read(path).decode("utf-8")
    rows = []
    for body in re.findall(r"<row\b[^>]*>(.*?)</row>", raw, re.S):
        cells = {}
        for cell in re.findall(r"<c\b[^>]*/?>(?:.*?</c>)?", body, re.S):
            ref = re.search(r'r="([A-Z]+)(\d+)"', cell)
            if not ref:
                continue
            col = ref.group(1)
            typ = re.search(r't="(\w+)"', cell)
            sty = re.search(r's="(\d+)"', cell)
            val = re.search(r"<v>([^<]*)</v>", cell)
            if val is None:
                continue
            v, t = val.group(1), (typ.group(1) if typ else "n")
            if t == "s":
                v = strings[int(v)] if v.isdigit() and int(v) < len(strings) else v
            elif t in ("n", "") and sty and int(sty.group(1)) in datestyles:
                try:
                    v = (EPOCH + datetime.timedelta(days=int(float(v)))).isoformat()
                except (ValueError, OverflowError):
                    pass
            else:
                try:
                    v = float(v)
                    if v == int(v):
                        v = int(v)
                except ValueError:
                    pass
            cells[col] = v
        rows.append(cells)
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = dict(a.split("=", 1) if "=" in a else (a, True)
                 for a in sys.argv[1:] if a.startswith("--"))
    if not args:
        print(__doc__)
        return 1
    src = args[0]
    person = flags.get("--person") or "philipp"
    if "--person" not in flags:
        print("No --person given, assuming %r. Pass --person=eunice if that is wrong.\n"
              % person)

    z = zipfile.ZipFile(src)
    strings, datestyles = shared_strings(z), date_styles(z)
    out_dir = os.path.join(OUT_ROOT, person)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    written = 0
    for name, path in sheets(z):
        rows = read_sheet(z, path, strings, datestyles)
        if not rows:
            print("  %-18s empty, skipped" % name)
            continue
        header = rows[0]
        cols = [header[k] for k in sorted(header)]
        records = []
        for r in rows[1:]:
            rec = {}
            for k in sorted(r):
                label = header.get(k, k)
                rec[str(label)] = r[k]
            if rec:
                records.append(rec)

        fname = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") + ".json"
        payload = {
            "_source": os.path.basename(src),
            "_imported": datetime.date.today().isoformat(),
            "_note": "Written by scripts/import_macrofactor.py. private/ is gitignored "
                     "because this repo is public.",
            "person": person, "sheet": name, "columns": cols, "rows": records,
        }
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        written += 1

        print("  %-18s %4d rows  columns: %s" % (name, len(records), ", ".join(map(str, cols))))
        dates = [r.get(cols[0]) for r in records if isinstance(r.get(cols[0]), str)]
        if dates:
            print("  %-18s %s to %s" % ("", min(dates), max(dates)))
        for c in cols[1:]:
            nums = [r[c] for r in records if isinstance(r.get(c), (int, float))]
            if nums:
                print("  %-18s %s: min %.0f, max %.0f, latest %.0f"
                      % ("", c, min(nums), max(nums), nums[-1]))
        print("  %-18s -> private/macrofactor/%s/%s" % ("", person, fname))

    print("\n%d sheet(s) imported." % written)
    return 0


if __name__ == "__main__":
    sys.exit(main())
