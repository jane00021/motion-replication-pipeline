"""Measured foreground title and word-level gold wave; independent roles and clock."""
from functools import lru_cache
from pathlib import Path
import json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import components as base
W,H=284,504
@lru_cache(maxsize=256)
def tile(text,spec_json):
 s=json.loads(spec_json);font=ImageFont.truetype(s['font'],round(s['size']*4));bb=font.getbbox(text);mask=Image.new('L',(bb[2]-bb[0]+32,bb[3]-bb[1]+32));ImageDraw.Draw(mask).text((16-bb[0],16-bb[1]),text,font=font,fill=255,stroke_width=round(s.get('weight',0)*4));bb=mask.getbbox();mask=mask.crop(bb)
 if s.get('inkWidth'):mask=mask.resize((round(s['inkWidth']*4),round(s['inkHeight']*4)),Image.Resampling.LANCZOS)
 pad=24;full=Image.new('L',(mask.width+pad*2,mask.height+pad*2));full.paste(mask,(pad,pad));out=Image.new('RGBA',full.size);sh=s.get('shadow',{})
 shadow=Image.new('L',out.size);shadow.paste(mask,(pad+round(sh.get('dx',1)*4),pad+round(sh.get('dy',1.5)*4)));layer=Image.new('RGBA',out.size,sh.get('color','#12100c'));layer.putalpha(shadow.filter(ImageFilter.GaussianBlur(sh.get('blur',.5)*4)).point(lambda v:round(v*sh.get('opacity',.9))));out.alpha_composite(layer)
 if s.get('outline',0):
  rim=Image.new('RGBA',out.size,s.get('outlineColor','#51461c'));rim.putalpha(full.filter(ImageFilter.MaxFilter(round(s['outline']*4)*2+1)));out.alpha_composite(rim)
 arr=np.zeros((out.height,out.width,4),np.uint8);top=np.array(s.get('top',[253,235,123]));bottom=np.array(s.get('bottom',[190,153,43]));yy=np.clip((np.arange(out.height)-pad)/max(1,mask.height),0,1)
 for y,t in enumerate(yy):arr[y,:,:3]=top*(1-t)+bottom*t
 arr[:,:,3]=np.asarray(full);out.alpha_composite(Image.fromarray(arr));return out.resize((round(out.width/4),round(out.height/4)),Image.Resampling.LANCZOS),(mask.width/4,mask.height/4)
def put(out,text,s,cx,y,scale=1,op=1,blur=0,angle=0):
 im,(w,h)=tile(text,json.dumps(s,sort_keys=True));im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.LANCZOS)
 if blur:im=im.filter(ImageFilter.GaussianBlur(blur))
 if angle:im=im.rotate(angle,Image.Resampling.BICUBIC,expand=True)
 im=base.alpha(im,op);out.alpha_composite(im,(round(cx-im.width/2),round(y+h/2-im.height/2)));return [cx-w*scale/2,y,cx+w*scale/2,y+h*scale]
def interp(n,keys,field):
 if n<=keys[0]['frame']:return keys[0][field]
 for a,b in zip(keys,keys[1:]):
  if n<=b['frame']:
   p=(n-a['frame'])/max(1,b['frame']-a['frame']);return a[field]+(b[field]-a[field])*p
 return keys[-1][field]
def subtitle(family,n,c):
 out=base.blank();roles=c['roles'];motion=c['motion']
 if family=='T08':
  s=interp(n,motion['keys'],'scale');op=interp(n,motion['keys'],'opacity');blur=interp(n,motion['keys'],'blur');y=interp(n,motion['keys'],'y')
  # Red English is actual independent content, not a projected Chinese shadow.
  english=base.blank();put(english,c['text']['english'],roles['english'],142,motion['englishY'],scale=s,op=op,blur=blur*.4)
  put(out,c['text']['headline'],roles['headline'],142,y,scale=s,op=op,blur=blur)
  return {'english':english,'headline':out}
 if family=='gold-wave':
  text=c['text']['sentence'];spec=roles['sentence'];font=ImageFont.truetype(spec['font'],round(spec['size']*4));adv=[font.getlength(ch)/4 for ch in text];total=sum(adv)+motion.get('tracking',0)*(len(text)-1);left=(284-total)/2
  for j,ch in enumerate(text):
   age=n-motion.get('start',0);phase=age*2*math.pi/motion['period']-j*motion['phaseStep'];dy=motion['amplitude']*math.sin(phase);angle=motion['rotation']*math.sin(phase+.4);cx=left+adv[j]/2;put(out,ch,spec,cx,motion['y']+dy,angle=angle);left+=adv[j]+motion.get('tracking',0)
  return {'goldSentence':out}
 raise ValueError(family)
