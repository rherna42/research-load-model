"""Turn a Watermark vita export into the dashboard's dataset.

  python3 scripts/build_model.py export.doc --jql ABDC-JQL.xlsx --out private/

Reads the export, keeps tenure-line faculty, pulls their journal-article
entries inside the window, works out the outlet and its ABDC rating, and
writes de-identified data plus a name crosswalk.

The crosswalk never enters the repository. Codes are pinned to it across runs,
so a code keeps meaning the same person from one export to the next.

Hand corrections live in overrides.json, which is gitignored because it
contains real names and citations. See overrides.example.json for the shape.
"""
import argparse, csv, json, os, re, subprocess, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify import classify, cite_key
from journal import outlet
from parse_vita import TL
import abdc

WINDOW_START, FORTHCOMING_YEAR = 2021, 2026
ABBR_FALLBACK = lambda d: re.sub(r'[^A-Z]', '', d.title())[:3] or d[:3].upper()

def norm(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode()
    s = s.lower().replace('&', ' and ')
    s = re.sub(r'^(the)\s+', '', s); s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def load_overrides(path):
    d = {"drop": [], "as_proceedings": [], "dept_fix": {}, "journal_fix": {},
         "dept_abbr": {}, "house": [], "merge": {}}
    if path and os.path.exists(path):
        d.update(json.load(open(path, encoding='utf-8')))
    return d

def to_text(doc, workdir):
    out = os.path.join(workdir, '.vita.txt')
    subprocess.run(['textutil', '-convert', 'txt', '-output', out, doc], check=True)
    return out

def assign_codes(roster, crosswalk_path, abbr):
    have = {}
    if crosswalk_path and os.path.exists(crosswalk_path):
        for r in csv.DictReader(open(crosswalk_path, encoding='utf-8')):
            have[r['name']] = r['code']
    used = {}
    for c in have.values():
        d, n = c.rsplit('-', 1); used.setdefault(d, set()).add(int(n))
    out = {f['name']: have[f['name']] for f in roster if f['name'] in have}
    for f in roster:
        if f['name'] in out: continue
        d = abbr.get(f['dept']) or ABBR_FALLBACK(f['dept'])
        s = used.setdefault(d, set()); n = 1
        while n in s: n += 1
        s.add(n); out[f['name']] = f'{d}-{n:02d}'
    return out

def main(a):
    ov = load_overrides(a.overrides)
    os.makedirs(a.out, exist_ok=True)
    jql = abdc.load(a.jql) if a.jql else {}
    txt = to_text(a.export, a.out)

    roster, rows = [], []
    for name, v in classify(txt).items():
        if v['rank'] not in TL: continue
        dept = ov['dept_fix'].get(name, v['dept'])
        roster.append({'name': name, 'dept': dept, 'rank': v['rank']})
        for it in v['items']:
            y, fwd = it['year'], it['year'] is None
            if not (fwd or y >= a.window_start): continue
            cite = it['cite']
            if any(d['name'] == name and d['match'] in cite for d in ov['drop']): continue
            jn = outlet(cite)
            for frag, real in ov['journal_fix'].items():
                if frag in cite: jn = real
            proc = it['proc'] or any(p in cite for p in ov['as_proceedings'])
            rating = '' if proc else abdc.rate(jql, jn, y)[0]
            rows.append({'name': name, 'dept': dept, 'rank': v['rank'],
                         'year': FORTHCOMING_YEAR if fwd else y, 'fwd': fwd,
                         'journal': jn, 'rating': rating,
                         'itype': 'proceedings/other' if proc else 'journal', 'cite': cite})
    os.remove(txt)

    cross = os.path.join(a.out, 'crosswalk.csv')
    code = assign_codes(roster, cross, ov['dept_abbr'])
    hkey = {norm(h): i for i, h in enumerate(ov['house'])}
    merge = {norm(k): norm(v) for k, v in ov['merge'].items()}

    by = {f['name']: {'id': code[f['name']], 'dept': f['dept'], 'rank': f['rank'], 'pubs': []}
          for f in roster}
    hc, ha = {}, {}
    for r in rows:
        tier = r['rating'] if r['rating'] in ('A*', 'A', 'B', 'C') else 'other'
        rec = {'y': r['year'], 'r': tier, 't': 'j' if r['itype'] == 'journal' else 'p'}
        k = norm(r['journal']); k = merge.get(k, k)
        if tier == 'other' and r['itype'] == 'journal' and k in hkey:
            rec['h'] = hkey[k]
            hc[rec['h']] = hc.get(rec['h'], 0) + 1
            ha.setdefault(rec['h'], set()).add(r['name'])
        if r['fwd']: rec['f'] = 1
        by[r['name']]['pubs'].append(rec)
    data = sorted(by.values(), key=lambda x: x['id'])
    for f in data: f['pubs'].sort(key=lambda p: -p['y'])

    json.dump(data, open(os.path.join(a.out, 'data.json'), 'w'), separators=(',', ':'))
    json.dump([[h, hc.get(i, 0), len(ha.get(i, set()))] for i, h in enumerate(ov['house'])],
              open(os.path.join(a.out, 'house.json'), 'w'), indent=1)
    json.dump(rows, open(os.path.join(a.out, 'rows.json'), 'w'), indent=1)
    with open(cross, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['code', 'name', 'department', 'rank'])
        for f in sorted(roster, key=lambda x: code[x['name']]):
            w.writerow([code[f['name']], f['name'], f['dept'], f['rank']])
    print(f"{len(roster)} faculty, {len(rows)} items in the window -> {a.out}")
    print(f"crosswalk written to {cross}. Keep it out of version control.")

def newest(paths):
    """A shell glob matches every draw you have kept. Take the most recent, and say so."""
    paths = sorted(paths)
    if len(paths) > 1:
        print('several exports matched:')
        for q in paths: print('   ', os.path.basename(q))
        print('using the most recent:', os.path.basename(paths[-1]))
    return paths[-1]

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('export', nargs='+', help='Watermark vita export(s); the newest is used')
    p.add_argument('--jql', help='ABDC Journal Quality List workbook')
    p.add_argument('--overrides', default='overrides.json')
    p.add_argument('--out', default='private')
    p.add_argument('--window-start', type=int, default=WINDOW_START)
    args = p.parse_args()
    args.export = newest(args.export)
    main(args)
