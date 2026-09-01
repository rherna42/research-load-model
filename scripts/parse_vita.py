"""Parse a Watermark vita export into per-faculty journal-article entries.

Header shape:  Name line / [optional photo file] / Department / Rank
The department is whatever line sits immediately above the rank line, so a
person filed under "College of Business" instead of a department is still found.
"""
import re, sys, json
from collections import Counter

RANKS = {'Affiliate','Assistant Professor','Associate Professor','Full Professor','Professor',
         'Lecturer','Senior Lecturer','Instructor','Emeritus','Emeritus Professor'}
TL = {'Assistant Professor','Associate Professor','Full Professor','Professor'}
NAME = re.compile(r"^[A-ZÀ-Þ][A-Za-zÀ-ÿ'’\-\. ]{1,30},\s+[A-ZÀ-Þ][A-Za-zÀ-ÿ'’\-\. ()]{0,30}$")
AUTH = re.compile(r"^[A-ZÀ-Þ][A-Za-zÀ-ÿ'’\-\. ]{1,45},\s*[A-ZÀ-Þ]\.")
YEAR = re.compile(r'\((\d{4})\)')
UPPER = re.compile(r'^[A-Z][A-Z ,&/]{4,}$')
STOP = {'Refereed / Peer Reviewed Publications','Journal Articles','Chapters in Books','Peer Reviewed Proceedings',
 'Non-Refereed Publications','Other Publications and Presentations','Non-peer Reviewed Presentations',
 'Refereed / Peer Reviewed Presentations','Other Non-Peer Reviewed Publications','Non-peer Reviewed Journals',
 'Books, Textbooks and Instructional Materials','Book Reviews, Interviews, and Comments','Research Monographs',
 'Research/Work in Progress','Grants','Grants Funded or Under Review','Grants Not Funded','Conferences Attended',
 'Professional Organizations','Professional Memberships','Certifications and Licensures','Consulting Positions',
 'Honors and Awards Received','Advanced Study and Professional Training','College','Community','School',
 'Honor Society Memberships'}

def headers(L):
    out = []
    for i, l in enumerate(L):
        if not NAME.match(l.strip()): continue
        for k in range(1, 5):
            if i + k >= len(L): break
            if L[i+k].strip() in RANKS:
                out.append((i, l.strip(), L[i+k-1].strip(), L[i+k].strip())); break
    return out

def parse(path):
    L = [l.rstrip() for l in open(path, encoding='utf-8')]
    st = headers(L); res = {}
    for n, (i, name, dept, rank) in enumerate(st):
        end = st[n+1][0] if n+1 < len(st) else len(L)
        blk = [x.strip() for x in L[i:end]]
        ent = []; j = 0
        while j < len(blk):
            if blk[j] == 'Journal Articles':
                k = j + 1
                while k < len(blk):
                    s = blk[k]
                    if s in STOP or UPPER.match(s) or s.startswith('Department of '): break
                    if AUTH.match(s): ent.append(s)
                    k += 1
                j = k
            else: j += 1
        res[name] = {'dept': dept, 'rank': rank, 'entries': ent}
    return st, res

def year(e):
    m = YEAR.search(e)
    return int(m.group(1)) if m else None

if __name__ == '__main__':
    st, res = parse(sys.argv[1])
    tl = {k: v for k, v in res.items() if v['rank'] in TL}
    print('people:', len(st), ' tenure-line:', len(tl))
    print('TL depts:', dict(Counter(v['dept'] for v in tl.values())))
    y = Counter()
    for v in tl.values():
        for e in v['entries']: y[year(e)] += 1
    ky = sorted(x for x in y if x)
    print('entries:', sum(y.values()), ' undated:', y[None], ' range:', ky[0], '-', ky[-1])
    print('2021+ dated:', sum(v for k, v in y.items() if k and k >= 2021))
    if len(sys.argv) > 2: json.dump(res, open(sys.argv[2], 'w'))
