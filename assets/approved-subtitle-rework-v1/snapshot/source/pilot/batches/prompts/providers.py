"""Unique prompt families. T01 and V01 delegate to user-approved components, never copy them."""
from pathlib import Path
import sys,json,math,copy,random
import cv2
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps
import components as shared
P=Path(__file__).resolve().parents[4];W,H=284,504
blank=shared.blank;progress=shared.progress

def ease(n,a,b):q=progress(n,a,b);return 1-(1-q)**3

def caption(out,text,c,y=333):
 style=c.get('captionStyle',c['subtitle']['bodyStyle']);shared.puttext(out,text,style,142,y)

def circle(raw,size):
 im=ImageOps.fit(raw.crop((31,76,253,298)),(size,size),method=Image.Resampling.LANCZOS).convert('RGBA');mask=Image.new('L',(size*4,size*4));ImageDraw.Draw(mask).ellipse((2,2,size*4-3,size*4-3),fill=255);im.putalpha(mask.resize(im.size,Image.Resampling.LANCZOS));return im

@lru_cache(maxsize=4)
def video_capture(path):return cv2.VideoCapture(str(P/path))
def scene_frame(slot,n,fps=30):
 if isinstance(slot,str):return Image.open(P/slot).convert('RGBA')
 cap=video_capture(slot['path']);srcfps=cap.get(cv2.CAP_PROP_FPS) or 30;frame=round((slot.get('start',0)+n/fps)*srcfps);cap.set(cv2.CAP_PROP_POS_FRAMES,frame);ok,a=cap.read()
 if not ok:raise ValueError('Missing video asset frame '+str(frame))
 return Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).convert('RGBA')

def visual(family,raw,n,c):
 if family=='raw':return {'presenter':raw.convert('RGBA')}
 if family=='V01':return shared.visual(family,raw,n,c)
 if family=='V02':
  out=Image.new('RGBA',(W,H),'#050708');sz=c.get('circleSize',90);im=circle(raw,sz);out.alpha_composite(im,((W-sz)//2,22));d=ImageDraw.Draw(out);d.ellipse(((W-sz)//2,22,(W+sz)//2,22+sz),outline='#fffce9',width=1)
  slots=c['sceneAssets'];idx=0 if n<c['sceneChange'] else 1;art=scene_frame(slots[idx],n if idx==0 else n-c['sceneChange']);q=ease(n,0,10);h=round(310*q);art=ImageOps.fit(art,(W,max(1,h)),method=Image.Resampling.LANCZOS);out.alpha_composite(art,(0,194+310-h));return {'stage':out}
 if family=='V03':
  q=ease(n,0,max(1,c['frames']-1));w=round(90+(284-90)*q);h=round(90+(504-90)*q);x=(284-w)//2;y=round(22*(1-q));crop=np.array([31,76,253,298])*(1-q)+np.array([0,0,284,504])*q;im=ImageOps.fit(raw.crop(tuple(crop)),(w,h),method=Image.Resampling.LANCZOS).convert('RGBA');mask=Image.new('L',(w*4,h*4));ImageDraw.Draw(mask).rounded_rectangle((0,0,w*4-1,h*4-1),radius=round((1-q)*min(w,h)*2),fill=255);im.putalpha(mask.resize((w,h),Image.Resampling.LANCZOS));out=Image.new('RGBA',(W,H),'#050708');out.alpha_composite(im,(x,y));return {'expandingPresenter':out}
 if family=='V15':
  q=ease(n,0,13);s=1+.12*q;im=raw.resize((round(W*s),round(H*s)),Image.Resampling.LANCZOS);x=(im.width-W)//2;y=round((im.height-H)*.36);return {'zoomedPresenter':im.crop((x,y,x+W,y+H)).convert('RGBA')}
 if family=='V07':
  out=blank();op=ease(n,c.get('stickerIn',0),c.get('stickerIn',0)+7)*(1-progress(n,c['frames']-7,c['frames']));kind=c['sticker'];cx,cy=c.get('stickerCenter',[142,57]);scale=.5+.5*ease(n,0,7);tile=sticker(kind,n);tile=tile.resize((round(tile.width*scale),round(tile.height*scale)),Image.Resampling.LANCZOS);out.alpha_composite(shared.alpha(tile,op),(round(cx-tile.width/2),round(cy-tile.height/2)));return {'sticker':out}
 raise ValueError('Unsupported visual family '+family)

def sticker(kind,n):
 im=Image.new('RGBA',(188*4,98*4));d=ImageDraw.Draw(im);S=4
 if kind=='clock':
  cx,cy,r=52*S,48*S,41*S;d.ellipse((cx-r,cy-r,cx+r,cy+r),fill='#fffdf2',outline='#26303d',width=3*S)
  font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',10*S)
  for k in range(12):
   a=k*math.pi/6-math.pi/2;x=cx+math.cos(a)*r*.79;y=cy+math.sin(a)*r*.79;d.text((x,y),str(k or 12),font=font,fill='#17212b',anchor='mm')
  a=n*.035;d.line((cx,cy,cx+math.sin(a)*r*.6,cy-math.cos(a)*r*.6),fill='#182633',width=2*S);d.line((cx,cy,cx-r*.43,cy+r*.17),fill='#182633',width=3*S)
  d.rounded_rectangle((112*S,24*S,180*S,78*S),radius=8*S,fill='#203a52',outline='#f4d986',width=2*S);d.line((126*S,42*S,165*S,42*S),fill='#f4d986',width=3*S);d.line((126*S,57*S,156*S,57*S),fill='#f4d986',width=3*S)
 elif kind=='swirl':
  for cx,cy in [(32,56),(88,22),(146,49)]:
   pts=[]
   for t in np.linspace(0,math.pi*5,180):r=1+t*.9;pts.append(((cx+math.cos(t+n*.035)*r)*S,(cy+math.sin(t+n*.035)*r)*S))
   d.line(pts,fill='#9b8cbc',width=3*S)
 elif kind=='warning':
  d.polygon([(89*S,8*S),(143*S,87*S),(35*S,87*S)],fill='#e2b84b',outline='#fff4ae',width=2*S);d.line((89*S,30*S,89*S,58*S),fill='#49392c',width=7*S);d.ellipse((85*S,67*S,93*S,75*S),fill='#49392c')
 return im.resize((188,98),Image.Resampling.LANCZOS)

def t01(family,n,c):
 """Cue adapter to approved T01. Only timing/semantic inputs are adapted."""
 cues=c.get('t01Cues')
 if not cues:return shared.subtitle('T01',n,c)
 out=blank()
 for cue in cues:
  if cue['in']<=n<cue['out']:
   cc=copy.deepcopy(c);cc['subtitle'].update(cue['subtitle']);layer=shared.subtitle('T01',n-cue['in'],cc)['speech'];out.alpha_composite(layer)
 return {'speech':out}

def subtitle(family,n,c):
 out=blank();s=c['subtitle']
 if family=='T03':
  caption(out,s['prefix'],c,s.get('y',332));age=n-s['keywordIn'];q=ease(n,s['keywordIn'],s['keywordIn']+6)
  if age>=0:shared.puttext(out,s['emphasis'],s['focusStyle'],142,s.get('y',332)+24,scale=1+.1*math.sin(progress(age,0,10)*math.pi),glow=.5*(1-progress(age,2,10)))
  # Actual cursor silhouette, independent editable vector geometry, enters and taps keyword.
  if n>=s['cursorIn']:
   q=ease(n,s['cursorIn'],s['cursorIn']+6);x=142+37*(1-q);y=s.get('y',332)+46+12*(1-q);cursor=Image.new('RGBA',(45*4,54*4));d=ImageDraw.Draw(cursor);pts=[(12,48),(7,30),(11,27),(16,32),(16,6),(20,3),(24,6),(24,25),(28,21),(33,24),(37,23),(41,28),(40,44),(33,51),(12,48)];pts=[(x*4,y*4) for x,y in pts];d.polygon(pts,fill='white',outline='#111922',width=5);cursor=cursor.resize((31,37),Image.Resampling.LANCZOS);out.alpha_composite(cursor,(round(x),round(y)))
  return {'cursorText':out}
 if family=='T07':
  for j,dx in enumerate([-31,0,30]):
   q=ease(n,j*2,j*2+5);style=c['questionStyle'];shared.puttext(out,'?',style,142+dx,52-18*q,op=q,scale=.65+.35*q)
  return {'questions':out}
 if family=='T10':
  q=ease(n,*c['rollClock']);y=c.get('captionY',333);style=c['captionStyle'];shared.puttext(out,c['rollLines'][0],style,142,y-23*q,op=1-q);shared.puttext(out,c['rollLines'][1],style,142,y+23*(1-q),op=q)
  return {'rollingSpeech':out}
 if family=='T08':
  q=ease(n,0,7);tile,(w,h)=shared.text_tile(c['headline'],json.dumps(c['headlineStyle'],sort_keys=True));tile=tile.filter(ImageFilter.GaussianBlur(4*(1-q)));sc=1.35-.35*q;tile=tile.resize((round(tile.width*sc),round(tile.height*sc)),Image.Resampling.LANCZOS);red=Image.new('RGBA',tile.size,'#a31637');red.putalpha(tile.getchannel('A').filter(ImageFilter.GaussianBlur(.8)));out.alpha_composite(shared.alpha(red,q*.8),(round(142-tile.width/2)+2,round(301-tile.height/2)+3));out.alpha_composite(shared.alpha(tile,q),(round(142-tile.width/2),round(301-tile.height/2)));return {'headline':out}
 if family=='ordinary':caption(out,c['caption'],c);return {'speech':out}
 raise ValueError('Unsupported subtitle family '+family)
