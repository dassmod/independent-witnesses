"""Render report/draft.md into the submission PDF, laid out on the Apart template's structure.

Usage: python report/build/build_report.py   ->  report/Two-Notes-One-Witness.pdf
Needs: markdown, playwright (chromium).
"""
import re
from pathlib import Path
import markdown
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
REPORT = HERE.parent
md = (REPORT / "draft.md").read_text()
md = re.sub(r"<!--.*?-->", "", md, flags=re.S)

# split off the title block and the abstract; the rest is the body
title = re.search(r"^# (.+)$", md, re.M).group(1)
main_t, sub_t = title.split(": ", 1)
abstract = re.search(r"## Abstract\n(.*?)\n## 1\.", md, re.S).group(1).strip()
body = md[md.index("## 1. Introduction"):]

conv = lambda s: markdown.markdown(s, extensions=["tables"])
body_html = conv(body).replace('src="../results/', 'src="../../results/')
# figure captions: an italic paragraph right after an image becomes a figcaption
body_html = re.sub(r'<p><img alt="([^"]*)" src="([^"]+)" /></p>\s*<p><em>(.*?)</em></p>',
                   r'<figure><img src="\2" alt="\1"><figcaption>\3</figcaption></figure>', body_html, flags=re.S)
# table captions: an italic paragraph right before a table
body_html = re.sub(r'<p><em>(Table \d+\..*?)</em></p>\s*<table>', r'<table><caption>\1</caption>', body_html, flags=re.S)
# appendix and back matter start on a fresh page
body_html = body_html.replace("<h2>References</h2>", '<h2 class="brk">References</h2>')

F = "../assets/fonts/"
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:"Serif";src:url("{F}SourceSerif4[opsz,wght].ttf");font-weight:200 900;font-style:normal}}
@font-face{{font-family:"Serif";src:url("{F}SourceSerif4-Italic[opsz,wght].ttf");font-weight:200 900;font-style:italic}}
@font-face{{font-family:"Poppins";src:url({F}Poppins-Light.ttf);font-weight:300}}
@font-face{{font-family:"Poppins";src:url({F}Poppins-LightItalic.ttf);font-weight:300;font-style:italic}}
@font-face{{font-family:"Poppins";src:url({F}Poppins-Regular.ttf);font-weight:400}}
@font-face{{font-family:"Poppins";src:url({F}Poppins-Medium.ttf);font-weight:500}}
@font-face{{font-family:"Poppins";src:url({F}Poppins-SemiBold.ttf);font-weight:600}}
@font-face{{font-family:"Mono";src:url({F}JetBrainsMono-Regular.ttf)}}
@page{{size:Letter;margin:0.85in 0.9in 0.8in}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:"Serif",Georgia,serif;font-size:10.1pt;line-height:1.46;color:#141414;
     font-variant-numeric:lining-nums;hyphens:auto;-webkit-font-smoothing:antialiased}}
.titleblock{{text-align:center;margin-top:0.15in}}
.rule1{{border-top:2.2pt solid #141414;margin:0 0.35in}}
.rule2{{border-top:0.6pt solid #141414;margin:0 0.35in}}
h1{{font-family:"Poppins";font-weight:500;font-size:21pt;line-height:1.18;letter-spacing:-.015em;margin:20pt 0.4in 6pt}}
h1 sup{{font-size:9pt;font-weight:400;vertical-align:top;position:relative;top:2pt;margin-left:1pt}}
.sub{{font-family:"Poppins";font-weight:300;font-size:12pt;line-height:1.35;color:#141414cc;margin:0 0.6in 18pt}}
.authors{{margin:18pt 0 0;font-size:10.5pt;line-height:1.35}}
.authors b{{font-weight:600}}
.aff{{color:#4a4a48}}
.with{{margin-top:12pt;font-size:10pt;line-height:1.35}} .with b{{font-weight:600}}
.abs{{margin:20pt 0.5in 0}}
.abs h2{{text-align:center;margin:0 0 8pt;border:0;padding:0}}
.abs p{{font-style:italic;font-size:10pt;line-height:1.48;margin:0 0 5.5pt;text-align:left}}
.fn{{position:absolute;bottom:0;left:0;right:0;font-size:8pt;color:#4a4a48}}
.fn:before{{content:"";display:block;width:1.6in;border-top:0.5pt solid #8a8984;margin-bottom:4pt}}
.first{{margin-bottom:6pt}} .note{{font-family:"Poppins";font-weight:300;font-size:7.8pt;color:#8a8984;margin-top:9pt;letter-spacing:.01em}}
h2{{font-family:"Poppins";font-weight:500;font-size:13pt;letter-spacing:-.005em;margin:20pt 0 6pt;break-after:avoid}}
h3{{font-family:"Poppins";font-weight:500;font-size:10.6pt;margin:13pt 0 3pt;break-after:avoid}}
h2.brk{{break-before:page;margin-top:0}}
p{{margin:0 0 7pt;text-align:justify}}
strong{{font-weight:650}}
ul,ol{{margin:0 0 7pt;padding-left:1.35em}} li{{margin-bottom:2.5pt}}
code{{font-family:"Mono";font-size:8.3pt;color:#3a3a38;background:#f2f2f0;padding:0.5pt 2.5pt;border-radius:2px}}
a{{color:inherit;text-decoration:underline;text-decoration-color:#b5b4ae;text-underline-offset:1.5pt}}
figure{{margin:12pt 0 12pt;break-inside:avoid}}
figure img{{width:90%;display:block;margin:0 auto}}
figure.narrow img{{width:74%;margin:0 auto}}
figcaption,caption{{font-family:"Poppins";font-weight:300;font-size:8.1pt;line-height:1.45;color:#4a4a48;text-align:left}}
figcaption{{margin-top:6pt}}
caption{{caption-side:top;margin-bottom:6pt}}
table{{width:100%;border-collapse:collapse;margin:10pt 0 12pt;font-family:"Poppins";font-size:8.4pt;break-inside:avoid;
       font-variant-numeric:tabular-nums}}
th{{font-weight:500;text-align:left;border-top:1pt solid #141414;border-bottom:0.5pt solid #141414;padding:4pt 6pt 4pt 0}}
td{{font-weight:300;padding:3.2pt 6pt 3.2pt 0;border-bottom:0.4pt solid #e2e2df;vertical-align:top}}
tr:last-child td{{border-bottom:0.8pt solid #141414}}
.refs ol, ol.refs{{font-size:9pt;line-height:1.42}}
</style></head><body>
<section class="first">
 <div class="titleblock">
  <div class="rule1"></div>
  <h1>{main_t}</h1>
  <div class="sub">{sub_t}</div>
  <div class="rule2"></div>
  <div class="authors"><b>Dastan Modubash</b><br><span class="aff">Independent</span></div>
  <div class="with"><b>With</b><br>Apart Research</div>
  <div class="note">Research conducted at the AI x Epistemics Research Sprint, November 2026</div>
 </div>
 <div class="abs"><h2>Abstract</h2>{conv(abstract)}</div>
</section>
{body_html}
</body></html>"""
html = html.replace('<h2>References</h2>', '<h2>References</h2>')
html = re.sub(r'(<h2 class="brk">References</h2>\s*)<ol>', r'\1<ol class="refs">', html)
html = html.replace('<figure><img src="../../results/figures/fig2', '<figure class="narrow"><img src="../../results/figures/fig2')

out_html = HERE / "report.html"
out_html.write_text(html)
foot = ('<div style="width:100%;font-family:Helvetica;font-size:7.5px;color:#8a8984;'
        'padding:0 0.9in;display:flex;justify-content:space-between">'
        '<span>Two Notes, One Witness</span><span class="pageNumber"></span></div>')
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto(out_html.as_uri()); pg.wait_for_timeout(600)
    pg.pdf(path=str(REPORT / "Two-Notes-One-Witness.pdf"), format="Letter", display_header_footer=True,
           header_template="<div></div>", footer_template=foot, prefer_css_page_size=True)
    b.close()
print("ok")
