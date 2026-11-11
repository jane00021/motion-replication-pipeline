from pathlib import Path
import sys,json,subprocess,hashlib,copy
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'));import components as e
S=P/'source/pilot';O=P/'render/pilot';R=P/'reviews/pilot'
def load(p):return json.loads(Path(p).read_text('utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),'utf-8')
assert load(P/'.pipeline/state.json')['stages'][3]['status']=='active'
rows=[]
for oid,start,end in [('N01',0,52),('N02',54,111)]:
 c=load(S/f'{oid}-input.json');r=load(S/f'{oid}-recipe.json');assert sha(S/'components.py')==r['sourceSha256'];assert sha(S/f'{oid}-input.json')==r['inputSha256'];N=c['frames'];alpha=O/(oid+'-subtitle-rgba');alpha.mkdir(exist_ok=True)
 dec=subprocess.Popen(['ffmpeg','-v','error','-ss',str(c['rawStart']),'-i',c['rawSource'],'-frames:v',str(N),'-vf','fps=30,scale=284:504','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
 output=O/(oid+'-applied.mp4');enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-s','284x504','-pix_fmt','rgb24','-r','30','-i','pipe:0','-ss',str(c['rawStart']),'-i',c['rawSource'],'-t',str(N/30),'-map','0:v','-map','1:a:0','-vf','scale=568:1008:flags=lanczos','-c:v','libx264','-threads','2','-crf','15','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(output)],stdin=subprocess.PIPE)
 for n in range(N):
  data=dec.stdout.read(284*504*3);assert len(data)==284*504*3;raw=Image.frombytes('RGB',(284,504),data);im=e.compose(r,raw,n,c);enc.stdin.write(im.convert('RGB').tobytes());sub=e.subtitle(r['subtitleFamily'],n,c)
  for k,v in sub.items():v.save(alpha/f'{n:04d}-{k}.png')
  if n in [0,5,N//3,N//2,round(N*.75),N-1]:im.save(R/f'{oid}-{n:03d}.png')
 enc.stdin.close();assert enc.wait()==dec.wait()==0
 subprocess.run(['ffmpeg','-v','error','-i',str(output),'-f','null','-'],check=True)
 # Exact source-frame trim via filter, then re-encode rather than keyframe copy.
 ref=O/(oid+'-reference.mp4');source=load(P/'project.json')['references'][0]['path'];subprocess.run(['ffmpeg','-v','error','-y','-i',source,'-vf',f'trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS','-an','-c:v','libx264','-threads','2','-crf','15','-pix_fmt','yuv420p','-movflags','+faststart',str(ref)],check=True)
 rows.append({'occurrence':oid,'file':output.relative_to(P).as_posix(),'referenceFile':ref.relative_to(P).as_posix(),'sha256':sha(output),'frameCount':N,'sourceFrames':[start,end],'rawRange':[c['rawStart'],c['rawStart']+N/30],'recipe':r,'input':'source/pilot/'+oid+'-input.json','status':'trial-awaiting-user-review'})
 dump(O/'manifest.json',{'groups':rows,'stage':'03-pilot','approved':False,'stopAfterTwo':True})
 print(oid,'encoded',flush=True)
