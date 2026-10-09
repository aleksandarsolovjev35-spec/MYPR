#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Перерисовка рисунков отчётов в строгом стиле draw.io (UML-нотация).

Общий стиль: белый фон, чёрные линии, рубленые рубежи без теней и градиентов;
скруглённые прямоугольники (действия), квадраты и круги (дерево игры),
начальный (●) и конечный (◉) узлы, стрелки с открытой «V»-образной головкой,
ортогональные соединители. Заголовки и легенды внутри картинки убраны —
названия рисунков вынесены в подписи в документе. Единственный акцент:
в интеллект-карте ПЗ-04 выбранные экспертами пункты отмечены ★ и зелёным
цветом (как описано в тексте отчёта).

Запуск: python3 tools/redraw_figures.py
"""

import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, PathPatch
from matplotlib.path import Path

plt.rcParams["font.family"] = "DejaVu Sans"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DPI = 150

BLACK = "#000000"
GREY = "#555555"
GREEN_TXT = "#375623"


# --------------------------------------------------------------------------- #
#  общие помощники
# --------------------------------------------------------------------------- #
def new_canvas(w, h):
    fig = plt.figure(figsize=(w, h), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    ax.set_facecolor("white")
    return fig, ax


def char_w(fs):
    """Оценка ширины среднего знака DejaVu Sans в дюймах."""
    return 0.68 * fs / 72.0


def wrap(text, width, fs):
    n = max(8, int(width / char_w(fs)))
    return textwrap.fill(text, n)


def rbox(ax, x, y, w, h, fc="white", ec=BLACK, lw=1.3, r=0.10):
    b = FancyBboxPatch((x, y), w, h,
                       boxstyle="round,pad=0,rounding_size=%.3f" % r,
                       fc=fc, ec=ec, lw=lw)
    ax.add_patch(b)
    return b


def sqbox(ax, x, y, w, h, fc="white", ec=BLACK, lw=1.3):
    b = FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0", fc=fc, ec=ec, lw=lw)
    ax.add_patch(b)
    return b


def arrow(ax, x0, y0, x1, y1, lw=1.2):
    a = FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="->",
                        mutation_scale=11, lw=lw, color=BLACK,
                        shrinkA=0, shrinkB=0)
    ax.add_patch(a)


def line(ax, pts, lw=1.2):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs, ys, color=BLACK, lw=lw, solid_capstyle="round",
            solid_joinstyle="round")


def elbow(ax, pts, lw=1.2, head=True):
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        if head and i == len(pts) - 2:
            arrow(ax, x0, y0, x1, y1, lw)
        else:
            line(ax, [(x0, y0), (x1, y1)], lw)


def curve(ax, p0, c1, c2, p1, lw=1.5):
    path = Path([p0, c1, c2, p1],
                [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
    ax.add_patch(PathPatch(path, fill=False, ec=BLACK, lw=lw))


def initial_node(ax, x, y, r=0.11):
    ax.add_patch(Circle((x, y), r, fc=BLACK, ec=BLACK))


def final_node(ax, x, y, r=0.17):
    ax.add_patch(Circle((x, y), r, fc="white", ec=BLACK, lw=1.3))
    ax.add_patch(Circle((x, y), r * 0.55, fc=BLACK, ec=BLACK))


def save(fig, relpath):
    path = os.path.join(ROOT, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=DPI, facecolor="white")
    plt.close(fig)
    print("сохранён", relpath)


# --------------------------------------------------------------------------- #
#  ПЗ-01: дерево решений (UML activity-диаграмма)
# --------------------------------------------------------------------------- #
ASPECTS = [
    ("1. Продукт", "отклонить: много несвязанных изделий",
     "принять: тяжёлый мотоцикл-одиночка"),
    ("2. Целевой рынок", "отклонить: прежний утилитарный сегмент как основной",
     "принять: досуг, обеспеченные покупатели и байкеры"),
    ("3. Разработка и качество", "отклонить: быстрый выпуск без полного цикла испытаний",
     "принять: прототип, испытания, устранение дефектов, допуск"),
    ("4. Производство", "отклонить: избыточные площади и сохранение всех переделов",
     "принять: специализация, сокращение площадей, система качества"),
    ("5. Финансирование", "отклонить: единое крупное вложение без контроля",
     "принять: этапный бюджет, лимиты и условия остановки"),
    ("6. Вывод на рынок", "отклонить: немедленный массовый выпуск",
     "принять: пилотная партия, обратная связь, PR и бренд"),
]


def draw_decision_tree():
    W, H = 11.0, 15.0
    fig, ax = new_canvas(W, H)

    initial_node(ax, 5.5, 14.55)
    arrow(ax, 5.5, 14.44, 5.5, 14.32)

    # главное решение
    rbox(ax, 2.0, 13.20, 7.0, 1.10)
    ax.text(5.5, 13.75, wrap("Главное решение: поэтапно инвестировать в новую "
                            "технику и новую рыночную сферу", 6.4, 11.5),
            ha="center", va="center", fontsize=11.5, fontweight="bold",
            linespacing=1.3)

    # ортогональный «хребет» дерева
    arrow(ax, 5.5, 13.20, 5.5, 12.78)
    spine_x = 5.5
    spine_top, spine_bot = 12.78, 3.62
    line(ax, [(spine_x, spine_top), (spine_x, spine_bot)])

    # шесть аспектов: 2 колонки × 3 строки
    bw, bh = 4.9, 1.75
    col_l, col_r = 0.35, 5.75
    row_tops = [12.30, 10.20, 8.10]
    for i, (title, reject, accept) in enumerate(ASPECTS):
        col = col_l if i % 2 == 0 else col_r
        top = row_tops[i // 2]
        y = top - bh
        rbox(ax, col, y, bw, bh)
        mid = y + bh / 2.0
        # ветка от хребта к боксу
        if i % 2 == 0:
            line(ax, [(spine_x, mid), (col + bw, mid)])
        else:
            line(ax, [(spine_x, mid), (col, mid)])
        # содержимое бокса (центрировано по вертикали)
        tx = col + 0.25
        tw = bw - 0.5
        w_title = wrap(title, tw, 10.5)
        w_rej = wrap(reject, tw, 9.5)
        w_acc = wrap(accept, tw, 9.5)
        n_rej = len(w_rej.split("\n"))
        n_acc = len(w_acc.split("\n"))
        block = 0.22 + 0.06 + n_rej * 0.19 + 0.08 + n_acc * 0.19
        y0 = y + (bh + block) / 2.0
        ax.text(tx, y0, w_title, ha="left", va="top",
                fontsize=10.5, fontweight="bold")
        ax.text(tx, y0 - 0.28, w_rej, ha="left", va="top",
                fontsize=9.5, color=GREY, linespacing=1.3)
        ax.text(tx, y0 - 0.28 - n_rej * 0.19 - 0.08, w_acc,
                ha="left", va="top", fontsize=9.5, color=BLACK,
                linespacing=1.3)

    # итог
    arrow(ax, spine_x, spine_bot, spine_x, 3.22)
    rbox(ax, 2.0, 2.00, 7.0, 1.20)
    ax.text(5.5, 2.60, wrap("Итог: масштабировать выпуск только после "
                            "подтверждения качества, спроса и экономической "
                            "приемлемости", 6.4, 11.5),
            ha="center", va="center", fontsize=11.5, fontweight="bold",
            linespacing=1.3)
    arrow(ax, 5.5, 2.00, 5.5, 1.73)
    final_node(ax, 5.5, 1.55)

    save(fig, "П-41_Соловьев_АС_ПЗ-01_assets/дерево-решений.png")


# --------------------------------------------------------------------------- #
#  ПЗ-03: дерево игры (квадрат — решение менеджера, круг — ответ среды)
# --------------------------------------------------------------------------- #
GAME = [
    ("А. Рост выручки", "А", "+8,5%", 9.6, [
        "Сильный отклик рынка: p = 0,5; +14%",
        "Ограниченный отклик: p = 0,3; +7%",
        "Отрицательная реакция: p = 0,2; −3%",
    ]),
    ("Б. Снижение затрат", "Б", "+8,0%", 5.9, [
        "Полная экономия: p = 0,6; +11%",
        "Частичная экономия: p = 0,3; +6%",
        "Потеря качества: p = 0,1; −4%",
    ]),
    ("В. Комбинированная программа", "В", "+10,4%", 2.2, [
        "Согласованная реализация: p = 0,7; +12%",
        "Частичный результат: p = 0,2; +9%",
        "Сбой программы: p = 0,1; +2%",
    ]),
]


def draw_game_tree():
    W, H = 15.4, 11.8
    fig, ax = new_canvas(W, H)

    # точка решения (квадрат)
    sqbox(ax, 0.4, 5.05, 2.6, 1.7)
    ax.text(1.7, 5.9, "Точка решения\nвыбор стратегии\nроста прибыли",
            ha="center", va="center", fontsize=10.5, linespacing=1.35)

    cx, r = 6.2, 1.0
    for name, letter, ev, cy, outs in GAME:
        chosen = letter == "В"
        # название стратегии над кругом
        ax.text(cx, cy + r + 0.32, name, ha="center", va="bottom",
                fontsize=11, fontweight="bold" if chosen else "normal")
        # круг — ответ среды
        ax.add_patch(Circle((cx, cy), r, fc="white", ec=BLACK, lw=1.3))
        ax.text(cx, cy + 0.17, letter, ha="center", va="center",
                fontsize=13, fontweight="bold")
        ax.text(cx, cy - 0.28, "E = " + ev, ha="center", va="center",
                fontsize=10, fontweight="bold" if chosen else "normal")
        # ветвь от точки решения к кругу
        arrow(ax, 3.0, 5.9, cx - r - 0.03, cy)
        # исходы среды
        for k, out in enumerate(outs):
            ty = cy + (1 - k) * 1.15 - 0.0
            ty = cy + 1.15 - k * 1.15
            arrow(ax, cx + r + 0.03, cy, 9.3, ty)
            ax.text(9.45, ty, out, ha="left", va="center", fontsize=10.5)

    # легенда обозначения
    ax.text(0.4, 0.45,
            "□: точка решения менеджера;   ○: ответ среды (случайное событие);   "
            "у конечного узла: p - вероятность, % - изменение прибыли",
            ha="left", va="center", fontsize=9.5, color=GREY)

    save(fig, "П-41_Соловьев_АС_ПЗ-03_assets/дерево-игры.png")


# --------------------------------------------------------------------------- #
#  ПЗ-03: причинно-следственная диаграмма (Ishikawa)
# --------------------------------------------------------------------------- #
FISH = [
    ("Продажи и рынок", "слабый спрос; низкая конверсия; отток покупателей"),
    ("Продукт и цена", "низкомаржинальный портфель; избыточные скидки; возвраты"),
    ("Материалы и затраты", "рост закупочных цен; перерасход сырья; дорогая энергия и логистика"),
    ("Процессы и оборудование", "простои; брак; низкая производительность; длинный цикл"),
    ("Персонал и управление", "дефицит навыков; слабая мотивация; конфликт; размытая ответственность"),
    ("Информация и контроль", "ошибочный прогноз; поздние данные; неточная себестоимость и маржа"),
]


def draw_ishikawa():
    W, H = 15.4, 10.2
    fig, ax = new_canvas(W, H)

    spine_y = 5.1
    bw, bh = 4.1, 1.5
    centers = [2.95, 7.7, 12.45]
    top_y, bot_y = 7.7, 2.5   # низ верхних boxes, верх нижних boxes

    # хребет и следствие
    arrow(ax, 0.5, spine_y, 12.25, spine_y)
    rbox(ax, 12.35, 3.9, 2.75, 2.4, r=0.12)
    ax.text(13.72, 5.1, "Следствие:\nприрост прибыли\nменее 10%",
            ha="center", va="center", fontsize=11.5, fontweight="bold",
            linespacing=1.35)

    for i, (cat, causes) in enumerate(FISH):
        cx = centers[i % 3]
        top = i < 3
        if top:
            by = top_y               # box снизу
            line(ax, [(cx - 1.0, spine_y), (cx, by)])
        else:
            by = bot_y - bh          # box сверху
            line(ax, [(cx - 1.0, spine_y), (cx, by + bh)])
        rbox(ax, cx - bw / 2, by, bw, bh, r=0.08)
        w_cat = wrap(cat, bw - 0.5, 11)
        w_cau = wrap(causes, bw - 0.5, 9.5)
        n_cau = len(w_cau.split("\n"))
        block = len(w_cat.split("\n")) * 0.22 + 0.06 + n_cau * 0.19
        y0 = by + (bh + block) / 2.0
        ax.text(cx, y0, w_cat, ha="center", va="top",
                fontsize=11, fontweight="bold")
        ax.text(cx, y0 - len(w_cat.split("\n")) * 0.22 - 0.06, w_cau,
                ha="center", va="top", fontsize=9.5, color=GREY,
                linespacing=1.3)

    save(fig, "П-41_Соловьев_АС_ПЗ-03_assets/причинно-следственная-диаграмма.png")


# --------------------------------------------------------------------------- #
#  ПЗ-04: интеллект-карта (mind map, ветви-кривые, текстовые узлы)
# --------------------------------------------------------------------------- #
MIND = [
    # (заголовок, (пункты), сторона, y темы)
    ("Пассажирские формальности", [
        ("★ Упрощение таможенного и пограничного контроля", True),
        ("Стойки самостоятельной регистрации", False),
        ("«Единое окно» для трансферных пассажиров", False),
    ], "L", 10.1),
    ("Сервис и персонал", [
        ("Стандарты обслуживания, обучение и мотивация персонала", False),
        ("Развитие коммерческой зоны и зон ожидания", False),
    ], "L", 6.1),
    ("Транспортная связность", [
        ("Сообщение между «Шереметьево-I» и «Шереметьево-II»", False),
        ("Подъездные дороги и привокзальные проезды", False),
        ("Скоростная связь с городом", False),
    ], "L", 2.35),
    ("Перронное обслуживание", [
        ("★ Автобусы на лётном поле и новые телескопические трапы", True),
        ("Сокращение времени заправки и обслуживания судна", False),
        ("Оптимизация технологического графика", False),
    ], "R", 10.1),
    ("Информация, багаж, качество", [
        ("★ Навигация и информирование пассажиров", True),
        ("Модернизация обработки и выдачи багажа", False),
        ("Система показателей качества обслуживания", False),
    ], "R", 6.1),
    ("Инфраструктура и техника", [
        ("Строительство нового паркинга", False),
        ("Реконструкция взлётно-посадочной полосы и слоты", False),
        ("Обновление технического оснащения", False),
        ("Электроосвещение и энергосбережение", False),
    ], "R", 2.35),
]


def draw_mindmap():
    W, H = 15.4, 11.4
    fig, ax = new_canvas(W, H)

    # центральный узел
    rbox(ax, 5.9, 5.1, 3.6, 1.2, r=0.14)
    ax.text(7.7, 5.7, "Повышение качества\nработы аэропорта\n«Шереметьево»",
            ha="center", va="center", fontsize=11.5, fontweight="bold",
            linespacing=1.3)

    for title, items, side, ty in MIND:
        if side == "L":
            tx = 0.4
            curve(ax, (5.9, 5.7), (5.45, 5.7), (5.25, ty), (4.85, ty))
        else:
            tx = 10.6
            curve(ax, (9.5, 5.7), (9.95, 5.7), (10.15, ty), (10.55, ty))
        ax.text(tx, ty, title, ha="left", va="center", fontsize=11.5,
                fontweight="bold")
        yy = ty - 0.40
        for item, picked in items:
            lines = wrap(item, 4.4, 10).split("\n")
            color = GREEN_TXT if picked else BLACK
            weight = "bold" if picked else "normal"
            ax.text(tx, yy, "\n".join(lines), ha="left", va="top",
                    fontsize=10, color=color, fontweight=weight,
                    linespacing=1.3)
            yy -= 0.25 * len(lines) + 0.09

    save(fig, "П-41_Соловьев_АС_ПЗ-04_assets/интеллект-карта.png")


# --------------------------------------------------------------------------- #
#  ПЗ-05: дерево целей (иерархия, ортогональные соединители)
# --------------------------------------------------------------------------- #
GOALS = [
    ("1. Раннее выявление риска", "вес 0,25", [
        ("1.1 Диагностика всех 1200 студентов в первые 4 недели", "0,138"),
        ("1.2 Панель риска и список сопровождения к 6-й неделе", "0,113"),
    ]),
    ("2. Адресная поддержка", "вес 0,35", [
        ("2.1 Наставники, норматив не более 1:20", "0,140"),
        ("2.2 Групповые консультации по дисциплинам риска", "0,123"),
        ("2.3 Маршрут сложного случая к профильной службе", "0,088"),
    ]),
    ("3. Организация и обратная связь", "вес 0,25", [
        ("3.1 Единый навигатор курса", "0,100"),
        ("3.2 Еженедельная короткая обратная связь", "0,088"),
        ("3.3 Материалы по типовым ошибкам", "0,063"),
    ]),
    ("4. Ресурсная устойчивость", "вес 0,15", [
        ("4.1 Бюджет не выше 4,5 млн руб.", "0,045"),
        ("4.2 Нагрузка не выше 2 ч/нед.", "0,038"),
        ("4.3 Запуск ≤ 4 мес.; защита данных", "0,038"),
        ("4.4 Контрольная точка после семестра", "0,030"),
    ]),
]


def draw_goal_tree():
    W, H = 15.4, 12.9
    fig, ax = new_canvas(W, H)

    # генеральная цель
    rbox(ax, 3.2, 11.35, 9.0, 1.1)
    ax.text(7.7, 11.9, wrap("Генеральная цель: задолженности ≤ 18%; "
                            "сохранность ≥ 93%; бюджет ≤ 4,5 млн руб.",
                            8.4, 12),
            ha="center", va="center", fontsize=12, fontweight="bold",
            linespacing=1.3)

    # разводка на четыре направления
    arrow(ax, 7.7, 11.35, 7.7, 10.92)
    bw = 3.4
    gap = (15.4 - 2 * 0.35 - 4 * bw) / 3.0
    cols = [0.35 + i * (bw + gap) for i in range(4)]
    centers = [c + bw / 2 for c in cols]
    bus_y = 10.92
    line(ax, [(centers[0], bus_y), (centers[-1], bus_y)])

    dir_h, sg_h, sg_gap = 1.5, 1.35, 0.28
    dir_top = 10.5
    for (name, weight, subs), cx in zip(GOALS, centers):
        elbow(ax, [(cx, bus_y), (cx, dir_top + 0.02)], head=True)
        # направление
        rbox(ax, cx - bw / 2, dir_top - dir_h, bw, dir_h)
        ax.text(cx, dir_top - 0.30, wrap(name, bw - 0.4, 10.5),
                ha="center", va="top", fontsize=10.5, fontweight="bold",
                linespacing=1.25)
        nlines = len(wrap(name, bw - 0.4, 10.5).split("\n"))
        ax.text(cx, dir_top - 0.30 - 0.24 * nlines, weight,
                ha="center", va="top", fontsize=9, color=GREY)
        # подцели
        top = dir_top - dir_h - 0.35
        for j, (task, gw) in enumerate(subs):
            y = top - j * (sg_h + sg_gap) - sg_h
            if j == 0:
                elbow(ax, [(cx, dir_top - dir_h), (cx, y + sg_h + 0.02)])
            else:
                elbow(ax, [(cx, y + sg_h + sg_gap), (cx, y + sg_h + 0.02)])
            rbox(ax, cx - bw / 2, y, bw, sg_h, r=0.08)
            ax.text(cx, y + sg_h - 0.22, wrap(task, bw - 0.4, 9.5),
                    ha="center", va="top", fontsize=9.5, linespacing=1.25)
            nl = len(wrap(task, bw - 0.4, 9.5).split("\n"))
            ax.text(cx, y + sg_h - 0.22 - 0.21 * nl, "глобальный вес " + gw,
                    ha="center", va="top", fontsize=8.5, color=GREY)

    save(fig, "П-41_Соловьев_АС_ПЗ-05_assets/дерево-целей.png")


if __name__ == "__main__":
    draw_decision_tree()
    draw_game_tree()
    draw_ishikawa()
    draw_mindmap()
    draw_goal_tree()
