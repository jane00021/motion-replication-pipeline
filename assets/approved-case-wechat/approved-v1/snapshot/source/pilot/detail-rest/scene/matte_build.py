import sys,json,subprocess,hashlib
from pathlib import Path
import numpy as np,onnxruntime as ort,cv2
from PIL import Image,ImageDraw
P=Path.cwd();S=P/'source/pilot/detail-rest/scene';R=P/'reviews/detail-rest/scene';M=S/'matte';M.mkdir(exist_ok=True)
s=ort.SessionOptions();s.intra_op_num_threads=2;s.inter_op_num_threads=1;model=S/'models/rvm.onnx';session=ort.InferenceSession(str(model),s,providers=['CPUExecutionProvider'])
source=json.loads((P/'source/pilot/new-input/manifest.json').read_text('utf-8'))['path'];N=146;W,H=628,1118
# Warm up recurrent state with preceding 12 frames so first visible frame is settled.
start=24.466667-12/30;dec=subprocess.Popen(['ffmpeg','-v','error','-threads','2','-ss',str(start),'-i',source,'-frames:v',str(N+12),'-vf','fps=30,scale=628:1118','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
rec=[np.zeros((1,1,1,1),np.float32) for _ in range(4)];stats=[]
for k in range(N+12):
 b=dec.stdout.read(W*H*3);assert len(b)==W*H*3;a=np.frombuffer(b,np.uint8).reshape(H,W,3);src=a.transpose(2,0,1)[None].astype(np.float32)/255
 fgr,pha,*rec=session.run(None,dict(src=src,r1i=rec[0],r2i=rec[1],r3i=rec[2],r4i=rec[3],downsample_ratio=np.array([.35],np.float32)))
 if k<12:continue
 n=k-12;alpha=np.uint8(np.clip(pha[0,0],0,1)*255);foreground=np.uint8(np.clip(fgr[0].transpose(1,2,0),0,1)*255);rgba=np.dstack((foreground,alpha));im=Image.fromarray(rgba);im.save(M/f'{n:04d}.png');stats.append({'frame':n,'alphaArea':int((alpha>127).sum()),'softAlphaPixels':int(((alpha>1)&(alpha<254)).sum())})
 if n in [0,1,2,35,70,105,143,144,145]:
  im.save(R/f'matte-f{n:03d}.png');raw=Image.fromarray(a);raw.save(R/f'raw-f{n:03d}.jpg')
 if n%30==0:print('matte',n,flush=True)
assert dec.wait()==0
(S/'models/provenance.json').write_text(json.dumps({'model':'Robust Video Matting MobileNetV3 fp32','author':'PeterL1n','source':'https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx','mirror':'https://ghfast.top/https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx','sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'runtime':'onnxruntime CPU 2 threads','rawInputResolution':[628,1118],'downsampleRatio':.35,'recurrentWarmupFrames':12,'rgbaUsesModelForeground':True},indent=2),encoding='utf-8');(R/'matte-stats.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
