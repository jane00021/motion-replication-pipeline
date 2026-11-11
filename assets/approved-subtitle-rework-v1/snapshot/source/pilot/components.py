"""Reference-specific mechanisms; transferable parameters, no source-video pixels in text layers."""
from pathlib import Path
from functools import lru_cache
import json,math,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
P=Path(__file__).resolve().parents[2];W,H=284,504;S=4

def progress(n,a,b):return max(0,min(1,(n-a)/max(1,b-a)))
def alpha(im,op):
 im=im.copy();im.putalpha(im.getchannel('A').point(lambda x:round(x*max(0,min(1,op)))));return im
def blank():return Image.new('RGBA',(W,H))
@lru_cache(maxsize=256)
def text_tile(text,style_json):
 s=json.loads(style_json);font=ImageFont.truetype(s['font'],round(s['size']*4));bb=font.getbbox(text);mask=Image.new('L',(bb[2]-bb[0]+16,bb[3]-bb[1]+16));ImageDraw.Draw(mask).text((8-bb[0],8-bb[1]),text,font=font,fill=255,stroke_width=round(s.get('weight',0)*4));mask=mask.crop(mask.getbbox())
 if s.get('inkWidth') and s.get('inkHeight'):mask=mask.resize((round(s['inkWidth']*4),round(s['inkHeight']*4)),Image.Resampling.LANCZOS)
 if s.get('skew'):
  sk=s['skew'];mask=mask.transform((mask.width+round(mask.height*abs(sk)),mask.height),Image.Transform.AFFINE,(1,sk,-mask.height*sk,0,1,0),Image.Resampling.BICUBIC)
 pad=24;out=Image.new('RGBA',(mask.width+48,mask.height+48));shadow=Image.new('L',out.size);shadow.paste(mask,(pad+round(s.get('shadowX',.6)*4),pad+round(s.get('shadowY',.8)*4)));layer=Image.new('RGBA',out.size,'#08090c');layer.putalpha(shadow.filter(ImageFilter.GaussianBlur(s.get('shadowBlur',.35)*4)).point(lambda a:round(a*.85)));out.alpha_composite(layer)
 color=Image.new('RGBA',mask.size,s.get('fill','#ffffff'));color.putalpha(mask);out.alpha_composite(color,(pad,pad))
 return out.resize((round(out.width/4),round(out.height/4)),Image.Resampling.LANCZOS),(mask.width/4,mask.height/4)

def puttext(out,text,style,cx,y,op=1,scale=1,glow=0):
 tile,(w,h)=text_tile(text,json.dumps(style,sort_keys=True));pad=6
 if glow:
  g=Image.new('RGBA',tile.size,'#ffe38a');g.putalpha(tile.getchannel('A').filter(ImageFilter.GaussianBlur(3)).point(lambda a:round(min(255,a*1.8*glow))));out.alpha_composite(g,(round(cx-w/2-pad),round(y-pad)))
 if scale!=1:tile=tile.resize((round(tile.width*scale),round(tile.height*scale)),Image.Resampling.BICUBIC)
 out.alpha_composite(alpha(tile,op),(round(cx-w*scale/2-pad*scale),round(y-(h*(scale-1))/2-pad*scale)))

def visual(family,raw,n,c):
 if family=='V01':
  v=c['visual'];yy,xx=np.mgrid[:H,:W];r=np.sqrt(((xx-v['center'][0])/v['radii'][0])**2+((yy-v['center'][1])/v['radii'][1])**2);op=v['opacity']*(1-progress(n,*v['exit']));a=np.zeros((H,W,4),np.uint8);a[:,:,3]=np.uint8(np.clip((r-.60)/.48,0,1)*op*255)
  return {'presenter':raw.convert('RGBA'),'focus':Image.fromarray(a)}
 if family=='V14':
  v=c['visual'];q=progress(n,*v['dim']);out={'background':ImageEnhance.Brightness(raw.convert('RGB')).enhance(1-q*(1-v['brightness'])).convert('RGBA')}
  if n>=v['dim'][0]:
   fg=Image.open(P/c['matteFrames']/f'{n:04d}.png').convert('RGBA');out['foreground']=fg
  return out
 raise ValueError(family)

def subtitle(family,n,c):
 s=c['subtitle'];out=blank()
 if family=='T01':
  if n<s['bodyIn']:return {'speech':out}
  emph=progress(n,*s['emphasisIn']);prefix=s['prefix'];focus=s['emphasis'];bs=s['bodyStyle'];fs=s['focusStyle'];_,(pw,ph)=text_tile(prefix,json.dumps(bs,sort_keys=True));_,(fw,fh)=text_tile(focus,json.dumps(bs,sort_keys=True));_,(ew,eh)=text_tile(focus,json.dumps(fs,sort_keys=True));ew=fw+(ew-fw)*emph;total=pw+ew+2;x=(W-total)/2;puttext(out,prefix,bs,x+pw/2,s['y'],progress(n,s['bodyIn']-1,s['bodyIn']+2))
  if emph<=0:puttext(out,focus,bs,x+pw+2+fw/2,s['y'])
  else:
   age=n-s['emphasisIn'][0];peak=math.sin(progress(age,0,8)*math.pi)*.1;puttext(out,focus,fs,x+pw+2+ew/2,s['y']-(eh-ph)/2,scale=1+peak,glow=.9*(1-progress(age,2,12)))
  return {'speech':out}
 if family=='T02':
  for cue in s['cues']:
   if cue['in']<=n<cue['out']:
    a=cue['white'];b=cue['gold'];bs=s['bodyStyle'];gs=s['goldStyle'];_,(wa,ha)=text_tile(a,json.dumps(bs,sort_keys=True));_,(wb,hb)=text_tile(b,json.dumps(gs,sort_keys=True));x=(W-wa-wb-1)/2;puttext(out,a,bs,x+wa/2,s['y']);puttext(out,b,gs,x+wa+1+wb/2,s['y'])
  title=blank();e=s['titleClock']
  if n>=e[0]:
   q=progress(n,e[0],e[1]);settle=progress(n,e[1],e[2]);y=s['titleY']-60*(1-q) if n<e[1] else s['titleY']+5*(1-settle);puttext(title,s['title'],s['titleStyle'],142,y,progress(n,e[0]-1,e[0]+3),glow=.05)
  return {'behindTitle':title,'speech':out}
 raise ValueError(family)

def compose(recipe,raw,n,c,disable=()):
 ls={}
 if 'visual' not in disable:ls.update({'visual.'+k:v for k,v in visual(recipe['visualFamily'],raw,n,c).items()})
 if 'subtitle' not in disable:ls.update({'subtitle.'+k:v for k,v in subtitle(recipe['subtitleFamily'],n,c).items()})
 out=blank()
 for name in recipe['layerOrder']:
  if name in ls:out.alpha_composite(ls[name])
 return out
