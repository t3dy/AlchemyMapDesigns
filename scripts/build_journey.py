#!/usr/bin/env python3
"""
build_journey.py — the BIOGRAPHICAL JOURNEY template.

Reads a curated journey JSON (ordered stops with dates, dwell, evidence, source,
and per-leg evidence) and emits a self-contained MapLibre GL + deck.gl map that:
  - DRAWS ITSELF stop by stop, camera trucking ahead, WITHHOLDING the ending
    (future stops/legs are never shown — the reader can stop mid-life knowing
    nothing of what comes);
  - styles each leg by evidence (solid = attested, dashed = inferred/approximate);
  - sizes nodes by dwell time (the staying, not just the going);
  - offers four UNCERTAINTY TREATMENTS as switchable experiments:
      Lay (clean story) · Understated (quiet apparatus) ·
      Scholar (full citations + gap notes) · Centerpiece (doubt made visible).

Usage:  python build_journey.py <journey.json> [--out <out.html>]
"""
import argparse, json, html
from pathlib import Path

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet">
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script src="https://unpkg.com/deck.gl@9.0.33/dist.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=EB+Garamond:ital@0;1&family=Spectral:wght@300;400;600&display=swap" rel="stylesheet">
<style>
  :root{--page:#0e0f12;--ink:#e9e2cf;--muted:#9aa0aa;--gold:#c9a24b;--panel:#171a20;--bd:#2c3138;}
  *{box-sizing:border-box;}
  html,body{margin:0;height:100%;font-family:"EB Garamond",Georgia,serif;background:var(--page);color:var(--ink);}
  #map{position:absolute;inset:0;background:var(--page);}
  .card{background:rgba(23,26,32,.92);border:1px solid var(--bd);border-radius:12px;box-shadow:0 16px 44px rgba(0,0,0,.5);backdrop-filter:blur(4px);}
  /* story panel bottom-left */
  #story{position:absolute;left:20px;bottom:22px;width:min(420px,84vw);padding:18px 20px;z-index:6;}
  #story .place{font-family:"Cinzel",serif;font-size:22px;color:#f1e4c4;margin:0;}
  #story .yr{font-size:13px;color:var(--gold);letter-spacing:.08em;margin:2px 0 10px;}
  #story .what{font-size:16px;line-height:1.55;color:#e3dcc8;margin:0;}
  #story .src{font-size:11.5px;color:var(--muted);font-style:italic;margin-top:10px;border-top:1px solid var(--bd);padding-top:8px;display:none;}
  #story .ev{display:inline-block;font-family:"Cinzel",serif;font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;border:1px solid var(--gold);color:var(--gold);border-radius:999px;padding:2px 8px;margin-left:8px;vertical-align:middle;}
  /* controls top-left */
  #ctl{position:absolute;top:18px;left:20px;z-index:6;padding:12px 14px;width:248px;}
  #ctl h1{font-family:"Cinzel",serif;font-size:15px;margin:0 0 2px;color:#f1e4c4;}
  #ctl .sub{font-size:12px;color:var(--muted);font-style:italic;margin-bottom:10px;}
  .row{display:flex;gap:8px;align-items:center;margin:8px 0;}
  button{font-family:"EB Garamond",serif;cursor:pointer;border:1px solid var(--bd);background:#20242c;color:var(--ink);border-radius:8px;padding:7px 13px;font-size:14px;}
  button.primary{background:var(--gold);color:#1a1206;border-color:var(--gold);font-weight:600;}
  button:hover{border-color:var(--gold);}
  .lbl{font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin:10px 0 5px;}
  select{width:100%;font-family:"EB Garamond",serif;background:#20242c;color:var(--ink);border:1px solid var(--bd);border-radius:8px;padding:6px 8px;font-size:13px;}
  /* doubt panel (centerpiece) top-right */
  #doubt{position:absolute;top:18px;right:20px;width:min(300px,84vw);padding:14px 16px;z-index:6;display:none;}
  #doubt h3{font-family:"Cinzel",serif;font-size:12px;letter-spacing:.06em;color:var(--gold);margin:0 0 8px;}
  #doubt ul{margin:0;padding-left:16px;font-size:12.5px;color:#d8cfba;line-height:1.5;}
  #doubt .none{color:var(--muted);font-style:italic;font-size:12.5px;}
  .maplibregl-popup-content{font-family:"EB Garamond",serif;background:#171a20;color:#e9e2cf;border:1px solid var(--bd);border-radius:8px;max-width:260px;}
  .maplibregl-popup-tip{border-top-color:#171a20!important;}
  .legend{position:absolute;bottom:22px;right:20px;z-index:6;padding:10px 13px;font-size:12px;}
  .legend .li{display:flex;align-items:center;gap:8px;margin:3px 0;}
  .legend .ln{width:26px;height:0;border-top:2px solid var(--gold);}
  .legend .ln.dash{border-top:2px dashed var(--gold);}
  body.ui-min #ctl{display:none;}
</style>
</head>
<body>
<div id="map"></div>

<div id="ctl" class="card">
  <h1>__TITLE__</h1>
  <div class="sub">__SUBTITLE__</div>
  <div class="row">
    <button id="play" class="primary">▶ Play</button>
    <button id="next">Next ▸</button>
    <button id="back">◂</button>
  </div>
  <div class="lbl">Uncertainty treatment</div>
  <select id="mode">
    <option value="understated">Understated — quiet apparatus</option>
    <option value="lay">Lay — clean story</option>
    <option value="scholar">Scholar — citations + gaps</option>
    <option value="centerpiece">Centerpiece — doubt made visible</option>
  </select>
  <div class="lbl">Theme</div>
  <select id="theme"><option value="noir">Alchemical Noir</option><option value="atlas">Modern Atlas</option></select>
</div>

<div id="story" class="card">
  <p class="place" id="place">—</p>
  <div class="yr" id="yr"></div>
  <p class="what" id="what">Press ▶ Play to set out.</p>
  <div class="src" id="src"></div>
</div>

<div id="doubt" class="card"><h3>What we don't know — so far</h3><div id="doubtBody"></div></div>

<div class="legend card" id="legend">
  <div class="li"><span class="ln"></span> documented presence / travel</div>
  <div class="li"><span class="ln dash"></span> inferred or approximate</div>
</div>

<script>
const J = __DATA__;
const THEMES = {
  noir:{page:"#0e0f12",water:"#11141a",land:"#1b1f27",border:"#333a44",ink:[233,226,207],accent:[201,162,75],ghost:[201,162,75]},
  atlas:{page:"#f5f3ee",water:"#cdd8dd",land:"#eceae4",border:"#d3ccbe",ink:[40,32,20],accent:[150,60,40],ghost:[150,60,40]},
};
const STATE={idx:-1, t:1, theme:(J.theme&&["noir","atlas"].includes(J.theme))?J.theme:"noir", mode:"understated", playing:null, anim:null};
const hasDash = (typeof deck.PathStyleExtension!=="undefined");

let map, overlay;
function applyTheme(){const t=THEMES[STATE.theme],r=document.documentElement.style;
  r.setProperty("--page",t.page); r.setProperty("--ink",`rgb(${t.ink.join(",")})`);
  if(STATE.theme==="atlas"){r.setProperty("--panel","rgba(250,248,243,.94)");r.setProperty("--bd","#d3ccbe");r.setProperty("--muted","#6b5f48");}
  else{r.setProperty("--panel","rgba(23,26,32,.92)");r.setProperty("--bd","#2c3138");r.setProperty("--muted","#9aa0aa");}
}
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
  if(!J.basegeo) return [];
  const t=THEMES[STATE.theme];
  return [
    new deck.GeoJsonLayer({id:"bg-land",data:J.basegeo.land,stroked:true,filled:true,
      getFillColor:[...hexish(t.land),255],getLineColor:[...hexish(t.border),200],
      getLineWidth:0.9,lineWidthUnits:"pixels",pickable:false,
      updateTriggers:{getFillColor:[STATE.theme],getLineColor:[STATE.theme]}}),
    new deck.GeoJsonLayer({id:"bg-lakes",data:J.basegeo.lakes,stroked:true,filled:true,
      getFillColor:[...hexish(t.water),255],getLineColor:[...hexish(t.border),140],
      getLineWidth:0.6,lineWidthUnits:"pixels",pickable:false,
      updateTriggers:{getFillColor:[STATE.theme],getLineColor:[STATE.theme]}}),
    new deck.GeoJsonLayer({id:"bg-rivers",data:J.basegeo.rivers,stroked:true,filled:false,
      getLineColor:[...riverColor(t),190],getLineWidth:0.8,lineWidthUnits:"pixels",pickable:false,
      updateTriggers:{getLineColor:[STATE.theme]}}),
  ];
}

function lerp(a,b,t){return [a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t];}
function isUncertain(s){return s && (s.evidence==="inferred"||s.evidence==="approximate");}
function legUncertain(s){return s && (s.leg_evidence==="inferred"||s.leg_evidence==="approximate");}

function revealedStops(){return J.stops.slice(0,STATE.idx+1);}
function makeLayers(){
  const t=THEMES[STATE.theme], L=[...basegeoLayers()], showEvidence=(STATE.mode!=="lay");
  // legs (paths) up to idx; the active leg (idx) animates by STATE.t
  const paths=[];
  for(let i=1;i<=STATE.idx;i++){
    const a=[J.stops[i-1].lon,J.stops[i-1].lat], b=[J.stops[i].lon,J.stops[i].lat];
    const end = (i===STATE.idx)? lerp(a,b,STATE.t) : b;
    const dashed = showEvidence && legUncertain(J.stops[i]);
    paths.push({path:[a,end], dashed, leg:J.stops[i]});
  }
  if(paths.length){
    const props={id:"legs",data:paths,getPath:d=>d.path,widthUnits:"pixels",
      getWidth:d=>(STATE.mode==="centerpiece"&&d.dashed)?4:2.5,
      getColor:d=>{ if(!showEvidence) return [...t.accent,230];
        return d.dashed? [...t.ghost, STATE.mode==="centerpiece"?255:150] : [...t.accent,235]; },
      pickable:true, capRounded:true, jointRounded:true};
    if(hasDash){ props.extensions=[new deck.PathStyleExtension({dash:true})];
      props.getDashArray=d=> d.dashed? [4,3] : [0,0]; props.dashJustified=true; }
    L.push(new deck.PathLayer(props));
  }
  // glow under dashed ghost legs in centerpiece
  if(STATE.mode==="centerpiece"){
    const ghosts=paths.filter(p=>p.dashed);
    if(ghosts.length) L.push(new deck.PathLayer({id:"ghostglow",data:ghosts,getPath:d=>d.path,widthUnits:"pixels",getWidth:10,getColor:[...t.ghost,40],capRounded:true}));
  }
  // nodes up to idx, radius by dwell
  const nodes=revealedStops();
  L.push(new deck.ScatterplotLayer({id:"nodes",data:nodes,getPosition:d=>[d.lon,d.lat],
    getRadius:d=>6+Math.sqrt(Math.max(1,d.dwell))*3.2,radiusUnits:"pixels",radiusMinPixels:5,
    getFillColor:d=>[...t.accent, 235], getLineColor:STATE.theme==="noir"?[14,15,18,255]:[255,255,255,235],
    lineWidthMinPixels:1.6,stroked:true,pickable:true,
    updateTriggers:{getFillColor:[STATE.theme]}}));
  // halo for uncertain dates (centerpiece)
  if(STATE.mode==="centerpiece"){
    const unc=nodes.filter(isUncertain);
    if(unc.length)L.push(new deck.ScatterplotLayer({id:"halo",data:unc,getPosition:d=>[d.lon,d.lat],
      getRadius:d=>14+Math.sqrt(Math.max(1,d.dwell))*3.2,radiusUnits:"pixels",stroked:true,filled:false,
      getLineColor:[...t.ghost,150],lineWidthMinPixels:1.5}));
  }
  // current label
  if(STATE.idx>=0){const cur=J.stops[STATE.idx];
    L.push(new deck.TextLayer({id:"lbl",data:[cur],getPosition:d=>[d.lon,d.lat],getText:d=>d.place,
      getSize:15,getColor:t.ink,getPixelOffset:[0,-18],fontFamily:"Cinzel, Georgia, serif",
      outlineWidth:3,outlineColor:THEMES[STATE.theme].page==="#0e0f12"?[14,15,18]:[245,243,238],fontSettings:{sdf:true},getAlignmentBaseline:"bottom"}));}
  return L;
}
function render(){overlay.setProps({layers:makeLayers()});}

function showStory(){
  const i=STATE.idx; if(i<0)return;
  const s=J.stops[i], showEvidence=(STATE.mode!=="lay");
  document.getElementById("place").textContent=s.place;
  const evBadge = (showEvidence && isUncertain(s))? `<span class="ev">${s.evidence}</span>`:"";
  document.getElementById("yr").innerHTML=`${s.year_start}${s.year_end&&s.year_end!=s.year_start?"–"+s.year_end:""} CE`+evBadge;
  document.getElementById("what").textContent=s.what;
  const src=document.getElementById("src");
  if(STATE.mode==="scholar"){ src.style.display="block"; src.textContent="Source: "+(s.source||"—")+(legUncertain(s)?"  ·  travel into this stop is reconstructed, not documented.":""); }
  else src.style.display="none";
  // doubt panel
  const doubt=document.getElementById("doubt");
  if(STATE.mode==="centerpiece"){ doubt.style.display="block";
    const items=[]; for(let k=0;k<=i;k++){const st=J.stops[k];
      if(legUncertain(st)&&k>0)items.push(`The road from ${J.stops[k-1].place} to ${st.place} is <b>reconstructed</b> — no record survives.`);
      if(isUncertain(st))items.push(`${st.place}: dating is <b>${st.evidence}</b>.`);}
    document.getElementById("doubtBody").innerHTML = items.length? "<ul>"+items.map(x=>`<li>${x}</li>`).join("")+"</ul>" : '<div class="none">Nothing uncertain on the road so far.</div>';
  } else doubt.style.display="none";
  document.getElementById("legend").style.display=(showEvidence?"block":"none");
}

function flyTo(s){try{map.flyTo({center:[s.lon,s.lat],zoom:5.1,duration:1400,essential:true});}catch(e){}}

function goTo(i, animate){
  i=Math.max(0,Math.min(J.stops.length-1,i));
  STATE.idx=i; flyTo(J.stops[i]); showStory();
  if(animate && i>0){ STATE.t=0; cancelAnimationFrame(STATE.anim);
    const dur=1300, t0=performance.now();
    const step=(now)=>{ STATE.t=Math.min(1,(now-t0)/dur);
      STATE.t = STATE.t<.5?2*STATE.t*STATE.t:1-Math.pow(-2*STATE.t+2,2)/2; // ease-in-out
      render(); if(STATE.t<1) STATE.anim=requestAnimationFrame(step); };
    STATE.anim=requestAnimationFrame(step);
  } else { STATE.t=1; render(); }
}

function advance(){ if(STATE.idx>=J.stops.length-1){stopPlay();return;} goTo(STATE.idx+1,true); }
function stopPlay(){ if(STATE.playing){clearInterval(STATE.playing);STATE.playing=null;document.getElementById("play").textContent="▶ Play";} }

(async function(){
  const u=new URLSearchParams(location.search);
  if(u.get("ui")==="min")document.body.classList.add("ui-min");
  if(u.get("theme")&&THEMES[u.get("theme")])STATE.theme=u.get("theme");
  if(u.get("mode"))STATE.mode=u.get("mode");
  document.getElementById("mode").value=STATE.mode; document.getElementById("theme").value=STATE.theme;
  applyTheme();
  const style=await basemap();
  map=new maplibregl.Map({container:"map",style,center:[J.stops[0].lon,J.stops[0].lat],zoom:4.4,attributionControl:true});
  overlay=new deck.MapboxOverlay({interleaved:true,layers:[],getTooltip:({object,layer})=>{
    if(!object)return null;
    if(layer.id==="legs"){const s=object.leg;return {html:`<b>${J.stops[s.order-2]?J.stops[s.order-2].place:"?"} → ${s.place}</b><br><span style="color:#c9a24b">${s.leg_evidence||"?"}</span>`};}
    if(layer.id!=="nodes")return null;
    return {html:`<div style="max-width:240px"><b>${object.place}</b> <span style="color:#9aa0aa">${object.year_start}${object.year_end!=object.year_start?"–"+object.year_end:""}</span><br><span style="font-size:12px">${object.what}</span>`+
      (STATE.mode!=="lay"?`<br><span style="font-size:11px;color:#9aa0aa;font-style:italic">${object.source||""}</span>`:"")+`</div>`};
  }});
  map.addControl(overlay);
  window._map=map;window._overlay=overlay;window._STATE=STATE;
  map.on("error",e=>console.log("maplibre error:",e&&e.error&&e.error.message));
  goTo(0,false);
  setTimeout(()=>{try{map.resize();}catch(e){}},250);
  window.addEventListener("resize",()=>{try{map.resize();}catch(e){}});

  document.getElementById("next").onclick=()=>{stopPlay();advance();};
  document.getElementById("back").onclick=()=>{stopPlay();goTo(STATE.idx-1,false);};
  document.getElementById("play").onclick=function(){
    if(STATE.playing){stopPlay();return;}
    if(STATE.idx>=J.stops.length-1)goTo(0,false);
    this.textContent="⏸ Pause"; advance();
    STATE.playing=setInterval(advance,2100);
  };
  document.getElementById("mode").onchange=e=>{STATE.mode=e.target.value;showStory();render();};
  document.getElementById("theme").onchange=e=>{STATE.theme=e.target.value;applyTheme();restyle();render();};
  map.on("load",()=>{restyle();render();});

  // embedding: postMessage {type:'journeyctl', goto:n, mode, theme, play:true}
  window.addEventListener("message",ev=>{const d=ev.data||{};if(d.type!=="journeyctl")return;
    if(d.mode){STATE.mode=d.mode;document.getElementById("mode").value=d.mode;}
    if(d.theme){STATE.theme=d.theme;document.getElementById("theme").value=d.theme;applyTheme();restyle();}
    if(d.goto!=null)goTo(d.goto, d.animate!==false);
    if(d.play){document.getElementById("play").click();}
    showStory();render();});
})();
</script>
</body>
</html>
"""


EVIDENCE_LEVELS = {"attested", "inferred", "approximate"}


def validate_journey(J):
    """Every stop must carry its evidence and its source — no unsourced lives."""
    errors = []
    stops = J.get("stops") or []
    if not stops:
        errors.append("journey has no stops")
    prev_year = None
    for i, s in enumerate(stops):
        where = f"stop {i+1} ({s.get('place', '?')})"
        for field in ("place", "lat", "lon", "year_start", "what", "evidence", "source"):
            if s.get(field) in (None, ""):
                errors.append(f"{where}: missing '{field}'")
        if s.get("evidence") and s["evidence"] not in EVIDENCE_LEVELS:
            errors.append(f"{where}: evidence '{s['evidence']}' not in {sorted(EVIDENCE_LEVELS)}")
        if s.get("leg_evidence") and s["leg_evidence"] not in EVIDENCE_LEVELS:
            errors.append(f"{where}: leg_evidence '{s['leg_evidence']}' not in {sorted(EVIDENCE_LEVELS)}")
        y = s.get("year_start")
        if isinstance(y, int) and isinstance(prev_year, int) and y < prev_year:
            errors.append(f"{where}: year_start {y} is before previous stop ({prev_year}) — stops must be in order")
        if isinstance(y, int):
            prev_year = y
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("journey")
    ap.add_argument("--out", default=None)
    ap.add_argument("--allow-unsourced", action="store_true",
                    help="build even if stops lack evidence/source fields (drafts only)")
    args = ap.parse_args()
    J = json.loads(Path(args.journey).read_text(encoding="utf-8"))
    from build_map import load_basegeo
    J["basegeo"] = load_basegeo()
    if not J["basegeo"]:
        print("  WARNING: no base geography cache — run scripts/fetch_basegeo.py first")
    errors = validate_journey(J)
    if errors:
        for e in errors:
            print(f"  {'warning' if args.allow_unsourced else 'DATA ERROR'}: {e}")
        if not args.allow_unsourced:
            raise SystemExit(2)
    out = TEMPLATE.replace("__TITLE__", html.escape(J.get("title", "A Journey")))
    out = out.replace("__SUBTITLE__", html.escape(J.get("subtitle", "")))
    out = out.replace("__DATA__", json.dumps(J, ensure_ascii=False))
    out_path = Path(args.out) if args.out else (Path(__file__).resolve().parents[1] / "prototypes" / ("journey-" + Path(args.journey).stem.replace("journey-", "") + ".html"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    print(f"Built: {out_path}")
    print(f"  {len(J['stops'])} stops · {sum(1 for s in J['stops'] if s.get('leg_evidence') in ('inferred','approximate'))} reconstructed legs · dash={'PathStyleExtension' if True else 'n/a'}")


if __name__ == "__main__":
    main()
