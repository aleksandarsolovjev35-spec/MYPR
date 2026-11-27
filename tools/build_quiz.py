#!/usr/bin/env python3
# Генератор квиза по терминам: читает Список_терминов.md и собирает quiz/index.html.
# Запуск: python3 tools/build_quiz.py
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "Список_терминов.md"
OUT_DIR = ROOT / "quiz"
OUT = OUT_DIR / "index.html"


def parse_items():
    items = []
    for line in SRC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^- \*\*(.+?)\*\* - (.+?)\s*\*\(семинары: ([\d, ]+)\)\*\s*$", line)
        if m:
            sems = [int(x) for x in m.group(3).split(",")]
            items.append({"t": m.group(1).strip(), "e": m.group(2).strip(), "sems": sems})
    return items


HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Квиз по терминам</title>
<style>
  :root {
    --accent: #3f51b5; --ok: #2e7d32; --bad: #c62828;
    --bg: #f4f5fa; --card: #ffffff; --text: #1c2333; --muted: #6b7280;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font: 17px/1.5 -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
    -webkit-tap-highlight-color: transparent;
  }
  .wrap { max-width: 680px; margin: 0 auto; padding: 16px; }
  h1 { font-size: 1.35rem; margin: 8px 0 4px; }
  .sub { color: var(--muted); margin: 0 0 16px; font-size: .95rem; }
  .card {
    background: var(--card); border-radius: 16px; padding: 18px;
    box-shadow: 0 2px 10px rgba(28,35,51,.07); margin-bottom: 14px;
  }
  .chip {
    display: inline-block; background: #e8eaf6; color: var(--accent);
    border-radius: 999px; padding: 2px 12px; font-size: .82rem; font-weight: 600;
    margin-bottom: 10px;
  }
  .term { font-size: 1.3rem; font-weight: 700; margin: 4px 0 6px; overflow-wrap: anywhere; }
  .prompt { color: var(--muted); font-size: .92rem; margin: 0 0 12px; }
  .opt {
    display: block; width: 100%; text-align: left; font: inherit;
    background: #f0f2f9; border: 2px solid transparent; border-radius: 12px;
    padding: 13px 15px; margin: 9px 0; cursor: pointer; transition: all .15s;
  }
  .opt:hover { background: #e7eaf5; }
  .opt.ok { background: #e3f2e4; border-color: var(--ok); }
  .opt.bad { background: #fde8e8; border-color: var(--bad); }
  .opt.dim { opacity: .55; }
  .bar { height: 8px; background: #e3e6f0; border-radius: 99px; overflow: hidden; margin: 10px 0 2px; }
  .bar > i { display: block; height: 100%; width: 0; background: var(--accent); transition: width .25s; }
  .stats { display: flex; justify-content: space-between; color: var(--muted); font-size: .88rem; }
  .btn {
    display: inline-block; font: inherit; font-weight: 600; cursor: pointer;
    background: var(--accent); color: #fff; border: 0; border-radius: 12px;
    padding: 13px 22px; margin: 6px 6px 0 0;
  }
  .btn.ghost { background: #e7eaf5; color: var(--accent); }
  .btn.wide { width: 100%; text-align: center; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; margin-top: 10px; }
  .grid .btn { margin: 0; text-align: center; padding: 12px 8px; }
  .score-big { font-size: 2.2rem; font-weight: 800; margin: 6px 0; }
  .wrong-item { border-left: 4px solid var(--bad); padding: 8px 12px; margin: 8px 0; background: #faf5f5; border-radius: 8px; }
  .wrong-item b { display: block; }
  .wrong-item span { color: var(--muted); font-size: .93rem; }
  .hidden { display: none; }
  .foot { color: var(--muted); font-size: .82rem; text-align: center; margin: 18px 0; }
</style>
</head>
<body>
<div class="wrap">

  <!-- Меню -->
  <section id="menu">
    <h1>Квиз по терминам</h1>
    <p class="sub">Показан термин - выберите правильное пояснение. Всего понятий: <b id="total"></b>. Ошибёшься - увидишь верный ответ.</p>
    <div class="card">
      <div class="prompt">Выберите набор:</div>
      <div class="grid" id="sets"></div>
    </div>
    <p class="foot">Источник: Список_терминов.md (уникальные термины перечней заданий семинаров 1-8)</p>
  </section>

  <!-- Квиз -->
  <section id="quiz" class="hidden">
    <div class="stats"><span id="qnum">Вопрос 1</span><span id="snum">Верно: 0</span></div>
    <div class="bar"><i id="prog"></i></div>
    <div class="card">
      <span class="chip" id="sem">Семинар</span>
      <div class="term" id="term"></div>
      <p class="prompt">Выберите подходящее пояснение:</p>
      <div id="opts"></div>
      <button class="btn wide hidden" id="next">Далее &rarr;</button>
    </div>
  </section>

  <!-- Итог -->
  <section id="done" class="hidden">
    <h1>Готово!</h1>
    <div class="card">
      <div class="score-big" id="result"></div>
      <p class="prompt" id="verdict"></p>
      <button class="btn" id="again">Новый проход</button>
      <button class="btn ghost" id="retry-wrong">Пройти ошибки заново</button>
      <button class="btn ghost" id="to-menu">К выбору семинара</button>
    </div>
    <div id="wrongbox"></div>
  </section>

</div>

<script>
const DATA = __DATA_JSON__;

let order = [], idx = 0, score = 0, wrong = [], locked = false, autoTimer = null;

const $ = (id) => document.getElementById(id);
const shuffle = (a) => a.map(v => [Math.random(), v]).sort((x, y) => x[0] - y[0]).map(p => p[1]);

function show(name) {
  for (const s of ["menu", "quiz", "done"]) $(s).classList.toggle("hidden", s !== name);
}

function buildMenu() {
  $("total").textContent = DATA.length;
  const sets = [["Все термины (" + DATA.length + ")", 0]];
  for (let s = 1; s <= 8; s++) {
    sets.push(["Семинар " + s + " (" + DATA.filter(i => i.sems.includes(s)).length + ")", s]);
  }
  $("sets").innerHTML = sets.map(([label, s]) =>
    `<button class="btn ghost" data-sem="${s}">${label}</button>`).join("");
  for (const b of document.querySelectorAll("#sets .btn")) {
    b.onclick = () => start(parseInt(b.dataset.sem, 10));
  }
}

function start(sem) {
  order = shuffle(sem ? DATA.filter(i => i.sems.includes(sem)) : DATA.slice());
  idx = 0; score = 0; wrong = []; locked = false;
  show("quiz");
  render();
}

function distractors(item) {
  const same = shuffle(DATA.filter(i => i.t !== item.t && i.sems.some(s => item.sems.includes(s))));
  const picked = same.slice(0, 3);
  if (picked.length < 3) {
    picked.push(...shuffle(DATA.filter(i => i.t !== item.t && !i.sems.some(s => item.sems.includes(s)))).slice(0, 3 - picked.length));
  }
  return picked;
}

function render() {
  clearTimeout(autoTimer);
  const item = order[idx];
  locked = false;
  $("sem").textContent = "Семинары: " + item.sems.join(", ");
  $("term").textContent = item.t;
  $("qnum").textContent = "Вопрос " + (idx + 1) + " из " + order.length;
  $("snum").textContent = "Верно: " + score;
  $("prog").style.width = (idx / order.length * 100) + "%";
  $("next").classList.add("hidden");
  const opts = shuffle([item, ...distractors(item)]);
  $("opts").innerHTML = "";
  for (const o of opts) {
    const b = document.createElement("button");
    b.className = "opt";
    b.textContent = o.e;
    b.onclick = () => answer(o, b);
    $("opts").appendChild(b);
  }
}

function answer(chosen, btn) {
  if (locked) return;
  locked = true;
  const item = order[idx];
  const buttons = [...document.querySelectorAll("#opts .opt")];
  if (chosen.t === item.t) {
    score++;
    btn.classList.add("ok");
    $("snum").textContent = "Верно: " + score;
    autoTimer = setTimeout(next, 850);
  } else {
    btn.classList.add("bad");
    for (const b of buttons) {
      if (b.textContent === item.e) b.classList.add("ok");
      else if (b !== btn) b.classList.add("dim");
    }
    wrong.push(item);
    $("next").classList.remove("hidden");
  }
}

function next() {
  idx++;
  if (idx >= order.length) finish();
  else render();
}

function finish() {
  show("done");
  const pct = Math.round(score / order.length * 100);
  $("result").textContent = score + " из " + order.length + " (" + pct + "%)";
  $("verdict").textContent =
    pct === 100 ? "Идеально! Все понятия усвоены." :
    pct >= 85 ? "Отлично - почти безупречно." :
    pct >= 60 ? "Хорошая база - повторите ошибки ниже." :
    "Стоит пройти ещё раз - термины закрепятся.";
  $("retry-wrong").style.display = wrong.length ? "" : "none";
  $("wrongbox").innerHTML = wrong.length
    ? "<h2>Разбор ошибок</h2>" + wrong.map(w =>
        `<div class="wrong-item"><b>${w.t}</b><span>${w.e}</span></div>`).join("")
    : "";
}

$("next").onclick = next;
$("again").onclick = () => start(0);
$("retry-wrong").onclick = () => {
  order = shuffle(wrong.slice());
  idx = 0; score = 0; wrong = []; locked = false;
  show("quiz"); render();
};
$("to-menu").onclick = () => { show("menu"); };

document.addEventListener("keydown", (ev) => {
  if (!$("quiz").classList.contains("hidden")) {
    if (ev.key >= "1" && ev.key <= "4") {
      const b = document.querySelectorAll("#opts .opt")[parseInt(ev.key, 10) - 1];
      if (b) b.click();
    }
    if (ev.key === "Enter" && !$("next").classList.contains("hidden")) next();
  }
});

buildMenu();
</script>
</body>
</html>
"""


def main():
    items = parse_items()
    if not items:
        raise SystemExit("Не найдено ни одного термина в " + str(SRC))
    OUT_DIR.mkdir(exist_ok=True)
    html = HTML.replace("__DATA_JSON__", json.dumps(items, ensure_ascii=False))
    OUT.write_text(html, encoding="utf-8")
    counts = {s: sum(1 for it in items if s in it["sems"]) for s in range(1, 9)}
    print(f"Собрано уникальных терминов: {len(items)}")
    print("Требуется по семинарам:", ", ".join(f"С{s}:{counts[s]}" for s in sorted(counts)))
    print("Файл:", OUT)


if __name__ == "__main__":
    main()
