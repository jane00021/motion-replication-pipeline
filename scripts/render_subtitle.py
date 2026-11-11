"""Render measured editable subtitle roles to RGBA and encoded viewing preview.
No reference-video pixels or original project imports are required.
"""
from pathlib import Path
import argparse, copy, hashlib, json, subprocess
import numpy as np
from PIL import Image
from fontTools.ttLib import TTFont
from subtitle_engine import split_title, emphasis, closing
ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'assets/approved-subtitle-rework-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def resolve(c):
 if isinstance(c,dict):return {k:resolve(v) for k,v in c.items()}
 if isinstance(c,list):return [resolve(v) for v in c]
 if isinstance(c,str) and c.startswith('asset:'):
  p=(CASE/c[6:]).resolve()
  if not p.is_relative_to(CASE.resolve()):raise ValueError('Invalid asset path')
  if not p.is_file():raise FileNotFoundError(p)
  return str(p)
 return c
def render_layers(c,n):
 mechanism=c['mechanism']
 if mechanism=='split-title':return split_title.subtitle('T04',n,c)
 if mechanism=='bilingual-title':return emphasis.subtitle('T08',n,c)
 if mechanism=='gold-wave':return emphasis.subtitle('gold-wave',n,c)
 if mechanism in ('split-line','diagonal-line','typed-relay'):return closing.subtitle('',n,c)
 raise ValueError('Unobserved/unsupported mechanism: '+mechanism)
def combined(c,n):
 out=Image.new('RGBA',(284,504))
 for im in render_layers(c,n).values():out.alpha_composite(im)
 return out
def validate(c):
 if c.get('canvas')!=[284,504]:raise ValueError('Native executor is 284x504; measure in native coordinates and scale the resulting layer uniformly')
 if not 1<=c['frameCount']<=18000:raise ValueError('Invalid frame count')
 m=c['mechanism'];runs=[]
 if m=='split-title':
  s=c['splitSubtitle'];runs=[(s['white'],s['whiteStyle']),(s['gold'],s['goldStyle'])]+[(q['text'],s['setupStyle']) for q in s.get('setupCues',[])]
  if sorted(s.get('entryOrder',list(range(len(s['white'])))))!=list(range(len(s['white']))):raise ValueError('entryOrder must map the current white phrase, not previous character indices')
 elif m=='bilingual-title':runs=[(c['text'][k],c['roles'][k]) for k in ['headline','english']]
 elif m=='gold-wave':runs=[(c['text']['sentence'],c['roles']['sentence'])]
 else:
  s=c['subtitle']
  if s['mode']!=m:raise ValueError('Mechanism and subtitle mode disagree')
  if m=='typed-relay':
   if len(s['first'])!=len(s['clock']['first']):raise ValueError('One measured reveal time required per new character')
   runs=[(s['first'],s.get('firstStyle',s['styles']['gold']))]+[(v['text'],s['styles'][v['role']]) for v in s['second']]
  else:runs=[(s.get('setup',''.join(s.get('setupParts',[]))),s['styles']['white']),(s['conclusion'],s['styles']['gold'])]
 for text,s in runs:
  font=TTFont(s['font'],lazy=True);cmap=font.getBestCmap();font.close()
  missing=[ch for ch in text if not ch.isspace() and ord(ch) not in cmap]
  if missing:raise ValueError('Missing glyphs: '+''.join(missing))
  if ('inkWidth' in s or 'inkHeight' in s) and not c.get('measuredGlyphTransformEvidence'):raise ValueError('Fixed ink resizing requires actual reference evidence; use natural font size for normal captions')
 return runs
def render(c,output,background='#283038'):
 c=resolve(copy.deepcopy(c));validate(c);output=Path(output).resolve()
 if output.exists():raise ValueError('Choose a new output directory; approved output is immutable')
 output.mkdir(parents=True);rgba=output/'rgba';rgba.mkdir();rows=[]
 fps=c.get('fps',30);count=c['frameCount']
 enc=subprocess.Popen(['ffmpeg','-v','error','-f','rawvideo','-s','284x504','-r',str(fps),'-pix_fmt','rgb24','-i','pipe:0','-an','-c:v','libx264','-threads','2','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(output/'preview.mp4')],stdin=subprocess.PIPE)
 try:
  for n in range(count):
   ls=render_layers(c,n);im=Image.new('RGBA',(284,504))
   for name,layer in ls.items():
    assert layer.mode=='RGBA' and layer.size==(284,504)
    dest=output/'roles'/name/f'{n:05d}.png';dest.parent.mkdir(parents=True,exist_ok=True);layer.save(dest);im.alpha_composite(layer)
   dest=rgba/f'{n:05d}.png';im.save(dest);rows.append({'frame':n,'sha256':sha(dest),'alphaBBox':im.getchannel('A').getbbox()})
   bg=Image.new('RGBA',im.size,background);bg.alpha_composite(im);enc.stdin.write(bg.convert('RGB').tobytes())
 finally:enc.stdin.close()
 if enc.wait()!=0:raise RuntimeError('Encoding failed')
 subprocess.run(['ffmpeg','-v','error','-i',str(output/'preview.mp4'),'-f','null','-'],check=True)
 # Re-run after sequential rendering: catches mutation of cached glyphs by reveal masks.
 for n in sorted({0,count//2,count-1}):
  assert np.array_equal(np.asarray(combined(c,n)),np.asarray(Image.open(rgba/f'{n:05d}.png'))),'Sequential/cache inconsistency'
 receipt={'mechanism':c['mechanism'],'frameCount':count,'fps':fps,'canvas':[284,504],'rgba':rows,'previewSha256':sha(output/'preview.mp4'),'fullDecode':True,'sequentialCacheStable':True,'referencePixelsUsed':False,'previewBackgroundOnly':background,'userApproved':False,'visualCalibrationRequired':True,'executorBindings':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'scripts/subtitle_engine').glob('*.py')}}
 (output/'verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),'utf-8')
 return receipt
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--input',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);args=ap.parse_args();c=json.loads(args.input.read_text('utf-8-sig'));r=render(c,args.output);print(json.dumps({k:v for k,v in r.items() if k!='rgba'},ensure_ascii=False))
