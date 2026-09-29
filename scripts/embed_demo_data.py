"""Re-embed data/demo_data.json into rural-road-map-v1.html (the `const DATA = {...};` line), so the map's copy of
the data can't drift from the file. Run after scripts/extract_demo_data.py."""
import json

HTML = "rural-road-map-v1.html"

def main():
    data = json.load(open("data/demo_data.json", encoding="utf-8"))
    lines = open(HTML, encoding="utf-8").read().split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith("const DATA = ")]
    if len(idx) != 1:
        raise SystemExit(f"expected exactly one 'const DATA = ' line, found {len(idx)}")
    lines[idx[0]] = "const DATA = " + json.dumps(data) + ";"
    open(HTML, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print(f"embedded data/demo_data.json into {HTML} line {idx[0] + 1}")

if __name__ == "__main__":
    main()
