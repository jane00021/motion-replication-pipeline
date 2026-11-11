from pathlib import Path
import json,sys,subprocess,hashlib
import numpy as np,onnxruntime as ort
from PIL import Image
P=Path.cwd();S=P/'source/pilot/last-four/opening';S.mkdir(exist_ok=True);M=S/'matte02';M.mkdir(exist_ok=True)
old=P/'source/pilot/detail-rest/scene';model=old/'models/rvm.onnx';source=json.loads((P/'source/pilot/new-input/manifest.json').read_text('utf-8'))['path']
opts=ort.SessionOptions();opts.intra_op_num_threads=2;opts.inter_op_num_threads=1;session=ort.InferenceSession(str(model),opts,providers=['CPUExecutionProvider'])
N=84;W,H=628,1118;warm=12
p=subprocess.Popen(['ffmpeg','-v','error','-ss',str(29.3-warm/30),'-i',source,'-frames:v',str(N+warm),'-vf','fps=30,scale=628:1118','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
rec=[np.zeros((1,1,1,1),np.float32) for _ in range(4)];rows=[]
for k in range(N+warm):
 data=p.stdout.read(W*H*3);assert len(data)==W*H*3;a=np.frombuffer(data,np.uint8).reshape(H,W,3)
 fgr,pha,*rec=session.run(None,dict(src=a.transpose(2,0,1)[None].astype(np.float32)/255,r1i=rec[0],r2i=rec[1],r3i=rec[2],r4i=rec[3],downsample_ratio=np.array([.35],np.float32)))
 if k<warm:continue
 n=k-warm;im=Image.fromarray(np.dstack((np.uint8(np.clip(fgr[0].transpose(1,2,0),0,1)*255),np.uint8(np.clip(pha[0,0],0,1)*255)))).resize((286,508),Image.Resampling.LANCZOS);fp=M/f'{n:04d}.png';im.save(fp);rows.append({'frame':n,'sha256':hashlib.sha256(fp.read_bytes()).hexdigest()})
assert p.wait()==0
(M/'manifest.json').write_text(json.dumps({'model':str(model.relative_to(P)),'modelSha256':hashlib.sha256(model.read_bytes()).hexdigest(),'generator':'source/pilot/last-four/opening/matte.py','sourceRange':[29.3,32.1],'downsampleRatio':.35,'warmup':12,'frames':rows},indent=2),'utf-8');print('84 recurrent alpha frames')
