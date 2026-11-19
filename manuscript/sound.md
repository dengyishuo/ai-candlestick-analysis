<!-- PART:附录 -->
# 复现环境、API字典与研究审计 {#sound}

## 构建环境

本书是在线开源书稿，源稿为纯 Markdown，使用 pandoc 构建静态站点：

```bash
python3 scripts/build_site.py
```

统计表与配图已在迁移时固化为静态资源，因此阅读与再构建均不需要安装 R 或运行 knitr。研究复现所需的 R / Python 接口与版本仍在下面列出。

正文不安装软件、不联网下载数据。R端需要 `eCandleSticks`、`eFinCharts`、`eTTR`、`ebacktest` 及其依赖；Python端从 `xquant-work/My-Pkg/eQuant-Py` 当前源码导入对应包。具体版本应在每次发布时写入构建日志。

- **R**：`4.6.0`
- **knitr**：`1.51`
- **bookdown**：`0.47`
- **eCandleSticks**：`0.1.1`
- **eFinCharts**：`0.2.0`

## 冻结数据与哈希

正文数据位于 `data/aapl_daily.csv.gz`。为适应纸面宽度，下面把SHA-256分成两段显示；两段直接拼接即为完整值：

```
f9da35a7bbeba3e7e8d5fde7b46acd9b06
ba17fb98820b51d129365aa2a7efb4
```

核心字段为 `date, code, open, high, low, close, volume`。复权OHLC用于形态与收益连续性，`raw_*` 字段用于审计当时价格，`adj_factor` 记录转换比例。

## eCandleSticks形态字典

R端当前导出接口采用 `add_csp_*()`；Python采用 `add_*()`。本书主路径使用以下对照，长函数名采用逐项列举以保证电子版与纸面版均可读：

- 锤子（单根、看涨候选）：R为 `add_csp_hammer()`；Python为 `add_hammer()`。
- 流星（单根、看跌候选）：R为 `add_csp_shooting_star()`；Python为 `add_shooting_star()`。
- 倒锤子（单根、看涨候选）：R为 `add_csp_inverted_hammer()`；Python为 `add_inverted_hammer()`。
- 十字（单根、中性）：R为 `add_csp_doji()`；Python为 `add_doji()`，方向需由上下文确定。
- 吞没（双根、双向）：R为 `add_csp_engulfing()`；Python为 `add_engulfing()`。
- 孕线（双根、双向）：R为 `add_csp_harami()`；Python为 `add_harami()`。
- 反击线（双根、双向）：R为 `add_csp_counter_attack()`；Python为 `add_counter_attack()`。
- 星线（三根、双向）：R为 `add_csp_star()`；Python为 `add_star()`。
- 上升/下降三法（多根、双向）：R为 `add_csp_three_methods()`；Python为 `add_three_methods()`。
- 三兵/三鸦（多根、双向）：R分别为 `add_csp_three_white_soldiers()` 与 `add_csp_three_black_crows()`；Python使用对应的 `add_*()` 接口。

包仍包含更多形态。正式研究不应因 `scan_all()` 新增列而自动扩大假设范围，必须保存明确列表和包版本。

## eTTR与eFinCharts主接口

- 移动平均：R为 `eTTR::add_sma()` 与 `add_ema()`；Python为 `ettr.sma()` 与 `ettr.ema()`。
- RSI：R为 `eTTR::add_rsi()`；Python为 `ettr.rsi()`。
- OBV：R为 `eTTR::add_obv()`；Python为 `ettr.obv()`。
- 唐奇安通道：R为 `eTTR::add_donchian_channel()`；Python为 `ettr.donchian()`。
- ZigZag：R为 `eTTR::add_zig_zag()`；Python为 `ettr.zigzag()`。
- 金融图：R为 `eFinCharts::ecandlesticks()`；Python为 `efincharts.candlestick()`。
- 完整回测：R为 `ebacktest::run_backtest()`；Python为 `ebacktestcraft.run()`。

API以源码导出为准。README中的历史驼峰名称可能与当前版本不同。

## 市场状态与HMM扩展

隐马尔可夫模型（HMM）可以把收益与波动观察序列表示为若干潜在状态，但状态编号没有固定经济含义，模型也存在标签交换、初值敏感和样本外漂移。本书正文采用透明的波动率与趋势状态。若扩展到HMM，应遵守：只用训练期估计；滚动或扩展窗口更新；每次重估对状态按可解释统计量重新命名；信号时点只能使用过滤概率，不能使用包含未来观测的平滑概率。

## 发布前自动检查

1. 所有章节包含12个固定二级标题；
2. 所有R代码块标签唯一；
3. 所有 `add_csp_*`、`draw_*` 和 `eTTR` 函数存在于当前导出表；
4. R/Python读取同一数据哈希；
5. 信号仅取 `-1/0/1`，长度与行情一致；
6. 事件从次日开盘成交，末尾不可完成事件为缺失；
7. 图表可由代码重新生成；
8. HTML与PDF交叉引用无断链；
9. 样本外结果、失败结果与成本假设均保留；
10. 不出现“稳赚”“必涨”或未被证据支持的保证性表述。

## 研究记录模板

每次实验至少记录：研究问题、假设版本、数据哈希、包提交或版本、函数与参数、信号最晚可用时点、成交规则、成本、样本切分、评价指标、全部结果文件、已知失败条件和下一步是否允许继续。AI参与时额外保存AI任务、输入约束、产物与验收记录。
