from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw
import numpy as np,cv2
import t04_render as r
P=r.P;O=P/'reviews/t04-calibration'
def run(cmd):return subprocess.run(cmd,capture_output=True,check=True)
def decoded(path):
 d=run(['ffmpeg','-v','error','-i',str(path),'-f','rawvideo','-pix_fmt','rgb24','pipe:1']).stdout
 return np.frombuffer(d,np.uint8).reshape(-1,508,286,3)
def compare(label):
 c=json.loads((r.S/'input-same.json').read_text('utf-8'));frames=decoded(r.O/'input-same.mp4');records=[]
 for part,ns in [('entry',[0,1,3,6,11,18,27,30]),('emphasis',[31,32,33,34,36,38,42,48]),('exit',[56,59,60,61,62,63,64,65])]:
  out=Image.new('RGB',(4*572,2*335),'#181d24');d=ImageDraw.Draw(out)
  for j,n in enumerate(ns):
   ref=Image.open(P/'observations/frame-audit/frames'/f'{n+301:04d}.jpg').crop((10,335,276,415)).resize((532,160))
   cand=Image.fromarray(frames[n]).crop((10,335,276,415)).resize((532,160));x=j%4*572;y=j//4*335
   out.paste(ref,(x,y+15));out.paste(cand,(x,y+175));d.text((x+2,y+1),f'local f{n} source / decoded reconstruction',fill='white')
  out.save(O/f'{label}-{part}.jpg',quality=95)
 ref=Image.open(P/'observations/frame-audit/frames/0349.jpg').crop((10,338,276,410)).resize((798,216));cand=Image.fromarray(frames[48]).crop((10,338,276,410)).resize((798,216))
 out=Image.new('RGB',(798,470),'#202631');out.paste(ref,(0,20));out.paste(cand,(0,250));d=ImageDraw.Draw(out);d.text((5,3),'Source same word / native f348',fill='white');d.text((5,234),'Decoded same word / local f48',fill='white');out.save(O/f'{label}-static.jpg',quality=96)
 # Metric only on golden glyph role, not presenter/background differences.
 src=np.array(Image.open(P/'observations/frame-audit/frames/0349.jpg'));dst=frames[48]
 def gold(a):
  h=cv2.cvtColor(a,cv2.COLOR_RGB2HSV);return (h[363:395,139:260,0]>14)&(h[363:395,139:260,0]<39)&(h[363:395,139:260,1]>65)&(h[363:395,139:260,2]>115)
 a,b=gold(src),gold(dst);dice=float(2*(a&b).sum()/max(1,a.sum()+b.sum()))
 r.dump(O/f'{label}-metrics.json',{'goldRoleMaskDice':dice,'metricLimitation':'compressed chroma threshold, does not certify font identity or overall quality','encodedFrames':len(frames)})
 print(json.dumps({'iteration':label,'goldMaskDice':dice}))
if __name__=='__main__':
 import sys;compare(sys.argv[1])
