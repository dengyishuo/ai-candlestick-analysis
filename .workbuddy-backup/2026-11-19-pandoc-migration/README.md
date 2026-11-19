# AI时代的蜡烛图分析

**在线阅读**：<https://dengyishuo.github.io/ai-candlestick-analysis/>

这里保存独立的《AI时代的蜡烛图分析》bookdown工程。全书包含19章正文与复现附录，用 `xquant-work/My-Pkg` 的R/Python双生态把图形经验改写为可计算、可复现、可证伪的研究。

全书以形态结构为主线、方向含义为辅线：

1. **基础篇（第1—2章）**：图形语言、数据与可审计制图；
2. **形态篇（第3—8章）**：单根、双根、三根及多根、跳空与持续、十字失败、统一字典；
3. **证据篇（第9—16章）**：评分、趋势、位置、均线、动量、成交量、波段和价格剖面；
4. **决策篇（第17—19章）**：期权、动态套保与完整研究案例。

每个形态章再区分看涨、看跌和中性候选。方向标签表示条件性研究假设，不表示确定预测。

- 书稿入口：`index.Rmd`
- 章节顺序：`_bookdown.yml`
- RStudio 项目：`AI时代的蜡烛图分析.Rproj`
- HTML成书：`docs/index.html`（GitHub Pages 发布目录，由 `_book/` 同步而来）
- PDF成书：`docs/ai-candlestick-analysis.pdf`（亦见 `output/pdf/AI时代的蜡烛图分析.pdf`）
- 自动检查：`scripts/check_book.R`、`scripts/validate_python.py`
- 历史构建快照：`_book-archive/`

```r
bookdown::render_book("index.Rmd", "bookdown::gitbook")
bookdown::render_book("index.Rmd", "bookdown::pdf_book")
```
