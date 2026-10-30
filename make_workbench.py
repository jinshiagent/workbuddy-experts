#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成工作台 MVP 单页原型 workbench.html（自包含、可直接双击打开）。
数据来源：experts/manifest.json + experts/prompts/** 全部正文。
版权标注：腾讯专区 -> 腾讯专有(禁外发)；其余 -> 上游 MIT(保留署名)。
"""
import json, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))

def load_manifest():
    with open(os.path.join(ROOT, "experts", "manifest.json"), encoding="utf-8") as f:
        return json.load(f)

def read_body(prompt_file):
    rel = prompt_file.lstrip("/").replace("\\", "/")
    path = os.path.join(ROOT, "experts", "prompts", rel)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""

def txt(d, lang="zh"):
    if isinstance(d, dict):
        return d.get(lang) or d.get("zh") or d.get("en") or ""
    return d or ""

def build_data():
    m = load_manifest()
    cat_map = {c["id"]: c for c in m.get("categories", [])}
    out = []
    for e in m.get("experts", []):
        cid = e.get("categoryId", "")
        cat = cat_map.get(cid, {})
        provenance = "tencent" if cid == "13-TencentZone" else "mit"
        tags = [txt(t, "zh") for t in e.get("tags", []) if isinstance(t, dict)]
        out.append({
            "id": e.get("id", ""),
            "nameZh": txt(e.get("displayName"), "zh"),
            "nameEn": txt(e.get("displayName"), "en"),
            "profZh": txt(e.get("profession"), "zh"),
            "profEn": txt(e.get("profession"), "en"),
            "catId": cid,
            "catZh": txt(cat.get("name"), "zh"),
            "catEn": txt(cat.get("name"), "en"),
            "descZh": txt(e.get("description"), "zh"),
            "tags": tags,
            "expertType": e.get("expertType", ""),
            "isOPC": bool(e.get("isOPC")),
            "promptFile": e.get("promptFile", ""),
            "body": read_body(e.get("promptFile", "")),
            "prov": provenance,
        })
    return out

def esc_json(s):
    # 避免 </script> 破坏 HTML
    return json.dumps(s, ensure_ascii=False).replace("</", "<\\/")

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>提示词资产工作台 · MVP 原型</title>
<style>
  :root{
    --bg:#0f1115; --panel:#171a21; --panel2:#1f242e; --line:#2a2f3a;
    --txt:#e6e9ef; --muted:#9aa4b2; --acc:#5b8cff; --acc2:#3ad0a0;
    --warn:#ffb454; --danger:#ff6b6b; --chip:#232a36;
  }
  *{box-sizing:border-box}
  body{margin:0;font:14px/1.5 -apple-system,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--txt)}
  header{display:flex;align-items:center;gap:12px;padding:10px 16px;background:var(--panel);border-bottom:1px solid var(--line)}
  header h1{font-size:16px;margin:0;font-weight:600}
  header .badge{font-size:11px;color:#0f1115;background:var(--warn);padding:2px 8px;border-radius:10px;font-weight:700}
  .search{flex:1;max-width:520px;margin-left:auto;position:relative}
  .search input{width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--txt);outline:none}
  .search input:focus{border-color:var(--acc)}
  .layout{display:flex;height:calc(100vh - 53px)}
  aside{width:230px;flex:0 0 230px;background:var(--panel);border-right:1px solid var(--line);overflow:auto;padding:10px}
  .cat{display:flex;justify-content:space-between;align-items:center;padding:7px 10px;border-radius:7px;cursor:pointer;color:var(--muted)}
  .cat:hover{background:var(--panel2)}
  .cat.active{background:var(--chip);color:var(--txt)}
  .cat .n{font-size:11px;color:var(--muted)}
  .sectitle{font-size:11px;color:var(--muted);text-transform:uppercase;margin:14px 4px 6px;letter-spacing:.5px}
  .filter{display:flex;flex-wrap:wrap;gap:6px;padding:0 4px}
  .filter label{font-size:12px;color:var(--muted);display:flex;gap:4px;align-items:center;cursor:pointer}
  main{flex:1;display:flex;flex-direction:column;overflow:hidden}
  .toolbar{display:flex;align-items:center;gap:10px;padding:8px 14px;border-bottom:1px solid var(--line);color:var(--muted);font-size:13px}
  .grid{overflow:auto;padding:14px;display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;align-content:start}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px;cursor:pointer;transition:.15s;position:relative}
  .card:hover{border-color:var(--acc);transform:translateY(-2px)}
  .card .top{display:flex;gap:10px;align-items:center}
  .avatar{width:38px;height:38px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-weight:700;color:#fff;flex:0 0 38px}
  .card .nm{font-weight:600}
  .card .pr{font-size:12px;color:var(--muted)}
  .card .meta{margin-top:8px;display:flex;flex-wrap:wrap;gap:5px}
  .tag{font-size:11px;background:var(--chip);color:var(--muted);padding:2px 7px;border-radius:8px}
  .src{position:absolute;top:10px;right:10px;font-size:10px;padding:1px 6px;border-radius:6px;font-weight:700}
  .src.mit{background:#1d3a2c;color:var(--acc2)}
  .src.tencent{background:#3a1d1d;color:var(--danger)}
  .empty{padding:40px;text-align:center;color:var(--muted)}
  aside.right{width:330px;flex:0 0 330px;border-left:1px solid var(--line);display:flex;flex-direction:column;overflow:auto}
  .modebar{display:flex;gap:6px;padding:10px;border-bottom:1px solid var(--line)}
  .modebar button{flex:1;padding:7px;border-radius:7px;border:1px solid var(--line);background:var(--panel2);color:var(--muted);cursor:pointer}
  .modebar button.on{background:var(--acc);color:#fff;border-color:var(--acc)}
  .sess{padding:10px;border-bottom:1px solid var(--line)}
  .sess h3,.slots h3{font-size:12px;color:var(--muted);margin:0 0 8px;text-transform:uppercase;letter-spacing:.5px}
  .chipx{display:inline-flex;align-items:center;gap:6px;background:var(--chip);border:1px solid var(--line);border-radius:16px;padding:4px 10px;margin:3px;font-size:12px}
  .chipx b{cursor:pointer;color:var(--danger);font-weight:700}
  .slots{padding:10px}
  .slot{margin-bottom:8px}
  .slot label{font-size:12px;color:var(--muted);display:block;margin-bottom:3px}
  .slot textarea{width:100%;height:42px;background:var(--panel2);border:1px solid var(--line);border-radius:6px;color:var(--txt);padding:6px;resize:vertical;font:12px monospace}
  /* modal */
  .overlay{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;align-items:center;justify-content:center;z-index:50}
  .overlay.show{display:flex}
  .modal{width:min(820px,92vw);max-height:88vh;background:var(--panel);border:1px solid var(--line);border-radius:12px;display:flex;flex-direction:column;overflow:hidden}
  .modal header{display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--line);background:transparent}
  .modal .close{margin-left:auto;cursor:pointer;color:var(--muted);font-size:20px}
  .modal .body{overflow:auto;padding:16px}
  .modal pre{white-space:pre-wrap;word-break:break-word;background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:12px;font:12px/1.6 monospace;max-height:46vh;overflow:auto}
  .acts{display:flex;flex-wrap:wrap;gap:8px;padding:12px 16px;border-top:1px solid var(--line)}
  .btn{padding:8px 14px;border-radius:8px;border:1px solid var(--line);background:var(--panel2);color:var(--txt);cursor:pointer;font-size:13px}
  .btn.acc{background:var(--acc);border-color:var(--acc);color:#fff}
  .btn.green{background:var(--acc2);border-color:var(--acc2);color:#0f1115;font-weight:600}
  .kv{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 12px}
  .kv .tag{background:var(--chip)}
  .note{font-size:12px;color:var(--muted);background:var(--panel2);border:1px dashed var(--line);padding:8px 10px;border-radius:8px;margin-bottom:10px}
  footer{font-size:11px;color:var(--muted);padding:6px 16px;border-top:1px solid var(--line);background:var(--panel)}
  .toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--acc2);color:#0f1115;padding:8px 16px;border-radius:20px;font-size:13px;font-weight:600;opacity:0;transition:.25s;z-index:60}
  .toast.show{opacity:1}
  .stars{cursor:pointer;color:var(--warn);font-size:16px}
  .flow-acts{display:flex;gap:8px;margin:6px 0 4px}
  .node{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:12px;margin-bottom:12px}
  .node-h{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
  .lbl{font-size:12px;color:var(--muted);margin:6px 0 3px}
  .eval-row{display:grid;grid-template-columns:130px 90px 1fr;gap:8px;align-items:center;margin-bottom:8px}
  .eval-row label{font-size:13px}
  .eval-v{background:var(--panel2);border:1px solid var(--line);border-radius:6px;color:var(--acc2);padding:6px;font-weight:600}
  .eval-n{background:var(--panel2);border:1px solid var(--line);border-radius:6px;color:var(--txt);padding:6px}
  .fexp{width:100%;background:var(--panel);border:1px solid var(--line);border-radius:6px;color:var(--txt);padding:7px;font-size:13px}
  .frow{display:flex;gap:8px;align-items:flex-start;margin-bottom:6px}
  .frow>span{font-size:13px;color:var(--muted);line-height:32px}
  .nbtn{padding:5px 10px;border-radius:6px;border:1px solid var(--line);background:var(--panel2);color:var(--txt);cursor:pointer;font-size:12px}
  .nbtn.acc{background:var(--acc);border-color:var(--acc);color:#fff}
  .nbtn.green{background:var(--acc2);border-color:var(--acc2);color:#0f1115;font-weight:600}
  .warnchip{font-size:10px;background:#3a1d1d;color:var(--danger);padding:1px 6px;border-radius:6px;font-weight:700;margin-left:6px}
  .demo-flag{display:inline-block;font-size:11px;background:#2a2410;color:var(--warn);border:1px solid var(--warn);padding:2px 8px;border-radius:8px;font-weight:700;margin:4px 0}
  .runrow{width:100%;background:var(--panel);border:1px solid var(--line);border-radius:6px;color:var(--txt);padding:6px;font:12px/1.5 monospace}
</style>
</head>
<body>
<header>
  <h1>提示词资产工作台</h1>
  <span class="badge">MVP 原型 · 仅限个人学习</span>
  <div class="search"><input id="q" placeholder="搜索：名字 / 职业 / 标签 / 描述，例如“数据报告”"></div>
</header>

<div class="layout">
  <aside class="left">
    <div class="sectitle">分类</div>
    <div id="cats"></div>
    <div class="sectitle">筛选</div>
    <div class="filter">
      <label><input type="checkbox" id="f-agent"> 单专家(agent)</label>
      <label><input type="checkbox" id="f-team"> 团队(team)</label>
      <label><input type="checkbox" id="f-plugin"> 插件(plugin)</label>
      <label><input type="checkbox" id="f-opc"> 一人公司(OPC)</label>
    </div>
    <div class="sectitle">我的工作台</div>
    <div class="cat" id="nav-fav">★ 我的收藏 <span class="n" id="favn">0</span></div>
    <div class="cat" id="nav-mine">⚙ 我的角色 <span class="n" id="minen">0</span></div>
    <div class="cat" id="nav-new">＋ 新建角色</div>
    <div class="sectitle">演示</div>
    <div class="cat" id="nav-flow">▣ 协作流 / 评测台</div>
  </aside>

  <main>
    <div class="toolbar"><span id="count"></span><span style="margin-left:auto" id="sorttip">点击卡片查看详情</span></div>
    <div class="grid" id="grid"></div>
  </main>

  <aside class="right">
    <div class="modebar">
      <button data-mode="craft" class="on">Craft 编辑</button>
      <button data-mode="plan">Plan 规划</button>
      <button data-mode="ask">Ask 只读</button>
    </div>
    <div class="sess">
      <h3>当前会话 · 已挂起专家</h3>
      <div id="sess"></div>
      <div class="note" id="modehint"></div>
    </div>
    <div class="slots">
      <h3>记忆插槽（可视化）</h3>
      <div class="slot"><label>SoulContent · 人设</label><textarea placeholder="工作区 SOUL.md"></textarea></div>
      <div class="slot"><label>UserContent · 用户档案</label><textarea placeholder="工作区 USER.md"></textarea></div>
      <div class="slot"><label>WorkingMemory · 短期</label><textarea placeholder="本次会话记忆"></textarea></div>
      <div class="slot"><label>UserMemory · 长期</label><textarea placeholder="跨会话记忆"></textarea></div>
      <div class="slot"><label>ClawMemory 1/2/3 · 插入</label><textarea placeholder="多段插入记忆"></textarea></div>
      <div class="slot"><label>BootstrapContent · 启动</label><textarea placeholder="首次启动 BOOTSTRAP.md"></textarea></div>
    </div>
  </aside>
</div>

<footer>来源：WorkBuddy 4.22.16 提示词资产集 · 整理层 MIT；专家正文上游 MIT（保留署名）；腾讯专区属腾讯专有，禁止外发或商用。本原型不含云端同步。</footer>

<div class="overlay" id="ov">
  <div class="modal">
    <header>
      <div class="avatar" id="m-av"></div>
      <div><div id="m-name" style="font-weight:600;font-size:15px"></div><div id="m-prof" style="font-size:12px;color:var(--muted)"></div></div>
      <span class="close" id="m-close">×</span>
    </header>
    <div class="body">
      <div class="kv" id="m-kv"></div>
      <div class="note" id="m-note"></div>
      <div style="font-size:12px;color:var(--muted);margin-bottom:4px">提示词正文（Role Override 注入后生效）</div>
      <pre id="m-body"></pre>
    </div>
    <div class="acts">
      <button class="btn acc" id="m-load">加载到会话</button>
      <button class="btn" id="m-fav">★ 收藏</button>
      <button class="btn" id="m-copy">复制 system prompt</button>
      <button class="btn" id="m-derive">派生改写</button>
      <span id="m-loaded" style="color:var(--acc2);font-size:12px;align-self:center"></span>
    </div>
  </div>
</div>

<div class="overlay" id="ov2">
  <div class="modal">
    <header><div id="e2-title" style="font-weight:600">编辑角色</div><span class="close" id="e2-close">×</span></header>
    <div class="body">
      <div class="slot"><label>名称(中文)</label><input id="e2-name" style="width:100%;padding:7px;background:var(--panel2);border:1px solid var(--line);border-radius:6px;color:var(--txt)"></div>
      <div class="slot"><label>职业</label><input id="e2-prof" style="width:100%;padding:7px;background:var(--panel2);border:1px solid var(--line);border-radius:6px;color:var(--txt)"></div>
      <div class="slot"><label>提示词正文 (frontmatter 可省略)</label><textarea id="e2-body" style="height:300px"></textarea></div>
    </div>
    <div class="acts">
      <button class="btn green" id="e2-save">保存到我的角色</button>
      <span id="e2-hint" style="color:var(--muted);font-size:12px;align-self:center"></span>
    </div>
  </div>
</div>

<div class="overlay" id="ovFlows">
  <div class="modal" style="width:min(760px,94vw)">
    <header><div style="font-weight:600">协作流 · 流程管理（本地）</div><button class="nbtn green" onclick="newFlow()" style="margin-left:auto;margin-right:10px">＋ 新建流程</button><span class="close" id="mf-close">×</span></header>
    <div class="body" id="flows-body"></div>
  </div>
</div>

<div class="overlay" id="ovFlowEdit">
  <div class="modal" style="width:min(960px,96vw);max-height:92vh">
    <header><div style="font-weight:600" id="fe-name">协作流编辑器</div><span class="close" id="me-close">×</span></header>
    <div class="body" id="fe-body"></div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const DATA = __DATA__;
const MODE_HINT = {
  craft:"Craft 模式：允许自由编辑文件，末尾追加 <craft_mode>。",
  plan:"Plan 模式：先规划后执行，产出方案供确认。",
  ask:"Ask 模式：只读问答，禁止任何写入操作（<ask_mode>）。"
};
const CAT_COLORS = ["#5b8cff","#3ad0a0","#ffb454","#ff6b6b","#a78bfa","#22d3ee","#f472b6","#84cc16","#fb923c","#60a5fa","#e879f9","#34d399","#f87171"];
function catColor(id){let h=0;for(const c of id)h=(h*31+c.charCodeAt(0))%CAT_COLORS.length;return CAT_COLORS[h];}

let state={cat:'__ALL__',q:'',f:{agent:false,team:false,plugin:false,opc:false},mode:'craft',sess:[],fav:load('wb_fav',[]),mine:load('wb_mine',[])};

function load(k,d){try{return JSON.parse(localStorage.getItem(k))||d}catch(e){return d}}
function save(k,v){localStorage.setItem(k,JSON.stringify(v))}
function toast(t){const e=document.getElementById('toast');e.textContent=t;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),1600)}

function filtered(){
  const q=state.q.trim().toLowerCase();
  return DATA.filter(d=>{
    if(state.cat!=='__ALL__' && d.catId!==state.cat) return false;
    if(state.f.agent && d.expertType!=='agent') return false;
    if(state.f.team && d.expertType!=='team') return false;
    if(state.f.plugin && d.expertType!=='plugin') return false;
    if(state.f.opc && !d.isOPC) return false;
    if(q){
      const hay=(d.nameZh+d.nameEn+d.profZh+d.profEn+d.descZh+d.tags.join('')+d.catZh).toLowerCase();
      if(!hay.includes(q)) return false;
    }
    return true;
  });
}

function renderCats(){
  const c=document.getElementById('cats');
  const counts={};DATA.forEach(d=>counts[d.catId]=(counts[d.catId]||0)+1);
  let h='<div class="cat '+(state.cat==='__ALL__'?'active':'')+'" data-c="__ALL__">全部 <span class="n">'+DATA.length+'</span></div>';
  const seen={};
  DATA.forEach(d=>{if(seen[d.catId])return;seen[d.catId]=1;
    h+='<div class="cat '+(state.cat===d.catId?'active':'')+'" data-c="'+d.catId+'">'+d.catZh+' <span class="n">'+(counts[d.catId]||0)+'</span></div>';
  });
  c.innerHTML=h;
  c.querySelectorAll('.cat').forEach(el=>el.onclick=()=>{state.cat=el.dataset.c;renderCats();renderGrid();});
}

function renderGrid(){
  const list=filtered();
  document.getElementById('count').textContent='共 '+list.length+' 位专家';
  const g=document.getElementById('grid');
  if(!list.length){g.innerHTML='<div class="empty">无匹配结果</div>';return;}
  g.innerHTML=list.map(d=>{
    const ini=(d.nameZh||d.nameEn||'?').slice(0,1);
    const tags=d.tags.slice(0,3).map(t=>'<span class="tag">'+esc(t)+'</span>').join('');
    const src=d.prov==='tencent'?'<span class="src tencent">腾讯专有·禁外发</span>':'<span class="src mit">MIT</span>';
    return '<div class="card" data-id="'+d.id+'">'+src+
      '<div class="top"><div class="avatar" style="background:'+catColor(d.catId)+'">'+esc(ini)+'</div>'+
      '<div><div class="nm">'+esc(d.nameZh)+' <span style="color:var(--muted);font-weight:400;font-size:12px">'+esc(d.nameEn)+'</span></div>'+
      '<div class="pr">'+esc(d.profZh)+'</div></div></div>'+
      '<div class="meta">'+tags+'</div></div>';
  }).join('');
  g.querySelectorAll('.card').forEach(el=>el.onclick=()=>openDetail(el.dataset.id));
}

function openDetail(id){
  const d=DATA.find(x=>x.id===id);if(!d)return;
  document.getElementById('m-av').textContent=(d.nameZh||'?').slice(0,1);
  document.getElementById('m-av').style.background=catColor(d.catId);
  document.getElementById('m-name').textContent=d.nameZh+' ('+d.nameEn+')';
  document.getElementById('m-prof').textContent=d.profZh+' · '+d.catZh;
  const kv=['类型:'+d.expertType, d.isOPC?'OPC 一人公司':'', '标签:'+d.tags.slice(0,5).join('/')].filter(Boolean).map(x=>'<span class="tag">'+esc(x)+'</span>').join('');
  document.getElementById('m-kv').innerHTML=kv;
  document.getElementById('m-note').textContent=d.prov==='tencent'
    ? '来源：腾讯专区（腾讯专有）。仅限本地学习，禁止复制外发或商用。'
    : '来源：上游 msitarzewski/agency-agents（MIT），保留署名即可复用。';
  document.getElementById('m-body').textContent=d.body||'（正文缺失）';
  const favBtn=document.getElementById('m-fav');
  favBtn.textContent=state.fav.includes(id)?'★ 已收藏':'★ 收藏';
  favBtn.onclick=()=>{if(state.fav.includes(id))state.fav=state.fav.filter(x=>x!==id);else state.fav.push(id);save('wb_fav',state.fav);favBtn.textContent=state.fav.includes(id)?'★ 已收藏':'★ 收藏';updFav();toast('已更新收藏');};
  document.getElementById('m-load').onclick=()=>{if(!state.sess.find(s=>s.id===id)){state.sess.push({id,name:d.nameZh,cat:d.catId});renderSess();toast('已挂起到会话');}else toast('已在会话中');};
  document.getElementById('m-copy').onclick=()=>{
    if(d.prov==='tencent'){toast('腾讯专有内容，禁止复制外发');return;}
    const txt='[Role Override]\n你是 '+d.nameZh+'。\n'+d.body+'\n\n[Mode: '+state.mode+']\n'+(MODE_HINT[state.mode]||'');
    copyText(txt);
  };
  document.getElementById('m-derive').onclick=()=>openEditor(d.nameZh+' 的改写',d.profZh,d.body);
  document.getElementById('m-loaded').textContent=state.sess.find(s=>s.id===id)?'✓ 已在会话':'';
  document.getElementById('ov').classList.add('show');
}

function renderSess(){
  document.getElementById('sess').innerHTML=state.sess.length?state.sess.map(s=>'<span class="chipx">'+esc(s.name)+'<b data-id="'+s.id+'">×</b></span>').join(''):'<span style="color:var(--muted);font-size:12px">未挂起任何专家</span>';
  document.getElementById('sess').querySelectorAll('b').forEach(b=>b.onclick=()=>{state.sess=state.sess.filter(s=>s.id!==b.dataset.id);renderSess();});
  document.getElementById('modehint').textContent=MODE_HINT[state.mode];
}
function updFav(){document.getElementById('favn').textContent=state.fav.length;}
function updMine(){document.getElementById('minen').textContent=state.mine.length;}

function openEditor(name,prof,body){
  document.getElementById('e2-name').value=name||'';
  document.getElementById('e2-prof').value=prof||'';
  document.getElementById('e2-body').value=body||'';
  document.getElementById('e2-hint').textContent='';
  document.getElementById('ov2').classList.add('show');
  document.getElementById('e2-save').onclick=()=>{
    const nm=document.getElementById('e2-name').value.trim();
    if(!nm){document.getElementById('e2-hint').textContent='请填写名称';return;}
    state.mine.push({id:'mine_'+Date.now(),nameZh:nm,nameEn:nm,profZh:document.getElementById('e2-prof').value,catZh:'我的角色',tags:[],expertType:'agent',isOPC:false,prov:'mit',body:document.getElementById('e2-body').value});
    save('wb_mine',state.mine);updMine();document.getElementById('ov2').classList.remove('show');toast('已保存到我的角色');
  };
}

function esc(s){return (s==null?'':String(s)).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}

// 我的收藏 / 我的角色 / 新建 视图
function showMine(kind){
  const g=document.getElementById('grid');
  let list = kind==='fav'? DATA.filter(d=>state.fav.includes(d.id)) : state.mine;
  document.getElementById('count').textContent=(kind==='fav'?'我的收藏':'我的角色')+' · '+list.length;
  if(!list.length){g.innerHTML='<div class="empty">'+(kind==='fav'?'暂无收藏，打开专家详情点 ★ 收藏':'暂无角色，点左侧“新建角色”')+'</div>';return;}
  g.innerHTML=list.map(d=>{
    const ini=(d.nameZh||'?').slice(0,1);
    return '<div class="card" data-mid="'+d.id+'"><div class="top"><div class="avatar" style="background:'+catColor(d.catId||'mine')+'">'+esc(ini)+'</div><div><div class="nm">'+esc(d.nameZh)+'</div><div class="pr">'+esc(d.profZh||'')+'</div></div></div></div>';
  }).join('');
  g.querySelectorAll('.card').forEach(el=>el.onclick=()=>{
    const d=list.find(x=>x.id===el.dataset.mid);
    document.getElementById('m-av').textContent=(d.nameZh||'?').slice(0,1);
    document.getElementById('m-name').textContent=d.nameZh;
    document.getElementById('m-prof').textContent=d.profZh||'我的角色';
    document.getElementById('m-kv').innerHTML='<span class="tag">我的角色</span>';
    document.getElementById('m-note').textContent='本地创建，仅存于本浏览器。';
    document.getElementById('m-body').textContent=d.body||'';
    document.getElementById('m-fav').style.display='none';
    document.getElementById('m-copy').onclick=()=>navigator.clipboard.writeText(d.body||'').then(()=>toast('已复制'));
    document.getElementById('m-derive').style.display='none';
    document.getElementById('m-load').onclick=()=>{if(!state.sess.find(s=>s.id===d.id)){state.sess.push({id:d.id,name:d.nameZh,cat:d.catId});renderSess();toast('已挂起');}else toast('已在会话中');};
    document.getElementById('ov').classList.add('show');
  });
}

// events
document.getElementById('q').oninput=e=>{state.q=e.target.value;renderGrid();};
['agent','team','plugin','opc'].forEach(k=>document.getElementById('f-'+k).onchange=e=>{state.f[k]=e.target.checked;renderGrid();});
document.querySelectorAll('.modebar button').forEach(b=>b.onclick=()=>{state.mode=b.dataset.mode;document.querySelectorAll('.modebar button').forEach(x=>x.classList.remove('on'));b.classList.add('on');renderSess();});
document.getElementById('m-close').onclick=()=>document.getElementById('ov').classList.remove('show');
document.getElementById('e2-close').onclick=()=>document.getElementById('ov2').classList.remove('show');
document.getElementById('nav-fav').onclick=()=>showMine('fav');
document.getElementById('nav-mine').onclick=()=>showMine('mine');
document.getElementById('nav-new').onclick=()=>openEditor('','', '');

function copyText(t){if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(()=>toast('已复制')).catch(()=>fallbackCopy(t));}else fallbackCopy(t);}
function fallbackCopy(t){const ta=document.createElement('textarea');ta.value=t;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{document.execCommand('copy');toast('已复制');}catch(e){toast('复制失败，请手动选择复制');}document.body.removeChild(ta);}

// ===== P2 协作流引擎（可配置 / 本地 / 离线演示）=====
const EXPERT_BY_ID={}; DATA.forEach(d=>EXPERT_BY_ID[d.id]=d);
function expertName(id){const d=EXPERT_BY_ID[id];return d?(d.nameZh||d.nameEn):'(未配置)';}
function expertProv(id){const d=EXPERT_BY_ID[id];return d?d.prov:'';}

const FLOW_EVAL=[
 {k:"任务完成度",v:"9 / 10",n:"覆盖核心指标与下钻；缺实时刷新与权限说明。"},
 {k:"输出质量",v:"8.5 / 10",n:"结构清晰、口径严谨、可落地。"},
 {k:"角色配合度",v:"9 / 10",n:"后继节点正确承接前序布局，输入→输出链路闭合。"},
 {k:"需人工修订处",v:"3 项",n:"① 指标目标值需业务确认；② 视觉与品牌色冲突复核；③ 缺移动端适配。"}
];
const TEMPLATES=[
 {id:"tpl-dashboard",name:"数据分析仪表盘（示例）",source:"上游 MIT 专家演示 · 个人学习授权",license:"MIT",
  taskTemplate:"任务：为一家电商 SaaS 设计「经营数据仪表盘」。\n目标用户：运营负责人。\n核心诉求：一屏看清 GMV、转化率、复购率、库存周转，并能下钻到渠道 / 品类。\n要求：先由 UI Designer 给出界面结构与视觉建议；再由 DataAnalyticsReporter 据此给出指标布局与解读建议。",
  nodes:[
   {id:"n1",expertId:"UiDesigner",inputMode:"task",instructions:"",demoOutput:"一、信息架构\n· 顶部 KPI 条：4 张核心卡（GMV / 转化率 / 复购率 / 库存周转），含同环比角标\n· 中部趋势区：GMV 柱 + 转化率折线（双轴），默认 7/30 天切换\n· 底部下钻区：渠道 / 品类双 Tab，支持下钻到明细\n· 右侧栏：异常预警 + 目标进度环\n\n二、布局（12 栅格）\n· 主区 8 列：KPI 条(行1) → 趋势区(行2) → 下钻区(行3)\n· 右栏 4 列：预警(上) + 目标进度(下)\n· 卡片间距 16px，页面外边距 24px\n\n三、视觉\n· 底色 #0F172A 深色仪表盘；主色蓝 #5B8CFF=增长，红 #FF6B6B=下滑\n· 关键数字 28px 半粗；图表优先面积图，减少饼图认知负担\n· 圆角 12、柔和阴影；状态用「颜色+图标」双编码（无障碍 WCAG AA）\n\n四、交付物\n· 组件清单：KpiCard / TrendChart / DrillTab / AlertList / GoalRing\n· 间距 token：space-1=4 … space-6=24"},
   {id:"n2",expertId:"DataAnalyticsReporter",inputMode:"prev",instructions:"",demoOutput:"一、指标口径\n· GMV = 已支付订单金额（剔除退款）；同比=去年同期，环比=上一周期\n· 转化率 = 支付用户 / 访问用户；复购率 = 近 90 天≥2 单用户占比\n· 库存周转 = 销售成本 / 平均库存金额（天）\n\n二、卡片与趋势\n· KPI 卡含：当前值 + 环比箭头 + 目标完成度\n· 趋势区：GMV(柱) 与 转化率(线) 双轴；下钻维度=渠道(自然/付费/私域)、品类 Top10\n· 建议下钻字段：channel_id, category_id, pay_ts, order_amt\n\n三、解读话术\n· 若 GMV 涨但转化降：流量质量或客单价上升，需排查渠道结构\n· 若复购降：权益 / 触达频次可能不足\n\n四、数据质量提示\n· 需补齐：退款回写、渠道归因、库存快照，否则周转与复购口径不准"}
  ]},
 {id:"tpl-competitor",name:"竞品分析报告",source:"上游 MIT 专家演示 · 个人学习授权",license:"MIT",
  taskTemplate:"任务：对目标 SaaS 竞品做结构化竞品分析。\n要求：先由深研研做市场与竞品调研，再由产品通产出定位、功能对比与差异化建议。",
  nodes:[
   {id:"n1",expertId:"DeepResearchExpert",inputMode:"task",instructions:""},
   {id:"n2",expertId:"ProductManagementExpert",inputMode:"prev",instructions:""}
  ]},
 {id:"tpl-content",name:"内容营销策划",source:"上游 MIT 专家演示 · 个人学习授权",license:"MIT",
  taskTemplate:"任务：为某消费品牌策划一轮内容营销战役。\n要求：先由策动动产出战役框架与主题，再由传声声产出各渠道分发文案。",
  nodes:[
   {id:"n1",expertId:"MarketingCampaignExpert",inputMode:"task",instructions:""},
   {id:"n2",expertId:"SocialMediaStrategist",inputMode:"prev",instructions:""}
  ]}
];

let flows = load('wb_flows', null);
if(!flows || !flows.length){
  const t=TEMPLATES.find(x=>x.id==='tpl-dashboard');
  const f=JSON.parse(JSON.stringify(t)); f.id='f'+Date.now(); f.name=t.name; f.fromTemplate=t.id;
  f.nodes.forEach(n=>n.id='n'+Date.now()+Math.floor(Math.random()*1e4));
  flows=[f];
}
let runs = load('wb_runs', []);
let activeFlowId=null, activeRun=null;
function saveFlows(){save('wb_flows',flows);}
function getFlow(id){return flows.find(x=>x.id===id);}

function renderFlowsList(){
 const b=document.getElementById('flows-body');
 let h='<div class="sectitle" style="color:var(--muted);margin:0 0 6px">模板库（只读 · 可基于此新建，原模板不覆盖）</div>';
 TEMPLATES.forEach(t=>{
   const chain=t.nodes.map(n=>expertName(n.expertId)).join(' → ')||'未配置';
   h+='<div class="nwrap"><div style="display:flex;justify-content:space-between;align-items:center"><b>'+esc(t.name)+'</b><span class="src mit">'+esc(t.license)+'</span></div>';
   h+='<div style="color:var(--muted);font-size:12px;margin:4px 0">来源：'+esc(t.source)+' · '+chain+'</div>';
   h+='<div class="flow-acts"><button class="nbtn green" onclick="newFromTemplate(\''+t.id+'\')">基于此新建流程</button></div></div>';
 });
 h+='<div class="sectitle" style="color:var(--muted);margin:12px 0 6px">我的流程（本机）</div>';
 if(!flows.length){h+='<div class="empty">暂无流程，点右上“新建流程”或从模板新建。</div>';}
 else h+=flows.map(f=>{
   const ten=f.nodes.some(n=>expertProv(n.expertId)==='tencent');
   const chain=f.nodes.map(n=>expertName(n.expertId)).join(' → ')||'未配置';
   return '<div class="nwrap"><div style="display:flex;justify-content:space-between;align-items:center"><b>'+esc(f.name)+'</b>'+(ten?'<span class="warnchip">含腾讯专有</span>':'')+'</div>'+
     '<div style="color:var(--muted);font-size:12px;margin:4px 0">'+f.nodes.length+' 个节点 · '+chain+(f.fromTemplate?' · 来自模板':'')+'</div>'+
     '<div class="flow-acts"><button class="nbtn acc" onclick="openFlowEditor(\''+f.id+'\')">打开</button>'+
     '<button class="nbtn" onclick="copyFlow(\''+f.id+'\')">复制</button>'+
     '<button class="nbtn" onclick="renameFlow(\''+f.id+'\')">重命名</button>'+
     '<button class="nbtn" onclick="delFlow(\''+f.id+'\')">删除</button></div></div>';
 }).join('');
 b.innerHTML=h;
}
function copyFlow(id){const f=getFlow(id);if(!f)return;const c=JSON.parse(JSON.stringify(f));c.id='f'+Date.now();c.name=f.name+' 副本';flows.push(c);saveFlows();renderFlowsList();toast('已复制流程');}
function renameFlow(id){const f=getFlow(id);if(!f)return;const n=prompt('流程名称',f.name);if(n){f.name=n;saveFlows();renderFlowsList();toast('已重命名');}}
function delFlow(id){if(!confirm('确认删除该流程？'))return;flows=flows.filter(x=>x.id!==id);saveFlows();renderFlowsList();}
function newFlow(){const f={id:'f'+Date.now(),name:'未命名流程',taskTemplate:'在此填写统一任务简报……',nodes:[{id:'n'+Date.now(),expertId:'',inputMode:'task',instructions:''}]};flows.push(f);saveFlows();openFlowEditor(f.id);}
function newFromTemplate(tid){
  const t=TEMPLATES.find(x=>x.id===tid); if(!t){toast('模板不存在');return;}
  const f=JSON.parse(JSON.stringify(t)); f.id='f'+Date.now(); f.name=t.name+'（副本）'; f.fromTemplate=t.id;
  f.nodes.forEach(n=>n.id='n'+Date.now()+Math.floor(Math.random()*1e4));
  flows.push(f); saveFlows(); openFlowEditor(f.id); toast('已从模板新建流程（原模板未改动）');
}

function resolvedFor(f,idx,nr){
 const mode=f.nodes[idx].inputMode;
 const prev=(idx>0&&nr[idx-1])?nr[idx-1].output:'';
 const task=f.taskTemplate||'';
 if(mode==='prev') return prev||task;
 if(mode==='task+prev') return task+(prev?'\n\n【上一步输出】\n'+prev:'');
 return task;
}
function demoOutputFor(f,idx){
 const node=f.nodes[idx];
 if(node.demoOutput) return node.demoOutput;
 const inp=activeRun&&activeRun.nodeRuns[idx]?activeRun.nodeRuns[idx].resolvedInput:resolvedFor(f,idx,activeRun?activeRun.nodeRuns:[]);
 return '[离线演示样例 · 非实时推理]\n专家「'+expertName(node.expertId)+'」收到输入：\n--- 输入开始 ---\n'+String(inp).slice(0,400)+'\n--- 输入结束 ---\n\n（此为演示占位输出。接入模型后由输出适配器生成该专家真实回答；当前未连接任何模型。）';
}
function ensureRun(f){if(!activeRun)activeRun={id:'r'+Date.now(),flowId:f.id,taskInput:f.taskTemplate,nodeRuns:[],evaluation:null,createdAt:new Date().toISOString()};}
function runNode(f,idx){
 ensureRun(f);
 while(activeRun.nodeRuns.length<=idx) activeRun.nodeRuns.push({nodeId:f.nodes[activeRun.nodeRuns.length].id,resolvedInput:'',output:'',status:'pending'});
 const ri=resolvedFor(f,idx,activeRun.nodeRuns);
 activeRun.nodeRuns[idx]={nodeId:f.nodes[idx].id,resolvedInput:ri,output:demoOutputFor(f,idx),status:'done'};
 toast('已运行：'+expertName(f.nodes[idx].expertId)); renderFlowEditor();
}
function runAll(f){ensureRun(f);activeRun.nodeRuns=[];for(let i=0;i<f.nodes.length;i++)runNode(f,i);saveRun();renderFlowEditor();toast('全流程已运行（演示样例）');}
function saveRun(){if(!activeRun)return;runs.unshift(activeRun);if(runs.length>20)runs=runs.slice(0,20);save('wb_runs',runs);}

function openFlowEditor(id){activeFlowId=id;activeRun=null;const f=getFlow(id);if(!f){toast('流程不存在');return;}document.getElementById('fe-name').textContent='协作流编辑器 · '+f.name;renderFlowEditor();document.getElementById('ovFlowEdit').classList.add('show');}
function renderFlowEditor(){
 const f=getFlow(activeFlowId);if(!f)return;
 const b=document.getElementById('fe-body');
 let h='<div class="demo-flag">离线演示样例 · 非实时推理（未连接模型；未来仅替换适配器即可接真实模型）</div>';
 if(f.source) h+='<div style="font-size:12px;color:var(--muted);margin-bottom:4px">来源：'+esc(f.source)+' · 仅限个人学习 · 默认不含腾讯专有专家</div>';
 h+='<div class="lbl">流程名称</div><input id="fe-name-in" class="fexp" value="'+esc(f.name)+'">';
 h+='<div class="lbl">统一任务简报（首个节点输入）</div><textarea id="fe-task" class="runrow" style="height:80px">'+esc(f.taskTemplate)+'</textarea>';
 f.nodes.forEach((n,idx)=>{
   const prov=expertProv(n.expertId);
   h+='<div class="nwrap"><div class="frow"><b>第 '+(idx+1)+' 步</b>'+(prov==='tencent'?'<span class="warnchip">腾讯专有·禁外发</span>':'')+'</div>';
   h+='<div class="frow"><span style="width:60px">专家</span><select class="fexp" onchange="setNodeExpert(\''+n.id+'\',this.value)"><option value="">— 选择专家 —</option>';
   DATA.forEach(d=>{h+='<option value="'+d.id+'"'+(d.id===n.expertId?' selected':'')+'>'+esc(d.nameZh)+' ('+esc(d.profZh)+')'+(d.prov==='tencent'?' [专有]':'')+'</option>';});
   h+='</select></div>';
   h+='<div class="frow"><span style="width:60px">输入来源</span><select class="fexp" onchange="setNodeMode(\''+n.id+'\',this.value)">';
   [['task','仅任务'],['prev','仅上一步输出'],['task+prev','任务+上一步输出']].forEach(m=>{h+='<option value="'+m[0]+'"'+(n.inputMode===m[0]?' selected':'')+'>'+m[1]+'</option>';});
   h+='</select></div>';
   h+='<div class="frow"><span style="width:60px">附加指令</span><input class="fexp" value="'+esc(n.instructions||'')+'" onchange="setNodeInstr(\''+n.id+'\',this.value)"></div>';
   h+='<div class="flow-acts"><button class="nbtn acc" onclick="runNode(getFlow(activeFlowId),'+idx+')">运行此节点</button>';
   if(idx>0)h+='<button class="nbtn" onclick="moveNode(\''+n.id+'\',-1)">↑ 上移</button>';
   if(idx<f.nodes.length-1)h+='<button class="nbtn" onclick="moveNode(\''+n.id+'\',1)">↓ 下移</button>';
   h+='<button class="nbtn" onclick="removeNode(\''+n.id+'\')">移除</button></div>';
   const nr=activeRun&&activeRun.nodeRuns[idx];
   if(nr){
     h+='<div class="lbl">输入（自动接力）</div><textarea class="runrow" style="height:70px" readonly>'+esc(nr.resolvedInput)+'</textarea>';
     h+='<div class="lbl">输出（可编辑）</div><textarea class="runrow" id="out-'+n.id+'" style="height:130px" onchange="editOut(\''+n.id+'\',this.value)">'+esc(nr.output)+'</textarea>';
     h+='<div class="flow-acts"><button class="nbtn" onclick="copyText(document.getElementById(\'out-'+n.id+'\').value)">复制输出</button></div>';
   }
   h+='</div>';
 });
 h+='<div class="flow-acts"><button class="nbtn green" onclick="addNode()">＋ 添加专家节点</button>';
 h+='<button class="nbtn acc" onclick="runAll(getFlow(activeFlowId))">运行全部</button>';
 h+='<button class="nbtn" onclick="saveFlowMeta()">保存配置</button></div>';
 h+='<div class="node" style="margin-top:12px"><div class="node-h"><b>评测台 · 人工/演示评测（非自动评估）</b></div>';
 const ev=(activeRun&&activeRun.evaluation)?activeRun.evaluation:FLOW_EVAL;
 ev.forEach((e,i)=>{h+='<div class="eval-row"><label>'+esc(e.k)+'</label><input class="eval-v" value="'+esc(e.v)+'" onchange="setEval('+i+',this.value,\'v\')"><textarea class="eval-n" style="height:42px" onchange="setEval('+i+',this.value,\'n\')">'+esc(e.n)+'</textarea></div>';});
 h+='<div class="flow-acts"><button class="nbtn green" onclick="copyEval()">复制评测汇总</button></div></div>';
 h+='<div class="lbl" style="margin-top:10px">运行记录（本机，≤20 条）</div>';
 const my=runs.filter(r=>r.flowId===f.id);
 h+=(my.length?my.map(r=>'<div style="font-size:12px;color:var(--muted);padding:3px 0">'+new Date(r.createdAt).toLocaleString()+' · '+r.nodeRuns.length+' 节点</div>').join(''):'<div class="empty">本流程暂无记录</div>');
 h+='<div class="flow-acts"><button class="nbtn" onclick="clearRuns()">清空记录</button><button class="nbtn" onclick="document.getElementById(\'ovFlowEdit\').classList.remove(\'show\')">关闭</button></div>';
 b.innerHTML=h;
}
function saveFlowMeta(){const f=getFlow(activeFlowId);f.name=document.getElementById('fe-name-in').value;f.taskTemplate=document.getElementById('fe-task').value;saveFlows();toast('已保存配置');}
function setNodeExpert(nid,v){const f=getFlow(activeFlowId),n=f.nodes.find(x=>x.id===nid);if(n){n.expertId=v;saveFlows();renderFlowEditor();}}
function setNodeMode(nid,v){const f=getFlow(activeFlowId),n=f.nodes.find(x=>x.id===nid);if(n){n.inputMode=v;saveFlows();}}
function setNodeInstr(nid,v){const f=getFlow(activeFlowId),n=f.nodes.find(x=>x.id===nid);if(n){n.instructions=v;saveFlows();}}
function editOut(nid,v){if(activeRun){const nr=activeRun.nodeRuns.find(x=>x.nodeId===nid);if(nr){nr.output=v;saveRun();}}}
function setEval(i,v,field){ensureRun(getFlow(activeFlowId));if(!activeRun.evaluation)activeRun.evaluation=JSON.parse(JSON.stringify(FLOW_EVAL));activeRun.evaluation[i][field]=v;saveRun();}
function addNode(){const f=getFlow(activeFlowId);f.nodes.push({id:'n'+Date.now(),expertId:'',inputMode:'prev',instructions:''});saveFlows();renderFlowEditor();}
function removeNode(nid){const f=getFlow(activeFlowId);if(f.nodes.length<=1){toast('至少保留一个节点');return;}f.nodes=f.nodes.filter(x=>x.id!==nid);saveFlows();renderFlowEditor();}
function moveNode(nid,dir){const f=getFlow(activeFlowId);const i=f.nodes.findIndex(x=>x.id===nid),j=i+dir;if(j<0||j>=f.nodes.length)return;const t=f.nodes[i];f.nodes[i]=f.nodes[j];f.nodes[j]=t;saveFlows();renderFlowEditor();}
function clearRuns(){if(!confirm('清空全部运行记录？'))return;runs=[];save('wb_runs',runs);toast('已清空');renderFlowEditor();}
function copyEval(){let s='【协作流评测汇总 · 离线演示样例，非实时推理】\n';const ev=(activeRun&&activeRun.evaluation)?activeRun.evaluation:FLOW_EVAL;ev.forEach(e=>{s+='· '+e.k+'：'+e.v+'\n  '+e.n+'\n';});copyText(s);}

document.getElementById('nav-flow').onclick=()=>{renderFlowsList();document.getElementById('ovFlows').classList.add('show');};
document.getElementById('mf-close').onclick=()=>document.getElementById('ovFlows').classList.remove('show');
document.getElementById('me-close').onclick=()=>document.getElementById('ovFlowEdit').classList.remove('show');

renderCats();renderGrid();renderSess();updFav();updMine();
</script>
</body>
</html>
"""

def main():
    data = build_data()
    payload = "window.DATA = " + esc_json(data) + ";"
    out = HTML.replace("__DATA__", payload)
    dst = os.path.join(ROOT, "workbench.html")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(out)
    print("已生成:", dst)
    print("专家数:", len(data))
    tencent = sum(1 for d in data if d["prov"] == "tencent")
    print("腾讯专有:", tencent, " 上游MIT:", len(data) - tencent)
    sizes = sum(len(d["body"]) for d in data)
    print("正文总字节:", sizes)

if __name__ == "__main__":
    main()
