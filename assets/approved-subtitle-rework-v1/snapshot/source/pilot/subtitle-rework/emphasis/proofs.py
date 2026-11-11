from pathlib import Path
import sys,importlib,json,copy,subprocess,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'));import batch_runtime as rt
pr=importlib.import_module('subtitle-rework.emphasis.providers');S=P/'source/pilot/subtitle-rework/emphasis';R=P/'reviews/pilot/subtitle-rework/emphasis';O=P/'render/pilot/subtitle-rework/emphasis';manifest=rt.load(O/'manifest.json')
for g in manifest['groups']:
 id=g['occurrence'];c=rt.load(P/g['input']);r=rt.load(P/g['recipe']);N=c['frames'];fam=r['components'][-1]['id'];sf,ef=g['sourceRange'];same=copy.deepcopy(c);same['frames']=ef-sf
 if id=='N13':same['text']={'headline':'真正作用','english':'The real function'};same['roles']['headline'].update(inkWidth=190,inkHeight=53)
 else:same['text']={'sentence':'再不睡觉我就要炸掉了'}
 rt.dump(R/f'{id}-same-word-input.json',same)
 # Real full-frame RGBA sequence, independent text roles no native raw pixels.
 rows=[];adir=O/f'{id}-full-rgba';adir.mkdir(exist_ok=True)
 for n in range(N):
  ls=pr.subtitle(fam,n,c);out=Image.new('RGBA',(284,504))
  for slot in ['english','headline','goldSentence']:
   if slot in ls:out.alpha_composite(ls[slot])
  fp=adir/f'{n:04d}.png';out.save(fp);rows.append({'frame':n,'sha256':rt.sha(fp),'alphaBBox':out.getchannel('A').getbbox()})
 rt.dump(adir/'sequence.json',{'width':284,'height':504,'fps':30,'frames':rows,'referencePixels':False})
 # Same-word actual encoded output on neutral viewing background, not baseline.
 sameout=O/f'{id}-same-word-calibration.mp4';enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-s','284x504','-pix_fmt','rgb24','-r','30','-i','pipe:0','-c:v','libx264','-threads','2','-crf','15','-pix_fmt','yuv420p',str(sameout)],stdin=subprocess.PIPE)
 for n in range(same['frames']):
  im=Image.new('RGBA',(284,504),'#282a2e');ls=pr.subtitle(fam,n,same)
  for slot in ['english','headline','goldSentence']:
   if slot in ls:im.alpha_composite(ls[slot])
  enc.stdin.write(im.convert('RGB').tobytes())
 enc.stdin.close();assert enc.wait()==0;subprocess.run(['ffmpeg','-v','error','-i',str(sameout),'-f','null','-'],check=True)
 frames=[0,2,4,7,12,21] if id=='N13' else [0,6,12,24,36,47];cap=cv2.VideoCapture(str(sameout));sheet=Image.new('RGB',(284*6,1040),'#20252a');draw=ImageDraw.Draw(sheet)
 for k,n in enumerate(frames):
  ref=Image.open(P/f'observations/frame-audit/frames/{sf+n+1:05d}.jpg');sheet.paste(ref,(k*284,24));cap.set(cv2.CAP_PROP_POS_FRAMES,n);ok,a=cap.read();assert ok;sheet.paste(Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)),(k*284,536));draw.text((k*284+4,4),f'ref/local {sf+n}/{n}',fill='white')
 cap.release();sheet.save(R/f'{id}-same-word-encoded-process.jpg')
 cap=cv2.VideoCapture(str(P/g['file']));sheet=Image.new('RGB',(1704,1040),'#20252a');draw=ImageDraw.Draw(sheet)
 for k,n in enumerate([0,4,N//4,N//2,N*3//4,N-1]):
  f=sf+round(n/max(1,N-1)*(ef-sf-1));ref=Image.open(P/f'observations/frame-audit/frames/{f+1:05d}.jpg');sheet.paste(ref,(k*284,24));cap.set(cv2.CAP_PROP_POS_FRAMES,n);ok,a=cap.read();assert ok;sheet.paste(Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((284,504)),(k*284,536));draw.text((k*284+4,4),f'ref {f}/ new {n} phase',fill='white')
 cap.release();sheet.save(R/f'{id}-encoded-complete-compare.jpg');g['evidence']={'sameWord':f'reviews/pilot/subtitle-rework/emphasis/{id}-same-word-encoded-process.jpg','completeCompare':f'reviews/pilot/subtitle-rework/emphasis/{id}-encoded-complete-compare.jpg','rgba':f'render/pilot/subtitle-rework/emphasis/{id}-full-rgba/sequence.json'}
 # Visual refs byte-exact compared to old package, ensure this is only subtitle work.
 oldr=rt.load(P/f'source/pilot/batches/prompts/{id}-recipe.json');oldc=rt.load(P/f'source/pilot/batches/prompts/{id}-input.json');raw=Image.new('RGB',(284,504),'#777777')
 for n in [0,5,N-1]:
  oldls=rt.layers(oldr,raw,n,oldc);newls=rt.layers(r,raw,n,c)
  for key in newls:
   if not key.startswith('subtitle.'):assert newls[key].tobytes()==oldls[key].tobytes(),key
 g['visualRegression']='unchanged same inputs/reference providers and layer bytes on frames0,5,last'
rt.dump(O/'manifest.json',manifest)
