from pathlib import Path
import json,hashlib,subprocess
import numpy as np,onnxruntime as ort
from PIL import Image
P=Path.cwd();S=P/'source/pilot';M=S/'matte-N02';M.mkdir(exist_ok=True)
K=Path('C:/Users/Administrator/.codex/skills/motion-replication-pipeline');raw=K/'assets/migration-demo/talking-head-raw.mp4'
models=list((K/'assets/approved-case-wechat/approved-v1/snapshot').rglob('rvm.onnx'));assert models;model=models[0]
options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1;s=ort.InferenceSession(str(model),options,providers=['CPUExecutionProvider']);rec=[np.zeros((1,1,1,1),np.float32) for _ in range(4)]
start=19.48;N=93;warm=12;W,H=628,1118
proc=subprocess.Popen(['ffmpeg','-v','error','-ss',str(start-warm/30),'-i',str(raw),'-frames:v',str(N+warm),'-vf','fps=30,scale=628:1118','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
rows=[]
for k in range(N+warm):
 b=proc.stdout.read(W*H*3);assert len(b)==W*H*3;a=np.frombuffer(b,np.uint8).reshape(H,W,3);fgr,pha,*rec=s.run(None,dict(src=a.transpose(2,0,1)[None].astype(np.float32)/255,r1i=rec[0],r2i=rec[1],r3i=rec[2],r4i=rec[3],downsample_ratio=np.array([.35],np.float32)))
 if k<warm:continue
 n=k-warm;im=Image.fromarray(np.dstack((np.uint8(np.clip(fgr[0].transpose(1,2,0),0,1)*255),np.uint8(np.clip(pha[0,0],0,1)*255)))).resize((284,504),Image.Resampling.LANCZOS);file=M/f'{n:04d}.png';im.save(file);rows.append({'frame':n,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
assert proc.wait()==0
(M/'manifest.json').write_text(json.dumps({'raw':str(raw),'rawStart':start,'model':str(model),'modelSha256':hashlib.sha256(model.read_bytes()).hexdigest(),'warmup':12,'downsample':.35,'frames':rows},indent=2),'utf-8');print('N02 alpha93frames generated')
