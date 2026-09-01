"""Pull the outlet name out of a Watermark citation.

Shape: Authors (YYYY). Title. Outlet, vol(issue), pages. URL
Titles contain periods, so the outlet is found by walking the sentence pieces
after the year and taking the one that carries the volume/issue or sits last
before the trailing URL.
"""
import re, unicodedata
YEAR = re.compile(r'\((\d{4})\)\.\s*')
VOLISS = re.compile(r'^(.*?),\s*\d+\s*(\(\s*[\dA-Za-z\-/]+\s*\))?\s*(,.*)?$')
URL = re.compile(r'https?://\S+')
TRAIL = re.compile(r'[\s.,;:]+$')

def outlet(cite):
    s = URL.sub('', cite).strip()
    m = YEAR.search(s)
    s = s[m.end():] if m else re.sub(r'^.*?\.\s+', '', s, count=1)
    # split on sentence boundaries that are followed by a capital or a quote
    parts = [p.strip() for p in re.split(r'(?<=[A-Za-z0-9\?\"\)\]])\.\s+(?=[A-Z"“])', s) if p.strip()]
    if not parts: return ''
    # drop a trailing fragment that is only a page range or note
    cands = parts[1:] if len(parts) > 1 else parts
    best = ''
    for p in cands:
        p = TRAIL.sub('', p)
        vm = VOLISS.match(p)
        name = TRAIL.sub('', vm.group(1)) if vm else p
        name = re.sub(r'\s*\(\s*[A-Z]{2,8}\s*\)\s*$', '', name)   # trailing acronym
        name = re.sub(r'^(to appear in|forthcoming in|accepted (at|in))\s+', '', name, flags=re.I)
        name = re.split(r'\s+/\s+', name)[0]                      # "Journal / Publisher"
        name = re.sub(r'\s*\([^)]*\)\s*$', '', name)              # trailing (Spring 2025), (16)
        name = re.sub(r',?\s*Vol\.?\s*\d.*$', '', name, flags=re.I)
        name = re.sub(r',\s*\d+.*$', '', name)                     # ", 31(1 / Spring..."
        name = re.sub(r'\.?\s*(www\.|http)\S*$', '', name, flags=re.I)
        name = TRAIL.sub('', name)
        if not name: continue
        if len(name) < 4: continue
        best = name
        if vm: break        # a volume/issue is the strongest signal; stop here
    return TRAIL.sub('', best)

def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii','ignore').decode()
    s = s.lower().replace('&',' and ')
    s = re.sub(r'^(the)\s+','', s)
    s = re.sub(r'[^a-z0-9 ]',' ', s)
    return re.sub(r'\s+',' ', s).strip()
