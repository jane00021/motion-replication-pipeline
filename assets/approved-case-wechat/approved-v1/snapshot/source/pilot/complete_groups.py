from pathlib import Path
import json,math,copy,random
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
import t04_render as core
import render_migration as media
P=core.P
S=P/'source/pilot/complete01-02';O=P/'render/pilot/complete01-02';W,H=628,1118
from components.common import load,prog,text_tile,put,reveal
from components.visual import vignette,icon,symbols,reframe_presenter,head_matte
from components.subtitle import title_tile
from components.runtime import compose
def prepare():return [load(S/'input-01.json'),load(S/'input-02.json')]
def group1(raw,n,c,disabled=()):return compose(load(S/'recipes/01.json'),raw,n,c,disabled)
def group2(raw,n,c,disabled=()):return compose(load(S/'recipes/02.json'),raw,n,c,disabled)
def render(c):
 from components.runtime import validate_recipe
 from components.pairing import check
 validate_recipe(load(S/'recipes'/(c['id']+'.json')))
 check(load(S/'recipes'/(c['id']+'.json')),c,P)
 frames=c['frames'];raw=media.extract(c['rawStart'],frames/30);assert len(raw)==frames
 fun=group1 if c['id']=='01' else group2;encoded=[];alphaRows=[]
 for n,a in enumerate(raw):
  native=Image.fromarray(a).resize((286,508),Image.Resampling.LANCZOS);result=fun(native,n,c);encoded.append(result.resize((W,H),Image.Resampling.LANCZOS).convert('RGB'))
  if n in [0,round(frames*.2),round(frames*.5),round(frames*.75),frames-1]:result.save(O/f'{c["id"]}-frame-{n}.png')
 audio=media.audio('complete-'+c['id'],c['rawStart'],frames/30);path=O/f'group-{c["id"]}.mp4';media.encode(path,encoded,audio)
 # Verify each declared component changes the rendered complete group.
 n=round(frames*.75);rawim=Image.fromarray(raw[n]).resize((286,508));full=np.array(fun(rawim,n,c));tests={}
 for comp in ['vignette','photo','text'] if c['id']=='01' else ['symbols','text','title']:
  checkn=n if comp!='symbols' else 30
  native=Image.fromarray(raw[checkn]).resize((286,508));f=np.array(fun(native,checkn,c));off=np.array(fun(native,checkn,c,[comp]));tests[comp]=int(np.any(f!=off,2).sum());assert tests[comp]>0
 return {'id':c['id'],'file':path.relative_to(P).as_posix(),'sha256':core.file_sha(path),'frameCount':frames,'sourceRange':c['sourceRange'],'rawRange':[c['rawStart'],c['rawStart']+frames/30],'componentAblationChangedPixels':tests,'completeOccurrence':True}

def main():
 assert load(P/'.pipeline/state.json')['stages'][3]['status']=='active'
 cfgs=prepare();rows=[render(c) for c in cfgs];core.dump(O/'manifest.json',{'groups':rows,'status':'complete-group-trials-not-accepted','rawInput':load(P/'source/pilot/new-input/manifest.json'),'visualAndSubtitleSharedClock':True,'notUsed':'old cleaned presenter clips, rejected pseudo replicas, reference glyph pixels'})
 old=P/'render/pilot/index.html';(P/'reviews/panel-before-complete01-02.html').write_text(old.read_text('utf-8'),'utf-8')
 head=old.read_text('utf-8').split('<main>')[0];page=head+'<main><h1>完整动效组 01 / 02</h1><p>每组同时重建画面、字幕及表达接力；内部图层可独立编辑。当前为完整组试作，尚未验收。</p>'
 for c in cfgs:
  ref='cg01' if c['id']=='01' else 'cg02';name='暗角＋工作图片＋问句揭晓' if c['id']=='01' else '警示符号前景＋字幕接力＋警惕快钱标题'
  desc='新口播00:00.000–00:05.800：加班熬夜、收入留不住。' if c['id']=='01' else '新口播00:29.300–00:32.100：警惕短期快速赚钱的诱惑。金币换成警示符号，保留下落、旋转、近景模糊及标题接力。'
  page+=f'<article style="margin:28px 0"><h2>{c["id"]} · {name}</h2><p>{desc}</p><div class="columns"><section><h2>原对标完整组</h2><video controls muted playsinline preload="auto" src="../../observations/accepted-review/{ref}/reference-clip.mp4"></video></section><section><h2>新口播完整组复现</h2><video controls playsinline preload="auto" src="complete01-02/group-{c["id"]}.mp4?revision=complete-r1"></video></section></div><button onclick="playPair(this)">两条从头播放</button><button onclick="this.closest(\'article\').querySelectorAll(\'video\').forEach(v=>v.pause())">暂停</button><small>参考2.2秒；新片按语义保留时长，不变速。组件和素材差异尚待复审。</small></article>'
 page+='<small>03-pilot｜画面和字幕为同一完整组共同复现；未把组件试验当作整组通过。</small></main><script>async function playPair(b){for(const v of b.closest("article").querySelectorAll("video")){v.currentTime=0;await v.play();}}</script></html>'
 old.write_text(page,'utf-8');print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
