# AI时代的蜡烛图分析

**在线阅读**：<https://dengyishuo.github.io/ai-candlestick-analysis/>

《AI时代的蜡烛图分析》开源书稿。全书 19 章正文与复现附录，用 R / Python 双生态把图形经验改写为可计算、可复现、可证伪的研究。

全书以形态结构为主线、方向含义为辅线：

1. **基础篇（第1—2章）**：图形语言、数据与可审计制图；
2. **形态篇（第3—8章）**：单根、双根、三根及多根、跳空与持续、十字失败、统一字典；
3. **证据篇（第9—16章）**：评分、趋势、位置、均线、动量、成交量、波段和价格剖面；
4. **决策篇（第17—19章）**：期权、动态套保与完整研究案例。

每个形态章再区分看涨、看跌和中性候选。方向标签表示条件性研究假设，不表示确定预测。

## 内容结构

- **源稿**：`manuscript/*.md`（22 个纯 Markdown 文件，唯一维护入口）
- **配图**：`manuscript/figures/*.png`（38 张，已固化）
- **站点**：`docs/`（GitHub Pages 发布目录，由构建脚本生成）
- **参考文献**：`book.bib`
- **历史版本**：`.workbuddy-backup/2026-11-19-pandoc-migration/`（旧 `.Rmd` 与旧站点快照）

## 构建方式

已**从 bookdown/R Markdown 迁移到纯 Markdown + pandoc**，构建不再依赖 R、knitr 或 bookdown。统计表与配图均已静态化，阅读与再构建只需 pandoc（本机 3.7+）：

```bash
python3 scripts/build_site.py
```

脚本读取 `manuscript/` 下的 Markdown，用 pandoc（含 citeproc 处理引用、MathJax 渲染公式）生成带侧边栏导航、上下章、客户端搜索的静态站点，输出到 `docs/`。源文件维护只改 Markdown，不要直接编辑 `docs/`。

`scripts/convert_rmd_to_md.py` 是一次性迁移脚本（Rmd → Markdown），仅在需要从历史 `.Rmd` 重新转换时使用。

## 旧版产物（归档，非构建依赖）

- `docs/ai-candlestick-analysis.pdf`：旧排版 PDF，仅作下载保留
- `数据/`：`data/aapl_daily.csv.gz`（研究冻结数据）
- `R/`、`python/`、`scripts/check_book.R`、`scripts/validate_python.py`：研究复现代码与检查脚本
- `AUTHORING_GUIDE.md`：写作规范
