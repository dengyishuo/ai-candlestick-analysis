#!/usr/bin/env python3
"""把《AI时代的蜡烛图分析》的 bookdown/Rmd 源稿一次性转换为纯 Markdown。

转换内容：
- knitr 代码块 -> 标准围栏代码块（r/python）
- 绘图 chunk -> 静态图片引用（复用已渲染 PNG）
- lab_print_table chunk -> 固化的 Markdown 表格（从旧 HTML 抽取）
- \@ref(label) -> 章节内部链接或章节名
- {#label} / {-} 标题后缀 -> pandoc 可识别的 {#label}
- (PART) 分篇标题 -> 独立分篇页标记
- \[...\] 公式 -> $$...$$
- block2 / 行内 R 表达式 -> 静态文本
- [@cite] 保留，交给 pandoc --citeproc 处理

本脚本只在迁移时运行一次，之后维护只改 manuscript/*.md。
"""
import os
import re
import json
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUSCRIPT = os.path.join(ROOT, 'manuscript')
FIGURES = os.path.join(MANUSCRIPT, 'figures')
OLD_DOCS = os.path.join(ROOT, 'docs')

# Rmd 文件 -> 输出 md 文件名（保持与旧站 URL 一致）
FILE_MAP = {
    'index.Rmd': 'index.md',
    '01-introduction.Rmd': 'intro.md',
    '02-candle.Rmd': 'candle.md',
    '03-single-candle.Rmd': 'single-candle.md',
    '04-two-candle.Rmd': 'two-candle.md',
    '05-multi-candle.Rmd': 'multi-candle.md',
    '06-gap-continuation.Rmd': 'gap-continuation.md',
    '07-doji-failure.Rmd': 'doji-failure.md',
    '08-pattern-dictionary.Rmd': 'pattern-dictionary.md',
    '09-pattern-scoring.Rmd': 'pattern-scoring.md',
    '10-trend.Rmd': 'trend.md',
    '11-percentage.Rmd': 'percentage.md',
    '12-ma.Rmd': 'ma.md',
    '13-rsi.Rmd': 'rsi.md',
    '14-obv.Rmd': 'obv.md',
    '15-waves.Rmd': 'waves.md',
    '16-profile.Rmd': 'profile.md',
    '17-option.Rmd': 'option.md',
    '18-hedging.Rmd': 'hedging.md',
    '19-comprehensive.Rmd': 'comprehensive.md',
    '21-hmm.Rmd': 'sound.md',
    '22-references.Rmd': 'references.md',
}

# 旧站 HTML 文件名（抽取表格用）
HTML_MAP = {k: v.replace('.md', '.html') for k, v in FILE_MAP.items()}

# 版本信息（从旧站固化）
VERSIONS = [
    ('R', '4.6.0'), ('knitr', '1.51'), ('bookdown', '0.47'),
    ('eCandleSticks', '0.1.1'), ('eFinCharts', '0.2.0'),
]


def extract_dynamic_tables():
    """从旧 HTML 抽取 lab_print_table 生成的统计表，按 Rmd 文件名索引。"""
    tables = {}

    def cells(row):
        out = [re.sub(r'<[^>]+>', '', c)
               for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.S)]
        return [html.unescape(c).strip().replace('\n', ' ') for c in out]

    def to_md(tbl):
        thead = re.search(r'<thead>(.*?)</thead>', tbl, re.S)
        body = re.search(r'<tbody>(.*?)</tbody>', tbl, re.S)
        hdr = cells(thead.group(1)) if thead else []
        rows = [cells(r) for r in re.findall(r'<tr[^>]*>(.*?)</tr>', body.group(1), re.S)] if body else []
        if not hdr:
            return None
        lines = ['| ' + ' | '.join(hdr) + ' |',
                 '|' + '|'.join(['---'] * len(hdr)) + '|']
        for r in rows:
            r = (r + [''] * len(hdr))[:len(hdr)]
            lines.append('| ' + ' | '.join(r) + ' |')
        return '\n'.join(lines)

    for rmd, hf in HTML_MAP.items():
        fp = os.path.join(OLD_DOCS, hf)
        if not os.path.exists(fp):
            tables[rmd] = []
            continue
        text = open(fp, encoding='utf-8', errors='ignore').read()
        tbls = re.findall(r'<table.*?</table>', text, re.S)
        dyn = [to_md(t) for t in tbls]
        tables[rmd] = [t for t in dyn if t and 'events' in t.split('\n')[0]]
    return tables


def build_label_map():
    """扫描所有 Rmd，建立 label -> (标题文字, 输出文件名)。"""
    labels = {}
    for rmd, out in FILE_MAP.items():
        fp = os.path.join(ROOT, rmd)
        if not os.path.exists(fp):
            continue
        text = open(fp, encoding='utf-8', errors='replace').read()
        for m in re.finditer(r'^#{1,6}\s+(.+?)\s*\{#([\w-]+)\}\s*$', text, re.M):
            title = re.sub(r'\s*\{.*?\}', '', m.group(1)).strip()
            labels[m.group(2)] = (title, out.replace('.md', '.html'))
    return labels


def convert_chunk(match, rmd, table_iter):
    head = match.group(1).strip()
    body = match.group(2)
    if head.startswith('r '):
        spec = head[2:].strip()
        # 不输出的 setup chunk
        if 'include=FALSE' in spec or 'include = FALSE' in spec:
            return ''
        # 版本表（前言、附录）
        if 'version-table' in spec or 'session-info' in spec:
            return '\n'.join(f'- **{k}**：`{v}`' for k, v in VERSIONS)
        # 参考文献自动生成 chunk
        if 'write_bib' in body:
            return ''
        # 绘图 chunk -> 静态图片
        if 'fig.cap' in spec:
            cap = re.search(r'fig\.cap\s*=\s*"([^"]*)"', spec)
            caption = cap.group(1) if cap else ''
            label = re.match(r'[\w-]+', spec).group(0)
            img = label.replace('-chart', '-chart').replace('-plot', '-plot')
            src = f'figures/{img}-1.png'
            return f'![{caption}]({src})'
        # 统计表 chunk -> 固化表格
        if 'table' in spec:
            try:
                return next(table_iter)
            except StopIteration:
                return '<!-- 表格待补 -->'
        # 普通 R 代码
        lang = 'r'
        return f'```{lang}\n{body.strip()}\n```'
    if head.startswith('python'):
        return f'```python\n{body.strip()}\n```'
    if head.startswith('block2'):
        return body.strip()
    return f'```{head}\n{body.strip()}\n```'


def convert_file(rmd, out_md, tables, labels):
    fp = os.path.join(ROOT, rmd)
    text = open(fp, encoding='utf-8', errors='replace').read()

    # 去掉 YAML frontmatter（index.Rmd）
    if text.startswith('---'):
        end = text.find('\n---', 3)
        if end > 0:
            text = text[end + 4:].lstrip('\n')

    # 行内 R 表达式：参考文献标题 / 无关条件
    text = re.sub(r'`r if \(knitr:::is_html_output\(\)\).*?`', '# 参考文献', text)

    # \[...\] -> $$...$$
    text = re.sub(r'\\\[\s*\n', '$$\n', text)
    text = re.sub(r'\n\s*\\\]', '\n$$', text)

    # (PART) 分篇标题 -> 特殊标记（构建脚本识别）
    text = re.sub(r'^# \(PART\)\s+(.+?)\s*\{-\}\s*$',
                  r'<!-- PART:\1 -->', text, flags=re.M)
    # (APPENDIX) 附录标题
    text = re.sub(r'^# \(APPENDIX\)\s+(.+?)\s*\{-\}\s*$',
                  r'<!-- PART:\1 -->', text, flags=re.M)

    # {#label} 保留；{-} 去掉
    text = re.sub(r'\{-\}\s*$', '', text, flags=re.M)

    # \@ref(label) -> 内部链接
    def ref_repl(m):
        key = m.group(1)
        if key in labels:
            title, target = labels[key]
            return f'[{title}]({target})'
        return key
    text = re.sub(r'\\@ref\(([\w-]+)\)', ref_repl, text)

    # 代码块
    table_iter = iter(tables.get(rmd, []))
    text = re.sub(r'```\{([^}]*)\}(.*?)```',
                  lambda m: convert_chunk(m, rmd, table_iter), text, flags=re.S)

    # 普通 python 围栏（保持）
    # 清理多余空行
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.strip() + '\n'


def main():
    os.makedirs(MANUSCRIPT, exist_ok=True)
    os.makedirs(FIGURES, exist_ok=True)

    tables = extract_dynamic_tables()
    labels = build_label_map()

    for rmd, out in FILE_MAP.items():
        if not os.path.exists(os.path.join(ROOT, rmd)):
            print('SKIP (missing):', rmd)
            continue
        md = convert_file(rmd, out, tables, labels)
        with open(os.path.join(MANUSCRIPT, out), 'w', encoding='utf-8') as f:
            f.write(md)
        print(f'{rmd:30s} -> manuscript/{out:24s} {len(md):6d} chars')

    # 复制图片（去掉 -1 后缀）
    src_fig = os.path.join(OLD_DOCS, 'ai-candlestick-analysis_files', 'figure-html')
    n = 0
    if os.path.isdir(src_fig):
        for f in os.listdir(src_fig):
            if f.endswith('.png'):
                new = re.sub(r'-1\.png$', '.png', f)
                with open(os.path.join(src_fig, f), 'rb') as fh:
                    data = fh.read()
                with open(os.path.join(FIGURES, new), 'wb') as fh:
                    fh.write(data)
                n += 1
    print(f'copied {n} figures to manuscript/figures/')


if __name__ == '__main__':
    main()
