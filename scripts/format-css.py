from __future__ import annotations

import argparse
import sys
from pathlib import Path


def format_css(css_text: str, *, indent: str = "  ") -> str:
    out: list[str] = []

    level = 0
    paren_depth = 0

    in_string: str | None = None
    escape = False
    in_comment = False

    pending_space = False
    at_line_start = True

    def append(s: str) -> None:
        nonlocal at_line_start
        if not s:
            return
        for ch in s:
            if at_line_start and ch != "\n":
                out.append(indent * level)
                at_line_start = False
            out.append(ch)
            if ch == "\n":
                at_line_start = True

    def trim_trailing_spaces() -> None:
        while out and out[-1] == " ":
            out.pop()

    def newline() -> None:
        nonlocal pending_space, at_line_start
        trim_trailing_spaces()
        if not out or out[-1] != "\n":
            out.append("\n")
        at_line_start = True
        pending_space = False

    i = 0
    n = len(css_text)
    while i < n:
        c = css_text[i]

        if in_comment:
            # Copy through the end of the comment.
            if c == "*" and i + 1 < n and css_text[i + 1] == "/":
                append("*/")
                i += 2
                in_comment = False
                pending_space = True
                continue
            append(c)
            i += 1
            continue

        if in_string is not None:
            append(c)
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == in_string:
                in_string = None
            i += 1
            continue

        # Not in comment or string.
        if c == "\\":
            # CSS escape outside strings/comments (common in minified data: URLs).
            # Treat the next character as literal, so we don't accidentally start a string
            # on sequences like \'.
            if pending_space and not at_line_start:
                append(" ")
            pending_space = False

            append("\\")
            if i + 1 < n:
                append(css_text[i + 1])
                i += 2
            else:
                i += 1
            continue

        if c == "/" and i + 1 < n and css_text[i + 1] == "*":
            if pending_space and not at_line_start:
                append(" ")
            pending_space = False
            append("/*")
            i += 2
            in_comment = True
            continue

        if c in {"'", '"'}:
            if pending_space and not at_line_start:
                append(" ")
            pending_space = False
            append(c)
            in_string = c
            i += 1
            continue

        if c.isspace():
            pending_space = True
            i += 1
            continue

        if c == "(":
            if pending_space and not at_line_start:
                append(" ")
            pending_space = False
            append("(")
            paren_depth += 1
            i += 1
            continue

        if c == ")":
            pending_space = False
            append(")")
            if paren_depth > 0:
                paren_depth -= 1
            i += 1
            continue

        if c == "{":
            if pending_space and not at_line_start:
                append(" ")
            pending_space = False

            # Optional whitespace before '{' is always safe, and improves readability.
            if out and out[-1] not in {" ", "\n"}:
                append(" ")
            append("{")
            newline()
            level += 1
            i += 1
            continue

        if c == "}":
            pending_space = False
            level = max(0, level - 1)
            if not at_line_start:
                newline()
            append("}")
            newline()
            i += 1
            continue

        if c == ";":
            pending_space = False
            append(";")
            if paren_depth == 0:
                newline()
            i += 1
            continue

        if c == ",":
            if pending_space and not at_line_start:
                append(" ")
            pending_space = False
            append(",")
            # Space after comma improves readability in most contexts.
            if paren_depth == 0:
                pending_space = True
            i += 1
            continue

        # Default character.
        if pending_space and not at_line_start:
            append(" ")
        pending_space = False
        append(c)
        i += 1

    # Ensure a trailing newline.
    newline()
    return "".join(out)


def _default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}_formatted{input_path.suffix}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_input = repo_root / "tests" / "esignature-form.css"

    p = argparse.ArgumentParser(
        description="Format (pretty-print) a CSS file with indentation.",
    )
    p.add_argument(
        "-i",
        "--input",
        dest="input_path",
        type=Path,
        default=default_input,
        help="Path to the CSS file to format.",
    )
    p.add_argument(
        "-o",
        "--output",
        dest="output_path",
        type=Path,
        default=None,
        help='Where to write the formatted CSS (default: "<input>_formatted.css").',
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

    css_text = src.read_text(encoding="utf-8", errors="replace")
    formatted = format_css(css_text, indent=(" " * indent_spaces))

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(formatted, encoding="utf-8", newline="\n")

    print(f"Wrote: {out}")
    print(f"- input: {src}")
    print(f"- indent: {indent_spaces} spaces")
    print(f"- chars: {len(formatted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

