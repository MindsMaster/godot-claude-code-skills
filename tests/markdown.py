import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^(\s*)```([\w#+-]*)\s*$")
CHECK_TAG = re.compile(r"<!--\s*check:\s*(.+?)\s*-->")


@dataclass
class Block:
    where: str
    lang: str
    code: str
    tags: dict = field(default_factory=dict)


@dataclass
class Doc:
    path: Path
    where: str
    text: str
    prose: list
    blocks: list


def parse_tags(raw: str) -> dict:
    tags = {}
    for part in raw.split(";"):
        key, _, value = part.strip().partition(" ")
        if key:
            tags[key] = value.strip()
    return tags


def parse_doc(path: Path) -> Doc:
    where = str(path.relative_to(ROOT))
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    prose = []
    blocks = []
    pending = {}
    i = 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if m:
            indent = m.group(1)
            start = i + 1
            body = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i].removeprefix(indent))
                i += 1
            blocks.append(Block(f"{where}:{start}", m.group(2).lower(), "\n".join(body) + "\n", pending))
            pending = {}
            i += 1
            continue
        tag = CHECK_TAG.search(lines[i])
        if tag:
            pending = parse_tags(tag.group(1))
        elif lines[i].strip():
            pending = {}
        prose.append((i + 1, lines[i]))
        i += 1
    return Doc(path, where, text, prose, blocks)


def frontmatter(text: str):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    fields = {}
    for line in text[4:end].split("\n"):
        key, sep, value = line.partition(":")
        if sep and not line.startswith(" "):
            fields[key.strip()] = value.strip().strip('"')
    return fields
