"""Strip a private build down to what can be published.

Takes the de-identified-but-still-departmental data the model produces, replaces
each department with a single opaque letter, and reassigns codes so nothing about
the new code hints at the old one.

  python3 scripts/make_public_data.py private/data.json private/crosswalk.csv

Writes:
  data/faculty.json        publishable: code, department letter, rank, publications
  public_crosswalk.csv     code -> name. Gitignored. Never commit it.

Departments survive as bare letters so the dots can still be grouped and coloured,
but "K" says nothing to a reader without the key. Numbering is shuffled within each
department with a fixed seed, so a public code is not just a relabelled internal one
and stays stable across rebuilds.
"""
import argparse, csv, json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED = 4108

LETTER = {
    "Accounting": "A",
    "CISBA": "C",
    "Economics": "E",
    "Finance": "F",
    "Management": "G",
    "Marketing": "K",
}


def main(a):
    people = json.load(open(a.data, encoding="utf-8"))
    names = {}
    if a.crosswalk and os.path.exists(a.crosswalk):
        for r in csv.DictReader(open(a.crosswalk, encoding="utf-8")):
            names[r["code"]] = r["name"]

    unknown = sorted({p["dept"] for p in people if p["dept"] not in LETTER})
    if unknown:
        raise SystemExit(f"no letter assigned for: {unknown}. Add them to LETTER.")

    groups = {}
    for p in sorted(people, key=lambda x: x["id"]):
        groups.setdefault(p["dept"], []).append(p)

    rng = random.Random(SEED)
    out, cross = [], []
    for dept in sorted(groups):
        members = groups[dept]
        slots = list(range(1, len(members) + 1))
        rng.shuffle(slots)
        for person, n in zip(members, slots):
            code = f"{LETTER[dept]}-{n:02d}"
            out.append({"id": code, "dept": LETTER[dept],
                        "rank": person["rank"], "pubs": person["pubs"]})
            cross.append([code, names.get(person["id"], ""), person["id"],
                          dept, person["rank"]])
    out.sort(key=lambda p: p["id"])

    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "data", "faculty.json"), "w"),
              separators=(",", ":"))

    cw = os.path.join(ROOT, "public_crosswalk.csv")
    with open(cw, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["public_code", "name", "internal_code", "department", "rank"])
        for row in sorted(cross):
            w.writerow(row)

    leaked = sorted({k for p in out for k in p} - {"id", "dept", "rank", "pubs"})
    if leaked:
        raise SystemExit(f"unexpected field survived: {leaked}")
    spelled = sorted({p["dept"] for p in out} - set(LETTER.values()))
    if spelled:
        raise SystemExit(f"a department name survived unlettered: {spelled}")

    print(f"{len(out)} people, {sum(len(p['pubs']) for p in out)} items")
    print("  " + ", ".join(f"{LETTER[d]}={len(groups[d])}" for d in sorted(groups)))
    print(f"crosswalk -> {cw}   (gitignored, keep it local)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("data", help="the private data.json the model built")
    p.add_argument("crosswalk", nargs="?", help="its code-to-name crosswalk")
    main(p.parse_args())
