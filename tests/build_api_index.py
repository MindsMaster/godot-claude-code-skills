import argparse
import gzip
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

VERSIONS = ["4.3", "4.4", "4.5", "4.6", "4.7", "4.8"]


def load_api(cpp: Path, version: str) -> dict:
    return json.loads((cpp / "gdextension" / f"extension_api-{version.replace('.', '-')}.json").read_text())


def class_members(c: dict) -> dict:
    return {
        "inherits": c.get("inherits"),
        "methods": sorted(m["name"] for m in c.get("methods", [])),
        "properties": sorted(p["name"] for p in c.get("properties", [])),
        "signals": sorted(s["name"] for s in c.get("signals", [])),
        "constants": sorted(k["name"] for k in c.get("constants", [])),
        "enums": {e["name"]: sorted(v["name"] for v in e["values"]) for e in c.get("enums", [])},
    }


def deprecated_from_docs(godot: Path) -> dict:
    out = {}
    files = list((godot / "doc" / "classes").glob("*.xml")) + list(godot.glob("modules/*/doc_classes/*.xml"))
    for f in files:
        root = ET.parse(f).getroot()
        name = root.get("name")
        entry = []
        if root.get("deprecated") is not None:
            entry.append("")
        for tag in ("method", "member", "signal", "constant"):
            for el in root.iter(tag):
                if el.get("deprecated") is not None:
                    entry.append(el.get("name"))
        if entry:
            out[name] = sorted(set(entry))
    return out


def project_settings(godot: Path) -> list:
    root = ET.parse(godot / "doc" / "classes" / "ProjectSettings.xml").getroot()
    return sorted(m.get("name") for m in root.iter("member"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--godot-cpp", type=Path, required=True)
    ap.add_argument("--godot", type=Path, required=True, help="引擎源码根 或 godot --doctool 的输出目录")
    ap.add_argument("--target", default="4.7")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "data" / "godot_api.json.gz")
    args = ap.parse_args()

    since = {}
    for v in VERSIONS:
        for c in load_api(args.godot_cpp, v)["classes"]:
            since.setdefault(c["name"], v)

    api = load_api(args.godot_cpp, args.target)
    classes = {c["name"]: class_members(c) for c in api["classes"]}
    for name, c in classes.items():
        c["since"] = since.get(name, VERSIONS[0])
    builtins = {}
    for b in api["builtin_classes"]:
        builtins[b["name"]] = {
            "methods": sorted(m["name"] for m in b.get("methods", [])),
            "members": sorted(m["name"] for m in b.get("members", [])),
            "constants": sorted(k["name"] for k in b.get("constants", [])),
            "enums": {e["name"]: sorted(v["name"] for v in e["values"]) for e in b.get("enums", [])},
        }
    index = {
        "version": args.target,
        "classes": classes,
        "builtins": builtins,
        "singletons": sorted(s["name"] for s in api["singletons"]),
        "utility_functions": sorted(u["name"] for u in api["utility_functions"]),
        "global_enums": {e["name"]: sorted(v["name"] for v in e["values"]) for e in api["global_enums"]},
        "deprecated": deprecated_from_docs(args.godot),
        "project_settings": project_settings(args.godot),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.out, "wt", encoding="utf-8") as f:
        json.dump(index, f, separators=(",", ":"), sort_keys=True)
    print(f"{args.out} classes={len(classes)} builtins={len(builtins)}")


if __name__ == "__main__":
    main()
