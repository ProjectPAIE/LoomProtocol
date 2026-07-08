#!/usr/bin/env python3
"""
compile_epub.py — Package the Markdown Reader's Edition into a valid, formatted EPUB book.
"""
import os
import re
import uuid
import zipfile
import shutil
from pathlib import Path

def markdown_to_html(md_text):
    # Very simple markdown-to-HTML helper for basic tags
    html = md_text
    
    # Escape HTML special chars (but keep existing brackets/quotes safe)
    html = html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # Restore block elements
    # Bold
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    # Italic
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    # Headings
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Paragraphs (lines separated by double newlines)
    paragraphs = []
    for p in html.split('\n\n'):
        p_strip = p.strip()
        if not p_strip:
            continue
        if p_strip.startswith('<h') or p_strip.startswith('---'):
            paragraphs.append(p_strip)
        else:
            # Convert single newlines inside paragraph to space
            content = p_strip.replace('\n', ' ')
            paragraphs.append(f"<p>{content}</p>")
            
    return "\n".join(paragraphs)

def compile_epub():
    base_dir = Path("/Users/user/Projects/PAIE/Demo/Loom_Protocol/book")
    md_file = base_dir / "wagahai_wa_neko_de_aru_annotated_clean_reader.md"
    cover_file = base_dir / "cover.jpg"
    out_epub = base_dir / "wagahai_wa_neko_de_aru_consensus_edition.epub"

    print("📖 Starting EPUB compilation...")

    if not md_file.exists():
        print(f"❌ Markdown file not found: {md_file}")
        return
        
    # Read Markdown
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Parse title and author
    title = "I Am a Cat (Consensus Edition)"
    author = "Natsume Soseki"
    for line in md_content.split("\n")[:10]:
        if line.startswith("# "):
            title = line.replace("# ", "").replace("Consensus Debate Transcript:", "").strip()
        elif "Author:" in line:
            author = line.replace("**Author:**", "").replace("Author:", "").strip()

    # Split by section
    sections = re.split(r"(?=\n## Section \d+)", md_content)
    header = sections[0]
    chapters_md = sections[1:]

    # Create temporary build dir
    build_dir = base_dir / "build_epub"
    build_dir.mkdir(exist_ok=True)
    oebps_dir = build_dir / "OEBPS"
    oebps_dir.mkdir(exist_ok=True)
    meta_dir = build_dir / "META-INF"
    meta_dir.mkdir(exist_ok=True)

    # 1. mimetype file
    with open(build_dir / "mimetype", "w", encoding="utf-8") as f:
        f.write("application/epub+zip")

    # 2. container.xml
    with open(meta_dir / "container.xml", "w", encoding="utf-8") as f:
        f.write("""<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")

    # 3. Stylesheet
    with open(oebps_dir / "stylesheet.css", "w", encoding="utf-8") as f:
        f.write("""body { font-family: sans-serif; line-height: 1.5; padding: 1em; }
h1 { text-align: center; color: #111; margin-bottom: 2em; }
h2 { border-bottom: 1px solid #ddd; padding-bottom: 0.3em; margin-top: 1.5em; }
p { margin-bottom: 1em; text-indent: 1em; text-align: justify; }
.annotations { font-size: 0.85em; color: #555; background: #f9f9f9; padding: 1em; border-left: 3px solid #777; margin-top: 1.5em; }
.cover-img { text-align: center; max-width: 100%; height: auto; }""")

    # Write Title Page HTML
    with open(oebps_dir / "titlepage.xhtml", "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="stylesheet.css" />
</head>
<body>
  <h1>{title}</h1>
  <p style="text-align: center; font-weight: bold;">Author: {author}</p>
  <p style="text-align: center; font-style: italic; color: #666;">PAIE Multi-Agent Consensus Translation Edition</p>
</body>
</html>""")

    # 4. Copy Cover Image if exists
    manifest_items = [
        '<item id="stylesheet" href="stylesheet.css" media-type="text/css"/>',
        '<item id="titlepage" href="titlepage.xhtml" media-type="application/xhtml+xml"/>'
    ]
    spine_items = [
        '<itemref idref="titlepage"/>'
    ]
    
    if cover_file.exists():
        shutil.copy(cover_file, oebps_dir / "cover.jpg")
        manifest_items.append('<item id="cover-image" href="cover.jpg" media-type="image/jpeg"/>')
        # Create cover.xhtml
        with open(oebps_dir / "cover.xhtml", "w", encoding="utf-8") as f:
            f.write(f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Cover</title>
  <link rel="stylesheet" type="text/css" href="stylesheet.css" />
</head>
<body style="margin: 0; padding: 0; text-align: center; background-color: #000;">
  <div style="height: 100%; display: flex; align-items: center; justify-content: center;">
    <img src="cover.jpg" alt="Cover" style="max-width: 100%; max-height: 100%; object-fit: contain;" />
  </div>
</body>
</html>""")
        manifest_items.insert(0, '<item id="coverpage" href="cover.xhtml" media-type="application/xhtml+xml"/>')
        spine_items.insert(0, '<itemref idref="coverpage"/>')

    # 5. Write Chapters
    for idx, chap_md in enumerate(chapters_md):
        chap_id = f"chapter_{idx+1}"
        filename = f"{chap_id}.xhtml"
        html_content = markdown_to_html(chap_md)
        
        # Wrap annotations in a clean container
        html_content = html_content.replace("&lt;p&gt;&lt;em&gt;Annotations:&lt;/em&gt;&lt;/p&gt;", '<div class="annotations"><strong>Scholarly Annotations:</strong>')
        html_content = html_content.replace("<p><em>Annotations:</em></p>", '<div class="annotations"><strong>Scholarly Annotations:</strong>')
        if '<div class="annotations">' in html_content:
            html_content += "</div>"
            
        with open(oebps_dir / filename, "w", encoding="utf-8") as f:
            f.write(f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Section {idx+1}</title>
  <link rel="stylesheet" type="text/css" href="stylesheet.css" />
</head>
<body>
  {html_content}
</body>
</html>""")
        manifest_items.append(f'<item id="{chap_id}" href="{filename}" media-type="application/xhtml+xml"/>')
        spine_items.append(f'<itemref idref="{chap_id}"/>')

    # 6. content.opf
    manifest_str = "\n    ".join(manifest_items)
    spine_str = "\n    ".join(spine_items)
    book_uuid = f"urn:uuid:{uuid.uuid4()}"
    
    with open(oebps_dir / "content.opf", "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:identifier id="bookid">{book_uuid}</dc:identifier>
    <dc:language>en</dc:language>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
    {manifest_str}
  </manifest>
  <spine toc="ncx">
    {spine_str}
  </spine>
</package>""")

    # 7. toc.ncx (Table of Contents)
    nav_points = []
    for idx in range(len(chapters_md)):
        nav_points.append(f"""    <navPoint id="navpoint-{idx+1}" playOrder="{idx+1}">
      <navLabel><text>Section {idx+1}</text></navLabel>
      <content src="chapter_{idx+1}.xhtml"/>
    </navPoint>""")
    nav_points_str = "\n".join(nav_points)

    with open(oebps_dir / "toc.ncx", "w", encoding="utf-8") as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD NCX 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{book_uuid}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{title}</text></docTitle>
  <navMap>
    {nav_points_str}
  </navMap>
</ncx>""")

    # 8. Zip it all up (mimetype MUST be first and UNCOMPRESSED)
    with zipfile.ZipFile(out_epub, 'w', zipfile.ZIP_DEFLATED) as epub:
        # mimetype must be stored (uncompressed)
        epub.write(build_dir / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        
        # META-INF/container.xml
        epub.write(meta_dir / "container.xml", "META-INF/container.xml")
        
        # OEBPS contents
        for file in oebps_dir.glob("*"):
            epub.write(file, f"OEBPS/{file.name}")

    # Cleanup build dir
    shutil.rmtree(build_dir)
    print(f"🎉 EPUB successfully compiled to:\n   👉 {out_epub}")

if __name__ == "__main__":
    compile_epub()
