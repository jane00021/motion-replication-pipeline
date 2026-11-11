from pathlib import Path
import json,hashlib,subprocess
import numpy as np,onnxruntime as ort
from PIL import Image
P=Path(__file__).resolve().parents[2];K=Path('C:/Users/Administrator/.codex/skills/motion-replication-pipeline')
def make_matte(start,frames,folder):
 M=Path(folder);M=M if M.is_absolute() else P/M;M.mkdir(parents=True,exist_ok=True);model=next((K/'assets/approved-case-wechat/approved-v1/snapshot').rglob('rvm.onnx'));raw=K/'assets/migration-demo/talking-head-raw.mp4'
 options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1;session=ort.InferenceSession(str(model),options,providers=['CPUExecutionProvider']);rec=[np.zeros((1,1,1,1),np.float32) for _ in range(4)];warm=min(12,round(start*30));W,H=628,1118
 dec=subprocess.Popen(['ffmpeg','-v','error','-threads','1','-ss',str(start-warm/30),'-i',str(raw),'-frames:v',str(frames+warm),'-vf','fps=30,scale=628:1118','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE);rows=[]
 for k in range(frames+warm):
  data=dec.stdout.read(W*H*3);assert len(data)==W*H*3;a=np.frombuffer(data,np.uint8).reshape(H,W,3);fgr,pha,*rec=session.run(None,dict(src=a.transpose(2,0,1)[None].astype(np.float32)/255,r1i=rec[0],r2i=rec[1],r3i=rec[2],r4i=rec[3],downsample_ratio=np.array([.35],np.float32)))
  if k<warm:continue
  n=k-warm;im=Image.fromarray(np.dstack((np.uint8(np.clip(fgr[0].transpose(1,2,0),0,1)*255),np.uint8(np.clip(pha[0,0],0,1)*255)))).resize((284,504),Image.Resampling.LANCZOS);f=M/f'{n:04d}.png';im.save(f);rows.append({'frame':n,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 assert dec.wait()==0
 manifest={'model':str(model),'modelSha256':hashlib.sha256(model.read_bytes()).hexdigest(),'raw':str(raw),'rawStart':start,'warmup':warm,'downsample':.35,'canvas':[284,504],'frames':rows};(M/'manifest.json').write_text(json.dumps(manifest,indent=2),'utf-8');return manifest
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--start',type=float,required=True);p.add_argument('--frames',type=int,required=True);p.add_argument('--folder',required=True);a=p.parse_args();r=make_matte(a.start,a.frames,a.folder);print('RGBA',len(r['frames']),a.folder)
