from pathlib import Path
import sys,json,hashlib,copy
P=Path(__file__).resolve().parents[4];sys.path.insert(0,str(P/'source/pilot'))
import numpy as np,cv2
from PIL import Image
from fontTools.ttLib import TTFont
from components.runtime import validate_recipe,layers,compose
from components.circle_batch import render_subtitle
from components.detail_tools import glyph_tile
S=P/'source/pilot/detail-rest/circle';O=P/'render/pilot/detail-rest/circle';R=P/'reviews/detail-rest/circle'
def load(p):return json.loads(Path(p).read_text('utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,c):Path(p).write_text(json.dumps(c,ensure_ascii=False,indent=2),'utf-8')
raw=Image.open(P/'reviews/batches/circle/raw-face.png').convert('RGB');checks=[];fonts=[]
for row in load(O/'manifest.json')['groups']:
 c=load(P/row['input']);r=load(P/row['recipe']);validate_recipe(r);id=row['occurrence'];n=round(c['frames']*.6)
 roles=dict(c['typeRoles'])
 if 'numberRole' in c:roles['number']=c['numberRole']
 if 'tagRole' in c:roles['tag']=c['tagRole']
 for role,spec in roles.items():
  font=TTFont(spec['path'],fontNumber=0,lazy=True);cmap=font.getBestCmap();font.close();text=c['subtitle']['text'][role]
  if not text:continue
  assert all(ord(ch) in cmap for ch in text),(id,role,text)
  im,(w,h)=glyph_tile(text,json.dumps(spec,sort_keys=True));fonts.append({'occurrence':id,'role':role,'text':text,'font':spec['path'],'fontSha256':sha(spec['path']),'inkWidth':w,'inkHeight':h,'anchorX':spec['anchorX'],'inkY':spec['inkY'],'fill':spec['fill'],'shadow':spec['shadow'],'glyphCoverage':True})
 d=layers(r,raw,n,c);m=Image.new('RGBA',(286,508))
 for k in r['layerOrder']:
  if k in d:m.alpha_composite(d[k])
 assert np.array_equal(m,compose(r,raw,n,c))
 changed=copy.deepcopy(c);key={'t08':'subject','t09':'tag','t10':'left','t11':'warning','t12':'left'}[c['subtitleFamily']];changed['subtitle']['text'][key]='测试';assert not np.array_equal(compose(r,raw,n,c),compose(r,raw,n,changed))
 sub=render_subtitle(c['subtitleFamily'],n,c);assert all(im.getchannel('A').getbbox() is None or im.getpixel((0,0))[3]==0 for im in sub.values());assert render_subtitle(c['subtitleFamily'],n,c,['text'])=={}
 cap=cv2.VideoCapture(str(P/row['file']));count=0;dims=[]
 while True:
  ok,a=cap.read()
  if not ok:break
  count+=1
  if not dims:dims=[a.shape[1],a.shape[0]]
 cap.release();assert count==c['frames'];assert sha(P/row['file'])==row['sha256'];checks.append({'occurrence':id,'decodedFrames':count,'size':dims,'recipeValid':True,'fontCoverage':True,'parameterEditChangesPixels':True,'independentLayerRecomposePixelEqual':True,'subtitleDisabledEmpty':True,'newInputFileSha256':row['sha256'],'continuousVisualPlayback':False,'audioListening':False,'userApproved':False})
approval=load(P/'reviews/detail-two/user-approval.json')['groups'][1];assert sha(P/approval['file'])==approval['sha256'];assert sha(P/approval['input'])==approval['inputSha256'];assert sha(P/approval['recipe'])==approval['recipeSha256']
dump(R/'qa.json',{'groups':checks,'cg13ApprovedMediaInputRecipeHashesUnchanged':True,'cg13LayerRegression':load(R/'cg13-regression.json'),'implementationReuse':{'visualV04':6,'subtitleT09':['cg11','cg16'],'t09AlsoReferencesApprovedCg13':True},'actualInspection':'逐阶段过程表实际视觉检查＋完整编码解码；未把技术检查称为用户观感认可','stageAccepted':False})
dump(S/'fonts-and-ink.json',fonts);print('six groups QA, font coverage, referenced-layer recompose, cg13 unchanged: passed')
