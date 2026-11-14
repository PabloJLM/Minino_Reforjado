#!/usr/bin/env python3
"""Arma el libro/epub de la wiki del Minino Reforjado.

Uso:
  python3 build_book.py manuscrito   # wiki -> manuscrito.md + preview.html (para revisar)
  python3 build_book.py preview      # manuscrito.md -> preview.html (tras editar el manuscrito)
  python3 build_book.py epub         # manuscrito.md -> Minino_Reforjado.epub
  python3 build_book.py pdf          # manuscrito.md -> Minino_Reforjado.pdf
  python3 build_book.py todo         # los tres

Flujo: genera el manuscrito, lo revisas/editas (manuscrito.md o preview.html),
y luego empaquetas. 'epub' y 'pdf' NO regeneran el manuscrito, usan tus ediciones.
"""
import re, sys, shutil, subprocess, pathlib

HERE = pathlib.Path(__file__).resolve().parent
WIKI = HERE.parent / "Cyber_camioneta.wiki"
MS = HERE / "manuscrito.md"

TITLE = "Minino Reforjado: Guía de uso"
AUTHOR = "Pablo José López Mazariegos — Tesla Lab, Universidad Galileo"

# (título de la parte, [(archivo sin .md, título del capítulo)])
BOOK = [
    ("Introducción", [("Home", "Qué es el Minino Reforjado")]),
    ("Apps", [
        ("Wifi-Captive-Portal", None), ("AP-Flood", None), ("Bluetooth-Spam", None),
        ("Sniffer", None),
        ("PC-Mode", None), ("BLE-Scanner", None), ("Mensajes-ESP-NOW", None),
        ("Terminal-de-Mensajes", None)]),
    ("Ajustes", [
        ("Ajustes-Configuracion", None), ("Ajustes-SD-Storage", None),
        ("Ajustes-NEOPIXEL", None), ("Ajustes-Terminal-Avanzada", None),
        ("Ajustes-BT-Spam", None), ("Ajustes-Con-Remota-FTP", None)]),
    ("Tutoriales", [
        ("Tutoriales", None), ("Tutorial-Conexion-Serial", None),
        ("Tutorial-FileZilla-FTP", None), ("Tutorial-PuTTY-Terminal-Remota", None),
        ("Tutorial-Linux-FTP-Terminal", None), ("Tutorial-Mensajeria-ESPNOW", None),
        ("Tutorial-RISCV", None), ("Tutorial-AES", None), ("Tutorial-GUI-ALU", None)]),
    ("Addons", [("Addons", None)]),
]
NO_IMAGES = {"Addons"}   # estas páginas se mencionan sin fotos
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII"]
IMG = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")


def shift(text, strip_images, drop_h1):
    out, fence, first_h1 = [], False, None
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            out.append(line); continue
        if not fence:
            if strip_images and IMG.match(line):
                continue
            m = re.match(r"^(#{1,5})\s+(.*)$", line)
            if m:
                if len(m.group(1)) == 1 and first_h1 is None:
                    first_h1 = m.group(2)
                    if drop_h1:
                        continue
                line = "#" + line   # baja un nivel (los H1 pasan a ser partes)
            line = re.sub(r"\]\((?!https?:|#|imgs/|mailto:)([^)\s]+)\)", r"](#\1)", line)
        out.append(line)
    return "\n".join(out), first_h1


def make_manuscript():
    parts, used = [], set()
    for i, (part, pages) in enumerate(BOOK):
        parts.append(f"# Parte {ROMAN[i]}. {part}\n")
        for name, title in pages:
            src = (WIKI / f"{name}.md").read_text(encoding="utf-8")
            body, h1 = shift(src, name in NO_IMAGES, drop_h1=True)
            title = title or h1 or name
            parts.append(f"## {title} {{#{name}}}\n\n{body.strip()}\n")
            used.add(name)
    missing = {p.stem for p in WIKI.glob("*.md")} - used
    if missing:
        print("AVISO, páginas de la wiki que no entraron:", ", ".join(sorted(missing)))
    meta = f'---\ntitle: "{TITLE}"\nauthor: "{AUTHOR}"\nlang: es\n---\n\n'
    MS.write_text(meta + "\n".join(parts), encoding="utf-8")
    if (HERE / "imgs").exists():
        shutil.rmtree(HERE / "imgs")
    shutil.copytree(WIKI / "imgs", HERE / "imgs")
    css()
    preview()
    print("Listo: manuscrito.md y preview.html")


def preview():
    """preview.html autocontenido (imágenes y portada incrustadas), desde manuscrito.md."""
    css()
    (HERE / "portada.html").write_text(
        '<div style="text-align:center;page-break-after:always">'
        '<img src="cover.png" style="max-width:26em;width:100%;box-shadow:0 0 20px #0006"></div>',
        encoding="utf-8")
    run(["pandoc", "manuscrito.md", "-f", "markdown-implicit_figures", "-s", "--toc", "--toc-depth=2",
         "--css", "libro.css", "--self-contained",
         "--include-before-body=portada.html", "-o", "preview.html"])
    print("preview.html actualizado (portada incluida)")


def css():
    (HERE / "libro.css").write_text(PREVIEW_CSS, encoding="utf-8")
    (HERE / "epub.css").write_text(EPUB_CSS, encoding="utf-8")


ACCENT = "#6d28d9"
PREVIEW_CSS = """
html{background:#d9d4e4}
body{max-width:39em;margin:2.5em auto;padding:4em 4.5em;background:#fdfbf7;color:#222;
  font-family:'Palatino Linotype',Palatino,'Book Antiqua',Georgia,serif;font-size:1.08rem;
  line-height:1.65;text-align:justify;hyphens:auto;box-shadow:0 4px 40px #3b1d6e55}
p{margin:0 0 .85em;orphans:3;widows:3}
a{color:#6d28d9;text-decoration:none}a:hover{text-decoration:underline}
/* portada y título */
header#title-block-header{text-align:center;margin:3em 0 4em;page-break-after:always}
header#title-block-header h1.title{font-size:2.6rem;letter-spacing:.04em;margin:1.2em 0 .3em;color:#2e1065;
  font-variant:small-caps;border:0}
header#title-block-header p.author{font-style:italic;color:#555;margin:.2em 0;text-align:center}
/* índice */
nav#TOC{margin:0 0 4em;page-break-after:always}
nav#TOC:before{content:"Índice";display:block;text-align:center;font-size:1.6rem;font-variant:small-caps;
  letter-spacing:.1em;color:#2e1065;margin-bottom:1em}
nav#TOC ul{list-style:none;padding-left:0;margin:0;text-align:left}
nav#TOC ul ul{padding-left:1.6em;margin-bottom:.6em}
nav#TOC>ul>li{margin-top:.9em;font-weight:bold;font-variant:small-caps;letter-spacing:.04em}
nav#TOC>ul>li>ul>li{font-weight:normal;font-variant:normal;letter-spacing:0;margin:.15em 0}
nav#TOC a{color:#222}
/* partes (H1) */
h1{text-align:center;font-size:2.1rem;font-weight:normal;font-variant:small-caps;letter-spacing:.08em;color:#2e1065;
  margin:5em 0 3em;padding:2.2em 0;border-top:3px double #6d28d9;border-bottom:3px double #6d28d9;page-break-before:always}
/* capítulos (H2) */
h2{text-align:center;font-size:1.75rem;font-weight:bold;color:#2e1065;margin:3.2em 0 1.2em;padding-bottom:.5em;
  border-bottom:1px solid #c4b5fd;page-break-before:always;page-break-after:avoid}
h2:after{content:"❖";display:block;font-size:.8rem;color:#6d28d9;margin-top:.5em}
h3{font-size:1.25rem;color:#4c1d95;margin:2em 0 .6em;text-align:left;page-break-after:avoid}
h4,h5{font-size:1.05rem;font-style:italic;color:#4c1d95;margin:1.4em 0 .4em;text-align:left}
/* primer párrafo con capitular */
h2+p:first-letter,h2+p+p:first-letter{}
h2+p:first-letter{float:left;font-size:3.4em;line-height:.85;padding:.06em .1em 0 0;color:#6d28d9;font-weight:bold}
/* imágenes */
img{display:block;max-width:88%;height:auto;margin:1.4em auto;border:1px solid #ddd;border-radius:3px;
  box-shadow:0 2px 10px #0003}
li img{max-width:100%}
/* código */
pre{font-size:.82rem;line-height:1.4;text-align:left;background:#f5f2fb;border-left:4px solid #6d28d9;
  padding:.8em 1em;overflow-x:auto;border-radius:2px;hyphens:none}
code{font-family:Consolas,'DejaVu Sans Mono',monospace;font-size:.88em;background:#f1edf9;padding:.05em .3em;border-radius:3px;hyphens:none}
pre code{background:none;padding:0}
/* notas */
blockquote{margin:1.4em 0;padding:.8em 1.2em;background:#f5f2fb;border-left:4px solid #a78bfa;color:#333;font-size:.96em}
blockquote p{margin:.3em 0}
/* tablas */
table{border-collapse:collapse;width:100%;margin:1.4em 0;font-size:.92rem;text-align:left}
th{background:#ede9fe;color:#2e1065;border-bottom:2px solid #6d28d9;padding:.45em .6em}
td{border-bottom:1px solid #e5e0f0;padding:.4em .6em;vertical-align:top}
tr:nth-child(even) td{background:#faf8fe}
ul,ol{padding-left:1.6em;margin:.4em 0 1em;text-align:left}
li{margin:.25em 0}
hr{border:0;border-top:1px solid #c4b5fd;margin:2em 30%}
@media print{html{background:none}body{box-shadow:none;margin:0;padding:0;max-width:none}}
@media(max-width:700px){body{padding:1.5em 1.2em;margin:0}}
"""

EPUB_CSS = """
body{line-height:1.5;text-align:justify;hyphens:auto}
p{margin:0 0 .7em}
a{color:#6d28d9;text-decoration:none}
h1{text-align:center;font-weight:normal;font-variant:small-caps;letter-spacing:.06em;color:#2e1065;
  margin:30% 0 1em;padding:1em 0;border-top:3px double #6d28d9;border-bottom:3px double #6d28d9;page-break-before:always}
h2{text-align:center;color:#2e1065;margin:1.5em 0 1em;padding-bottom:.4em;border-bottom:1px solid #c4b5fd;page-break-after:avoid}
h3{color:#4c1d95;margin:1.6em 0 .5em;page-break-after:avoid}
h4,h5{font-style:italic;color:#4c1d95;margin:1.2em 0 .4em}
img{display:block;max-width:100%;height:auto;margin:1em auto;border:1px solid #ccc}
pre{font-size:.78em;text-align:left;white-space:pre-wrap;word-wrap:break-word;background:#f5f2fb;
  border-left:3px solid #6d28d9;padding:.6em .8em;hyphens:none}
code{font-family:monospace;font-size:.9em;hyphens:none}
blockquote{margin:1em 0;padding:.5em 1em;background:#f5f2fb;border-left:3px solid #a78bfa}
table{border-collapse:collapse;width:100%;font-size:.85em;text-align:left}
th{background:#ede9fe;border-bottom:2px solid #6d28d9;padding:.3em}
td{border-bottom:1px solid #ddd;padding:.3em;vertical-align:top}
ul,ol{text-align:left}
"""


def run(cmd):
    subprocess.run(cmd, check=True, cwd=HERE)


def build(fmt):
    if not MS.exists():
        sys.exit("No hay manuscrito.md: corre primero 'manuscrito'")
    css()
    if fmt == "epub":
        run(["pandoc", "manuscrito.md", "-f", "markdown-implicit_figures", "--toc", "--toc-depth=2",
             "--epub-chapter-level=2", "--epub-cover-image=cover.png", "--css", "epub.css", "-o", "Minino_Reforjado.epub"])
    else:
        run(["pandoc", "manuscrito.md", "-f", "markdown-implicit_figures", "--toc", "--toc-depth=2",
             "--pdf-engine=xelatex", "-V", "geometry:margin=2.2cm", "-V", "papersize=a5",
             "-V", "fontsize=10pt", "-V", "lang=es", "-o", "Minino_Reforjado.pdf"])
    print("Listo:", "Minino_Reforjado." + fmt)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "manuscrito"
    if cmd in ("manuscrito", "todo"): make_manuscript()
    if cmd == "preview": preview()
    if cmd in ("epub", "todo"): build("epub")
    if cmd in ("pdf", "todo"): build("pdf")
