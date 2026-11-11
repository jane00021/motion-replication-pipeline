from pathlib import Path
import sys,importlib,copy,json,subprocess
import numpy as np
from PIL import Image,ImageDraw
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'));R=importlib.import_module('batch_runtime');V=importlib.import_module('subtitle-rework.closing.provider')
S=P/'source/pilot/subtitle-rework/closing';O=P/'render/pilot/subtitle-rework/closing';Q=P/'reviews/pilot/subtitle-rework/closing';groups=[]
def decode(path,n):
 r=subprocess.run(['ffmpeg','-v','error','-threads','1','-ss',str(n/30),'-i',str(path),'-frames:v','1','-vf','scale=284:504','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True);return Image.frombytes('RGB',(284,504),r.stdout)
for oid,start,end in [('N21',2665,2710),('N22',2753,2794),('N24',2855,2950)]:
 c=R.load(S/(oid+'-input.json'));old=R.load(P/f'source/pilot/batches/prompts/{oid}-recipe.json');vref=next(x for x in old['components'] if x['kind']=='visual');refs=[vref,{'kind':'subtitle','id':'closing-measured','entrypoint':'subtitle-rework.closing.provider:subtitle','source':'source/pilot/subtitle-rework/closing/provider.py'}]
 recipe={'occurrence':oid,'components':refs,'layerOrder':['base.presenter','subtitle.closingText'],'verificationState':'trial','supportBindings':{'source/pilot/components.py':R.sha(P/'source/pilot/components.py'),'source/pilot/subtitle-rework/N07/providers.py':R.sha(P/'source/pilot/subtitle-rework/N07/providers.py')}}
 for st in c['subtitle']['styles'].values():recipe['supportBindings'][st['font']]=R.sha(st['font'])
 r=R.bind(recipe,S/(oid+'-input.json'));rp=S/(oid+'-recipe.json');R.dump(rp,r);record=R.run_group(rp,output=O/(oid+'-applied.mp4'));record['components']=r['components'];groups.append(record);R.dump(O/'manifest.json',{'groups':groups,'accepted':False,'stage':'03-pilot'})
 same=R.load(S/(oid+'-same-word.json'));count=same['frameCount'];samepath=O/(oid+'-same-word.mp4');enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-s','284x504','-r','30','-pix_fmt','rgb24','-i','pipe:0','-an','-c:v','libx264','-threads','2','-crf','14','-pix_fmt','yuv420p',str(samepath)],stdin=subprocess.PIPE)
 adir=O/(oid+'-rgba');adir.mkdir(exist_ok=True);alphas=[]
 for n in range(max(count,c['frameCount'])):
  if n<count:
   im=Image.new('RGBA',(284,504),'#283038');im.alpha_composite(V.subtitle('closing-measured',n,same)['closingText']);enc.stdin.write(im.convert('RGB').tobytes())
  if n<c['frameCount']:
   tile=V.subtitle('closing-measured',n,c)['closingText'];tile.save(adir/f'{n:04d}.png');alphas.append({'frame':n,'alphaBBox':tile.getchannel('A').getbbox()})
 enc.stdin.close();assert enc.wait()==0;subprocess.run(['ffmpeg','-v','error','-i',str(samepath),'-f','null','-'],check=True);R.dump(adir/'sequence.json',{'canvas':[284,504],'fps':30,'frames':alphas,'sourcePixelsUsed':False})
 ns=([0,2,4,6,8,12,30,41] if oid=='N21' else [0,1,3,5,7,12,25,40] if oid=='N22' else [0,4,10,24,31,36,42,85]);b=Image.new('RGB',(284*8,230*2),'#202830');d=ImageDraw.Draw(b)
 for i,n in enumerate(ns):
  src=Image.open(P/f'observations/frame-audit/frames/{start+n+1:05d}.jpg').crop((0,290,284,460));cand=decode(samepath,n).crop((0,290,284,460));b.paste(src,(i*284,0));b.paste(cand,(i*284,230));d.text((i*284+2,175),f'source local {n}',fill='white');d.text((i*284+2,405),f'encoded same local {n}',fill='white')
 b.save(Q/(oid+'-same-clock-process.jpg'))
 # Same original-word settle frame, static glyph/material evidence beside native reference.
 nn=12 if oid!='N24' else 42;static=Image.new('RGB',(568,230),'#283038');static.paste(Image.open(P/f'observations/frame-audit/frames/{start+nn+1:05d}.jpg').crop((0,290,284,460)),(0,0));static.paste(decode(samepath,nn).crop((0,290,284,460)),(284,0));static.save(Q/(oid+'-same-word-static.jpg'))
 # Editable text and visible shadow actually change rendered pixels.
 changed=copy.deepcopy(c);mode=c['subtitle']['mode']
 if mode=='typed-relay':changed['subtitle']['second'][1]['text']='逐步变好'
 else:changed['subtitle']['conclusion']='能够慢慢进步'
 n=round(c['frameCount']*.65);a=V.subtitle('',n,c)['closingText'];z=V.subtitle('',n,changed)['closingText'];assert np.any(np.asarray(a)!=np.asarray(z));off=copy.deepcopy(c)
 for st in off['subtitle']['styles'].values():st['shadow']['opacity']=0
 b=V.subtitle('',n,off)['closingText'];diff=int(np.any(np.asarray(a)!=np.asarray(b),axis=2).sum());assert diff>0
 R.dump(Q/(oid+'-verification.json'),{'frames':c['frameCount'],'fullDecode':True,'sameClockEncodedReferenceWords':True,'transparentSequence':True,'editableTextIntervention':True,'shadowPixelDifference':diff,'newInputSha256':R.sha(S/(oid+'-input.json')),'mediaSha256':record['sha256'],'sameWordSha256':R.sha(samepath),'fonts':[{**st,'sha256':R.sha(st['font'])} for st in c['subtitle']['styles'].values()],'continuousVisualWatch':False,'audioListening':False,'userApproved':False})
 print(oid+' ready',flush=True)
