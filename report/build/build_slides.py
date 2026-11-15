"""Render the slide deck (16:9 PDF) in the cover's style.

Usage: python report/build/build_slides.py   ->  report/Two-Notes-One-Witness-slides.pdf
Numbers come from results/tables (see report/slides-outline.md for the source of each slide).
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
REPORT = HERE.parent
A, FIG = "../assets/", "../../results/figures/"
TOTAL = 9

def slide(n, kicker, title, body, cls=""):
    return f"""<section class="s {cls}">
  <div class="kick">{kicker}</div>
  <h2>{title}</h2>
  <div class="body">{body}</div>
  <footer><span>Two Notes, One Witness</span><span>{n:02d} / {TOTAL:02d}</span></footer>
</section>"""

S = []
S.append(f'<section class="s cover"><img src="{A}cover.png"></section>')

S.append(slide(1, "The picture", "Two notes, one witness", """
<div class="pair">
  <div class="card"><div class="lab">Note A</div><div class="who">AI account 1</div>
    <div class="lines"><i></i><i></i><i class="short"></i></div>
    <div class="links"><span>link 1</span><span>link 2</span></div></div>
  <div class="mid"><div class="tick">same post</div><div class="tick">same minute</div><div class="tick">same two links</div></div>
  <div class="card"><div class="lab">Note B</div><div class="who">AI account 2</div>
    <div class="lines"><i></i><i class="short"></i><i></i></div>
    <div class="links"><span>link 2</span><span>link 1</span></div></div>
</div>
<p class="say">To a rater these look like two contributors who agree. They are two accounts of one system.
<span class="src">A real pair from the data, shown schematically: note text and account ids omitted.</span></p>"""))

S.append(slide(2, "The gap", "Community Notes checks that raters are independent.<br>Nobody checks the writers", """
<div class="flow">
  <div class="node"><b>Writers</b><span>propose notes</span><em>not checked</em></div>
  <div class="arrow"></div>
  <div class="node"><b>Raters</b><span>rate notes</span><em class="on">bridging: raters who usually disagree must agree</em></div>
  <div class="arrow"></div>
  <div class="node"><b>Readers</b><span>see the note</span></div>
</div>
<p class="say">Since September 2025 AI programs can write notes. They now submit more than half of new notes.
<span class="src">Wojcik et al. 2022; Gong and Wu 2026.</span></p>"""))

S.append(slide(3, "Finding 1", "Six accounts behave as one system", """
<div class="facts">
  <div><b>86%</b><span>of all AI notes come from six accounts</span></div>
  <div><b>17 Dec 2025</b><span>five of them wrote their first note on the same day</span></div>
  <div><b>Never 4</b><span>on a post: one, two or three of the six, never more</span></div>
</div>
<p class="say">We call them <span class="hl">the fleet</span> and count them as one author.
<span class="src">docs/data-notes.md, step1_ai_writers.csv</span></p>"""))

S.append(slide(4, "Finding 1", "That system writes half of what readers see", f"""
<div class="split">
  <img class="fig" src="{FIG}fig1_who_writes_shown_notes.png">
  <div class="side">
    <div class="big"><b>51%</b><span>of shown notes, April to November 2026</span></div>
    <div class="big"><b>34%</b><span>of covered posts: nobody else wrote a note</span></div>
    <p class="note">The notes are rated helpful. The issue is a dependence with no signal attached.</p>
  </div>
</div>"""))

S.append(slide(5, "Method", "The question, and three things that could fake the answer", """
<p class="q">On the same post, are two AI-written notes more alike than two human-written notes?</p>
<div class="three">
  <div><span class="n">1</span><b>One system, many names</b><span>The fleet counts as one author.</span></div>
  <div><span class="n">2</span><b>Time</b><span>Compare only inside the same window: under 1 h, 1 to 6 h, 6 to 24 h.</span></div>
  <div><span class="n">3</span><b>Viral posts</b><span>Every post weighs the same.</span></div>
</div>
<p class="say">Baseline: two human notes on the same post. Rules and refutation criteria were committed before any result.
<span class="src">docs/decisions.md</span></p>"""))

S.append(slide(6, "Finding 2", "Different operators mostly use different sources", """
<div class="bars">
  <div class="row"><span class="lbl">AI-AI, different operators</span><div class="track"><div class="bar ai" style="width:68.4%"></div></div><span class="val">0.171</span></div>
  <div class="row"><span class="lbl">Human-human</span><div class="track"><div class="bar hu" style="width:62.4%"></div></div><span class="val">0.156</span></div>
  <div class="axis"><span>0</span><span>0.25</span></div>
</div>
<p class="say">Source overlap (Jaccard). Difference <span class="hl">+0.015</span> [+0.010, +0.020]: real, preregistered, and small.
<span class="src">"At least one shared link" (40% vs 21%) overstates this: AI notes carry more links. step4_main.csv</span></p>"""))

S.append(slide(7, "Finding 3", "Given the same post, they write the same words", f"""
<div class="split">
  <img class="fig" src="{FIG}fig2_same_post_vs_cross_post.png">
  <div class="side">
    <div class="big"><b>12.1%</b><span>of AI-AI pairs pass a bar that 5% of human pairs pass</span></div>
    <div class="big"><b>0.0%</b><span>on different posts: not a house style</span></div>
    <div class="big"><b>0.05%</b><span>near copies: not copying</span></div>
  </div>
</div>"""))

S.append(slide(8, "Limits", "Two predictions failed", """
<div class="two">
  <div><b>Shared fate</b><span>Do AI notes share rating outcomes more than human notes?</span><em>+0.049 [-0.015, +0.111]. No.</em></div>
  <div><b>Trend</b><span>Is AI resemblance growing over time?</span><em>Sources +0.005, text -0.009. No.</em></div>
</div>
<table class="rob"><tr><th>Robustness</th><th>Source difference</th><th>AI-AI text above bar</th></tr>
<tr><td>Main</td><td>+0.014</td><td>12.1%</td></tr><tr><td>Fleet = 7 accounts</td><td>+0.028</td><td>12.9%</td></tr>
<tr><td>Fleet not merged</td><td>+0.051</td><td>14.4%</td></tr><tr><td>3-grams</td><td>+0.014</td><td>14.4%</td></tr></table>
<p class="say">We found concentration and resemblance, not harm to outcomes.
<span class="src">Fleet identified by behaviour, not proof of one operator. No post text in the data. Small reading sample.</span></p>"""))

S.append(slide(9, "What follows", "What to do, and what comes next", """
<ol class="asks">
  <li>Publish an operator field for AI writers, so one system is visible as one.</li>
  <li>Report writer concentration and pair similarity as a standing health metric.</li>
  <li>When routing rater attention, treat near-identical notes on a post as one.</li>
</ol>
<p class="next"><b>Next.</b> The Ratings file: how much rater attention goes to redundant AI notes.</p>
<p class="close">When machines write most of what we read, counting votes is no longer enough.<br>We need to know how many of them are independent.</p>
<p class="repo">github.com/dassmod/independent-witnesses</p>""", cls="end"))

css = f"""
@font-face{{font-family:"Poppins";src:url({A}fonts/Poppins-Light.ttf);font-weight:300}}
@font-face{{font-family:"Poppins";src:url({A}fonts/Poppins-Regular.ttf);font-weight:400}}
@font-face{{font-family:"Poppins";src:url({A}fonts/Poppins-Medium.ttf);font-weight:500}}
@font-face{{font-family:"Mono";src:url({A}fonts/JetBrainsMono-Regular.ttf)}}
@page{{size:1600px 900px;margin:0}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:"Poppins";color:#141414;-webkit-font-smoothing:antialiased}}
.s{{width:1600px;height:900px;position:relative;overflow:hidden;background:#f7f7f6;page-break-after:always;padding:92px 120px 0;display:flex;flex-direction:column}}
.cover{{padding:0}} .cover img{{width:1600px;height:900px;display:block}}
.end{{background:#f7f7f6 url({A}cover_bg.png) no-repeat;background-size:1600px 900px;background-position:960px 0}}
.end:after{{content:"";position:absolute;inset:0;background:linear-gradient(90deg,#f7f7f6 0,#f7f7f6 62%,rgba(247,247,246,.55) 84%,rgba(247,247,246,.15) 100%);z-index:0}}
.end>*:not(footer){{position:relative;z-index:1}} .end footer{{z-index:1}}
.kick{{font-family:"Mono";font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:#8a8984;display:flex;align-items:center;gap:12px}}
.kick:before{{content:"";width:12px;height:12px;background:#EAFF3D;border:1px solid #141414;clip-path:polygon(50% 0,100% 100%,0 100%)}}
h2{{font-weight:500;font-size:46px;line-height:1.16;letter-spacing:-.02em;margin:22px 0 0;max-width:1260px}}
.body{{flex:1;display:flex;flex-direction:column;justify-content:center;padding-bottom:120px;margin-top:20px}} .body>*{{flex:none}}
footer{{position:absolute;left:120px;right:120px;bottom:44px;display:flex;justify-content:space-between;
       font-family:"Mono";font-size:12px;letter-spacing:.08em;color:#a3a29d;border-top:1px solid #e3e3e0;padding-top:14px}}
.say{{font-size:22px;line-height:1.5;font-weight:300;max-width:1180px;margin-top:46px}}
.src{{display:block;font-family:"Mono";font-size:12.5px;color:#8a8984;margin-top:12px;letter-spacing:.02em}}
.hl{{background:linear-gradient(transparent 58%,#EAFF3D 58%);padding:0 3px}}
/* 1 */
.pair{{display:flex;align-items:center;gap:40px}}
.card{{width:430px;background:#fff;border:1px solid #dcdcd8;border-radius:14px;padding:30px 32px}}
.lab{{font-family:"Mono";font-size:12px;letter-spacing:.12em;color:#8a8984;text-transform:uppercase}}
.who{{font-size:22px;font-weight:500;margin-top:6px}}
.lines{{margin:22px 0}} .lines i{{display:block;height:9px;background:#e6e6e3;border-radius:5px;margin-bottom:11px}} .lines i.short{{width:62%}}
.links span{{display:inline-block;font-family:"Mono";font-size:13px;border:1px solid #141414;border-radius:20px;padding:5px 13px;margin-right:8px;background:#EAFF3D}}
.mid{{flex:1;display:flex;flex-direction:column;gap:14px;align-items:center}}
.tick{{font-family:"Mono";font-size:13px;letter-spacing:.06em;color:#4a4a48;border-bottom:1px solid #cfcfcb;padding:0 10px 6px}}
/* 2 */
.flow{{display:flex;align-items:stretch;gap:0}}
.node{{width:340px;border:1px solid #cfcfcb;border-radius:14px;background:#fff;padding:28px 30px;display:flex;flex-direction:column;gap:6px}}
.node b{{font-size:26px;font-weight:500}} .node span{{font-size:18px;font-weight:300;color:#4a4a48}}
.node em{{font-style:normal;font-family:"Mono";font-size:13px;color:#8a8984;margin-top:14px;line-height:1.5}}
.node em.on{{color:#141414}} .node em.on:before{{content:"";display:inline-block;width:9px;height:9px;background:#EAFF3D;border:1px solid #141414;margin-right:8px}}
.arrow{{width:70px;position:relative}} .arrow:before{{content:"";position:absolute;left:12px;right:12px;top:50%;border-top:1.5px solid #141414}}
.arrow:after{{content:"";position:absolute;right:12px;top:calc(50% - 5px);border-left:9px solid #141414;border-top:5px solid transparent;border-bottom:5px solid transparent}}
/* 3 */
.facts{{display:grid;grid-template-columns:repeat(3,1fr);gap:56px}}
.facts div{{border-top:1.5px solid #141414;padding-top:22px}}
.facts b{{display:block;font-size:58px;font-weight:500;letter-spacing:-.03em;line-height:1}}
.facts span{{display:block;font-size:19px;font-weight:300;line-height:1.45;margin-top:16px;color:#2a2a28}}
/* figs */
.split{{display:flex;gap:56px;align-items:flex-start;margin-top:-14px}}
.fig{{width:860px;background:#fff;border-radius:12px;padding:18px;border:1px solid #e6e6e3}}
.side{{flex:1;padding-top:10px}}
.big{{border-top:1.5px solid #141414;}} .big{{padding:18px 0 26px}}
.big>b{{display:block;font-size:52px;font-weight:500;letter-spacing:-.03em;line-height:1}}
.big>span{{display:block;font-size:18px;font-weight:300;line-height:1.45;margin-top:10px}}
.note{{font-size:16px;font-weight:300;color:#4a4a48;line-height:1.5;margin-top:4px}}
/* 5 */
.q{{font-size:30px;font-weight:300;line-height:1.4;max-width:1150px}}
.three{{display:grid;grid-template-columns:repeat(3,1fr);gap:40px;margin-top:48px}}
.three div{{background:#fff;border:1px solid #dcdcd8;border-radius:14px;padding:26px 28px}}
.three .n{{font-family:"Mono";font-size:13px;color:#8a8984}}
.three b{{display:block;font-size:23px;font-weight:500;margin:10px 0 8px}} .three span{{font-size:17px;font-weight:300;line-height:1.5}}
/* 6 */
.bars{{max-width:1180px}}
.row{{display:grid;grid-template-columns:330px 1fr 90px;align-items:center;gap:22px;margin-bottom:26px}}
.lbl{{font-size:20px;font-weight:400}} .val{{font-size:26px;font-weight:500;text-align:right}}
.track{{height:46px;background:#ececea;border-radius:4px}}
.bar{{height:46px;border-radius:0 4px 4px 0}} .bar.ai{{background:#EAFF3D;border:1px solid #141414}} .bar.hu{{background:#8f8e89}}
.axis{{margin-left:352px;margin-right:112px;display:flex;justify-content:space-between;font-family:"Mono";font-size:12px;color:#8a8984}}
/* 8 */
.two{{display:grid;grid-template-columns:1fr 1fr;gap:48px}}
.two div{{border-top:1.5px solid #141414;padding-top:20px}}
.two b{{font-size:28px;font-weight:500;display:block}} .two span{{font-size:18px;font-weight:300;display:block;margin:8px 0 12px;color:#2a2a28}}
.two em{{font-style:normal;font-family:"Mono";font-size:16px}}
.rob{{align-self:flex-start;min-width:760px;border-collapse:collapse;margin-top:40px;font-size:15px}} .rob th{{font-weight:500;text-align:left;padding:6px 40px 6px 0;border-bottom:1px solid #141414}}
.rob td{{font-weight:300;padding:5px 40px 5px 0;border-bottom:1px solid #e3e3e0;font-variant-numeric:tabular-nums}}
.s .rob+.say{{margin-top:30px}}
/* 9 */
.asks{{list-style:none;counter-reset:a;max-width:980px}}
.asks li{{counter-increment:a;font-size:24px;font-weight:300;line-height:1.45;padding:16px 0 16px 56px;border-top:1px solid #d6d6d2;position:relative}}
.asks li:before{{content:counter(a);position:absolute;left:0;top:18px;font-family:"Mono";font-size:14px;color:#8a8984}}
.next{{font-size:19px;font-weight:300;margin-top:26px}} .next b{{font-weight:500}}
.close{{font-size:24px;font-weight:400;line-height:1.45;margin-top:40px;max-width:980px}}
.repo{{font-family:"Mono";font-size:14px;color:#4a4a48;margin-top:26px;letter-spacing:.03em}}
"""
html = f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{"".join(S)}</body></html>'
out = HERE / "slides.html"; out.write_text(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1600, "height": 900})
    pg.goto(out.as_uri()); pg.wait_for_timeout(700)
    pg.pdf(path=str(REPORT / "Two-Notes-One-Witness-slides.pdf"), width="1600px", height="900px", print_background=True)
    b.close()
print("ok")
