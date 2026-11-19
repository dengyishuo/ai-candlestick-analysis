#!/usr/bin/env python3
"""用 pandoc 把 manuscript/*.md 构建为静态站点，输出到 docs/。

设计目标：
- 不依赖 R / bookdown / knitr，只依赖 pandoc（含 citeproc）
- 保持原有文件名与 URL 结构，GitHub Pages 配置不变
- 侧边栏导航、上下章链接、MathJax 公式、代码高亮、客户端搜索
- 分篇（PART）标记渲染为目录分组标题

用法：python3 scripts/build_site.py
"""
import os
import re
import json
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'manuscript')
OUT = os.path.join(ROOT, 'docs')
BIB = os.path.join(ROOT, 'book.bib')

SITE_TITLE = 'AI时代的蜡烛图分析'
SITE_SUBTITLE = '从经典形态到可验证证据：R与Python双语实践'
SITE_AUTHOR = '淮午'
SITE_DESC = '用可计算、可复现、可证伪的方法研究蜡烛图形态的开源书稿'

# 章节顺序（保持原书顺序与文件名）
CHAPTERS = [
    ('index.md', '前言', None),
    ('intro.md', '第1章 蜡烛图：从图形语言到可检验证据', '基础：从图形语言到可检验证据'),
    ('candle.md', '第2章 R与Python绘制可审计的蜡烛图', None),
    ('single-candle.md', '第3章 单根K线：压力、拒绝与失衡', '形态：按K线数量组织的结构语言'),
    ('two-candle.md', '第4章 双根K线：吞没、孕线与反击', None),
    ('multi-candle.md', '第5章 三根及多根K线：序列与确认', None),
    ('gap-continuation.md', '第6章 跳空与持续形态', None),
    ('doji-failure.md', '第7章 十字线、犹豫与失败信号', None),
    ('pattern-dictionary.md', '第8章 形态字典与统一扫描', None),
    ('pattern-scoring.md', '第9章 形态汇聚、冲突与概率评分', '证据：从方向标签到条件概率'),
    ('trend.md', '第10章 趋势、支撑阻力与极性转换', None),
    ('percentage.md', '第11章 蜡烛图与百分比回撤水平', None),
    ('ma.md', '第12章 蜡烛图与移动平均线', None),
    ('rsi.md', '第13章 蜡烛图与摆动指标', None),
    ('obv.md', '第14章 蜡烛图与成交量：OBV、CMF与VWAP', None),
    ('waves.md', '第15章 蜡烛图与波段结构', None),
    ('profile.md', '第16章 蜡烛图与成交量价格剖面', None),
    ('option.md', '第17章 蜡烛图与期权决策', '决策：从候选信号到风险暴露'),
    ('hedging.md', '第18章 蜡烛图与动态套期保值', None),
    ('comprehensive.md', '第19章 从形态到可运行研究：综合案例', None),
    ('sound.md', '附录 复现环境、API字典与研究审计', '附录'),
    ('references.md', '参考文献', None),
]

CSS = r'''
:root{--bg:#fff;--fg:#24292f;--muted:#57606a;--line:#d0d7de;--accent:#0969da;--code:#f6f8fa;--sidebar:270px}
@media(prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--muted:#8b949e;--line:#30363d;--accent:#58a6ff;--code:#161b22}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.75 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif}
#sidebar{position:fixed;top:0;left:0;bottom:0;width:var(--sidebar);overflow-y:auto;border-right:1px solid var(--line);padding:20px 0 40px;background:var(--bg)}
#sidebar .brand{padding:0 20px 16px;border-bottom:1px solid var(--line);margin-bottom:12px}
#sidebar .brand a{font-size:17px;font-weight:700;color:var(--fg);text-decoration:none;line-height:1.35}
#sidebar .brand small{display:block;color:var(--muted);font-size:12px;margin-top:6px;line-height:1.4}
#sidebar .group{color:var(--muted);font-size:12px;font-weight:600;letter-spacing:.05em;padding:16px 20px 4px}
#sidebar a.nav{display:block;padding:5px 20px;color:var(--fg);text-decoration:none;font-size:13.5px;border-left:3px solid transparent}
#sidebar a.nav:hover{background:var(--code);color:var(--accent)}
#sidebar a.nav.active{color:var(--accent);border-left-color:var(--accent);font-weight:600}
main{margin-left:var(--sidebar);padding:48px 56px 96px;max-width:920px}
.part-banner{display:inline-block;background:var(--accent);color:#fff;font-size:12.5px;font-weight:600;letter-spacing:.04em;padding:4px 14px;border-radius:20px;margin-bottom:18px}
h1{font-size:30px;line-height:1.3;margin:0 0 28px;padding-bottom:14px;border-bottom:2px solid var(--line)}
h2{font-size:23px;margin:40px 0 14px;padding-top:8px}
h3{font-size:18px;margin:28px 0 10px}
p,li{color:var(--fg)}
a{color:var(--accent)}
img{max-width:100%;height:auto;display:block;margin:22px auto;border:1px solid var(--line);border-radius:6px}
figcaption{text-align:center;color:var(--muted);font-size:13.5px;margin-top:-10px;margin-bottom:26px}
code{background:var(--code);padding:2px 6px;border-radius:4px;font-size:.88em;font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
pre{background:var(--code);border:1px solid var(--line);border-radius:8px;padding:16px;overflow-x:auto;line-height:1.55}
pre code{background:none;padding:0;font-size:13px}
table{border-collapse:collapse;width:100%;margin:22px 0;font-size:14px}
th,td{border:1px solid var(--line);padding:8px 12px;text-align:left}
th{background:var(--code);font-weight:600}
tr:nth-child(even){background:var(--code)}
.pager{display:flex;justify-content:space-between;gap:16px;margin-top:56px;padding-top:20px;border-top:1px solid var(--line)}
.pager a{flex:1;text-decoration:none;padding:12px 16px;border:1px solid var(--line);border-radius:8px;color:var(--fg)}
.pager a:hover{border-color:var(--accent);color:var(--accent)}
.pager .next{text-align:right}
.pager small{display:block;color:var(--muted);font-size:12px}
.footer{text-align:center;color:var(--muted);font-size:12.5px;margin-top:48px}
.search-box{width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);font-size:13px}
.search-results{margin-top:12px;font-size:13px}
.search-results a{display:block;padding:6px 0;text-decoration:none}
.search-results small{color:var(--muted)}
@media(max-width:900px){#sidebar{position:static;width:auto;height:auto;border-right:0;border-bottom:1px solid var(--line)}main{margin:0;padding:28px 20px 64px}}
'''


def pandoc_html(md_path, with_bib=False):
    cmd = ['pandoc', md_path, '--from=markdown+raw_tex', '--to=html5',
           '--section-divs', '--mathjax', '--wrap=none', '--highlight-style=tango']
    if with_bib and os.path.exists(BIB):
        cmd += ['--citeproc', '--bibliography=' + BIB]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print('pandoc FAILED:', md_path, r.stderr[:500], file=sys.stderr)
        sys.exit(1)
    return r.stdout


def build_nav(active):
    parts = []
    cur_group = None
    for fn, title, group in CHAPTERS:
        if group:
            cur_group = group
            parts.append(f'<div class="group">{group}</div>')
        href = fn.replace('.md', '.html')
        cls = 'nav active' if fn == active else 'nav'
        parts.append(f'<a class="{cls}" href="{href}">{title}</a>')
    return '\n'.join(parts)


def build_pager(idx):
    prev = next_ = ''
    if idx > 0:
        pfn, ptitle, _ = CHAPTERS[idx - 1]
        prev = f'<a href="{pfn.replace(".md",".html")}"><small>← 上一章</small>{ptitle}</a>'
    if idx < len(CHAPTERS) - 1:
        nfn, ntitle, _ = CHAPTERS[idx + 1]
        next_ = f'<a class="next" href="{nfn.replace(".md",".html")}"><small>下一章 →</small>{ntitle}</a>'
    return f'<div class="pager">{prev}{next_}</div>'


def page(title, active, body, idx):
    nav = build_nav(active)
    pager = build_pager(idx)
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{SITE_DESC}">
<title>{title} · {SITE_TITLE}</title>
<link rel="stylesheet" href="assets/style.css">
<script>window.MathJax={{tex:{{inlineMath:[['$','$'],['\\(','\\)']],displayMath:[['$$','$$'],['\\[','\\]']]}}}};</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head><body>
<nav id="sidebar"><div class="brand"><a href="index.html">{SITE_TITLE}</a><small>{SITE_SUBTITLE}</small>
<input class="search-box" id="q" placeholder="搜索章节…" autocomplete="off">
<div class="search-results" id="results"></div></div>
{nav}</nav>
<main>{body}{pager}
<div class="footer">{SITE_AUTHOR} · {SITE_TITLE} · 开源书稿 · <a href="https://github.com/dengyishuo/ai-candlestick-analysis">GitHub</a></div>
</main>
<script src="assets/search.js"></script></body></html>'''


def main():
    if shutil.which('pandoc') is None:
        print('ERROR: pandoc not found', file=sys.stderr)
        sys.exit(1)

    # 清理旧站点，重建
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, 'assets', 'figures'), exist_ok=True)

    # 复制图片
    fig_src = os.path.join(SRC, 'figures')
    n_fig = 0
    if os.path.isdir(fig_src):
        for f in os.listdir(fig_src):
            if f.lower().endswith('.png'):
                shutil.copy2(os.path.join(fig_src, f),
                             os.path.join(OUT, 'assets', 'figures', f))
                n_fig += 1
    print(f'copied {n_fig} figures')

    # 复制 CSS / 搜索脚本
    with open(os.path.join(OUT, 'assets', 'style.css'), 'w', encoding='utf-8') as f:
        f.write(CSS)
    with open(os.path.join(ROOT, 'scripts', 'search.js'), encoding='utf-8') as f:
        shutil.copyfile(os.path.join(ROOT, 'scripts', 'search.js'),
                        os.path.join(OUT, 'assets', 'search.js'))

    search_index = []
    for idx, (fn, title, _) in enumerate(CHAPTERS):
        src = os.path.join(SRC, fn)
        if not os.path.exists(src):
            print('MISSING:', fn, file=sys.stderr)
            continue
        body = pandoc_html(src, with_bib=(fn == 'references.md'))
        # 图片路径：figures/xxx-1.png -> assets/figures/xxx.png
        body = body.replace('src="figures/', 'src="assets/figures/')
        body = re.sub(r'(assets/figures/[^\"]+?)-1\.png', r'\1.png', body)
        # 分篇标记：HTML 注释 -> 可见的分篇横幅
        body = re.sub(r'<!-- PART:(.+?) -->',
                      r'<div class="part-banner">\1</div>', body)
        out_fn = fn.replace('.md', '.html')
        with open(os.path.join(OUT, out_fn), 'w', encoding='utf-8') as f:
            f.write(page(title, fn, body, idx))
        # 搜索索引：纯文本
        plain = re.sub(r'<[^>]+>', ' ', body)
        plain = re.sub(r'\s+', ' ', plain).strip()
        search_index.append({'title': title, 'url': out_fn, 'text': plain[:4000]})
        print(f'built {out_fn:24s} {len(body):7d} chars')

    with open(os.path.join(OUT, 'assets', 'search-index.json'), 'w', encoding='utf-8') as f:
        json.dump(search_index, f, ensure_ascii=False)

    # PDF（旧版，保留供下载）
    old_pdf = os.path.join(ROOT, '.workbuddy-backup', '2026-11-19-pandoc-migration',
                           'docs', 'ai-candlestick-analysis.pdf')
    if os.path.exists(old_pdf):
        shutil.copy2(old_pdf, os.path.join(OUT, 'ai-candlestick-analysis.pdf'))
        print('copied legacy PDF')

    with open(os.path.join(OUT, '.nojekyll'), 'w') as f:
        pass
    print(f'\nsite built: {OUT}')


if __name__ == '__main__':
    main()
