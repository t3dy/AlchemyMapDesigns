#!/usr/bin/env python3
"""
build_network.py — the SCHOLARLY NETWORK / PATRONAGE template.

Reads data/networks.json (curated, typed, directed, weighted, evidence-bearing
person-to-person edges) and emits ONE self-contained explorer (MapLibre GL +
deck.gl) with a subject switcher covering all four constellations:
  Rudolfine Prague · English Chymists · Paracelsian Movement · Republic of Letters.

Features the historian & designer asked for:
  - edges coloured by TYPE (categorical), width by WEIGHT, opacity by CONFIDENCE,
    direction shown by a source->target colour gradient (patron darker -> client);
  - click a node to PIVOT: incident edges highlight, the rest dim ("the centre is a
    choice, not a fact");
  - the SURVIVAL-BIAS toggle: 'only what survives' drops inferred/non-extant ties and
    over-centres the archive-keepers — the lie of correspondence maps, made visible;
  - a persistent 'what this map does NOT show' note;
  - four switchable themes; deep-link via ?subject=slug; postMessage embedding API.

Usage:  python build_network.py [--data networks.json] [--out network.html]
"""
import argparse, json, html
from pathlib import Path

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Scholarly Networks</title>
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet">
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/deck.gl@9.0.33/dist.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=EB+Garamond:ital@0;1&family=IM+Fell+English&family=Spectral:wght@300;400;600&display=swap" rel="stylesheet">
<style>
  :root{--page:#fff;--ink:#1f2937;--muted:#6b7280;--panel:#fff;--bd:#e5e7eb;--accent:#7a4a25;--chip:#f1efe9;--font:"Spectral",Georgia,serif;--head:"Spectral",serif;}
  *{box-sizing:border-box;}
  html,body{margin:0;height:100%;font-family:var(--font);color:var(--ink);background:var(--page);}
  #map{position:absolute;inset:0;background:var(--page);}
  .card{background:var(--panel);border:1px solid var(--bd);border-radius:12px;box-shadow:0 14px 38px rgba(40,30,15,.20);}
  #panel{position:absolute;top:16px;left:16px;width:300px;max-width:86vw;padding:15px 17px;z-index:6;max-height:88vh;overflow:auto;}
  #panel h1{font-family:var(--head);font-size:19px;margin:0 0 2px;}
  #panel .sub{font-size:12.5px;color:var(--muted);font-style:italic;margin-bottom:10px;}
  select,button{font-family:var(--font);color:var(--ink);}
  select{width:100%;padding:6px 8px;border:1px solid var(--bd);border-radius:8px;background:var(--page);font-size:13px;margin-bottom:8px;}
  .lbl{font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin:9px 0 5px;}
  .toggle{display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer;border:1px solid var(--bd);background:var(--chip);border-radius:8px;padding:8px 10px;margin:6px 0;}
  .toggle.on{background:var(--accent);color:#fff;border-color:var(--accent);}
  .legend{margin-top:8px;border-top:1px solid var(--bd);padding-top:8px;}
  .legend .li{display:flex;align-items:center;font-size:12px;margin:3px 0;}
  .legend .sw{width:22px;height:3px;border-radius:2px;margin-right:8px;flex:none;}
  .note{margin-top:10px;border-top:1px solid var(--bd);padding-top:8px;font-size:11.5px;color:var(--muted);line-height:1.45;}
  .note b{color:var(--accent);}
  #hint{position:absolute;bottom:16px;left:50%;transform:translateX(-50%);z-index:6;padding:7px 14px;font-size:12px;color:var(--muted);}
  body.ui-min #panel,body.ui-min #hint{display:none;}
  .maplibregl-popup-content{font-family:var(--font);max-width:280px;border-radius:10px;}
</style>
</head>
<body>
<div id="map"></div>
<div id="panel" class="card">
  <select id="subject"></select>
  <h1 id="title"></h1>
  <div class="sub" id="subtitle"></div>
  <div class="lbl">Theme</div>
  <select id="theme"><option value="atlas">Modern Atlas</option><option value="copperplate">Copperplate</option><option value="illuminated">Illuminated</option><option value="noir">Noir</option></select>
  <div class="toggle" id="survive"><input type="checkbox" id="surviveCb"><label for="surviveCb">Show only what survives</label></div>
  <div class="legend" id="legend"></div>
  <div class="note" id="note"></div>
</div>
<div id="hint" class="card">Click a figure to pivot the network · hover an arc for its evidence</div>
<script>
const NET = __DATA__;
const THEMES={
  atlas:{page:"#f7f6f3",water:"#cdd8dd",land:"#f0eee9",border:"#d8d2c6",ink:[31,41,55],panel:"#ffffff",bd:"#e5e7eb",muted:"#6b7280",accent:"#3f6f8f",chip:"#eef1f3",font:'"Spectral",Georgia,serif'},
  copperplate:{page:"#efe7d3",water:"#dde3da",land:"#e9e0c8",border:"#b59a6a",ink:[36,28,18],panel:"#f6efdc",bd:"#cbb98f",muted:"#6f6048",accent:"#5a3c1d",chip:"#e7dcc0",font:'"IM Fell English",Georgia,serif'},
  illuminated:{page:"#f4ead2",water:"#cfe0e6",land:"#f0e3c2",border:"#caa24e",ink:[58,31,18],panel:"#faf2dc",bd:"#d8b465",muted:"#7a5a36",accent:"#9c2b2b",chip:"#f0e2bf",font:'"EB Garamond",Georgia,serif'},
  noir:{page:"#0e0f12",water:"#11141a",land:"#1b1f27",border:"#333a44",ink:[233,226,207],panel:"#171a20",bd:"#2c3138",muted:"#9aa0aa",accent:"#c9a24b",chip:"#20242c",font:'"EB Garamond",Georgia,serif'},
};
const TYPE_COLORS={ "patron-of":[176,92,53],"collaborated":[60,130,100],"cited":[63,111,143],"collected":[120,70,150],
  "corresponded":[40,120,135],"influenced":[150,110,40],"polemicized-against":[180,55,60],"taught":[90,140,80],"studied-under":[110,100,55] };
function tc(t){return TYPE_COLORS[t]||[120,120,120];}

const STATE={subjectIdx:0, theme:"atlas", survive:false, sel:null};
let map, overlay, S, nodeById;

function subj(){return NET.subjects[STATE.subjectIdx];}
function activeEdges(){return subj().edges.filter(e=>!STATE.survive || e.survives);}
function degrees(){const d={}; subj().nodes.forEach(n=>d[n.id]=0);
  activeEdges().forEach(e=>{d[e.source]=(d[e.source]||0)+e.weight; d[e.target]=(d[e.target]||0)+e.weight;}); return d;}

function applyTheme(){const t=THEMES[STATE.theme],r=document.documentElement.style;
  r.setProperty("--page",t.page);r.setProperty("--ink",`rgb(${t.ink.join(",")})`);r.setProperty("--panel",t.panel);
  r.setProperty("--bd",t.bd);r.setProperty("--muted",t.muted);r.setProperty("--accent",t.accent);r.setProperty("--chip",t.chip);r.setProperty("--font",t.font);}
// Fully local basemap: sea-coloured canvas + embedded Natural Earth geography.
function basemap(){const t=THEMES[STATE.theme];
  return Promise.resolve({version:8,sources:{},
    layers:[{id:"background",type:"background",paint:{"background-color":t.water}}]});}
function restyle(){const t=THEMES[STATE.theme];
  try{map.setPaintProperty("background","background-color",t.water);}catch(e){}}
function hexish(h){const m=h.replace("#","");return [parseInt(m.substr(0,2),16),parseInt(m.substr(2,2),16),parseInt(m.substr(4,2),16)];}
function riverColor(t){const w=hexish(t.water),b=hexish(t.border);
  return [Math.round(w[0]*0.55+b[0]*0.45),Math.round(w[1]*0.55+b[1]*0.45),Math.round(w[2]*0.55+b[2]*0.45)];}
function basegeoLayers(){
  if(!NET.basegeo) return [];
  const t=THEMES[STATE.theme];
  return [
    new deck.GeoJsonLayer({id:"bg-land",data:NET.basegeo.land,stroked:true,filled:true,
      getFillColor:[...hexish(t.land),255],getLineColor:[...hexish(t.border),200],
      getLineWidth:0.9,lineWidthUnits:"pixels",pickable:false,
      updateTriggers:{getFillColor:[STATE.theme],getLineColor:[STATE.theme]}}),
    new deck.GeoJsonLayer({id:"bg-lakes",data:NET.basegeo.lakes,stroked:true,filled:true,
      getFillColor:[...hexish(t.water),255],getLineColor:[...hexish(t.border),140],
      getLineWidth:0.6,lineWidthUnits:"pixels",pickable:false,
      updateTriggers:{getFillColor:[STATE.theme],getLineColor:[STATE.theme]}}),
    new deck.GeoJsonLayer({id:"bg-rivers",data:NET.basegeo.rivers,stroked:true,filled:false,
      getLineColor:[...riverColor(t),190],getLineWidth:0.8,lineWidthUnits:"pixels",pickable:false,
      updateTriggers:{getLineColor:[STATE.theme]}}),
  ];
}

function adjacent(id){const s=new Set([id]); activeEdges().forEach(e=>{if(e.source===id)s.add(e.target);if(e.target===id)s.add(e.source);}); return s;}

function makeLayers(){
  const t=THEMES[STATE.theme], deg=degrees(), edges=activeEdges(), adj=STATE.sel?adjacent(STATE.sel):null, L=[...basegeoLayers()];
  // edges as arcs
  L.push(new deck.ArcLayer({id:"edges",data:edges,
    getSourcePosition:e=>[nodeById[e.source].lon,nodeById[e.source].lat],
    getTargetPosition:e=>[nodeById[e.target].lon,nodeById[e.target].lat],
    getSourceColor:e=>{const c=tc(e.type);const dim=adj&&!(e.source===STATE.sel||e.target===STATE.sel);
      const a=(e.evidence==="inferred"?70:200)*(dim?0.18:1); return e.direction?[c[0]*0.55,c[1]*0.55,c[2]*0.55,a]:[...c,a];},
    getTargetColor:e=>{const c=tc(e.type);const dim=adj&&!(e.source===STATE.sel||e.target===STATE.sel);
      const a=(e.evidence==="inferred"?90:230)*(dim?0.18:1); return [...c,a];},
    getWidth:e=>1+e.weight*1.3, widthUnits:"pixels", getHeight:0.3, pickable:true,
    updateTriggers:{getSourceColor:[STATE.sel,STATE.survive],getTargetColor:[STATE.sel,STATE.survive]}}));
  // nodes
  L.push(new deck.ScatterplotLayer({id:"nodes",data:subj().nodes,getPosition:n=>[n.lon,n.lat],
    getRadius:n=>7+Math.sqrt(deg[n.id]||0)*4, radiusUnits:"pixels", radiusMinPixels:6,
    getFillColor:n=>{const dim=adj&&!adj.has(n.id); const base=(n.id===STATE.sel)?[...t.ink,255]:[...t.ink,210];
      return dim?[t.ink[0],t.ink[1],t.ink[2],50]:base;},
    getLineColor:STATE.theme==="noir"?[201,162,75,255]:[255,255,255,235], lineWidthMinPixels:2, stroked:true, pickable:true,
    updateTriggers:{getFillColor:[STATE.theme,STATE.sel,STATE.survive],getRadius:[STATE.survive]}}));
  // labels
  L.push(new deck.TextLayer({id:"labels",data:subj().nodes,getPosition:n=>[n.lon,n.lat],getText:n=>n.label,
    getSize:13,getColor:n=>{const dim=adj&&!adj.has(n.id);return dim?[t.ink[0],t.ink[1],t.ink[2],90]:[...t.ink,255];},
    getPixelOffset:[0,-16],fontFamily:"Cinzel, Georgia, serif",outlineWidth:3,
    outlineColor:STATE.theme==="noir"?[14,15,18]:[245,243,238],fontSettings:{sdf:true},getAlignmentBaseline:"bottom",
    updateTriggers:{getColor:[STATE.sel,STATE.theme,STATE.survive]}}));
  return L;
}
function render(){overlay.setProps({layers:makeLayers()});}

function buildLegend(){
  const types=[...new Set(subj().edges.map(e=>e.type))];
  document.getElementById("legend").innerHTML='<div class="lbl" style="margin-top:0">Relationship type</div>'+
    types.map(t=>`<div class="li"><span class="sw" style="background:rgb(${tc(t).join(",")})"></span>${t.replace(/-/g," ")}</div>`).join("")+
    '<div class="li" style="margin-top:6px;color:var(--muted)"><span class="sw" style="background:#9999;opacity:.4"></span>faint = inferred · thick = stronger</div>';
}
function loadSubject(){
  S=subj(); nodeById={}; S.nodes.forEach(n=>nodeById[n.id]=n); STATE.sel=null;
  if(THEMES[S.theme]&&!STATE._userTheme){STATE.theme=S.theme;document.getElementById("theme").value=S.theme;}
  document.getElementById("title").textContent=S.title;
  document.getElementById("subtitle").textContent=S.subtitle;
  document.getElementById("note").innerHTML="<b>What this map does NOT show:</b> "+S.provenance_note;
  applyTheme(); restyle(); buildLegend();
  // fit
  const lons=S.nodes.map(n=>n.lon),lats=S.nodes.map(n=>n.lat);
  try{map.fitBounds([[Math.min(...lons)-1,Math.min(...lats)-1],[Math.max(...lons)+1,Math.max(...lats)+1]],{padding:90,duration:600});}catch(e){}
  render();
}

(async function(){
  const u=new URLSearchParams(location.search);
  if(u.get("ui")==="min")document.body.classList.add("ui-min");
  if(u.get("survive")==="1")STATE.survive=true;
  const sp=u.get("subject"); if(sp){const i=NET.subjects.findIndex(s=>s.slug===sp); if(i>=0)STATE.subjectIdx=i;}
  if(u.get("theme")&&THEMES[u.get("theme")]){STATE.theme=u.get("theme");STATE._userTheme=true;}
  document.getElementById("subject").innerHTML=NET.subjects.map((s,i)=>`<option value="${i}">${s.title}</option>`).join("");
  document.getElementById("subject").value=STATE.subjectIdx;
  applyTheme();
  const style=await basemap();
  map=new maplibregl.Map({container:"map",style,center:[8,48],zoom:4,attributionControl:true});
  overlay=new deck.MapboxOverlay({interleaved:true,layers:[],getTooltip:({object,layer})=>{
    if(!object)return null;
    if(layer.id==="edges"){return {html:`<b>${nodeById[object.source].label} ${object.direction?"→":"—"} ${nodeById[object.target].label}</b><br>`+
      `<span style="color:#b05c35">${object.type.replace(/-/g," ")}</span> · ${object.evidence}${object.survives?"":" · not extant"}<br>`+
      `<span style="font-size:11px;color:#888;font-style:italic">${object.note||""}</span>`};}
    if(layer.id!=="nodes")return null;
    return {html:`<b>${object.label}</b><br><span style="font-size:12px;color:#888">${object.role}${object.year?", from c."+object.year:""}</span>`+
      (object.slug?`<br><a href="../../ALCHEMYTIMELINEMAP/site/persons/${object.slug}.html" target="_blank" style="font-size:11px">open page →</a>`:"")};
  }});
  map.addControl(overlay);
  window._map=map;window._overlay=overlay;window._STATE=STATE;
  map.on("error",e=>console.log("maplibre error:",e&&e.error&&e.error.message));
  // click to pivot
  overlay.setProps({onClick:({object,layer})=>{ if(layer&&layer.id==="nodes"&&object){STATE.sel=(STATE.sel===object.id)?null:object.id;render();} else if(!object){STATE.sel=null;render();} }});
  loadSubject();
  setTimeout(()=>{try{map.resize();}catch(e){}},250);
  window.addEventListener("resize",()=>{try{map.resize();}catch(e){}});
  map.on("load",()=>{restyle();render();});

  document.getElementById("subject").onchange=e=>{STATE.subjectIdx=+e.target.value;STATE._userTheme=false;loadSubject();};
  document.getElementById("theme").onchange=e=>{STATE.theme=e.target.value;STATE._userTheme=true;applyTheme();restyle();render();};
  document.getElementById("surviveCb").onchange=e=>{STATE.survive=e.target.checked;document.getElementById("survive").classList.toggle("on",e.target.checked);render();};

  window.addEventListener("message",ev=>{const d=ev.data||{};if(d.type!=="netctl")return;
    if(d.subject){const i=NET.subjects.findIndex(s=>s.slug===d.subject);if(i>=0){STATE.subjectIdx=i;document.getElementById("subject").value=i;STATE._userTheme=!!d.theme;loadSubject();}}
    if(d.theme){STATE.theme=d.theme;document.getElementById("theme").value=d.theme;STATE._userTheme=true;applyTheme();restyle();}
    if(d.survive!=null){STATE.survive=d.survive;document.getElementById("surviveCb").checked=d.survive;document.getElementById("survive").classList.toggle("on",d.survive);}
    if(d.select!==undefined)STATE.sel=d.select;
    render();});
})();
</script>
</body>
</html>
"""


EVIDENCE_LEVELS = {"attested", "inferred", "approximate"}


def validate_network(net):
    """Edges must be typed, evidence-bearing, and resolve to real nodes."""
    errors = []
    for s in net.get("subjects") or []:
        slug = s.get("slug", "?")
        ids = [n.get("id") for n in s.get("nodes") or []]
        if len(ids) != len(set(ids)):
            errors.append(f"{slug}: duplicate node ids")
        idset = set(ids)
        for n in s.get("nodes") or []:
            for field in ("id", "label", "lat", "lon"):
                if n.get(field) in (None, ""):
                    errors.append(f"{slug}: node {n.get('id', '?')} missing '{field}'")
        for i, e in enumerate(s.get("edges") or []):
            where = f"{slug} edge {i+1} ({e.get('source', '?')}->{e.get('target', '?')})"
            for field in ("source", "target", "type", "evidence", "note"):
                if e.get(field) in (None, ""):
                    errors.append(f"{where}: missing '{field}'")
            if e.get("source") not in idset or e.get("target") not in idset:
                errors.append(f"{where}: endpoint not among this subject's nodes")
            if e.get("evidence") and e["evidence"] not in EVIDENCE_LEVELS:
                errors.append(f"{where}: evidence '{e['evidence']}' not in {sorted(EVIDENCE_LEVELS)}")
            if "survives" not in e:
                errors.append(f"{where}: missing 'survives' (the survival-bias toggle depends on it)")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(Path(__file__).resolve().parents[1] / "data" / "networks.json"))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "prototypes" / "network.html"))
    ap.add_argument("--allow-unsourced", action="store_true",
                    help="build even if edges lack evidence/note fields (drafts only)")
    args = ap.parse_args()
    net = json.loads(Path(args.data).read_text(encoding="utf-8"))
    from build_map import load_basegeo
    net["basegeo"] = load_basegeo()
    if not net["basegeo"]:
        print("  WARNING: no base geography cache — run scripts/fetch_basegeo.py first")
    errors = validate_network(net)
    if errors:
        for e in errors:
            print(f"  {'warning' if args.allow_unsourced else 'DATA ERROR'}: {e}")
        if not args.allow_unsourced:
            raise SystemExit(2)
    out = TEMPLATE.replace("__DATA__", json.dumps(net, ensure_ascii=False))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(out, encoding="utf-8")
    print(f"Built: {args.out}")
    for s in net["subjects"]:
        surv = sum(1 for e in s["edges"] if e["survives"])
        print(f"  {s['slug']:<22} {len(s['nodes'])} nodes · {len(s['edges'])} edges ({surv} survive)")


if __name__ == "__main__":
    main()
