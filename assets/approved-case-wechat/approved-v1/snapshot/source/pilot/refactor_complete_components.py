"""One-time migration: move actual implementations, never fork them into recipes."""
from pathlib import Path
import ast,json,shutil,hashlib
P=Path(__file__).resolve().parents[2];root=P/'source/pilot';old=root/'complete_groups.py';text=old.read_text('utf-8');tree=ast.parse(text)
nodes={n.name:ast.get_source_segment(text,n) for n in tree.body if isinstance(n,ast.FunctionDef)}
D=root/'components';D.mkdir(exist_ok=True);(D/'__init__.py').write_text('"""Pilot component sources; not an accepted production library."""\n','utf-8')
backup=P/'reviews/complete01-02/pre-component-refactor.py'
if not backup.exists():shutil.copy2(old,backup)
header='''from pathlib import Path
import json,math,copy,random
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
import t04_render as core
import render_migration as media
P=core.P
'''
common=header+'\n\n'.join(nodes[n] for n in ['load','prog','text_tile','put','reveal'])+'\n'
# Common style is a referenced source of truth; component parameters can override roles deliberately.
common=common.replace("load(P/'source/pilot/t04/input-A.json')['roles']['body']","load(P/'source/pilot/complete01-02/shared-text-style.json')")
(D/'common.py').write_text(common,'utf-8')
style=json.loads((root/'t04/input-A.json').read_text('utf-8'))['roles']['body'];(root/'complete01-02/shared-text-style.json').write_text(json.dumps(style,ensure_ascii=False,indent=2),'utf-8')
visual='from .common import *\n\n'+'\n\n'.join(nodes[n] for n in ['vignette','icon','symbols','reframe_presenter','head_matte'])+'\n'
visual+='''
def render(component_id, raw, frame, parameters, disabled=()):
 n=frame;c=parameters;layers={}
 if component_id=='v01':
  layers['presenter']=raw.convert('RGBA');clock=c['clock'];fade=1-prog(n,*clock['allExit'])
  if 'vignette' not in disabled:layers['focus']=vignette(prog(n,*clock['vignetteIn'])*fade)
  if 'photo' not in disabled:
   photo=Image.open(P/c['asset']).resize((286,153),Image.Resampling.LANCZOS).convert('RGBA')
   photo=ImageEnhance.Brightness(photo).enhance(c.get('photoBrightness',.62))
   yy=np.arange(153)[:,None];a=np.repeat(np.clip(yy/45,0,1),286,axis=1)*255
   photo.putalpha(Image.fromarray(a.astype(np.uint8)));q=prog(n,*clock['photoIn']);layer=Image.new('RGBA',(286,508));put(layer,photo,0,355+(1-q)*75,q*fade);layers['workPhoto']=layer
 elif component_id=='v02':
  presenter=reframe_presenter(raw,c);layers['presenter']=presenter
  if n>=c['clock']['titleStart'] and 'occlusion' not in disabled:
   fg=presenter.copy();fg.putalpha(head_matte(presenter));layers['presenterForeground']=fg
  if 'symbols' not in disabled:layers['symbols']=symbols(n,c)
 else:raise ValueError('Unknown visual component '+component_id)
 return layers
'''
# Symbol asset is an actual file input to the same mechanism, not hardcoded icon identity.
visual=visual.replace("tile=icon()","tile=Image.open(P/c['symbol']['assetPath']).convert('RGBA') if c['symbol'].get('assetPath') else icon()")
(D/'visual.py').write_text(visual,'utf-8')
subtitle='from .common import *\n\n'+nodes['title_tile']+'\n'+'''
def render(component_id, frame, parameters, disabled=()):
 n=frame;c=parameters;layers={}
 if component_id=='t01':
  if 'text' in disabled:return layers
  clock=c['clock'];fade=1-prog(n,*clock['allExit']);layer=Image.new('RGBA',(286,508))
  styles=c.get('textLayout',{})
  first=styles.get('first',{'size':26,'xy':[34,321]});second=styles.get('second',{'size':24,'xy':[34,355]})
  reveal(layer,c['text']['first'],first['size'],first['xy'],n-clock['firstText'][0]);reveal(layer,c['text']['second'],second['size'],second['xy'],n-clock['secondText'][0])
  age=n-clock['questionAndResult'][0]
  if age>=0:
   reveal(layer,c['text']['question'],43,(62,305),age,'#b70923',duration=9)
   reveal(layer,c['text']['result'],28,(105,326),age,'#fffff5',duration=9,dx=35)
  layers['questionText']=core.opacity(layer,fade)
 elif component_id=='t02':
  t=c['clock']
  if n>=t['titleStart'] and 'title' not in disabled:
   tile=title_tile(c['text']['title'],c);age=n-t['titleStart'];entry=prog(n,t['titleStart'],t['titleOvershoot']);settle=prog(n,t['titleOvershoot'],t['titleSettle'])
   y=core.mix(-90,16,1-(1-entry)**3) if n<t['titleOvershoot'] else core.mix(16,c['title']['inkY'],settle)
   title=Image.new('RGBA',(286,508));put(title,tile,c['title']['inkX']-6,y-6,prog(age,-1,3),3*(1-prog(age,0,6)));layers['behindTitle']=title
  if 'text' not in disabled:
   line=c['text']['first'] if n<t['captionChange'] else c['text']['second'];tile,m=text_tile(line,c.get('captionSize',12),'#ffffff');caption=Image.new('RGBA',(286,508));put(caption,tile,(286-m['inkWidth'])/2-8,374-8);layers['speechCaption']=caption
 else:raise ValueError('Unknown subtitle component '+component_id)
 return layers
'''
(D/'subtitle.py').write_text(subtitle,'utf-8')
recipes=root/'complete01-02/recipes';recipes.mkdir(exist_ok=True)
for i,vis,sub,order in [('01','v01','t01',['visual.presenter','visual.focus','visual.workPhoto','subtitle.questionText']),('02','v02','t02',['visual.presenter','subtitle.behindTitle','visual.presenterForeground','visual.symbols','subtitle.speechCaption'])]:
 c=json.loads((root/f'complete01-02/input-{i}.json').read_text('utf-8'))
 events={'01':{'focus':'vignetteIn','image':'photoIn','setup':'firstText','advance':'secondText','takeover':'questionAndResult','exit':'allExit'},'02':{'symbol':'symbolFirst','advance':'captionChange','takeover':'titleStart','settle':'titleSettle','symbolExit':'symbolExitEnd','readEnd':'titleHoldEnd'}}[i]
 recipe={'schema':1,'id':'complete-'+i,'status':'pilot-source-draft','occurrence':'cg'+i,'input':f'source/pilot/complete01-02/input-{i}.json','components':{'visual':{'id':vis,'entrypoint':'components.visual:render','sha256':hashlib.sha256((D/'visual.py').read_bytes()).hexdigest()},'subtitle':{'id':sub,'entrypoint':'components.subtitle:render','sha256':hashlib.sha256((D/'subtitle.py').read_bytes()).hexdigest()}},'commonSha256':hashlib.sha256((D/'common.py').read_bytes()).hexdigest(),'sharedStyle':'source/pilot/complete01-02/shared-text-style.json','sharedStyleSha256':hashlib.sha256((root/'complete01-02/shared-text-style.json').read_bytes()).hexdigest(),'clock':{'fps':30,'frameOrigin':0,'eventsFromInput':events},'layerOrder':order,'missingLayers':'inactive optional slots only; actual component errors raise','requires':['semantic-role-check','font-coverage','full-combination-review'],'completeGroupValidated':False}
 (recipes/f'{i}.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2),'utf-8')
# Retire duplicate implementation. Compatibility methods forward to the same recipe runtime.
legacy=header+"S=P/'source/pilot/complete01-02';O=P/'render/pilot/complete01-02';W,H=628,1118\n"
legacy+='from components.common import load,prog,text_tile,put,reveal\nfrom components.visual import vignette,icon,symbols,reframe_presenter,head_matte\nfrom components.subtitle import title_tile\nfrom components.runtime import compose\n'
legacy+='''def prepare():return [load(S/'input-01.json'),load(S/'input-02.json')]
def group1(raw,n,c,disabled=()):return compose(load(S/'recipes/01.json'),raw,n,c,disabled)
def group2(raw,n,c,disabled=()):return compose(load(S/'recipes/02.json'),raw,n,c,disabled)
'''
legacy+='\n\n'.join(nodes[n] for n in ['render','main'])+"\nif __name__=='__main__':main()\n"
old.write_text(legacy,'utf-8')
print('Moved visual/subtitle implementations; recipes reference exact shared sources.')
if __name__=='__main__':pass
