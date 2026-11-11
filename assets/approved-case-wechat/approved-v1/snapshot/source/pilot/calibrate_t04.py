"""Compare font-generated glyph masks to source; source pixels never become glyph assets."""
from pathlib import Path
import json,hashlib
import numpy as np, cv2
from PIL import Image,ImageDraw,ImageFont,ImageFilter
P=Path(__file__).resolve().parents[2];O=P/'reviews/t04-calibration';O.mkdir(parents=True,exist_ok=True)
FONTS={'AaYanSong':'D:/SKILL/Motion模板项目/第三套_待输入/artifacts/03-rebuild/assets/fonts/_work/dl/AaYanSong-Regular.ttf','SourceHanHeavy':'C:/Windows/Fonts/Source Han Serif SC Heavy (TrueType).ttf','Song':'C:/Windows/Fonts/simsun.ttc'}
def glyph(text,path,size,weight=0):
    f=ImageFont.truetype(path,round(size*4));b=f.getbbox(text,stroke_width=weight)
    im=Image.new('L',(b[2]-b[0]+16,b[3]-b[1]+16));ImageDraw.Draw(im).text((8-b[0],8-b[1]),text,font=f,fill=255,stroke_width=weight)
    box=im.getbbox();return im.crop(box).resize((round((box[2]-box[0])/4),round((box[3]-box[1])/4)),Image.Resampling.LANCZOS)
def calibrate():
    ref=np.array(Image.open(P/'observations/frame-audit/frames/0349.jpg').convert('RGB'));hsv=cv2.cvtColor(ref,cv2.COLOR_RGB2HSV)
    # Gold has a distinctive chromatic mask; excludes shirt, skin, compression edge halos.
    target=((hsv[:,:,0]>14)&(hsv[:,:,0]<39)&(hsv[:,:,1]>65)&(hsv[:,:,2]>115)).astype(np.uint8)
    target[:365]=0;target[400:]=0;target[:,:138]=0;target[:,262:]=0
    records=[]
    for name,path in FONTS.items():
      best=None
      for sz in np.arange(26,33,.5):
       for weight in [0,1,2]:
        orig=glyph('维持生活',path,sz,weight)
        for ratio in [.94,.97,1.,1.03,1.06]:
         im=orig.resize((round(orig.width*ratio),orig.height),Image.Resampling.LANCZOS)
         mask=(np.array(im)>100).astype(np.float32);area=mask.sum();targetf=target[361:403,130:268].astype(np.float32)
         if mask.shape[0]>targetf.shape[0] or mask.shape[1]>targetf.shape[1]:continue
         intersect=cv2.matchTemplate(targetf,mask,cv2.TM_CCORR)
         sums=cv2.matchTemplate(targetf,np.ones(mask.shape,np.float32),cv2.TM_CCORR)
         score=2*intersect/(area+sums+1e-6);_,val,_,xy=cv2.minMaxLoc(score)
         row={'font':name,'path':path,'size':float(sz),'weight4x':weight,'xRatio':ratio,'inkBBox':[130+xy[0],361+xy[1],130+xy[0]+im.width,361+xy[1]+im.height],'goldMaskDice':val}
         if best is None or val>best['goldMaskDice']:best=row
      records.append(best)
    records.sort(key=lambda r:r['goldMaskDice'],reverse=True)
    (O/'font-search.json').write_text(json.dumps({'method':'native source f348 thresholded gold mask vs generated font masks; not original font identification','candidates':records},ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(records,ensure_ascii=False))
if __name__=='__main__':calibrate()
