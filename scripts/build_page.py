"""Fold a dataset into template.html and write index.html.

  python3 scripts/build_page.py                          # demo data
  python3 scripts/build_page.py path/to/data.json path/to/house.json -o private.html
"""
import argparse, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def build(data_path, house_path, out_path):
    page = open(os.path.join(ROOT, "template.html"), encoding="utf-8").read()
    data = open(data_path, encoding="utf-8").read().strip()
    house = json.load(open(house_path, encoding="utf-8"))
    page = page.replace("__DATA__", data)
    page = page.replace("__HOUSE__", json.dumps(house, separators=(",", ":")))
    if "__DATA__" in page or "__HOUSE__" in page:
        raise SystemExit("template still has an unfilled placeholder")
    open(out_path, "w", encoding="utf-8").write(page)
    print(f"{out_path}  ({len(page):,} bytes, {len(json.loads(data))} faculty)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("data", nargs="?", default=os.path.join(ROOT, "data", "demo_data.json"))
    ap.add_argument("house", nargs="?", default=os.path.join(ROOT, "data", "demo_house.json"))
    ap.add_argument("-o", "--out", default=os.path.join(ROOT, "index.html"))
    a = ap.parse_args()
    build(a.data, a.house, a.out)
