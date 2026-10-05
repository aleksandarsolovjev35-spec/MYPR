#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Интеллект-карта результатов мозговой атаки для ПЗ-04 (аэропорт «Шереметьево»)."""

import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

plt.rcParams["font.family"] = "DejaVu Sans"

W, H = 15.4, 11.4
FIG = plt.figure(figsize=(W, H), dpi=100)
AX = FIG.add_axes([0, 0, 1, 1])
AX.set_xlim(0, W)
AX.set_ylim(0, H)
AX.axis("off")
AX.set_facecolor("white")

DARK = "#1F3864"
GREY = "#3B4A5A"
PICK = "#E8F3E8"

BRANCHES = [
    # (заголовок, цвет, позиция прямоугольника (x, y, w, h), сторона, пункты)
    ("ПАССАЖИРСКИЕ ФОРМАЛЬНОСТИ", "#2E6DA4", (0.45, 7.55, 4.3, 2.9), "left", [
        ("Упрощение таможенного и пограничного контроля", True),
        ("Стойки самостоятельной регистрации", False),
        ("«Единое окно» для трансферных пассажиров", False),
    ]),
    ("СЕРВИС И ПЕРСОНАЛ", "#4E6E8E", (0.45, 4.25, 4.3, 2.8), "left", [
        ("Стандарты обслуживания, обучение и мотивация персонала", False),
        ("Развитие коммерческой зоны и зон ожидания", False),
    ]),
    ("ТРАНСПОРТНАЯ СВЯЗНОСТЬ", "#9A7B2F", (0.45, 0.6, 4.3, 3.15), "left", [
        ("Сообщение между «Шереметьево-I» и «Шереметьево-II»", False),
        ("Подъездные дороги и парковки", False),
        ("Скоростная связь с городом", False),
    ]),
    ("ПЕРРОННОЕ ОБСЛУЖИВАНИЕ", "#7E4E9B", (10.65, 7.55, 4.3, 2.9), "right", [
        ("Автобусы на лётном поле и новые телескопические трапы", True),
        ("Сокращение времени заправки и обслуживания судна", False),
        ("Оптимизация технологического графика", False),
    ]),
    ("ИНФОРМАЦИЯ, БАГАЖ, КАЧЕСТВО", "#1F7A5A", (10.65, 4.25, 4.3, 2.8), "right", [
        ("Навигация и информирование пассажиров", True),
        ("Модернизация обработки и выдачи багажа", False),
        ("Система показателей качества обслуживания", False),
    ]),
    ("ИНФРАСТРУКТУРА И ТЕХНИКА", "#B5653A", (10.65, 0.6, 4.3, 3.15), "right", [
        ("Строительство новых терминалов", False),
        ("Реконструкция взлётно-посадочной полосы и слоты", False),
        ("Обновление технического оснащения", False),
        ("Электроосвещение и энергосбережение", False),
    ]),
]

CENTER = (5.35, 4.0, 4.7, 3.1)   # x, y, w, h


def rounded(x, y, w, h, fc, ec, lw=1.6, z=2, pad=0.02):
    box = FancyBboxPatch((x + pad, y + pad), w - 2 * pad, h - 2 * pad,
                         boxstyle="round,pad=0.02,rounding_size=0.18",
                         linewidth=lw, facecolor=fc, edgecolor=ec, zorder=z)
    AX.add_patch(box)
    return box


# ------------------------------- связи ------------------------------------ #
cx, cy, cw, ch = CENTER
ccx, ccy = cx + cw / 2, cy + ch / 2
for title, color, (bx, by, bw, bh), side, items in BRANCHES:
    px = bx + bw if side == "left" else bx
    py = by + bh / 2
    if side == "left":
        start = (cx, ccy)
    else:
        start = (cx + cw, ccy)
    AX.plot([start[0], (start[0] + px) / 2, px],
            [start[1], py, py], color=color, lw=5, solid_capstyle="round",
            zorder=1, alpha=0.9)

# ------------------------------- центр ------------------------------------ #
rounded(cx, cy, cw, ch, DARK, DARK, lw=0, z=3)
AX.text(ccx, ccy + 0.62, "ПОВЫШЕНИЕ КАЧЕСТВА\nРАБОТЫ АЭРОПОРТА\n«ШЕРЕМЕТЬЕВО»",
        ha="center", va="center", color="white", fontsize=19, fontweight="bold",
        linespacing=1.35, zorder=4)
AX.text(ccx, ccy - 0.85,
        "пассажиры • воздушные суда •\nинфраструктура • сервис",
        ha="center", va="center", color="#CBD6E8", fontsize=12.5,
        linespacing=1.4, zorder=4)

# ------------------------------- ветви ------------------------------------ #
for title, color, (bx, by, bw, bh), side, items in BRANCHES:
    rounded(bx, by, bw, bh, "#F6F8FC", color, lw=1.8, z=3)
    head_h = 0.52
    AX.add_patch(FancyBboxPatch((bx + 0.02, by + bh - head_h - 0.02),
                                bw - 0.04, head_h,
                                boxstyle="round,pad=0.02,rounding_size=0.16",
                                linewidth=0, facecolor=color, zorder=4))
    AX.text(bx + bw / 2, by + bh - head_h / 2 - 0.02, title, ha="center",
            va="center", color="white", fontsize=12.5, fontweight="bold",
            zorder=5)

    y = by + bh - head_h - 0.42
    for text, picked in items:
        lines = textwrap.wrap(text, 34)
        block_h = 0.3 * len(lines)
        if picked:
            AX.add_patch(Rectangle((bx + 0.12, y - block_h + 0.14), bw - 0.28,
                                   block_h + 0.06, facecolor=PICK,
                                   edgecolor="none", zorder=4))
            AX.text(bx + 0.3, y, "★", ha="center", va="center", color="#1F7A5A",
                    fontsize=12, zorder=5)
        else:
            AX.text(bx + 0.32, y, "•", ha="center", va="center", color=color,
                    fontsize=14, zorder=5)
        AX.text(bx + 0.52, y, "\n".join(lines), ha="left", va="center",
                color="#1A1A1A" if picked else "#222222", fontsize=11.5,
                fontweight="bold" if picked else "normal", linespacing=1.35,
                zorder=5)
        y -= block_h + 0.22

# ------------------------------- заголовок и легенда ----------------------- #
AX.text(W / 2, H - 0.45, "ИНТЕЛЛЕКТ-КАРТА РЕЗУЛЬТАТОВ МОЗГОВОЙ АТАКИ",
        ha="center", va="center", color=DARK, fontsize=22, fontweight="bold")
AX.add_patch(Rectangle((5.75, 9.42), 0.40, 0.32, facecolor=PICK,
                       edgecolor="#1F7A5A", linewidth=1.2))
AX.text(6.32, 9.58, "★ — предложения, отобранные\n      экспертной группой",
        ha="left", va="center", fontsize=11.5, color="#333333",
        linespacing=1.3)

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "П-41_Соловьев_АС_ПЗ-04_assets", "интеллект-карта.png")
FIG.savefig(out, dpi=100, facecolor="white")
print("saved", out)
