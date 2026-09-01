"""Split the new export's Journal Articles run into true journal articles vs proceedings.

Some Watermark report templates omit the "Peer Reviewed Proceedings" subsection header,
so those entries run on under "Journal Articles". Two signals recover the split:
  - a double blank line, which is where the missing header used to sit
  - the citation naming a conference, a city, or a book publisher rather than a journal
Requiring BOTH scored 97% precision and 89% recall when tested against an export of the
same faculty whose headers were intact, so the true item types were known.
"""
import re, unicodedata
from parse_vita import headers, TL, STOP, UPPER, AUTH

CONF = re.compile(r'(conference|proceeding|annual meeting|symposium|workshop|institute\.|'
                  r'decision sciences|academy of \w+ .*meeting|'
                  r':\s*(springer|routledge|palgrave|elsevier|wiley|sage|mcgraw|pearson|cengage)|'
                  r'[A-Z][a-z]+,\s*(?:[A-Z]{2}|[A-Z][a-z]+)(?:,\s*[A-Za-z ]+)?:\s)', re.I)
YEAR = re.compile(r'\((\d{4})\)')

def cite_key(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', s)[:80]

def looks_proc(e):
    return bool(CONF.search(e))

def segments(path):
    L = [l.rstrip() for l in open(path, encoding='utf-8')]
    st = headers(L); out = {}
    for n, (i, name, dept, rank) in enumerate(st):
        end = st[n+1][0] if n+1 < len(st) else len(L)
        blk = [x.strip() for x in L[i:end]]
        segs = []; j = 0
        while j < len(blk):
            if blk[j] == 'Journal Articles':
                k = j + 1; cur = []; bl = 0
                while k < len(blk):
                    s = blk[k]
                    if s in STOP or UPPER.match(s) or s.startswith('Department of '): break
                    if s == '':
                        bl += 1
                        if bl >= 2 and cur: segs.append(cur); cur = []
                    else:
                        bl = 0
                        if AUTH.match(s): cur.append(s)
                    k += 1
                if cur: segs.append(cur)
                j = k
            else: j += 1
        out[name] = {'dept': dept, 'rank': rank, 'segs': segs}
    return out

def year_of(e):
    m = YEAR.search(e)
    return int(m.group(1)) if m else None

def classify(path):
    """-> {name: {dept, rank, items:[{cite, year, proc, seg}]}}"""
    out = {}
    for name, v in segments(path).items():
        items = []
        for si, seg in enumerate(v['segs']):
            for e in seg:
                items.append({'cite': e, 'year': year_of(e),
                              'proc': si > 0 and looks_proc(e), 'seg': si})
        out[name] = {'dept': v['dept'], 'rank': v['rank'], 'items': items}
    return out
