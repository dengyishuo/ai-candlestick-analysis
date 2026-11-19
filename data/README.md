# 冻结数据说明

- 文件：`aapl_daily.csv.gz`
- 标的：AAPL日线
- 区间：2010-01-04至2025-05-16，共3,867个交易日
- 字段：`date`, `code`, `open`, `high`, `low`, `close`, `volume`, `raw_open`, `raw_high`, `raw_low`, `raw_close`, `adj_factor`
- 处理：使用调整后收盘价与原始收盘价的比值，同步调整开、高、低、收四价；原始OHLC及调整因子保留。
- SHA-256：`f9da35a7bbeba3e7e8d5fde7b46acd9b06ba17fb98820b51d129365aa2a7efb4`
- 渲染规则：正文只读取该冻结文件，不联网更新。
