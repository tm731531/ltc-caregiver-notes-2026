#!/usr/bin/env python3
"""從 quiz.html 的 QUIZ 資料產生獨立的「考場小抄（答案版）」mini.html。
- 選擇題只列正解文字；「以上皆是」型自動展開列出各選項內容。
- 問答題列出 answer_text。
- 純靜態、可列印、與 quiz.html/reference.html 獨立。
"""
import re, json, html as H, os

D = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(D, "quiz.html"), encoding="utf-8").read()
QUIZ = json.loads(re.search(r'const QUIZ=(\[.*?\]);', src, re.S).group(1))

ALLOF = re.compile(r'以上皆(是|對|為)|上述皆')
COMBO = re.compile(r'^[\s①②③④⑤⑥⑦⑧⑨1-9()（）、.,＋+和及與\-–]+$')  # 純數字組合答案

def esc(s): return H.escape(str(s or "")).strip()

def stem_items(stem):
    """把題幹的 ①②③… 拆成 {編號:內容}。"""
    parts = re.split(r'([①②③④⑤⑥⑦⑧⑨])', stem)
    items = {}
    i = 1
    while i < len(parts):
        n = ord(parts[i]) - 9311  # ①→1
        text = (parts[i + 1] if i + 1 < len(parts) else "")
        # 去掉最後一項尾巴的收尾語(。？：後面的字)
        text = re.split(r'[。？：]', text.strip(" 　、，."))[0].strip(" 　、，.")
        items[n] = text
        i += 2
    return items

def answer_html(q):
    if q.get("type") == "essay":
        return f'<span class="a">{esc(q.get("answer_text"))}</span>'
    corr = [o for o in q["options"] if o.get("correct")]
    if not corr:
        return f'<span class="a">（答案 {esc(q.get("answer"))}）</span>'
    txt = corr[0]["text"].strip()
    out = f'<span class="a">{esc(txt)}</span>'
    # (1)「以上皆是」型 → 展開其餘選項內容
    if ALLOF.search(txt):
        items = [o["text"] for o in q["options"] if not o.get("correct")]
        if items:
            exp = "　".join(f"{chr(9312+i)}{esc(t)}" for i, t in enumerate(items))
            out += f'<span class="exp">＝ {exp}</span>'
    # (2)「①③④」題幹編號組合型 → 依答案順序對應題幹內容
    elif COMBO.match(txt) and len(re.findall(r'[①②③④⑤⑥⑦⑧⑨1-9]', txt)) >= 2:
        items = stem_items(q["q"])
        seq = []
        for ch in txt:  # 保留答案給的順序
            if "①" <= ch <= "⑨":
                seq.append(ord(ch) - 9311)
            elif ch.isdigit():
                seq.append(int(ch))
        if items and all(n in items for n in seq):
            exp = "　".join(f"{chr(9311+n)}{esc(items[n])}" for n in seq)
            out += f'<span class="exp">＝ {exp}</span>'
    return out

rows = []
for c in QUIZ:
    qs = "".join(
        f'<div class="q"><span class="n">{q["num"]}.</span>'
        f'<span class="stem">{esc(q["q"])}</span>'
        f'<span class="arrow">→</span>{answer_html(q)}</div>'
        for q in c["questions"]
    )
    rows.append(
        f'<section><h2>第{c["chapter"]}章　{esc(c["title"])}'
        f'{"（問答）" if c.get("essay") else ""}</h2>{qs}</section>'
    )

body = "\n".join(rows)
doc = f"""<!doctype html><html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>照服員考照 · 考場小抄（答案版）</title>
<style>
:root{{color-scheme:light}}
*{{box-sizing:border-box}}
body{{font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif;
 margin:0;padding:16px;background:#fff;color:#111;line-height:1.5;font-size:15px}}
.top{{position:sticky;top:0;background:#fff;border-bottom:2px solid #0a7;padding:6px 0 10px;margin-bottom:10px}}
h1{{font-size:19px;margin:0 0 4px}}
.sub{{color:#555;font-size:13px}}
.controls{{margin-top:8px;font-size:13px}}
button{{font:inherit;font-size:13px;padding:4px 10px;border:1px solid #0a7;background:#0a7;color:#fff;border-radius:6px;cursor:pointer}}
section{{margin:0 0 14px;break-inside:avoid}}
h2{{font-size:15px;background:#eafaf3;border-left:4px solid #0a7;padding:4px 8px;margin:0 0 6px}}
.q{{padding:3px 4px 3px 10px;border-bottom:1px dotted #ddd}}
.n{{color:#0a7;font-weight:700;margin-right:4px}}
.stem{{color:#333}}
.arrow{{color:#bbb;margin:0 5px}}
.a{{font-weight:700;color:#c0392b}}
.exp{{display:block;margin:2px 0 2px 20px;color:#7a4;font-size:13px}}
@media(max-width:900px){{.stem{{display:block;margin:0 0 1px 16px;color:#666;font-size:13px}}.arrow{{display:none}}}}
@media print{{
 body{{padding:0;font-size:11px;line-height:1.35;color:#000}}
 .top{{position:static;border-color:#000}} .controls{{display:none}}
 h1{{font-size:14px}} h2{{font-size:11px;background:#eee !important;border-color:#000;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
 .a{{color:#000}} .exp{{color:#333}} .arrow{{color:#999}}
 section{{margin-bottom:6px}} .q{{padding:1px 2px 1px 8px}}
 @page{{margin:8mm}}
}}
</style></head><body>
<div class="top">
 <h1>✍️ 照服員考照 · 考場小抄（答案版）</h1>
 <div class="sub">《照顧服務員訓練指引》八版 · 23 章 · 每題只列正解；「以上皆是」已展開內容。答案以課本解答為準。</div>
 <div class="controls"><button onclick="window.print()">🖨️ 列印 / 存 PDF</button>　共 {sum(len(c['questions']) for c in QUIZ)} 題</div>
</div>
{body}
</body></html>"""

with open(os.path.join(D, "mini.html"), "w", encoding="utf-8") as f:
    f.write(doc)
print("mini.html 產生完成:", sum(len(c['questions']) for c in QUIZ), "題,", len(QUIZ), "章")
