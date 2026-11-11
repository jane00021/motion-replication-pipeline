from pathlib import Path
import sys,json,copy,hashlib
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[4];sys.path.insert(0,str(P/'source/pilot'))
from components import circle_batch as component,runtime
S=P/'source/pilot/batches/circle';R=P/'reviews/batches/circle';O=P/'render/pilot/batches/circle'
def load(p):return json.loads(Path(p).read_text('utf-8'))
def dump(p,c):Path(p).write_text(json.dumps(c,ensure_ascii=False,indent=2),'utf-8')
raw=Image.open(R/'raw-face.png').convert('RGB');checks=[]
for row in load(O/'manifest.json')['groups']:
 id=row['occurrence'];c=load(P/row['input']);recipe=load(P/row['recipe']);runtime.validate_recipe(recipe)
 # Every recipe invokes the exact shared runtime; test independent slot reconstruction.
 frame=min(c['frames']-1,round(c['frames']*.55));layers=runtime.layers(recipe,raw,frame,c);composed=runtime.compose(recipe,raw,frame,c);manual=Image.new('RGBA',(286,508))
 for key in recipe['layerOrder']:
  if key in layers:manual.alpha_composite(layers[key])
 assert np.array_equal(composed,manual)
 n=frame
 if c['subtitleFamily']=='t08':n=c['subtitle']['events']['subject']+6
 a=runtime.compose(recipe,raw,n,c);changed=copy.deepcopy(c)
 key={'t08':'subject','t09':'tag','t10':'left','t11':'warning','t12':'left'}[c['subtitleFamily']];changed['subtitle']['text'][key]='测试'
 b=runtime.compose(recipe,raw,n,changed);assert not np.array_equal(a,b)
 sub=component.render_subtitle(c['subtitleFamily'],n,c);disabled=component.render_subtitle(c['subtitleFamily'],n,c,['text']);assert disabled=={}
 assert all(layer.getpixel((0,0))[3]==0 and layer.getpixel((285,507))[3]==0 for layer in sub.values())
 bad=copy.deepcopy(recipe);bad['components']['visual']['sha256']='0'*64
 try:runtime.validate_recipe(bad)
 except ValueError:hash_rejected=True
 else:raise AssertionError('stale source not rejected')
 checks.append({'occurrence':id,'runtimeRecipeValid':True,'slotRecomposePixelEqual':True,'editedTextChangesPixels':True,'subtitleDisabledEmpty':True,'subtitleCornersTransparent':True,'staleHashRejected':True,'visualFamily':'v04','subtitleFamily':c['subtitleFamily'],'mediaSha256':row['sha256']})
assert len({load(P/r['recipe'])['components']['visual']['entrypoint'] for r in load(O/'manifest.json')['groups']})==1
assert len({load(S/f'{id}-recipe.json')['components']['subtitle']['entrypoint'] for id in ['cg11','cg13','cg16']})==1
dump(R/'reuse-checks.json',{'checks':checks,'visualImplementationCount':1,'subtitleImplementationCount':5,'sameFamilyNumberOccurrences':['cg11','cg13','cg16'],'userApproved':False,'stageAccepted':False})
print(json.dumps({'groups':len(checks),'technicalReuseChecks':True}))
