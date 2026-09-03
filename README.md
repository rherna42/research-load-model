# Research Load Model

An interactive model for the argument every business school eventually has: how
much research output should buy a course release, and who currently clears the bar.

Each faculty member is a dot, placed on a points axis by their publications over a
rolling six-year window. Shaded regions are teaching-load bands. You set what an
A\*, A, B, C, or unrated article is worth, you set where the band boundaries fall,
and the room re-sorts itself.

**[Open it](index.html)** — 63 real tenure-line faculty at one business school, 392
publications from 2021 on. Names and departments are both stripped. Each person is a
bare code and a rank.

## What it does

- **Weights by rating.** Points per article for A\*, A, B, C, and unrated, from the
  ABDC Journal Quality List in force at the article's publication year. A proceeding
  in a listed outlet is treated as a peer-reviewed journal article, for points and for
  the Scholarly Academic floor alike; an unlisted one earns points but never SA.
- **Bands with movable cutoffs.** Four loads, from 4/4 up to 3/3 plus a stipend.
  Type the thresholds or drag them on the chart.
- **A Scholarly Academic floor.** Set a minimum number of journal articles in the
  window. Optionally hold anyone below it at the heaviest load regardless of points.
- **A house list.** Name the unrated journals your faculty publish in repeatedly and
  score them as C, individually toggleable. This is usually the argument that matters.
- **Unrated for SA only.** Let unrated articles keep somebody Scholarly Academic
  while earning no points toward a release. Staying qualified and earning a release
  are different questions.
- **Three views.** A combined swarm, small multiples by rank, and a sortable
  table with the full tier breakdown.

## Why the unrated weight is the whole model

Most business-school output sits in journals no rating list covers. In the college
this was built for, three quarters of the six-year window was unrated. Whatever you
set that number to decides who earns a release. At one point per article, a
high-volume author in unrated outlets outscores a colleague with two A-level papers.

"Unrated" is also not one thing. It mixes practitioner outlets, journals a rating
list simply does not cover, and journals whose name in a CV was too imprecise to
match. Giving them all the same number is a claim the data cannot support. The
house list exists to break that apart.

## Running it on your own data

The page is self-contained. To point it at your own faculty:

```bash
python3 scripts/build_model.py "YourExport.doc" \
    --jql "ABDC-JQL.xlsx" \
    --overrides overrides.json \
    --out private/

python3 scripts/build_page.py private/data.json private/house.json -o private.html
```

`private/` and `private.html` are gitignored. So is `overrides.json`, and so is the
name crosswalk the build writes. **Nothing derived from real records should ever be
committed.**

### Input format

If you are not coming from a Watermark export, skip the parser and write
`data.json` yourself. One object per person:

```json
[
  {
    "id": "MKT-04",
    "rank": "Associate Professor",
    "pubs": [
      {"y": 2025, "r": "B",     "t": "j"},
      {"y": 2024, "r": "other", "t": "j", "h": 0},
      {"y": 2026, "r": "other", "t": "p", "f": 1}
    ]
  }
]
```

| field | meaning |
|---|---|
| `id` | display code. Use a code, not a name. |
| `rank` | drives the dot colour and the facet view |
| `r` | `A*`, `A`, `B`, `C`, or `other` |
| `t` | `j` journal article, `p` proceedings or chapter |
| `h` | index into `house.json`, when the outlet is on the house list |
| `f` | `1` if in press, dated to the current year |

`house.json` is `[["Journal name", article_count, distinct_author_count], ...]`.

### Overrides

`overrides.json` carries hand corrections: items filed under the wrong person,
conference papers the classifier read as journal articles, outlets a citation
buries after the title, and the house list itself. It holds real names, so it is
gitignored. `overrides.example.json` shows the shape.

## The Watermark parser, and when not to trust it

Watermark exports separate Journal Articles from Peer Reviewed Proceedings with a
subsection header. Some report templates drop that header, and then conference
papers run on under Journal Articles with nothing marking the break. That is not
cosmetic: it inflates journal-article counts, which is exactly what the Scholarly
Academic floor is built on.

`scripts/classify.py` recovers the split from two signals: the double blank line
where the missing header used to sit, and a conference, city, or book publisher in
the outlet. Requiring both scored 96% precision and 100% recall when tested against
an export of the same faculty whose headers were intact.

That is good, not good enough to leave alone. Read what it classified. If your
export has the headers, you do not need any of this.

## Handling real data

A build carrying real records is personnel material, whatever the dots are labelled.
A code and a rank still leave an exact publication profile on screen, which is enough
for a colleague at the same school to place the more prolific people. Keep the
crosswalk out of version control, and remember the page assigns each person a teaching
load: that is a model output and an argument worth having, not a decision anyone made.

## Layout

```
index.html                 built and committed so it can be served
template.html              the page, with data placeholders
data/faculty.json          published data: code, rank, publications. No names, no departments
data/house.json            the house-list journals and their counts
scripts/
  build_page.py            folds a dataset into the template
  make_public_data.py      strips department and reassigns neutral codes
  build_model.py           Watermark export -> de-identified dataset
  parse_vita.py            splits an export into faculty and their entries
  classify.py              journal article vs proceedings
  journal.py               pulls the outlet name out of a citation
  abdc.py                  ABDC lookup, by the list in force at publication
overrides.example.json     shape of the hand-correction file
```

## Requirements

Python 3.9+ and `openpyxl` for the pipeline. The page itself is one self-contained
HTML file with no build step and no dependencies.

```bash
pip install openpyxl
```

`build_model.py` shells out to `textutil`, which is macOS only. On Linux, convert
the export to text yourself and adapt `to_text()`.

## Licence

MIT.
