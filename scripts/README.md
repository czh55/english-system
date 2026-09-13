# scripts

| 脚本 | 作用 |
|------|------|
| `import-from-drama.py` | 从旁路 `../drama-analysis` 导入 entity / function / phrases |
| `import-from-paraphrase.py` | 从旁路 `../language_paraphrase` 导入 scenarios，并尝试挂 chunks→词/话术深链 |
| `validate-content.py` | 校验 `content/**/*.json` |
| `render-site.mjs` | 渲染 `docs/` 静态学习站 |

推荐顺序：drama 导入 → paraphrase 导入 → validate → render。
