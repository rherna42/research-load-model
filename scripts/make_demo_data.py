"""Generate the synthetic dataset the published demo runs on.

Department names and the house-list journals are real, because they are public
facts about a college and useful to see in a demo. The faculty are not: no real
person's record is copied, sampled, or derivable from anything here. Faculty are invented,
then given publication histories by drawing from plausible marginal
distributions: most business-school output sits in unrated outlets, a thin tail
reaches ABDC A and A*, and a handful of people publish nothing in a six-year
window. Re-run it and you get the same data, because the seed is fixed.
"""
import json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data")
SEED = 7

DEPTS = {                       # real department names and sizes; the people are not real
    "Accounting": ("ACC", 11), "CISBA": ("CIS", 9), "Economics": ("ECO", 7),
    "Finance": ("FIN", 7), "Management": ("MGT", 14), "Marketing": ("MKT", 15),
}
RANKS = [("Assistant Professor", .22), ("Associate Professor", .31), ("Full Professor", .47)]

# House-list journals: the real unrated outlets a business school publishes in
# repeatedly. The journals are real. The article counts against them are not.
HOUSE = [
         "Journal of Business Leadership",
         "Journal of Marketing Development and Competitiveness",
         "Small Business Institute Journal",
         "Journal of Higher Education Theory and Practice",
         "American Journal of Management",
         "Journal of Leadership, Accountability and Ethics",
         "Journal of Finance and Accountancy",
         "Journal of Business Diversity",
         "Journal of Management Policy and Practice",
         "Journal of Ethical and Legal Issues",
         "IUP Journal of International Relations",
         "Journal of Strategic Innovation and Sustainability",
         "\"Anveshak\" International Journal of Management",
         "Academy of Business Education Journal"
]

# Per-item tier draw. "other" dominates, mirroring the shape of real
# business-school output rather than any particular college's numbers.
TIERS = [("A*", .013), ("A", .056), ("B", .107), ("C", .084), ("other", .740)]

def pick(rng, table):
    r = rng.random(); c = 0
    for v, p in table:
        c += p
        if r < c: return v
    return table[-1][0]

def main():
    rng = random.Random(SEED)
    people = []
    for dept, (abbr, n) in DEPTS.items():
        for i in range(1, n + 1):
            rank = pick(rng, RANKS)
            # productivity is heavy tailed: a long quiet middle, a few prolific authors
            base = {"Assistant Professor": 3.2, "Associate Professor": 5.4, "Full Professor": 6.6}[rank]
            k = max(0, round(rng.lognormvariate(0.0, 0.72) * base))
            if rng.random() < .05: k = rng.randint(0, 1)
            if rng.random() < .05: k = rng.randint(18, 27)
            pubs = []
            for _ in range(k):
                y = rng.choices(range(2021, 2027), weights=[.14,.19,.16,.17,.19,.15])[0]
                tier = pick(rng, TIERS)
                proc = rng.random() < .26
                # Almost no conference proceeding is on the ABDC list.
                if proc and rng.random() < .96: tier = "other"
                # An ABDC-listed proceeding is a peer-reviewed journal outlet: it carries
                # the ABDC points and counts toward SA. An unlisted one never counts toward SA.
                rec = {"y": y, "r": tier, "t": "p" if (proc and tier == "other") else "j"}
                if tier == "other" and not proc and rng.random() < .64:
                    rec["h"] = rng.randrange(len(HOUSE))
                if rng.random() < .045: rec["f"] = 1
                pubs.append(rec)
            pubs.sort(key=lambda p: -p["y"])
            # Letters, not numbers. Real builds use ACC-01; the demo uses ACC-A, so a
            # demo code can never be mistaken for a real person's code.
            tag = chr(ord("A") + i - 1) if i <= 26 else f"A{i-26}"
            people.append({"id": f"{abbr}-{tag}", "dept": dept, "rank": rank, "pubs": pubs})
    people.sort(key=lambda p: p["id"])

    counts, authors = {}, {}
    for p in people:
        for it in p["pubs"]:
            if "h" in it:
                counts[it["h"]] = counts.get(it["h"], 0) + 1
                authors.setdefault(it["h"], set()).add(p["id"])
    house = [[h, counts.get(i, 0), len(authors.get(i, set()))] for i, h in enumerate(HOUSE)]

    os.makedirs(OUT, exist_ok=True)
    json.dump(people, open(os.path.join(OUT, "demo_data.json"), "w"), separators=(",", ":"))
    json.dump(house, open(os.path.join(OUT, "demo_house.json"), "w"), indent=1)
    items = sum(len(p["pubs"]) for p in people)
    print(f"{len(people)} synthetic faculty, {items} items, "
          f"{sum(counts.values())} on the house list -> {OUT}")

if __name__ == "__main__":
    main()
