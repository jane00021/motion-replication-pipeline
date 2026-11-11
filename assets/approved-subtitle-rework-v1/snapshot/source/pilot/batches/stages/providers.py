"""Stage, perspective, continuous viewport and stacked-card mechanisms. No reference pixels."""
from pathlib import Path
import json,math,random
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFilter,ImageFont
from functools import lru_cache
import components as C
P=C.P;W,H=C.W,C.H
FONT='D:/SKILL/font-check/SourceHanSerifSC-Bold.otf'
BLACK='C:/Windows/Fonts/Noto Sans SC Bold (TrueType).otf'
def q(n,a,b):return C.progress(n,a,b)
def put(base,im,x,y,op=1):base.alpha_composite(C.alpha(im,op),(round(x),round(y)))
def text(out,t,size,cx,y,fill='#fff8e9',font=FONT,op=1,**kw):
 st={'font':font,'size':size,'fill':fill,'shadowX':.7,'shadowY':1.1,'shadowBlur':.5,**kw};C.puttext(out,t,st,cx,y,op)
def blank():return C.blank()
@lru_cache(maxsize=4)
def grid():
 a=Image.new('RGBA',(W,H),'#030607');d=ImageDraw.Draw(a)
 for y in range(0,H,10):
  for x in range(0,W,10):d.ellipse((x,y,x+1,y+1),fill='#152022')
 return a

def circle(raw,cx,cy,r,glow=False):
 # New talking head crop encompasses hair to chin, not an arbitrary full-room window.
 crop=raw.crop((40,73,248,281)).resize((2*r,2*r),Image.Resampling.LANCZOS).convert('RGBA');m=Image.new('L',crop.size);ImageDraw.Draw(m).ellipse((1,1,2*r-2,2*r-2),fill=255);crop.putalpha(m)
 out=blank();d=ImageDraw.Draw(out)
 if glow:
  halo=blank();ImageDraw.Draw(halo).ellipse((cx-r-3,cy-r-3,cx+r+3,cy+r+3),fill='#e8efd9');put(out,halo.filter(ImageFilter.GaussianBlur(3)),0,0)
 d=ImageDraw.Draw(out);d.ellipse((cx-r-1,cy-r-1,cx+r+1,cy+r+1),fill='white');put(out,crop,cx-r,cy-r);return out

@lru_cache(maxsize=32)
def scene(index,width=400,height=540):
 # Original editable vector-derived illustration; not documentary/financial evidence.
 a=Image.new('RGBA',(width,height),'#162435');d=ImageDraw.Draw(a);sx=width/400;sy=height/540
 def r(box,fill,outline=None,width=1):d.rectangle(tuple(round(v*(sx if i%2==0 else sy)) for i,v in enumerate(box)),fill=fill,outline=outline,width=width)
 for y in range(height):d.line((0,y,width,y),fill=(25+int(y/height*18),40+int(y/height*12),57+int(y/height*13)))
 r((22,28,187,262),'#36576b');r((27,33,182,257),'#bbd7d7');r((102,33,108,257),'#668e9f');r((27,135,182,142),'#668e9f')
 d.ellipse((round(48*sx),round(58*sy),round(94*sx),round(104*sy)),fill='#f1cf7d' if index!=0 else '#c2cddd')
 for i in range(7):r((25+i*23,201-(i%3)*18,43+i*23,257),'#66839c')
 r((0,400,400,540),'#0e1a26');r((120,327,393,346),'#b99b73');r((142,346,153,492),'#7c6753');r((369,346,380,492),'#7c6753')
 # Person at desk, independently layered scene; figure is drawn rather than old presenter extraction.
 skin='#e2b9a0';d.ellipse((round(209*sx),round(173*sy),round(278*sx),round(246*sy)),fill='#322d32');d.ellipse((round(216*sx),round(186*sy),round(271*sx),round(250*sy)),fill=skin)
 d.polygon([(round(x*sx),round(y*sy)) for x,y in [(214,245),(273,245),(296,354),(191,354)]],fill=['#667d91','#567f79','#a78461'][index%3])
 d.line([(round(x*sx),round(y*sy)) for x,y in [(214,267),(176,310),(230,322)]],fill=skin,width=max(3,round(13*sx)))
 d.line([(round(x*sx),round(y*sy)) for x,y in [(270,270),(299,311),(270,325)]],fill=skin,width=max(3,round(13*sx)))
 if index==0:
  r((121,260,207,320),'#718e9f');r((128,266,200,313),'#233d57');r((116,320,220,325),'#b4c0c4')
 elif index==1:
  r((122,302,214,325),'#f0dfb5');d.line((round(169*sx),round(302*sy),round(169*sx),round(325*sy)),fill='#9b886d',width=2)
 else:
  r((132,281,209,324),'#70868a');r((139,287,202,316),'#b7d6c8');d.line((round(147*sx),round(307*sy),round(159*sx),round(296*sy),round(172*sx),round(301*sy),round(193*sx),round(291*sy)),fill='#368067',width=3)
 return a

@lru_cache(maxsize=1)
def schedule():
 a=Image.new('RGBA',(420,700),'#dfc28e');d=ImageDraw.Draw(a);d.rectangle((10,10,410,690),outline='#584326',width=5);d.rectangle((20,20,400,680),outline='#88653a',width=2)
 text(a,'落地练习计划',34,210,43,'#443422',font=BLACK);text(a,'自主规划示意 · 不是财务证明',15,210,100,'#655038')
 lines=[('选择方向','了解需求'),('每天学习','形成笔记'),('小步练习','完成作品'),('复盘改进','修正问题'),('长期积累','逐渐熟练')]
 for i,(x,y) in enumerate(lines):
  yy=160+i*92;d.rectangle((35,yy,385,yy+78),outline='#8e744a',width=2);d.line((190,yy,190,yy+78),fill='#8e744a',width=2);text(a,x,25,112,yy+24,'#43392a');text(a,y,24,286,yy+24,'#43392a')
 return a

def warped(tile,pts):
 src=np.float32([[0,0],[tile.width,0],[tile.width,tile.height],[0,tile.height]]);M=cv2.getPerspectiveTransform(src,np.float32(pts));arr=cv2.warpPerspective(np.asarray(tile),M,(W,H),flags=cv2.INTER_CUBIC);return Image.fromarray(arr)
def smooth(t):return 1-(1-t)**3

def visual(family,raw,n,c):
 v=c['visual'];N=c['frameCount'];out={};fade=1.
 if family=='V06':
  out['background']=grid().copy();obj=blank();d=ImageDraw.Draw(obj);sun=q(n,*v['sunIn'])*(1-q(n,*v['moonIn']));moon=q(n,*v['moonIn']);cy=160
  for op,typ in [(sun,'sun'),(moon,'moon')]:
   if op<=0:continue
   tile=Image.new('RGBA',(190,190));td=ImageDraw.Draw(tile);td.ellipse((2,2,188,188),fill='#f58c29' if typ=='sun' else '#e8e6b0')
   if typ=='moon':
    for j in range(6):td.ellipse((25+j*24,50+(j%3)*30,38+j*24,63+(j%3)*30),fill='#d0d09c')
   put(obj,tile,47,65,op)
  # Live new presenter on working-stage screen; scene illustrates overtime→learn→act.
  
  if c.get('matteFrames'):
   matte=Image.open(P/c['matteFrames']/f'{n:04d}.png').convert('RGBA');a=np.array(matte.getchannel('A'));binary=np.uint8(a>110)*255;flood=binary.copy();cv2.floodFill(flood,None,(0,0),255);holes=cv2.bitwise_not(flood);a=np.maximum(a,holes);stage=raw.convert('RGBA');stage.putalpha(Image.fromarray(a));stage=stage.resize((192,341),Image.Resampling.LANCZOS);put(obj,stage,45,-2,q(n,0,10))
  else:
   stage=raw.crop((18,100,266,430)).resize((155,206),Image.Resampling.LANCZOS);m=Image.new('L',stage.size);ImageDraw.Draw(m).rounded_rectangle((0,0,154,205),radius=16,fill=255);stage.putalpha(m);put(obj,stage,65,114,q(n,0,10))
  for i,start in enumerate(v['cardIn']):
   t=smooth(q(n,start,start+10));card=scene(i,69,80);m=Image.new('L',card.size);ImageDraw.Draw(m).rounded_rectangle((0,0,68,79),radius=6,fill=255);card.putalpha(m);put(obj,card,23+i*86,382+(1-t)*70,t)
  out['stage']=C.alpha(obj,fade);return out
 if family=='V08':
  t=smooth(q(n,0,12));r=round(142+(46-142)*t);cy=round(240+(86-240)*t);base=grid().copy();out['background']=base;out['presenter']=C.alpha(circle(raw,97,cy,r,True),fade)
  if n<12:
   ww=round(284+(92-284)*t);hh=round(504+(92-504)*t);xx=round((97-46)*t);yy=round((86-46)*t);cropbox=[round(a+(b-a)*t) for a,b in zip([0,0,284,504],[40,73,248,281])];moving=raw.crop(tuple(cropbox)).resize((ww,hh),Image.Resampling.LANCZOS).convert('RGBA');mask=Image.new('L',(ww,hh));ImageDraw.Draw(mask).rounded_rectangle((0,0,ww-1,hh-1),radius=round(min(ww,hh)*.5*t),fill=255);moving.putalpha(mask);motion=blank();put(motion,moving,xx,yy);out['presenter']=motion
  z=q(n,*v['panelIn']);t=smooth(z);pts0=[[200,280],[210,225],[220,420],[205,453]];pts1=[[68,135],[224,160],[217,438],[64,468]];pts=[[a+(b-a)*t for a,b in zip(x,y)] for x,y in zip(pts0,pts1)]
  out['panel']=C.alpha(warped(schedule(),pts),q(n,v['panelIn'][0]-1,v['panelIn'][0]+6)*fade);return out
 if family=='V10':
  base=raw.filter(ImageFilter.GaussianBlur(8));out['background']=base.convert('RGBA');panel=blank();ww,hh=208,278;progression=q(n,10,N-12)*2.99;index=min(2,int(progression));local=progression-index;im=scene(index,400,540)
  if index<2 and local>.78:im=Image.blend(im,scene(index+1,400,540),q(local,.78,1))
  # Continuous internal zoom and cross-scene handoff within one fixed rounded viewport.
  scale=1+.32*local;im=im.resize((round(ww*scale),round(hh*scale)),Image.Resampling.LANCZOS);im=im.crop(((im.width-ww)//2,(im.height-hh)//2,(im.width+ww)//2,(im.height+hh)//2));m=Image.new('L',(ww,hh));ImageDraw.Draw(m).rounded_rectangle((0,0,ww-1,hh-1),radius=20,fill=255);im.putalpha(m);put(panel,im,38,107);ImageDraw.Draw(panel).rounded_rectangle((37,106,247,385),radius=20,outline='#f9ffff',width=1);out['viewport']=C.alpha(panel,fade);out['presenter']=C.alpha(circle(raw,72,75,45),fade);cap=blank()
  for cue in c.get('ordinaryCaptions',[]):
   if cue['in']<=n<cue['out']:text(cap,cue['text'],16,142,399,op=fade)
  out['normalCaption']=cap;return out
 if family=='V13':
  out['background']=grid().copy();out['presenter']=C.alpha(circle(raw,65,83,43),fade);cards=blank();active=sum(n>=x for x in v['cardIn'])-1
  for i in range(max(0,active+1)):
   qin=smooth(q(n,v['cardIn'][i],v['cardIn'][i]+12));x=90-max(0,active-i-1)*18-(18*smooth(q(n,v['cardIn'][active],v['cardIn'][active]+12)) if i<active else 0);im=scene(i,148,250);d=ImageDraw.Draw(im);d.rectangle((0,0,147,249),outline='#f3f1e9',width=2);put(cards,im,x+(1-qin)*200,208,qin)
  out['cards']=C.alpha(cards,fade);return out
 raise ValueError(family)

def subtitle(family,n,c):
 s=c['subtitle'];out=blank();fade=1.
 if family=='T05':
  for col in s['columns']:
   for j,ch in enumerate(col['text']):
    op=q(n,col['entry']+j*2,col['entry']+j*2+9);style={'font':BLACK,'size':49,'fill':'#ffffff','shadowX':.8,'shadowY':1.2,'shadowBlur':.45};tile,(w,h)=C.text_tile(ch,json.dumps(style,sort_keys=True));alpha=tile.getchannel('A');outline=alpha.filter(ImageFilter.MaxFilter(3));layer=Image.new('RGBA',tile.size,'#eeeeea');layer.putalpha(outline);dark=Image.new('RGBA',tile.size,'#11181a');dark.putalpha(alpha);layer.alpha_composite(dark);layer=Image.blend(layer,tile,op);put(out,layer,col['x']-6,col['y']+j*61-6,q(n,2,10)*fade)
  for cue in s['captions']:
   if cue['in']<=n<cue['out']:text(out,cue['text'],15,142,335,op=fade)
  return {'type':out}
 if family=='T06':
  for tag in s['tags']:
   t=q(n,tag['in'],tag['in']+7)
   if t<=0:continue
   x,y,w,h=tag['rect'];a=Image.new('RGBA',(w,h),'#fff9ea');ImageDraw.Draw(a).rounded_rectangle((0,0,w-1,h-1),radius=3,fill='#fff9ea');text(a,tag['text'],16,w/2,7,'#b49a3a');put(out,a,x,y+(1-t)*8,t*fade)
  text(out,s['caption'],16,142,388,op=fade);return {'annotations':out}
 if family=='T09':
  active=[i for i,t in enumerate(s['times']) if n>=t]
  for i in active:
   rank=len(active)-1-i;target=24+rank*47;prev=24+max(0,len(active)-2-i)*47;last=s['times'][active[-1]];y=prev+(target-prev)*smooth(q(n,last,last+9));t=q(n,s['times'][i],s['times'][i]+8);x=153+(1-t)*130;a=Image.new('RGBA',(112,39));d=ImageDraw.Draw(a)
   for yy in range(39):d.line((0,yy,111,yy),fill=(112+int(yy*.9),216+int(yy*.6),215+int(yy*.5),255))
   mask=Image.new('L',a.size);ImageDraw.Draw(mask).rounded_rectangle((0,0,111,38),radius=19,fill=255);a.putalpha(mask);text(a,s['labels'][i],16,56,5);text(a,s['english'][i],7,56,25);put(out,a,x,y,t*fade)
  idx=max(0,len(active)-1);text(out,s['captions'][idx],16,156,419,op=fade);return {'labels':out}
 raise ValueError(family)
