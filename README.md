# english-system

四模块英语学习系统：统一内容层 + 静态学习站。

**学习闭环**：非实体词 + 话术框架 → 场景实训开口 → 实体词补语境深度。

| 模块 | 目录 | 语料源 |
|------|------|--------|
| 实体词 | `content/entity/` | [drama-analysis](../drama-analysis) `cast.md` + quotes |
| 非实体词 | `content/function/` | drama `english-vocab.html` / quotes |
| 话术结构 | `content/phrases/` | drama `english-phrases.html` |
| 场景实训 | `content/scenarios/` | [language_paraphrase](../language_paraphrase) 场景英译 |

旧仓继续做生产工厂；本仓只消费结构化导出。

## 结构

```
english-system/
├── content/           # 结构化学习内容（真相源）
├── schemas/           # JSON Schema
├── scripts/           # 导入 / 校验 / 渲染
└── docs/              # GitHub Pages 学习站
```

## 快速开始

```bash
# 校验内容
python3 scripts/validate-content.py

# 从 drama / paraphrase 冷启动或增量导入（需本机旁路源仓）
python3 scripts/import-from-drama.py
python3 scripts/import-from-paraphrase.py

# 渲染静态站
node scripts/render-site.mjs
```

本地预览：`cd docs && python3 -m http.server 8765`

## GitHub Pages

- 仓库：https://github.com/czh55/english-system  
- 站点：https://czh55.github.io/english-system/（Settings → Pages：`main` / `/docs`）
- 自定义域（若已绑定）：http://chenzhiheng.cn/english-system/


每条条目含 `id`、`module`、溯源 `examples[].source`（如 `drama:meigui-de-gushi:e01:s3-q1`）。
场景 chunks 可通过 `links` 挂到 function / phrases 的 `id`。

详见 `schemas/`。
