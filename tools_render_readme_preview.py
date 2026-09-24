from pathlib import Path
import html
import re


BASE = Path(__file__).resolve().parent
README = BASE / "README.md"
OUT = BASE / "README_PREVIEW.html"


def inline(text):
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img alt="\1" src="\2">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def flush_list(out, list_items):
    if list_items:
        out.append("<ul>")
        for item in list_items:
            out.append(f"<li>{inline(item)}</li>")
        out.append("</ul>")
        list_items.clear()


def flush_table(out, table_rows):
    if not table_rows:
        return
    rows = table_rows[:]
    table_rows.clear()
    if len(rows) >= 2 and all(c.strip("-: ") == "" for c in rows[1]):
        headers = rows[0]
        body = rows[2:]
        out.append("<table>")
        out.append("<thead><tr>" + "".join(f"<th>{inline(c.strip())}</th>" for c in headers) + "</tr></thead>")
        out.append("<tbody>")
        for row in body:
            out.append("<tr>" + "".join(f"<td>{inline(c.strip())}</td>" for c in row) + "</tr>")
        out.append("</tbody></table>")
    else:
        for row in rows:
            out.append("<p>" + inline(" | ".join(row)) + "</p>")


def render(md):
    out = []
    list_items = []
    table_rows = []
    in_code = False
    code_lines = []

    for raw in md.splitlines():
        line = raw.rstrip()

        if line.startswith("```"):
            flush_list(out, list_items)
            flush_table(out, table_rows)
            if not in_code:
                in_code = True
                code_lines = []
            else:
                out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                in_code = False
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            flush_list(out, list_items)
            flush_table(out, table_rows)
            continue

        if line.startswith("|") and line.endswith("|"):
            flush_list(out, list_items)
            table_rows.append([cell.strip() for cell in line.strip("|").split("|")])
            continue

        flush_table(out, table_rows)

        if line.startswith("# "):
            flush_list(out, list_items)
            out.append(f"<h1>{inline(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            flush_list(out, list_items)
            out.append(f"<h2>{inline(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            flush_list(out, list_items)
            out.append(f"<h3>{inline(line[4:].strip())}</h3>")
        elif line.startswith("- "):
            list_items.append(line[2:].strip())
        elif line.startswith("> "):
            flush_list(out, list_items)
            out.append(f"<blockquote>{inline(line[2:].strip())}</blockquote>")
        else:
            flush_list(out, list_items)
            out.append(f"<p>{inline(line)}</p>")

    flush_list(out, list_items)
    flush_table(out, table_rows)
    return "\n".join(out)


body = render(README.read_text(encoding="utf-8"))
html_doc = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>README Preview - Prestamos Universidad</title>
  <style>
    body {{
      margin: 0;
      background: #f6f8fa;
      color: #24292f;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      line-height: 1.55;
    }}
    main {{
      max-width: 980px;
      margin: 32px auto;
      padding: 36px 44px;
      background: #fff;
      border: 1px solid #d0d7de;
      border-radius: 8px;
    }}
    h1, h2, h3 {{
      margin-top: 24px;
      margin-bottom: 12px;
      line-height: 1.25;
    }}
    h1 {{
      padding-bottom: 0.3em;
      border-bottom: 1px solid #d8dee4;
      font-size: 2em;
    }}
    h2 {{
      padding-bottom: 0.3em;
      border-bottom: 1px solid #d8dee4;
      font-size: 1.5em;
    }}
    a {{ color: #0969da; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    code {{
      padding: 0.2em 0.4em;
      border-radius: 6px;
      background: rgba(175, 184, 193, 0.2);
      font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
      font-size: 85%;
    }}
    pre {{
      padding: 16px;
      overflow: auto;
      border-radius: 6px;
      background: #f6f8fa;
    }}
    pre code {{
      padding: 0;
      background: transparent;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0 18px;
    }}
    th, td {{
      padding: 8px 12px;
      border: 1px solid #d0d7de;
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: #f6f8fa; font-weight: 600; }}
    blockquote {{
      margin: 16px 0;
      padding: 0 1em;
      color: #57606a;
      border-left: 0.25em solid #d0d7de;
    }}
    img {{
      display: block;
      max-width: 100%;
      margin: 16px auto 28px;
      border: 1px solid #d0d7de;
      border-radius: 6px;
      background: #fff;
    }}
  </style>
</head>
<body>
  <main>
{body}
  </main>
</body>
</html>
"""

OUT.write_text(html_doc, encoding="utf-8")
print(OUT)
