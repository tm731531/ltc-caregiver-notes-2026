#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate docs/exam-quiz.html from the official 17800 學科 question-bank PDF.

Source of truth: 參考教材/考照/學科題庫/17800-學科測試參考資料-*.pdf
(官方公開免費題庫，勞動部勞動力發展署技能檢定中心公告)

Usage:  python3 docs/gen_exam_quiz.py
Requires: pdftotext (poppler-utils)
"""
import re, json, subprocess, glob, os, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PDF = sorted(glob.glob(os.path.join(REPO, "參考教材/考照/學科題庫/17800-學科測試參考資料-*.pdf")))
if not PDF:
    sys.exit("找不到官方學科 PDF")
PDF = PDF[-1]
OUT = os.path.join(HERE, "exam-quiz.html")

txt = subprocess.run(["pdftotext", "-layout", PDF, "-"],
                     capture_output=True, text=True, check=True).stdout

CIRCLE = {"①": 1, "②": 2, "③": 3, "④": 4}
ITEM_RE = re.compile(r"工作項目\s*0?(\d)\s*[:：]\s*(\S+)")
Q_START = re.compile(r"^\s*(\d+)\.\s*\((\d)\)\s*(.*)$")
PAGE_RE = re.compile(r"Page\s+\d+\s+of\s+\d+")
HDR_RE = re.compile(r"17800\s*照顧服務員")
VER_RE = re.compile(r"版次編號\s*[:：]\s*(\S+)")
DATE_RE = re.compile(r"公告日期\s*[:：]\s*([0-9 ]+年[0-9 ]+月[0-9 ]+日)")

ver = (VER_RE.search(txt) or [None, "?"])[1]
pubdate = re.sub(r"\s+", "", (DATE_RE.search(txt) or [None, "?"])[1])

items, cur_item, blocks, cur = {}, None, [], None
for ln in txt.splitlines():
    m = ITEM_RE.search(ln)
    if m and HDR_RE.search(ln):
        cur_item = int(m.group(1)); items[cur_item] = m.group(2)
        if cur: blocks.append(cur); cur = None
        continue
    if PAGE_RE.search(ln) or HDR_RE.search(ln):
        continue
    qs = Q_START.match(ln)
    if qs:
        if cur: blocks.append(cur)
        cur = {"item": cur_item, "num": int(qs.group(1)),
               "ans": int(qs.group(2)), "raw": qs.group(3)}
    elif cur is not None:
        cur["raw"] += " " + ln.strip()
if cur: blocks.append(cur)

CJK = r"一-鿿，、。：；？！（）「」『』〔〕％～"
CJK_SPACE = re.compile(rf"(?<=[{CJK}])\s+(?=[{CJK}])")

def norm(s):
    s = re.sub(r"\s+", " ", s).strip()
    # drop spaces inserted by PDF line-wrap between two CJK chars (Chinese has no word spaces)
    s = CJK_SPACE.sub("", s)
    return s.strip()

def split_opts(raw):
    raw = re.sub(r"\s+", " ", raw).strip()
    marks = [(i, CIRCLE[c]) for i, c in enumerate(raw) if c in CIRCLE]
    stem = norm(raw[:marks[0][0]]) if marks else norm(raw.strip(" 。"))
    opts = []
    for k, (pos, _) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(raw)
        opts.append(norm(raw[pos + 1:end]))
    if opts:
        opts[-1] = norm(opts[-1].rstrip(" 。"))
    return stem, opts

data, bad = [], 0
for b in blocks:
    stem, opts = split_opts(b["raw"])
    if len(opts) != 4 or not (1 <= b["ans"] <= 4) or any(not o for o in opts):
        bad += 1; continue
    data.append({"i": b["item"], "n": b["num"], "q": stem, "o": opts, "a": b["ans"]})

assert bad == 0, f"{bad} 題解析異常，請檢查 PDF 版面"
print(f"PDF: {os.path.basename(PDF)}")
print(f"版次 {ver} / 公告 {pubdate} / 共 {len(data)} 題 / 異常 {bad}")

ITEMS_JSON = json.dumps(items, ensure_ascii=False)
DATA_JSON = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

PAGE = r"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>照服員單一級 · 學科題庫測驗</title><style>
:root{--bg:#f4f6f5;--fg:#1f2a28;--card:#fff;--muted:#6b7a76;--line:#e0e6e3;
 --accent:#1f7a4d;--accent2:#0d6e6e;--ok:#1f7a4d;--okbg:#e8f5ee;--bad:#c0392b;--badbg:#fdecea;}
@media(prefers-color-scheme:dark){:root{--bg:#161a19;--fg:#e6ece9;--card:#202624;--muted:#9aa8a3;
 --line:#333c39;--accent:#4fc98a;--accent2:#3fb9b9;--okbg:#173a2a;--badbg:#3a1f1c;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
 font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif;line-height:1.7;font-size:16.5px}
.wrap{max-width:820px;margin:0 auto;padding:18px 16px 70px}
a{color:var(--accent)}
.back{display:inline-block;margin:0 0 12px;font-size:.9rem;text-decoration:none;color:var(--accent)}
.top{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border-radius:16px;padding:20px 22px;margin-bottom:16px}
.top h1{margin:0 0 6px;font-size:1.35rem}.top p{margin:0;opacity:.94;font-size:.9rem}
.note{background:#fff3e0;border-left:4px solid #a85a00;border-radius:9px;padding:11px 15px;margin:14px 0;font-size:.9rem}
@media(prefers-color-scheme:dark){.note{background:#33280f;border-left-color:#e0a54d}}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:14px 0;box-shadow:0 2px 8px rgba(0,0,0,.04)}
.selbox{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 2px}
.selbox label{border:1px solid var(--line);border-radius:8px;padding:7px 12px;cursor:pointer;background:var(--card);font-size:.9rem}
.selbox input{margin-right:6px}
.lbl{font-size:.82rem;color:var(--muted);font-weight:700;margin:12px 0 2px;letter-spacing:.03em}
.btn{background:var(--accent);color:#fff;border:0;border-radius:9px;padding:11px 20px;font-size:1rem;font-weight:700;cursor:pointer;font-family:inherit}
.btn.sec{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.btn:disabled{opacity:.4;cursor:default}
.bar{position:sticky;top:0;background:var(--bg);padding:10px 0;z-index:5;display:flex;gap:12px;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--line);margin-bottom:6px}
.prog{font-size:.9rem;color:var(--muted)}.prog b{color:var(--fg)}
.score{font-size:1rem;font-weight:800;color:var(--accent)}
.itemtag{display:inline-block;background:var(--accent2);color:#fff;border-radius:20px;padding:2px 10px;font-size:.72rem;font-weight:700;margin-bottom:10px}
.q{font-weight:600;margin:2px 0 14px;font-size:1.08rem}
.opt{display:flex;gap:11px;align-items:flex-start;border:1px solid var(--line);border-radius:10px;padding:11px 13px;margin:8px 0;background:var(--card);cursor:pointer;transition:.12s;font-size:1rem}
.opt:hover{border-color:var(--accent)}
.opt .lb{flex:0 0 auto;width:25px;height:25px;border-radius:6px;background:#eef2f1;color:#5c716f;font-weight:700;text-align:center;line-height:25px;font-size:.85rem}
@media(prefers-color-scheme:dark){.opt .lb{background:#2c3532;color:#9aa8a3}}
.opt.correct{background:var(--okbg);border-color:var(--ok)}.opt.correct .lb{background:var(--ok);color:#fff}
.opt.wrong{background:var(--badbg);border-color:var(--bad)}.opt.wrong .lb{background:var(--bad);color:#fff}
.opt.disabled{cursor:default}
.big{font-size:2.4rem;font-weight:800;color:var(--accent);text-align:center;margin:8px 0}
.rank{text-align:center;color:var(--muted);margin-bottom:8px}
.wrongq{border-top:1px solid var(--line);padding:12px 0;font-size:.95rem}
.wrongq .qq{font-weight:600;margin-bottom:6px}
.wrongq .aa{color:var(--ok);font-size:.92rem}
.wrongq .yy{color:var(--bad);font-size:.92rem}
.foot{color:var(--muted);font-size:.8rem;margin-top:34px;border-top:1px solid var(--line);padding-top:14px}
.hidden{display:none}
</style></head><body><div class="wrap">
<a class="back" href="index.html">← 回考照重點首頁</a>
<div class="top"><h1>📝 學科題庫測驗</h1><p>照顧服務員單一級技術士 · 官方公開學科題庫 <b>__VER__</b>（公告 __DATE__）· 共 <b>__TOTAL__</b> 題</p></div>

<div id="setup">
<div class="note">⚠️ <b>記「正確選項的內容」，不是記位置</b>——本測驗每題選項<b>隨機打亂</b>，跟正式考試一樣。答錯會即時標出正解。</div>
<div class="card">
<div class="lbl">選擇工作項目</div>
<div class="selbox" id="itemsel"></div>
<div class="lbl">每回題數</div>
<div class="selbox" id="countsel">
 <label><input type="radio" name="cnt" value="20" checked>20 題</label>
 <label><input type="radio" name="cnt" value="50">50 題</label>
 <label><input type="radio" name="cnt" value="100">100 題</label>
 <label><input type="radio" name="cnt" value="0">全部</label>
</div>
<div style="margin-top:16px"><button class="btn" id="start">開始測驗 →</button></div>
</div>
</div>

<div id="quiz" class="hidden">
 <div class="bar"><span class="prog">第 <b id="cur">1</b> / <span id="tot"></span> 題</span>
  <span class="itemtag" id="qitem"></span><span class="score" id="scoreb"></span>
  <button class="btn sec" id="quit" style="margin-left:auto;padding:7px 14px;font-size:.85rem">結束</button></div>
 <div class="card"><div class="q" id="qtext"></div><div id="opts"></div>
  <div style="margin-top:14px"><button class="btn hidden" id="next">下一題 →</button></div></div>
</div>

<div id="result" class="hidden">
 <div class="card"><div class="big" id="pct"></div><div class="rank" id="rank"></div>
  <div style="text-align:center;margin:10px 0"><span id="rsum" class="prog"></span></div>
  <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:14px">
   <button class="btn" id="redoWrong">只重練錯題</button>
   <button class="btn sec" id="restart">重新選題</button></div></div>
 <div class="card" id="wronglist"></div>
</div>

<div class="foot">資料來源：勞動部勞動力發展署技能檢定中心 官方公開學科題庫（__VER__，公告 __DATE__）。題庫每年可能微調，以官方最新版為準。個人備考用途。</div>

<script type="application/json" id="ITEMS">__ITEMS__</script>
<script type="application/json" id="DATA">__DATA__</script>
<script>
const ITEMS=JSON.parse(document.getElementById('ITEMS').textContent);
const DATA=JSON.parse(document.getElementById('DATA').textContent);
const LB=['A','B','C','D'];
let pool=[],idx=0,score=0,wrong=[],curOpts=[];
function shuffle(a){a=a.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
// build item selector
const isel=document.getElementById('itemsel');
let selItems=new Set(Object.keys(ITEMS).map(Number));
function chip(val,txt,on){const l=document.createElement('label');l.innerHTML=`<input type="checkbox" ${on?'checked':''} value="${val}">${txt}`;return l}
const allChip=chip('all','全部',true);isel.appendChild(allChip);
Object.keys(ITEMS).map(Number).sort().forEach(k=>{isel.appendChild(chip(k,`0${k} ${ITEMS[k]}`,true))});
isel.addEventListener('change',e=>{
 const cb=e.target;if(cb.value==='all'){document.querySelectorAll('#itemsel input').forEach(x=>{if(x.value!=='all')x.checked=cb.checked})}
 else{const all=document.querySelector('#itemsel input[value=all]');const others=[...document.querySelectorAll('#itemsel input')].filter(x=>x.value!=='all');all.checked=others.every(x=>x.checked)}
});
function chosenItems(){return [...document.querySelectorAll('#itemsel input')].filter(x=>x.value!=='all'&&x.checked).map(x=>Number(x.value))}
document.getElementById('start').onclick=()=>{
 const its=new Set(chosenItems());if(!its.size){alert('請至少選一個工作項目');return}
 const cnt=Number(document.querySelector('input[name=cnt]:checked').value);
 let q=DATA.filter(d=>its.has(d.i));q=shuffle(q);if(cnt>0)q=q.slice(0,cnt);
 startQuiz(q);
};
function startQuiz(q){pool=q;idx=0;score=0;wrong=[];
 document.getElementById('setup').classList.add('hidden');
 document.getElementById('result').classList.add('hidden');
 document.getElementById('quiz').classList.remove('hidden');
 document.getElementById('tot').textContent=pool.length;render()}
function render(){
 const d=pool[idx];
 document.getElementById('cur').textContent=idx+1;
 document.getElementById('qitem').textContent='0'+d.i+' '+ITEMS[d.i];
 document.getElementById('scoreb').textContent=`✓ ${score}`;
 document.getElementById('qtext').textContent=d.q;
 // build shuffled options carrying original correctness
 curOpts=shuffle(d.o.map((t,k)=>({t,correct:(k+1)===d.a})));
 const ob=document.getElementById('opts');ob.innerHTML='';
 curOpts.forEach((o,k)=>{const el=document.createElement('div');el.className='opt';
  el.innerHTML=`<span class="lb">${LB[k]}</span><span>${escapeHtml(o.t)}</span>`;
  el.onclick=()=>pick(el,o,d);ob.appendChild(el)});
 document.getElementById('next').classList.add('hidden');
}
function pick(el,o,d){
 document.querySelectorAll('#opts .opt').forEach((x,k)=>{x.classList.add('disabled');x.onclick=null;
   if(curOpts[k].correct)x.classList.add('correct')});
 if(o.correct){score++}else{el.classList.add('wrong');
   wrong.push({q:d.q,you:o.t,ans:d.o[d.a-1],item:d.i})}
 document.getElementById('scoreb').textContent=`✓ ${score}`;
 document.getElementById('next').classList.remove('hidden');
}
document.getElementById('next').onclick=()=>{idx++;if(idx<pool.length)render();else finish()};
document.getElementById('quit').onclick=()=>{pool=pool.slice(0,idx);finish()};
function finish(){
 document.getElementById('quiz').classList.add('hidden');
 document.getElementById('result').classList.remove('hidden');
 const done=idx>pool.length?pool.length:idx; const total=pool.length||1;
 const answered=score+wrong.length; const pct=answered?Math.round(score/answered*100):0;
 document.getElementById('pct').textContent=pct+'%';
 document.getElementById('rank').textContent=pct>=90?'🏆 穩了':pct>=60?'✅ 及格區':'📚 再練幾輪';
 document.getElementById('rsum').textContent=`答對 ${score} / 作答 ${answered}（及格門檻 60 分）`;
 const wl=document.getElementById('wronglist');
 if(!wrong.length){wl.innerHTML='<div style="text-align:center;color:var(--ok);font-weight:700">全對！沒有錯題 🎉</div>'}
 else{wl.innerHTML='<div class="lbl">錯題複習（'+wrong.length+'）</div>'+wrong.map(w=>
  `<div class="wrongq"><div class="qq">${escapeHtml(w.q)}</div>
   <div class="yy">✗ 你選：${escapeHtml(w.you)}</div>
   <div class="aa">✓ 正解：${escapeHtml(w.ans)}</div></div>`).join('')}
}
document.getElementById('redoWrong').onclick=()=>{
 if(!wrong.length){return}
 const set=DATA.filter(d=>wrong.some(w=>w.q===d.q));startQuiz(shuffle(set))};
document.getElementById('restart').onclick=()=>{
 document.getElementById('result').classList.add('hidden');
 document.getElementById('setup').classList.remove('hidden')};
function escapeHtml(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
</script>
</div></body></html>"""

out = (PAGE.replace("__VER__", ver).replace("__DATE__", pubdate)
           .replace("__TOTAL__", str(len(data)))
           .replace("__ITEMS__", ITEMS_JSON).replace("__DATA__", DATA_JSON))
open(OUT, "w", encoding="utf-8").write(out)
print("→ 寫出", OUT, f"({len(out)//1024} KB)")
