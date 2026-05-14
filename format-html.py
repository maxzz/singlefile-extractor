from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

RAWTEXT_ELEMENTS = {"script", "style", "textarea", "pre"}

IMPLIED_CLOSE_ON_OPEN: dict[str, set[str]] = {
    # Common optional-end-tag elements.
    "li": {"li"},
    "dt": {"dt", "dd"},
    "dd": {"dt", "dd"},
    "option": {"option"},
    "optgroup": {"option"},
    # Table elements (HTML often omits </td>, </th>, </tr>, etc).
    "td": {"td", "th"},
    "th": {"td", "th"},
    "tr": {"td", "th", "tr"},
    "thead": {"td", "th", "tr", "thead", "tbody", "tfoot"},
    "tbody": {"td", "th", "tr", "thead", "tbody", "tfoot"},
    "tfoot": {"td", "th", "tr", "thead", "tbody", "tfoot"},
}


@dataclass(frozen=True)
class Token:
    kind: str  # "tag" | "text"
    value: str


def _parse_tag(html_text: str, start: int) -> tuple[str, int]:
    """Parse a tag starting at '<' and return (tag_text, next_index)."""
    n = len(html_text)
    i = start + 1
    quote: str | None = None
    while i < n:
        c = html_text[i]
        if quote:
            if c == quote:
                quote = None
        else:
            if c in {"'", '"'}:
                quote = c
            elif c == ">":
                return html_text[start : i + 1], i + 1
        i += 1
    return html_text[start:], n


def _tag_name(tag_text: str) -> str | None:
    s = tag_text.strip()
    if not s.startswith("<") or len(s) < 3:
        return None
    if s.startswith(("<!--", "<!", "<?")):
        return None
    if s.startswith("</"):
        s2 = s[2:]
    else:
        s2 = s[1:]
    s2 = s2.lstrip()
    m = re.match(r"([a-zA-Z][a-zA-Z0-9:_-]*)", s2)
    return m.group(1).casefold() if m else None


def _is_closing_tag(tag_text: str) -> bool:
    return tag_text.lstrip().startswith("</")


def _is_self_closing_tag(tag_text: str) -> bool:
    s = tag_text.strip()
    return s.endswith("/>")


def tokenize_html(html_text: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    n = len(html_text)

    while i < n:
        if html_text[i] != "<":
            j = html_text.find("<", i)
            if j < 0:
                j = n
            tokens.append(Token("text", html_text[i:j]))
            i = j
            continue

        # Comment
        if html_text.startswith("<!--", i):
            j = html_text.find("-->", i + 4)
            if j < 0:
                tokens.append(Token("tag", html_text[i:]))
                break
            tokens.append(Token("tag", html_text[i : j + 3]))
            i = j + 3
            continue

        tag_text, next_i = _parse_tag(html_text, i)
        tokens.append(Token("tag", tag_text))
        i = next_i

        # If this is an opening rawtext element, don't try to tokenize its contents.
        name = _tag_name(tag_text)
        if not name:
            continue
        if _is_closing_tag(tag_text):
            continue
        if _is_self_closing_tag(tag_text) or name in VOID_ELEMENTS:
            continue
        if name not in RAWTEXT_ELEMENTS:
            continue

        close_re = re.compile(rf"</\s*{re.escape(name)}\s*>", flags=re.IGNORECASE)
        m = close_re.search(html_text, i)
        if not m:
            # No closing tag found; treat rest as text.
            tokens.append(Token("text", html_text[i:]))
            break
        tokens.append(Token("text", html_text[i : m.start()]))
        tokens.append(Token("tag", html_text[m.start() : m.end()]))
        i = m.end()

    return tokens


def _pop_through_nearest(stack: list[str], names: set[str]) -> None:
    """Pop stack down through the nearest open element in names (inclusive)."""
    for idx in range(len(stack) - 1, -1, -1):
        if stack[idx] in names:
            del stack[idx:]
            return


def _pop_close_tag(stack: list[str], name: str) -> int:
    """Pop stack to close name; returns indent level for printing the closing tag."""
    for idx in range(len(stack) - 1, -1, -1):
        if stack[idx] == name:
            del stack[idx:]
            return idx
    return len(stack)


def format_html(html_text: str, *, indent: str = "  ") -> str:
    tokens = tokenize_html(html_text)

    lines: list[str] = []
    stack: list[str] = []

    def emit(line: str) -> None:
        if line == "":
            return
        lines.append(line)

    for tok in tokens:
        if tok.kind == "text":
            # Skip pure whitespace between tags.
            if tok.value.strip() == "":
                continue
            for raw_line in tok.value.splitlines():
                s = raw_line.strip()
                if s == "":
                    continue
                emit(f"{indent * len(stack)}{s}")
            continue

        tag = tok.value.strip()
        if tag == "":
            continue

        name = _tag_name(tag)

        if _is_closing_tag(tag):
            if name:
                indent_level = _pop_close_tag(stack, name)
            else:
                indent_level = len(stack)
            emit(f"{indent * indent_level}{tag}")
            continue

        if not name:
            emit(f"{indent * len(stack)}{tag}")
            continue

        # Apply implied end-tag rules (improves indentation for common optional-end-tag
        # patterns, especially inside tables).
        implied = IMPLIED_CLOSE_ON_OPEN.get(name)
        if implied:
            _pop_through_nearest(stack, implied)

        emit(f"{indent * len(stack)}{tag}")

        if _is_self_closing_tag(tag) or name in VOID_ELEMENTS:
            continue
        stack.append(name)

    return "\n".join(lines).rstrip() + "\n"


def _default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}_formatted{input_path.suffix}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    default_input = root / "tests-local" / "esignature-form.external-css.html"

    p = argparse.ArgumentParser(
        description="Format (pretty-print) an HTML file with indentation.",
    )
    p.add_argument(
        "-i",
        "--input",
        dest="input_path",
        type=Path,
        default=default_input,
        help="Path to the HTML file to format.",
    )
    p.add_argument(
        "-o",
        "--output",
        dest="output_path",
        type=Path,
        default=None,
        help='Where to write the formatted HTML (default: "<input>_formatted.html").',
    )
    p.add_argument(
        "--indent",
        dest="indent",
        type=int,
        default=2,
        help="Spaces per indent level (default: 2).",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    src: Path = args.input_path
    out: Path = args.output_path or _default_output_path(src)
    indent_spaces: int = args.indent
    if indent_spaces < 0:
        raise ValueError("--indent must be >= 0")

    html_text = src.read_text(encoding="utf-8", errors="replace")
    formatted = format_html(html_text, indent=(" " * indent_spaces))

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(formatted, encoding="utf-8", newline="\n")

    print(f"Wrote: {out}")
    print(f"- input: {src}")
    print(f"- indent: {indent_spaces} spaces")
    print(f"- chars: {len(formatted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

