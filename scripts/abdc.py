"""ABDC lookup: the list in force at the publication year, with nearest-year fallback."""
import openpyxl, re
from journal import norm
SHEETS=['2010 JQL','2013 JQL','2016 JQL','2019 JQL','2022 JQL','2025 JQL']
YEARS=[2010,2013,2016,2019,2022,2025]
def load(path):
    """path: the ABDC Journal Quality List workbook, one sheet per edition."""
    wb=openpyxl.load_workbook(path,data_only=True,read_only=True)
    J={}
    for sh in SHEETS:
        ws=wb[sh]; ti=ri=None; started=False
        for r in ws.iter_rows(values_only=True):
            vals=[str(x).strip() if x is not None else '' for x in r]
            low=[v.lower() for v in vals]
            if not started:
                if any(v=='journal title' for v in low):
                    ti=low.index('journal title')
                    ri=next((k for k,v in enumerate(low) if 'rating' in v), None)
                    started=True
                continue
            if ti is None or ri is None or ri>=len(vals): continue
            t,rt=vals[ti],vals[ri]
            if not t or not rt or rt.lower()=='none': continue
            J.setdefault(norm(t),{})[sh]=rt.strip()
    return J
def edition(year):
    if not year: year=2026
    if year<=2012: return '2010 JQL'
    if year<=2015: return '2013 JQL'
    if year<=2018: return '2016 JQL'
    if year<=2021: return '2019 JQL'
    if year<=2024: return '2022 JQL'
    return '2025 JQL'
def rate(J, jname, year):
    """-> (rating or '', note)"""
    k=norm(jname or '')
    if not k or k not in J: return '', ''
    ed=edition(year); d=J[k]
    if ed in d: return d[ed], 'listed'
    # nearest edition that does list it
    tgt=YEARS[SHEETS.index(ed)]
    best=min(d, key=lambda s: abs(YEARS[SHEETS.index(s)]-tgt))
    return d[best], f'listed in {best} only'
