#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Рендеринг тела отчёта из Markdown в существующий .docx.

Титульный лист исходного файла сохраняется (все элементы до разрыва страницы
включительно), остальное тело заменяется содержимым Markdown-файла.
Оформление: Times New Roman 14 пт, полуторный интервал, абзацный отступ 1,25 см,
выравнивание по ширине; таблицы — 10 пт с заливкой шапки; рисунки — по центру
с подписью. Разрывы страниц — перед разделами с рисунками, перед «Списком
использованных источников» и перед приложениями. Поля 3,0/1,5/2,0/2,0 см,
номер страницы не выводится на титульном листе. Длинные тире и многоточия
заменяются на дефис и троеточие во всём документе, включая титульный лист.
"""

import os
import re
import sys

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Emu, Pt, Twips

PROFILE = "A"   # A — отчёты ПЗ-01…ПЗ-05, B — семинары ПЗ-06…ПЗ-08

FONT = "Times New Roman"
BODY_SZ = 14          # пт
TABLE_SZ = 10         # пт
INDENT = 709          # твипы (1,25 см)
CONTENT_W = 9355      # ширина полосы набора в твипах
MAX_PIC_W = Emu(5806440)


# --------------------------------------------------------------------------- #
#  разбор Markdown
# --------------------------------------------------------------------------- #
INLINE_RE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`)", re.S)


def parse_inline(text):
    """Возвращает список кортежей (текст, bold, italic, code)."""
    out = []
    for part in INLINE_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            out.append((part[2:-2], True, False, False))
        elif part.startswith("*") and part.endswith("*"):
            out.append((part[1:-1], False, True, False))
        elif part.startswith("`") and part.endswith("`"):
            out.append((part[1:-1], False, False, True))
        else:
            out.append((part, False, False, False))
    return out


def split_row(line):
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def parse_blocks(md):
    """Разбивает тело Markdown на блоки."""
    lines = md.split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue
        if s.startswith("#### "):
            blocks.append(("h4", s[5:].strip()))
            i += 1
        elif s.startswith("### "):
            blocks.append(("h3", s[4:].strip()))
            i += 1
        elif s.startswith("## "):
            blocks.append(("h2", s[3:].strip()))
            i += 1
        elif s.startswith("# "):
            i += 1
        elif s.startswith("---"):
            i += 1
        elif s.startswith("!["):
            m = re.match(r"!\[(.*?)\]\((.*?)\)", s)
            blocks.append(("img", m.group(2)))
            i += 1
        elif s.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q = lines[i].strip().lstrip(">").strip()
                if q:
                    quote.append(q)
                i += 1
            blocks.append(("quote", quote))
        elif s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            if len(rows) >= 2 and set("".join(rows[1])) <= set("-: "):
                header, body = rows[0], rows[2:]
            else:
                header, body = rows[0], rows[1:]
            blocks.append(("table", (header, body)))
        elif re.match(r"^[-*] ", s):
            items = []
            while i < len(lines) and re.match(r"^[-*] ", lines[i].strip()):
                items.append(re.sub(r"^[-*] ", "", lines[i].strip()))
                i += 1
            blocks.append(("ul", items))
        elif re.match(r"^\d+\. ", s):
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i].strip()):
                items.append(lines[i].strip())
                i += 1
            blocks.append(("ol", items))
        else:
            # мягкие переносы: строка, оканчивающаяся двумя пробелами,
            # продолжается следующей строкой внутри одного абзаца
            chunk = [s]
            while lines[i].endswith("  ") and i + 1 < len(lines) \
                    and lines[i + 1].strip():
                i += 1
                chunk.append(lines[i].strip())
            blocks.append(("p", " ".join(chunk)))
            i += 1
    return blocks


# --------------------------------------------------------------------------- #
#  низкоуровневые помощники docx
# --------------------------------------------------------------------------- #
def set_spacing(p, line=360, before=0, after=0):
    pPr = p._p.get_or_add_pPr()
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:line"), str(line))
    sp.set(qn("w:lineRule"), "auto")
    sp.set(qn("w:before"), str(before))
    sp.set(qn("w:after"), str(after))
    pPr.append(sp)


def set_ind(p, first_line=None, left=None, hanging=None):
    pPr = p._p.get_or_add_pPr()
    ind = OxmlElement("w:ind")
    if first_line is not None:
        ind.set(qn("w:firstLine"), str(first_line))
    if left is not None:
        ind.set(qn("w:left"), str(left))
    if hanging is not None:
        ind.set(qn("w:hanging"), str(hanging))
    pPr.append(ind)


def add_runs(p, chunks, size=BODY_SZ, bold_all=False):
    for text, b, i, code in chunks:
        parts = text.split("\n")
        r = p.add_run(parts[0])
        for extra in parts[1:]:
            r.add_break()
            r.add_text(extra)
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), r.font.name)
        r.font.size = Pt(size)
        r.bold = bool(b or bold_all)
        r.italic = bool(i or code)


def body_paragraph(doc, text, indent=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                   left=None, hanging=None, size=BODY_SZ):
    p = doc.add_paragraph()
    if PROFILE == "B":
        set_spacing(p, line=360, after=80)
        if left is not None or hanging is not None:
            set_ind(p, left=left, hanging=hanging)
        else:
            set_ind(p, first_line=INDENT)
        p.alignment = align
        add_runs(p, parse_inline(text), size=size)
        return p
    set_spacing(p)
    if left is not None or hanging is not None:
        set_ind(p, left=left, hanging=hanging)
    elif indent:
        set_ind(p, first_line=INDENT)
    p.alignment = align
    add_runs(p, parse_inline(text), size=size)
    return p


def heading(doc, text, level):
    if PROFILE == "B":
        p = doc.add_paragraph()
        pPr = p._p.get_or_add_pPr()
        pPr.append(OxmlElement("w:keepNext"))
        sp = OxmlElement("w:spacing")
        sp.set(qn("w:before"), "240" if level == 1 else "160")
        sp.set(qn("w:after"), "120")
        pPr.append(sp)
        set_ind(p, first_line=0)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(text)
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        r.font.size = Pt(14 if level == 1 else 13)
        r.bold = True
        if level == 1:
            c = OxmlElement("w:color")
            c.set(qn("w:val"), "1F4E79")
            r._element.rPr.append(c)
        return p
    p = doc.add_paragraph(style="Heading %d" % level)
    r = p.add_run(text)
    r.font.name = FONT
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    r.font.size = Pt(16 if level == 1 else 15)
    r.bold = True
    r.italic = False
    return p


def page_break(doc):
    p = doc.add_paragraph()
    set_spacing(p, line=240, after=0)
    p.add_run().add_break(docx.enum.text.WD_BREAK.PAGE)


def column_widths(header, rows):
    """Ширины колонок пропорционально содержимому, в твипах."""
    ncol = len(header)
    weight = []
    for c in range(ncol):
        cells = [header[c]] + [r[c] if c < len(r) else "" for r in rows]
        longest = max(len(re.sub(r"[*`]", "", x)) for x in cells)
        avg = sum(len(re.sub(r"[*`]", "", x)) for x in cells) / len(cells)
        weight.append(max(6.0, (longest + 3 * avg) / 4.0) ** 0.75)
    total = sum(weight)
    widths = [max(567, int(CONTENT_W * w / total)) for w in weight]
    # нормировка к ширине полосы набора
    k = CONTENT_W / sum(widths)
    widths = [int(w * k) for w in widths]
    widths[-1] += CONTENT_W - sum(widths)
    return widths


def add_table(doc, header, rows):
    ncol = len(header)
    t = doc.add_table(rows=0, cols=ncol)
    t.style = "Table Grid"
    t.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    t.autofit = PROFILE == "B"
    tblPr = t._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "autofit" if PROFILE == "B" else "fixed")
    tblPr.append(layout)
    widths = column_widths(header, rows)
    grid = t._tbl.find(qn("w:tblGrid"))
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(w))

    def fill(cells, values, head):
        for cell, value, w in zip(cells, values, widths):
            cell.width = Twips(w)
            tcPr = cell._tc.get_or_add_tcPr()
            if PROFILE == "B":
                va = OxmlElement("w:vAlign")
                va.set(qn("w:val"), "center")
                tcPr.append(va)
            mar = OxmlElement("w:tcMar")
            margins = ((("top", 80), ("start", 80), ("bottom", 80), ("end", 80))
                       if PROFILE == "B" else
                       (("top", 55), ("start", 65), ("bottom", 55), ("end", 65)))
            for tag, val in margins:
                e = OxmlElement("w:" + tag)
                e.set(qn("w:w"), str(val))
                e.set(qn("w:type"), "dxa")
                mar.append(e)
            tcPr.append(mar)
            if PROFILE != "B":
                va = OxmlElement("w:vAlign")
                va.set(qn("w:val"), "center")
                tcPr.append(va)
            if head:
                shd = OxmlElement("w:shd")
                shd.set(qn("w:fill"), "D9EAF7" if PROFILE == "B" else "D9E2F3")
                tcPr.append(shd)
            p = cell.paragraphs[0]
            if PROFILE == "B":
                set_spacing(p, line=240, after=0)
                set_ind(p, first_line=0)
                add_runs(p, parse_inline(value), size=TABLE_SZ, bold_all=head)
                continue
            set_spacing(p, line=240, after=0)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if head else WD_ALIGN_PARAGRAPH.LEFT
            add_runs(p, parse_inline(value), size=TABLE_SZ, bold_all=head)

    row = t.add_row()
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)
    fill(row.cells, header, True)
    for values in rows:
        values = (values + [""] * ncol)[:ncol]
        row = t.add_row()
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        fill(row.cells, values, False)
    p = doc.add_paragraph()
    set_spacing(p, line=240, after=0)
    return t


def add_picture(doc, path):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pPr.append(OxmlElement("w:keepNext"))
    pPr.append(OxmlElement("w:keepLines"))
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(path, width=MAX_PIC_W)


def add_caption(doc, text):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:after"), "120")
    pPr.append(sp)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_runs(p, parse_inline(text), bold_all=True)


# --------------------------------------------------------------------------- #
#  основной рендер
# --------------------------------------------------------------------------- #
def clear_after_title(doc):
    """Оставляет титульный лист и всё, что идёт до первого раздела «1. …»."""
    body = doc.element.body
    kids = list(body.iterchildren())
    cut = None
    for i, k in enumerate(kids):
        if not k.tag.endswith("}p"):
            continue
        txt = "".join(k.itertext()).strip()
        if 'w:pStyle w:val="Heading1"' in k.xml or re.match(r"^1\.\s+\S", txt):
            cut = i - 1
            break
    if cut is None:
        for i, k in enumerate(kids):
            if k.tag.endswith("}p") and 'w:type="page"' in k.xml:
                cut = i
                break
    for k in kids[cut + 1:]:
        if k.tag.endswith("}sectPr"):
            continue
        body.remove(k)


def normalize_layout(doc):
    """Приводит оформление к требованиям отчёта.

    Поля: левое 3,0 см, правое 1,5 см, верхнее и нижнее по 2,0 см.
    Номер страницы не выводится на титульном листе (titlePg).
    Шрифт номера страницы — Times New Roman 12 пт.
    """
    sec = doc.sections[0]
    sec.left_margin = Twips(1701)
    sec.right_margin = Twips(850)
    sec.top_margin = Twips(1134)
    sec.bottom_margin = Twips(1134)
    sec.different_first_page_header_footer = True
    for ftr in (sec.footer, sec.first_page_footer, sec.even_page_footer):
        for p in ftr.paragraphs:
            for r in p.runs:
                r.font.name = FONT
                r.font.size = Pt(12)


def sweep_dashes(doc):
    """Убирает длинные тире и многоточия во всём документе, включая титул.

    Тело отчёта приходит из .md уже нормализованным; титульный лист
    сохраняется из исходного файла, поэтому здесь он подчищается отдельно.
    """
    from docx.text.paragraph import Paragraph

    for p_el in doc.element.body.iter(qn("w:p")):
        p = Paragraph(p_el, doc)
        if "—" not in p.text and "…" not in p.text:
            continue
        for r in p.runs:
            if "—" in r.text:
                r.text = r.text.replace(" — ", " - ")
            if "…" in r.text:
                r.text = r.text.replace("…", "...")
        if "—" in p.text or "…" in p.text:
            # тире разбито между run'ами — склеиваем параграф
            text = p.text.replace(" — ", " - ").replace("…", "...")
            if p.runs:
                p.runs[0].text = text
                for r in p.runs[1:]:
                    r.text = ""


def render(md_path, docx_path, out_path=None):
    md = open(md_path, encoding="utf-8").read()
    base = os.path.dirname(os.path.abspath(md_path))
    # тело начинается с первого заголовка второго уровня «## 1. …»
    m = re.search(r"^## \d.*$", md, re.M)
    body_md = md[m.start():]
    blocks = parse_blocks(body_md)

    global PROFILE
    doc = docx.Document(docx_path)
    PROFILE = "A" if 'w:pStyle w:val="Heading1"' in doc.element.body.xml else "B"
    clear_after_title(doc)

    # картинки требуют разрыва страницы перед своим разделом
    img_sections = set()
    for i, (kind, _) in enumerate(blocks):
        if kind == "img":
            for j in range(i, -1, -1):
                if blocks[j][0] in ("h2", "h3", "h4"):
                    img_sections.add(j)
                    break

    for i, (kind, payload) in enumerate(blocks):
        if kind in ("h2", "h3", "h4"):
            # новые страницы: перед рисунком, перед списком источников,
            # перед приложением
            if (i in img_sections or payload.startswith("Приложение")
                    or "Список использованных источников" in payload):
                page_break(doc)
            heading(doc, payload, 1 if kind == "h2" else 2)
        elif kind == "p":
            body_paragraph(doc, payload)
        elif kind == "quote":
            for q in payload:
                p = doc.add_paragraph()
                set_spacing(p, line=360)
                set_ind(p, first_line=INDENT)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                add_runs(p, parse_inline(q))
        elif kind == "ul":
            for item in payload:
                body_paragraph(doc, "• " + item, left=INDENT, hanging=312)
        elif kind == "ol":
            for item in payload:
                body_paragraph(doc, item, left=INDENT, hanging=369)
        elif kind == "table":
            add_table(doc, payload[0], payload[1])
        elif kind == "img":
            add_picture(doc, os.path.join(base, payload))
            nxt = blocks[i + 1] if i + 1 < len(blocks) else None
            if nxt and nxt[0] == "p" and re.match(r"\*{1,2}Рисунок", nxt[1]):
                add_caption(doc, nxt[1])
                blocks[i + 1] = ("skip", "")
        elif kind == "skip":
            continue

    sweep_dashes(doc)
    normalize_layout(doc)
    doc.save(out_path or docx_path)


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
