#!/usr/bin/env python3
"""Build a compact three.js HTML viewer: indexed geometry, gzipped payload.

v2 - the naive version embedded ~4.3MB of base64 STL and expanded it into
unindexed Float32 triangle soup at load, which blew the preview sandbox's
memory ("RangeError: Array buffer allocation failed"). Now: merged-vertex
indexed meshes (uint16 indices where possible), one gzipped binary blob,
DecompressionStream at load, flatShading instead of duplicated normals.
"""
import base64, gzip, json, struct
import numpy as np, trimesh

order = ['fittes', 'kumiko', 'luxe', 'luxe1', 'key']
files = {'fittes': 'fittes_design.stl', 'kumiko': 'kumiko_design.stl',
         'luxe': 'luxe_design.stl', 'luxe1': 'luxe1_design.stl',
         'key': 'vent_lift_key_PRINT.stl'}

header, blob = {}, b''
for name in order:
    m = trimesh.load(files[name])          # trimesh merges duplicate vertices
    v = np.asarray(m.vertices, dtype=np.float32)
    f = np.asarray(m.faces)
    u16 = len(v) < 65535
    idx = f.astype(np.uint16 if u16 else np.uint32)
    seg = v.tobytes() + idx.tobytes()
    header[name] = {'v': int(len(v)), 't': int(len(f)), 'u16': u16, 'off': len(blob)}
    blob += seg + b'\x00' * ((4 - len(blob + seg) % 4) % 4)   # 4-byte align next segment
    print(f"{name}: {len(v)} verts, {len(f)} tris, {'u16' if u16 else 'u32'}, "
          f"{len(seg)//1024} KB raw")

gz = gzip.compress(blob, 9)
b64 = base64.b64encode(gz).decode()
print(f"payload: raw {len(blob)//1024} KB -> gzip {len(gz)//1024} KB -> b64 {len(b64)//1024} KB")

html = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Nursery Flush Vent - 350×147 (3 styles)</title>
<style>
 body{margin:0;font-family:-apple-system,'Segoe UI',sans-serif;background:#1b1d21;color:#eee;overflow:hidden}
 #bar{position:fixed;top:0;left:0;right:0;display:flex;gap:8px;align-items:center;flex-wrap:wrap;
      padding:10px 14px;background:rgba(20,22,26,.85);backdrop-filter:blur(6px);z-index:2}
 #bar b{font-weight:600;margin-right:6px;font-size:14px}
 button{background:#2e3238;border:1px solid #444;color:#ddd;padding:6px 14px;border-radius:8px;
        cursor:pointer;font-size:13px}
 button.on{background:#4d7fd6;border-color:#4d7fd6;color:#fff}
 #info{position:fixed;bottom:10px;left:14px;font-size:12px;color:#9aa0a8;z-index:2;line-height:1.5}
 #err{position:fixed;top:40%;left:0;right:0;text-align:center;color:#e88;font-size:14px;display:none}
 canvas{display:block}
</style></head><body>
<div id="bar"><b>Nursery flush drop-in vent</b>
 <button id="bF" class="on">Fittes slots</button>
 <button id="bK">Kumiko lattice</button>
 <button id="bL">Luxe 3-channel</button>
 <button id="bL1">Luxe single</button>
 <button id="bKey">show lift key</button>
 <button id="bFloor" class="on">show floor</button>
</div>
<div id="info">349 × 171 × 20.5&nbsp;mm one-piece (two-part versions in two-print/) · PETG ·
 5&nbsp;mm child-safe openings · drag = orbit, wheel = zoom, right-drag = pan</div>
<div id="err"></div>
<script type="importmap">{"imports":{
 "three":"https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.module.min.js"}}
</script>
<script type="module">
import * as THREE from 'three';
const HDR = __HDR__;
const ORDER = __ORDER__;
async function payload(){
  const b = atob("__B64__"), u = new Uint8Array(b.length);
  for (let i=0;i<b.length;i++) u[i]=b.charCodeAt(i);
  const ds = new Response(new Blob([u]).stream().pipeThrough(
      new DecompressionStream('gzip')));
  return await ds.arrayBuffer();
}
function geom(buf, h){
  const pos = new Float32Array(buf, h.off, h.v*3);
  const idx = h.u16 ? new Uint16Array(buf, h.off + h.v*12, h.t*3)
                    : new Uint32Array(buf, h.off + h.v*12, h.t*3);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  g.computeVertexNormals();
  return g;
}
try {
  const buf = await payload();
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x1b1d21);
  const cam = new THREE.PerspectiveCamera(40, innerWidth/innerHeight, 1, 5000);
  cam.up.set(0,0,1);
  const ren = new THREE.WebGLRenderer({antialias:true});
  ren.setSize(innerWidth, innerHeight);
  ren.setPixelRatio(Math.min(devicePixelRatio, 2));
  document.body.appendChild(ren.domElement);
  scene.add(new THREE.AmbientLight(0xffffff, .55));
  const d1 = new THREE.DirectionalLight(0xffffff, 1.1); d1.position.set(-200,-300,400); scene.add(d1);
  const d2 = new THREE.DirectionalLight(0xbfd4ff, .4); d2.position.set(300,200,150); scene.add(d2);

  const petg = new THREE.MeshStandardMaterial({color:0xf2eee7, roughness:.55, metalness:.05, flatShading:true});
  const meshes = {};
  for (const k of ['fittes','kumiko','luxe','luxe1']){
    meshes[k] = new THREE.Mesh(geom(buf, HDR[k]), petg);
    meshes[k].position.z = 4.5; scene.add(meshes[k]);
  }
  meshes.key = new THREE.Mesh(geom(buf, HDR.key),
    new THREE.MeshStandardMaterial({color:0x88b04b, roughness:.6, flatShading:true}));
  meshes.key.position.set(-120, -150, 4.5); meshes.key.visible=false; scene.add(meshes.key);

  // wood floor with the 350x147 opening, floor top at z=0
  const shape = new THREE.Shape();
  shape.moveTo(-500,-380); shape.lineTo(500,-380); shape.lineTo(500,380); shape.lineTo(-500,380);
  const hole = new THREE.Path();
  hole.moveTo(-175,-73.5); hole.lineTo(175,-73.5); hole.lineTo(175,73.5); hole.lineTo(-175,73.5);
  shape.holes.push(hole);
  const floorGeo = new THREE.ExtrudeGeometry(shape,{depth:19,bevelEnabled:false});
  floorGeo.translate(0,0,-19);
  const floor = new THREE.Mesh(floorGeo,
    new THREE.MeshStandardMaterial({color:0xa87f4f, roughness:.8}));
  scene.add(floor);

  let theta=-1.05, phi=.9, dist=560, tx=0, ty=0, tz=-5;
  function applyCam(){
    cam.position.set(tx+dist*Math.cos(phi)*Math.cos(theta),
                     ty+dist*Math.cos(phi)*Math.sin(theta), tz+dist*Math.sin(phi));
    cam.lookAt(tx,ty,tz);
  }
  applyCam();
  let drag=null;
  addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,b:e.button}});
  addEventListener('pointerup',()=>drag=null);
  addEventListener('contextmenu',e=>e.preventDefault());
  addEventListener('pointermove',e=>{
    if(!drag) return;
    const dx=e.clientX-drag.x, dy=e.clientY-drag.y; drag.x=e.clientX; drag.y=e.clientY;
    if(drag.b===2){ tx-=dx*.6*Math.sin(-theta); ty-=dx*.6*Math.cos(theta); tz+=dy*.6; }
    else { theta-=dx*.006; phi=Math.min(1.5,Math.max(.05,phi+dy*.006)); }
    applyCam();
  });
  addEventListener('wheel',e=>{dist=Math.min(2500,Math.max(120,dist*(1+e.deltaY*.001)));applyCam();});
  addEventListener('resize',()=>{cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();
    ren.setSize(innerWidth,innerHeight)});

  const bF=document.getElementById('bF'), bK=document.getElementById('bK'),
        bL=document.getElementById('bL'), bL1=document.getElementById('bL1'),
        bKey=document.getElementById('bKey'), bFl=document.getElementById('bFloor');
  function setStyle(s){
    for (const k of ['fittes','kumiko','luxe','luxe1']) meshes[k].visible = (s===k);
    bF.classList.toggle('on', s==='fittes'); bK.classList.toggle('on', s==='kumiko');
    bL.classList.toggle('on', s==='luxe'); bL1.classList.toggle('on', s==='luxe1');
  }
  setStyle('fittes');
  bF.onclick=()=>setStyle('fittes'); bK.onclick=()=>setStyle('kumiko');
  bL.onclick=()=>setStyle('luxe');
  bL1.onclick=()=>setStyle('luxe1');
  bKey.onclick=()=>{meshes.key.visible=!meshes.key.visible;bKey.classList.toggle('on')};
  bFl.onclick=()=>{floor.visible=!floor.visible;bFl.classList.toggle('on')};
  (function loop(){requestAnimationFrame(loop);ren.render(scene,cam);})();
} catch (e) {
  const el = document.getElementById('err');
  el.style.display='block';
  el.textContent = 'Viewer failed to load: ' + e.message +
    ' - open this file in a regular Chrome tab (uses gzip DecompressionStream + WebGL).';
  throw e;
}
</script></body></html>
"""
html = (html.replace('__HDR__', json.dumps(header))
            .replace('__ORDER__', json.dumps(order))
            .replace('__B64__', b64))
open('vent_viewer.html', 'w').write(html)
print('vent_viewer.html', len(html)//1024, 'KB')
