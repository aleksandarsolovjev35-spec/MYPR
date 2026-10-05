#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Вырезает из сканов учебника (Part1.pdf, Part2.pdf) страницы с заданиями
практических занятий РАЗДЕЛА II и сохраняет их в папку «Задания_учебника».

Разворот скана содержит две книжные страницы:
  Part1.pdf, лист i -> книжные страницы 2i+2 (слева) и 2i+3 (справа);
  Part2.pdf, лист i -> книжные страницы 2i+180 (слева) и 2i+181 (справа).

Для каждой практической работы создаётся отдельный PDF, где один лист —
одна книжная страница. Дополнительно создаётся общий PDF со всеми страницами
и PNG-превью каждой страницы.
"""
import os
import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Задания_учебника")
PREVIEW = os.path.join(OUT, "Превью_PNG")

# (имя файла, подпись, список книжных страниц)
WORKS = [
    ("ПЗ-01_с.169-170", "Практическое занятие № 1. Анализ факторов, критериев и ограничений", [169, 170]),
    ("ПЗ-02_с.171-172", "Практическое занятие № 2. Принятие решения с учётом ограничивающих факторов", [171, 172]),
    ("ПЗ-03_с.173-175", "Практическое занятие № 3. Уровни принятия решений (с. 175 — тест)", [173, 174, 175]),
    ("ПЗ-04_с.176-178", "Практическое занятие № 4. Мозговая атака, аэропорт «Шереметьево»", [176, 177, 178]),
    ("ПЗ-05_с.179-180", "Практическое занятие № 5. Экспертные методы (с. 180 — тест)", [179, 180]),
    ("ПЗ-07_с.181-183", "Практическое занятие № 6 учебника = ПЗ-07. Метод сценариев (с. 183 — тест)", [181, 182, 183]),
    ("ПЗ-08_с.184-185", "Практическое занятие № 7 учебника = ПЗ-08. Пошаговый разбор ситуаций", [184, 185]),
]

MARGIN = 0.02  # небольшой запас по краям колонки


def locate(book_page: int):
    """Возвращает (файл, индекс листа, страница слева?) для книжной страницы."""
    if book_page <= 179:
        return "Part1.pdf", (book_page - 2) // 2, book_page % 2 == 0
    return "Part2.pdf", (book_page - 180) // 2, book_page % 2 == 0


def clip_rect(page, left: bool) -> pymupdf.Rect:
    r = page.rect
    half = r.width / 2
    if left:
        return pymupdf.Rect(0, 0, half * (1 + MARGIN), r.height)
    return pymupdf.Rect(half * (1 - MARGIN), 0, r.width, r.height)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PREVIEW, exist_ok=True)
    src = {name: pymupdf.open(os.path.join(ROOT, name)) for name in ("Part1.pdf", "Part2.pdf")}

    everything = pymupdf.open()
    for fname, title, pages in WORKS:
        doc = pymupdf.open()
        for bp in pages:
            name, idx, left = locate(bp)
            page = src[name][idx]
            clip = clip_rect(page, left)
            for target in (doc, everything):
                new = target.new_page(width=clip.width, height=clip.height)
                new.show_pdf_page(new.rect, src[name], idx, clip=clip)
            pix = page.get_pixmap(dpi=150, clip=clip, colorspace=pymupdf.csGRAY)
            pix.save(os.path.join(PREVIEW, f"с.{bp}.png"))
        doc.set_metadata({"title": title})
        doc.save(os.path.join(OUT, fname + ".pdf"), deflate=True, garbage=4)
        doc.close()
        print("готово:", fname + ".pdf", pages)

    everything.set_metadata({"title": "Задания практических занятий, РАЗДЕЛ II, с. 169–185"})
    everything.save(os.path.join(OUT, "Все_задания_с.169-185.pdf"), deflate=True, garbage=4)
    everything.close()
    print("готово: Все_задания_с.169-185.pdf")


if __name__ == "__main__":
    main()
