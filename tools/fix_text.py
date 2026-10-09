#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Нормализация текста отчётов (md-исходники): убирает «AI-маркеры».

- длинное тире « — » заменяется на дефис « - »; в заголовках и пунктах
  маркированных списков — на двоеточие (там оно читается естественнее);
- многоточие «…» заменяется на троеточие «...";
- вложенные кавычки „…“ заменяются на «…»;
- подпись рисунка в ПЗ-01 приводится к единому виду (**…**), чтобы
  рендерер распознал её как подпись.

Запуск: python3 tools/fix_text.py
"""

import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fix_line(line):
    if re.match(r"^#{2,4} ", line):
        # заголовок: «Тема — пояснение» -> «Тема: пояснение»
        return line.replace(" — ", ": ")
    if line.startswith("- "):
        # пункт списка: «что — чем компенсируется» -> «что: чем компенсируется»
        return line.replace(" — ", ": ")
    return line.replace(" — ", " - ")


def main():
    for path in sorted(glob.glob(os.path.join(ROOT, "П-41*.md"))):
        src = open(path, encoding="utf-8").read()
        out = "\n".join(fix_line(ln) for ln in src.split("\n"))
        out = out.replace("…", "...")
        out = out.replace("„", "«").replace("“", "»")
        if path.endswith("ПЗ-01.md"):
            out = out.replace(
                "*Рисунок 1 - Дерево решений по выбранному направлению изменений*",
                "**Рисунок 1 - Дерево решений по выбранному направлению изменений**",
            )
        if out != src:
            open(path, "w", encoding="utf-8").write(out)
            print(os.path.basename(path), "- исправлено")
        else:
            print(os.path.basename(path), "- без изменений")


if __name__ == "__main__":
    main()
