from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


STYLE = """
:root {
  color-scheme: light;
  --bg: #f6f7f9;
  --paper: #ffffff;
  --ink: #17202a;
  --muted: #5b6776;
  --line: #d9dee7;
  --soft-line: #edf0f4;
  --accent: #0f6bff;
  --accent-soft: #eaf2ff;
  --code-bg: #f1f4f8;
  --warn-bg: #fff7e6;
  --warn-line: #ffd27a;
  --shadow: 0 18px 50px rgba(23, 32, 42, 0.08);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font: 15px/1.58 "Segoe UI", Roboto, Arial, sans-serif;
}

.page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px 22px 48px;
}

.document {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: var(--shadow);
  overflow: hidden;
}

.hero {
  padding: 34px 42px 28px;
  border-bottom: 1px solid var(--line);
  background:
    linear-gradient(135deg, rgba(15, 107, 255, 0.12), transparent 42%),
    linear-gradient(180deg, #ffffff, #f9fbff);
}

.hero h1 {
  margin: 0 0 10px;
  font-size: 30px;
  line-height: 1.2;
  letter-spacing: 0;
}

.hero-meta {
  color: var(--muted);
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
}

.content {
  padding: 30px 42px 42px;
}

h2 {
  margin: 34px 0 12px;
  padding-top: 8px;
  border-top: 1px solid var(--soft-line);
  font-size: 22px;
  line-height: 1.25;
}

h2:first-child {
  margin-top: 0;
  padding-top: 0;
  border-top: 0;
}

h3 {
  margin: 26px 0 10px;
  font-size: 18px;
  line-height: 1.3;
}

p {
  margin: 0 0 14px;
}

ul,
ol {
  margin: 0 0 18px 22px;
  padding: 0;
}

li {
  margin: 5px 0;
}

strong {
  font-weight: 650;
}

code {
  background: var(--code-bg);
  border: 1px solid #e2e7ef;
  border-radius: 5px;
  padding: 1px 5px;
  font-family: "Cascadia Mono", Consolas, "Liberation Mono", monospace;
  font-size: 0.92em;
}

.table-wrap {
  margin: 14px 0 24px;
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 720px;
}

th,
td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--soft-line);
  text-align: left;
  vertical-align: top;
}

th {
  background: #f4f7fb;
  color: #263242;
  font-weight: 650;
  white-space: nowrap;
}

tr:nth-child(even) td {
  background: #fbfcfe;
}

tr:last-child td {
  border-bottom: 0;
}

.callout {
  margin: 16px 0 22px;
  padding: 13px 15px;
  border: 1px solid var(--warn-line);
  border-radius: 8px;
  background: var(--warn-bg);
}

.section-number {
  color: var(--accent);
}

a {
  color: var(--accent);
}

@media print {
  body {
    background: #fff;
  }

  .page {
    max-width: none;
    padding: 0;
  }

  .document {
    border: 0;
    box-shadow: none;
  }

  .table-wrap {
    overflow: visible;
  }
}

@media (max-width: 720px) {
  .page {
    padding: 0;
  }

  .document {
    border-radius: 0;
    border-left: 0;
    border-right: 0;
  }

  .hero,
  .content {
    padding-left: 20px;
    padding-right: 20px;
  }
}
""".strip()


def inline_markup(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def render_table(lines: list[str], start: int) -> tuple[str, int]:
    headers = split_table_row(lines[start])
    rows: list[list[str]] = []
    i = start + 2
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append(split_table_row(lines[i]))
        i += 1

    output = ["<div class=\"table-wrap\"><table>", "<thead><tr>"]
    output.extend(f"<th>{inline_markup(cell)}</th>" for cell in headers)
    output.append("</tr></thead><tbody>")
    for row in rows:
        output.append("<tr>")
        padded = row + [""] * max(0, len(headers) - len(row))
        output.extend(f"<td>{inline_markup(cell)}</td>" for cell in padded[: len(headers)])
        output.append("</tr>")
    output.append("</tbody></table></div>")
    return "\n".join(output), i


def render_markdown(markdown: str) -> tuple[str, str, list[str]]:
    lines = markdown.splitlines()
    html_parts: list[str] = []
    title = "Dokumentation"
    meta: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("# "):
            title = stripped[2:].strip()
            i += 1
            continue

        if not html_parts and re.match(r"^[A-Za-z].*?:", stripped):
            while i < len(lines) and lines[i].strip():
                meta.append(lines[i].strip().rstrip("  "))
                i += 1
            continue

        if (
            stripped.startswith("|")
            and i + 1 < len(lines)
            and lines[i + 1].strip().startswith("|")
            and is_table_separator(lines[i + 1])
        ):
            table_html, i = render_table(lines, i)
            html_parts.append(table_html)
            continue

        heading_match = re.match(r"^(#{2,3})\s+(.+)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            heading = heading_match.group(2)
            heading = re.sub(
                r"^(\d+(?:\.\d+)*)\.\s+",
                lambda m: f"<span class=\"section-number\">{m.group(1)}.</span> ",
                inline_markup(heading),
            )
            html_parts.append(f"<h{level}>{heading}</h{level}>")
            i += 1
            continue

        if stripped.startswith("- "):
            html_parts.append("<ul>")
            while i < len(lines) and lines[i].strip().startswith("- "):
                html_parts.append(f"<li>{inline_markup(lines[i].strip()[2:])}</li>")
                i += 1
            html_parts.append("</ul>")
            continue

        ordered_match = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ordered_match:
            html_parts.append("<ol>")
            while i < len(lines):
                item_match = re.match(r"^\d+\.\s+(.+)$", lines[i].strip())
                if not item_match:
                    break
                item_text = inline_markup(item_match.group(1))
                following: list[str] = []
                i += 1
                while i < len(lines) and lines[i].startswith("   ") and lines[i].strip():
                    following.append(inline_markup(lines[i].strip()))
                    i += 1
                if following:
                    item_text += "<br>" + "<br>".join(following)
                html_parts.append(f"<li>{item_text}</li>")
            html_parts.append("</ol>")
            continue

        paragraph = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{2,3})\s+", lines[i].strip()):
            next_line = lines[i].strip()
            if next_line.startswith("|") or next_line.startswith("- ") or re.match(r"^\d+\.\s+", next_line):
                break
            paragraph.append(next_line)
            i += 1

        text = " ".join(paragraph)
        cls = " class=\"callout\"" if text.lower().startswith(("auffaellig:", "wichtig:")) else ""
        html_parts.append(f"<p{cls}>{inline_markup(text)}</p>")

    return title, "\n".join(html_parts), meta


def build_html(title: str, body: str, meta: list[str]) -> str:
    meta_html = "\n".join(f"<span>{inline_markup(item)}</span>" for item in meta)
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{STYLE}</style>
</head>
<body>
  <main class="page">
    <article class="document">
      <header class="hero">
        <h1>{inline_markup(title)}</h1>
        <div class="hero-meta">
          {meta_html}
        </div>
      </header>
      <div class="content">
        {body}
      </div>
    </article>
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render doku.md to a styled doku.html file.")
    parser.add_argument("source", nargs="?", default="doku.md", help="Markdown source file")
    parser.add_argument("target", nargs="?", default="doku.html", help="HTML target file")
    args = parser.parse_args()

    source = Path(args.source)
    target = Path(args.target)

    markdown = source.read_text(encoding="utf-8")
    title, body, meta = render_markdown(markdown)
    target.write_text(build_html(title, body, meta), encoding="utf-8")
    print(f"Rendered {source} -> {target}")


if __name__ == "__main__":
    main()
