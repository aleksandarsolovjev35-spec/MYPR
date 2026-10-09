#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Инспекция оформления .docx: разрывы страниц, шрифты, размеры, колонтитулы."""

import glob
import os
import sys

import docx
from docx.oxml.ns import qn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "П-41*.docx")))
    for path in paths:
        doc = docx.Document(path)
        body = doc.element.body
        n_p = len(doc.paragraphs)
        n_pagebreaks = sum(
            1 for br in body.iter(qn("w:br")) if br.get(qn("w:type")) == "page"
        )
        n_pbb = len(body.findall(".//" + qn("w:pageBreakBefore")))
        fonts = {}
        sizes = {}
        for r in body.iter(qn("w:r")):
            rpr = r.find(qn("w:rPr"))
            if rpr is None:
                continue
            rf = rpr.find(qn("w:rFonts"))
            if rf is not None and rf.get(qn("w:ascii")):
                fonts[rf.get(qn("w:ascii"))] = fonts.get(rf.get(qn("w:ascii")), 0) + 1
            sz = rpr.find(qn("w:sz"))
            if sz is not None:
                s = int(sz.get(qn("w:val"))) / 2
                sizes[s] = sizes.get(s, 0) + 1
        sec = doc.sections[0]
        # колонтитулы
        foot_parts = [r for r in sec.footer.part.rels.values() if "header" not in r.reltype]
        has_footer_ref = bool(sec.footer._element.findall(qn("w:p")))
        # номер страницы в футере?
        ftr_xml = sec.footer._element.xml
        has_pagenum = "PAGE" in ftr_xml
        # заголовки разделов (Heading1) и наличие перед ними разрыва
        heads = []
        for p in doc.paragraphs:
            if p.style.name.startswith("Heading") or (
                p.runs and p.runs[0].bold and p.text.strip().startswith(("1.", "2.", "3."))
            ):
                heads.append(p.text.strip()[:60])
        print(f"== {os.path.basename(path)}")
        print(f"   paras={n_p}, pagebreaks={n_pagebreaks}, pageBreakBefore={n_pbb}, "
              f"footer_pagenum={has_pagenum}")
        print(f"   fonts={fonts}")
        print(f"   sizes={sizes}")
        print(f"   margins L={sec.left_margin} R={sec.right_margin} "
              f"T={sec.top_margin} B={sec.bottom_margin} "
              f"page={sec.page_width}x{sec.page_height}")
        print(f"   headings({len(heads)}): {heads[:12]}")


if __name__ == "__main__":
    main()
