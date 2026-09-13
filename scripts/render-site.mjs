#!/usr/bin/env node
/**
 * Render english-system content/*.json → docs/ static learning site.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const CONTENT = path.join(ROOT, "content");
const DOCS = path.join(ROOT, "docs");

function readJsonDir(module) {
  const dir = path.join(CONTENT, module);
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")));
}

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const CSS = `
:root {
  --bg: #0c1222;
  --surface: rgba(255,255,255,0.045);
  --border: rgba(255,255,255,0.1);
  --text: #e8eef7;
  --muted: #93a4bd;
  --accent: #5ec8c0;
  --accent2: #7eb6ff;
  --accent3: #e8b86d;
  --ok: #6ed3a1;
  --font-display: "Iowan Old Style", "Palatino Linotype", Palatino, "Songti SC", serif;
  --font-body: "Avenir Next", "PingFang SC", "Helvetica Neue", sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; scroll-padding-top: 72px; }
body {
  font-family: var(--font-body);
  background:
    radial-gradient(900px 500px at 12% -10%, rgba(94,200,192,0.16), transparent 55%),
    radial-gradient(700px 420px at 90% 0%, rgba(126,182,255,0.12), transparent 50%),
    var(--bg);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.65;
}
a { color: var(--accent2); text-decoration: none; }
a:hover { text-decoration: underline; }
.wrap { max-width: 980px; margin: 0 auto; padding: 28px 20px 80px; }
nav.top {
  display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: center;
  padding: 14px 0 22px; border-bottom: 1px solid var(--border); margin-bottom: 28px;
}
nav.top .brand {
  font-family: var(--font-display);
  font-size: 1.15rem; font-weight: 700; color: var(--text); margin-right: auto;
}
nav.top a { color: var(--muted); font-size: 0.9rem; }
nav.top a.active { color: var(--accent); }
.hero h1 {
  font-family: var(--font-display);
  font-size: clamp(2rem, 4.5vw, 2.9rem);
  letter-spacing: -0.02em; line-height: 1.15; margin-bottom: 12px;
}
.hero p { color: var(--muted); max-width: 42rem; }
.grid4 {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 28px 0;
}
@media (max-width: 820px) { .grid4 { grid-template-columns: 1fr 1fr; } }
@media (max-width: 480px) { .grid4 { grid-template-columns: 1fr; } }
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 18px 16px; display: block; color: inherit;
}
.card:hover { border-color: rgba(94,200,192,0.45); text-decoration: none; }
.card .kicker { font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--accent); font-weight: 700; }
.card h2 { font-size: 1.15rem; margin: 8px 0 6px; font-family: var(--font-display); }
.card p { color: var(--muted); font-size: 0.88rem; }
.path {
  background: linear-gradient(135deg, rgba(94,200,192,0.12), rgba(126,182,255,0.08));
  border: 1px solid var(--border); border-radius: 16px; padding: 22px 20px; margin-top: 8px;
}
.path h2 { font-family: var(--font-display); font-size: 1.35rem; margin-bottom: 8px; }
.path ol { margin: 12px 0 0 1.2rem; color: var(--muted); }
.path li { margin: 8px 0; }
.path strong { color: var(--text); }
.search {
  width: 100%; margin: 8px 0 18px; padding: 12px 14px; border-radius: 10px;
  border: 1px solid var(--border); background: rgba(0,0,0,0.25); color: var(--text);
  font-size: 1rem;
}
.meta { color: var(--muted); font-size: 0.85rem; margin-bottom: 16px; }
table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
th, td { text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }
th { color: var(--muted); font-weight: 600; font-size: 0.78rem; letter-spacing: 0.04em; text-transform: uppercase; }
.lemma { font-weight: 700; color: var(--accent); }
.zh { color: var(--text); }
.freq { color: var(--accent3); font-variant-numeric: tabular-nums; white-space: nowrap; }
.tag {
  display: inline-block; font-size: 0.72rem; padding: 2px 8px; border-radius: 999px;
  background: rgba(126,182,255,0.12); color: var(--accent2); margin: 0 4px 4px 0;
}
.ex { display: block; color: var(--muted); font-size: 0.82rem; margin-top: 4px; }
.ex .en { color: #c9d7ea; }
.group { margin: 28px 0; }
.group h2 { font-family: var(--font-display); font-size: 1.4rem; margin-bottom: 6px; }
.group .desc { color: var(--muted); margin-bottom: 12px; }
.frame { font-weight: 700; color: var(--accent); }
.usage { color: var(--muted); font-size: 0.85rem; }
.scene-list a.card { margin-bottom: 12px; }
.scene-block {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 18px; margin: 16px 0;
}
.scene-block h3 { font-family: var(--font-display); margin-bottom: 4px; }
.sent { margin: 12px 0; padding: 10px 0; border-top: 1px solid var(--border); }
.sent .pair { display: grid; gap: 4px; }
.sent .label { font-size: 0.7rem; color: var(--muted); letter-spacing: 0.08em; }
.note { color: var(--accent3); font-size: 0.82rem; margin-top: 4px; }
.para { margin-top: 12px; padding-top: 10px; border-top: 1px dashed var(--border); }
.para li { margin: 8px 0 8px 1rem; }
.chunk-link { margin-left: 6px; font-size: 0.8rem; }
.external { margin: 10px 0 18px; font-size: 0.9rem; }
footer { margin-top: 48px; padding-top: 16px; border-top: 1px solid var(--border); color: var(--muted); font-size: 0.82rem; }
`;

function layout({ title, active, body }) {
  const links = [
    ["index.html", "首页", "home"],
    ["function/index.html", "非实体词", "function"],
    ["phrases/index.html", "话术结构", "phrases"],
    ["scenarios/index.html", "场景实训", "scenarios"],
    ["entity/index.html", "实体词", "entity"],
  ];
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} · english-system</title>
<style>${CSS}</style>
</head>
<body>
<div class="wrap">
<nav class="top">
  <a class="brand" href="${active === "home" ? "index.html" : "../index.html"}">english-system</a>
  ${links
    .map(([, label, key]) => {
      let real;
      if (active === "home") {
        real = key === "home" ? "index.html" : links.find((x) => x[2] === key)[0];
      } else if (active === "scenarios-detail") {
        real = key === "home" ? "../index.html" : `../${links.find((x) => x[2] === key)[0]}`;
      } else if (key === active) {
        real = "index.html";
      } else if (key === "home") {
        real = "../index.html";
      } else {
        real = `../${links.find((x) => x[2] === key)[0]}`;
      }
      const isActive =
        key === active || (active === "scenarios-detail" && key === "scenarios");
      return `<a class="${isActive ? "active" : ""}" href="${real}">${label}</a>`;
    })
    .join("\n  ")}
</nav>
${body}
<footer>语料来自 drama-analysis / language_paraphrase · 本站只做结构化学习壳</footer>
</div>
</body>
</html>`;
}

function searchScript(rowSelector = "tr[data-search]") {
  return `<script>
(function(){
  var box = document.getElementById('q');
  if (!box) return;
  box.addEventListener('input', function(){
    var q = box.value.trim().toLowerCase();
    document.querySelectorAll('${rowSelector}').forEach(function(row){
      var hay = row.getAttribute('data-search') || '';
      row.style.display = (!q || hay.indexOf(q) !== -1) ? '' : 'none';
    });
  });
})();
</script>`;
}

function write(file, html) {
  const full = path.join(DOCS, file);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.writeFileSync(full, html, "utf8");
}

function todayPath(functions, phrases, scenarios) {
  const priority = functions
    .filter((f) => (f.tags || []).includes("priority"))
    .sort((a, b) => (b.freq || 0) - (a.freq || 0));
  const top = (priority.length ? priority : [...functions].sort((a, b) => (b.freq || 0) - (a.freq || 0))).slice(0, 8);
  const phrase = phrases[0];
  const scenario = scenarios[0];
  return { top, phrase, scenario };
}

function renderHome(functions, phrases, scenarios, entities) {
  const { top, phrase, scenario } = todayPath(functions, phrases, scenarios);
  const body = `
<header class="hero">
  <h1>英语四模块学习站</h1>
  <p>非实体词 + 话术框架 → 场景开口 → 实体词补语境。语料从剧台词与真实视频场景提炼，本站负责结构化练习路径。</p>
</header>
<section class="grid4">
  <a class="card" href="function/index.html"><div class="kicker">Module 02</div><h2>非实体词</h2><p>${functions.length} 个功能/框架词 · 频次倒排</p></a>
  <a class="card" href="phrases/index.html"><div class="kicker">Module 03</div><h2>话术结构</h2><p>${phrases.length} 个句子框架 · 可直接套用</p></a>
  <a class="card" href="scenarios/index.html"><div class="kicker">Module 04</div><h2>场景实训</h2><p>${scenarios.length} 期情景英译 · paraphrase + chunks</p></a>
  <a class="card" href="entity/index.html"><div class="kicker">Module 01</div><h2>实体词</h2><p>${entities.length} 个角色/专名 · 剧中语境</p></a>
</section>
<section class="path">
  <h2>今日建议路径</h2>
  <p style="color:var(--muted)">约 20 分钟：先记词，再套框架，最后开口练一场。</p>
  <ol>
    <li><strong>非实体词 ×8</strong>：${top.map((w) => `<a href="function/index.html#${esc(w.id)}">${esc(w.lemma)}</a>`).join(" · ")}</li>
    <li><strong>话术框架 ×1</strong>：${phrase ? `<a href="phrases/index.html#${esc(phrase.id)}">${esc(phrase.frame_en)}</a>（${esc(phrase.frame_zh)}）` : "—"}</li>
    <li><strong>场景开口 ×1</strong>：${scenario ? `<a href="scenarios/${esc(scenario.slug)}.html">${esc(scenario.title)}</a>` : "—"}</li>
  </ol>
</section>`;
  write("index.html", layout({ title: "首页", active: "home", body }));
}

function renderFunction(functions) {
  const rows = [...functions]
    .sort((a, b) => (b.freq || 0) - (a.freq || 0))
    .map((w) => {
      const ex = (w.examples || [])[0];
      return `<tr id="${esc(w.id)}" data-search="${esc((w.lemma + " " + w.zh + " " + (w.tags || []).join(" ")).toLowerCase())}">
  <td><span class="lemma">${esc(w.lemma)}</span><div>${(w.tags || []).map((t) => `<span class="tag">${esc(t)}</span>`).join("")}</div>
  ${ex ? `<span class="ex"><span class="en">${esc(ex.en)}</span> · ${esc(ex.zh)}</span>` : ""}</td>
  <td class="zh">${esc(w.zh)}</td>
  <td class="freq">${w.freq ?? "—"}</td>
</tr>`;
    })
    .join("\n");
  const body = `
<header class="hero"><h1>非实体词</h1><p>连接 / 情态 / 程度 / 填充语等功能词与框架填空词。先背高频，再塞进话术框架。</p></header>
<p class="meta">${functions.length} 条 · 来源 drama-analysis 高频词手册</p>
<input class="search" id="q" type="search" placeholder="搜索 lemma / 中文 / 标签…" autocomplete="off">
<table>
<thead><tr><th>词</th><th>中文</th><th>频次</th></tr></thead>
<tbody>${rows}</tbody>
</table>
${searchScript()}`;
  write("function/index.html", layout({ title: "非实体词", active: "function", body }));
}

function renderPhrases(phrases) {
  const groups = new Map();
  for (const p of phrases) {
    const g = p.group || "其他";
    if (!groups.has(g)) groups.set(g, []);
    groups.get(g).push(p);
  }
  const sections = [...groups.entries()]
    .map(([group, items]) => {
      const rows = items
        .map((p) => {
          const ex = (p.examples || [])[0];
          return `<tr id="${esc(p.id)}" data-search="${esc((p.frame_en + " " + p.frame_zh + " " + (p.usage || "")).toLowerCase())}">
  <td class="zh">${esc(p.frame_zh)}</td>
  <td><span class="frame">${esc(p.frame_en)}</span>${ex ? `<span class="ex"><span class="en">${esc(ex.en)}</span></span>` : ""}</td>
  <td class="usage">${esc(p.usage || "")}</td>
</tr>`;
        })
        .join("\n");
      return `<section class="group"><h2>${esc(group)}</h2>
<table><thead><tr><th>中文话术</th><th>英文框架</th><th>用法</th></tr></thead><tbody>${rows}</tbody></table></section>`;
    })
    .join("\n");
  const body = `
<header class="hero"><h1>话术结构</h1><p>中文意图 → 英文句子框架。难的不是单词，是不知道用哪个框架起头。</p></header>
<p class="meta">${phrases.length} 个框架 · 来源 drama-analysis 话术手册</p>
<input class="search" id="q" type="search" placeholder="搜索 although / 万一 / rather…" autocomplete="off">
${sections}
${searchScript()}`;
  write("phrases/index.html", layout({ title: "话术结构", active: "phrases", body }));
}

function renderEntity(entities) {
  const rows = [...entities]
    .sort((a, b) => (b.freq || 0) - (a.freq || 0) || a.zh.localeCompare(b.zh, "zh"))
    .map((e) => {
      const ex = (e.examples || [])[0];
      return `<tr id="${esc(e.id)}" data-search="${esc((e.lemma + " " + e.zh + " " + (e.aliases || []).join(" ") + " " + (e.drama || "")).toLowerCase())}">
  <td><span class="lemma">${esc(e.lemma)}</span> <span class="tag">${esc(e.type)}</span>
  <div class="ex">${esc(e.drama || "")}${(e.aliases || []).length ? " · " + esc(e.aliases.join(" / ")) : ""}</div>
  ${ex ? `<span class="ex"><span class="en">${esc(ex.en)}</span> · ${esc(ex.zh)}</span>` : ""}</td>
  <td class="zh">${esc(e.zh)}</td>
  <td class="freq">${e.freq ?? 0}</td>
</tr>`;
    })
    .join("\n");
  const body = `
<header class="hero"><h1>实体词</h1><p>人物 / 地点 / 物品等具体指称。从剧集 cast 冷启动，台词共现补例句。</p></header>
<p class="meta">${entities.length} 条 · 来源 drama-analysis cast.md + quotes</p>
<input class="search" id="q" type="search" placeholder="搜索角色名 / 剧名…" autocomplete="off">
<table>
<thead><tr><th>实体</th><th>中文</th><th>命中</th></tr></thead>
<tbody>${rows}</tbody>
</table>
${searchScript()}`;
  write("entity/index.html", layout({ title: "实体词", active: "entity", body }));
}

function renderScenarios(scenarios) {
  const list = scenarios
    .map(
      (s) => `<a class="card" href="${esc(s.slug)}.html">
  <div class="kicker">${esc(s.platform || "scenario")}</div>
  <h2>${esc(s.title)}</h2>
  <p>${esc(s.title_en || "")} · ${s.scenes?.length || 0} 场景 · ${(s.practice || []).length} 练习</p>
</a>`
    )
    .join("\n");
  const body = `
<header class="hero"><h1>场景实训</h1><p>真实视频情景：中英对照、paraphrase、chunks。完整音频/截图可回链原学习卡。</p></header>
<p class="meta">${scenarios.length} 期 · 来源 language_paraphrase</p>
<div class="scene-list">${list}</div>`;
  write("scenarios/index.html", layout({ title: "场景实训", active: "scenarios", body }));

  for (const s of scenarios) {
    const scenesHtml = (s.scenes || [])
      .map((sc) => {
        const sents = (sc.sentences || [])
          .map(
            (x) => `<div class="sent"><div class="pair">
  <div><span class="label">ZH</span><div>${esc(x.zh)}</div></div>
  <div><span class="label">EN</span><div>${esc(x.en)}</div></div>
</div>${x.note ? `<div class="note">${esc(x.note)}</div>` : ""}</div>`
          )
          .join("");
        const paras = (sc.paraphrase || [])
          .map((p) => {
            const links = (p.links || [])
              .map((lk) => {
                const href =
                  lk.module === "function"
                    ? `../function/index.html#${esc(lk.id)}`
                    : lk.module === "phrases"
                      ? `../phrases/index.html#${esc(lk.id)}`
                      : `../entity/index.html#${esc(lk.id)}`;
                return `<a class="chunk-link" href="${href}">→ ${esc(lk.module)}</a>`;
              })
              .join("");
            const chunks = (p.chunks || []).map((c) => `<code>${esc(c)}</code>`).join(" · ");
            return `<li><strong>${esc(p.label)}</strong> → ${esc(p.en)}<div>${chunks} ${links}</div></li>`;
          })
          .join("");
        return `<section class="scene-block" id="${esc(sc.id)}">
  <h3>${esc(sc.id.toUpperCase())} · ${esc(sc.title_cn)}</h3>
  <p class="meta">${esc(sc.title_en || "")}${sc.time ? " · " + esc(sc.time) : ""}</p>
  ${sents}
  ${paras ? `<div class="para"><strong>Paraphrase &amp; Chunks</strong><ul>${paras}</ul></div>` : ""}
</section>`;
      })
      .join("\n");

    const practice = (s.practice || [])
      .map((p) => `<li><span class="zh">${esc(p.zh)}</span><div class="ex"><span class="en">${esc(p.en)}</span></div></li>`)
      .join("");

    const body = `
<header class="hero"><h1>${esc(s.title)}</h1><p>${esc(s.title_en || "")}</p></header>
${s.external_html ? `<p class="external"><a href="${esc(s.external_html)}" target="_blank" rel="noopener">打开原场景学习卡（音频 / 截图）↗</a></p>` : ""}
${scenesHtml}
${practice ? `<section class="scene-block"><h3>今日可练</h3><ol>${practice}</ol></section>` : ""}`;
    write(
      `scenarios/${s.slug}.html`,
      layout({ title: s.title, active: "scenarios-detail", body })
    );
  }
}

function main() {
  const functions = readJsonDir("function");
  const phrases = readJsonDir("phrases");
  const scenarios = readJsonDir("scenarios");
  const entities = readJsonDir("entity");

  renderHome(functions, phrases, scenarios, entities);
  renderFunction(functions);
  renderPhrases(phrases);
  renderEntity(entities);
  renderScenarios(scenarios);

  // content index for debugging / future apps
  fs.writeFileSync(
    path.join(DOCS, "index.json"),
    JSON.stringify(
      {
        generated_at: new Date().toISOString(),
        counts: {
          function: functions.length,
          phrases: phrases.length,
          scenarios: scenarios.length,
          entity: entities.length,
        },
        scenarios: scenarios.map((s) => ({
          id: s.id,
          slug: s.slug,
          title: s.title,
          html: `scenarios/${s.slug}.html`,
        })),
      },
      null,
      2
    ) + "\n"
  );

  console.log("rendered docs/", {
    function: functions.length,
    phrases: phrases.length,
    scenarios: scenarios.length,
    entity: entities.length,
  });
}

main();
