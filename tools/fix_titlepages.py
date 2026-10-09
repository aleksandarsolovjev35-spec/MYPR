#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Приведение титульных листов отчётов к единому году выполнения.

* год на титульном листе отчётов ПЗ-01…ПЗ-05 заменяется на 2026;
* строка «Дата проведения: …» в семинарах ПЗ-07, ПЗ-08 заменяется строкой
  «Год выполнения: 2026»;
* в семинаре ПЗ-06 строка «Год выполнения: 2026» добавляется;
* в ПЗ-04 на титульный лист добавляется подзаголовок с объектом анализа.
"""

import copy
import glob
import os
import re

import docx
from docx.text.paragraph import Paragraph

YEAR = "2026"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def paragraphs(doc):
    for k in doc.element.body.iterchildren():
        if k.tag.endswith("}p"):
            yield Paragraph(k, doc)


def set_text(par, text):
    runs = par.runs
    runs[0].text = text
    for r in runs[1:]:
        r.text = ""


def main():
    for path in sorted(glob.glob(os.path.join(ROOT, "П-41*.docx"))):
        doc = docx.Document(path)
        changed = []
        pars = list(paragraphs(doc))
        head = pars[:30]

        for p in head:
            t = p.text.strip()
            if re.fullmatch(r"(19|20)\d\d", t):
                if t != YEAR:
                    set_text(p, YEAR)
                    changed.append("год %s → %s" % (t, YEAR))
                break
            if t.startswith("Дата проведения"):
                set_text(p, "Год выполнения: %s" % YEAR)
                changed.append("дата проведения → год выполнения")
                break
            if t.startswith("Год выполнения"):
                # строка уже есть — проверяем, что год верный
                if YEAR not in t:
                    set_text(p, "Год выполнения: %s" % YEAR)
                    changed.append("год выполнения исправлен")
                break
        else:
            # год на титуле отсутствует — добавляем после строки «Киноматериал»
            for p in head:
                if p.text.strip().startswith("Киноматериал"):
                    new = copy.deepcopy(p._p)
                    p._p.addnext(new)
                    set_text(Paragraph(new, doc), "Год выполнения: %s" % YEAR)
                    changed.append("добавлен год выполнения")
                    break

        if path.endswith("ПЗ-04.docx"):
            for p in head:
                if p.text.strip().startswith("«ПРИНЯТИЕ РЕШЕНИЙ"):
                    if "Шереметьево" not in pars[head.index(p) + 1].text:
                        new = copy.deepcopy(p._p)
                        p._p.addnext(new)
                        np = Paragraph(new, doc)
                        set_text(np, "(на примере аэропорта «Шереметьево»)")
                        r = np.runs[0]
                        r.bold = False
                        r.font.size = docx.shared.Pt(14)
                        sp = new.find(
                            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr"
                        ).find(
                            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}spacing"
                        )
                        if sp is not None:
                            sp.set(
                                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}before",
                                "240",
                            )
                        changed.append("добавлен подзаголовок")
                    break

        if changed:
            doc.save(path)
        print(os.path.basename(path), "—", ", ".join(changed) or "без изменений")


if __name__ == "__main__":
    main()
