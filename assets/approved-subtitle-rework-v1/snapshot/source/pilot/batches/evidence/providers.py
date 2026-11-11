"""Five complete occurrences, four visual families and one shared T04.
Documents are explicitly authored diagrams, not fabricated scientific sources.
"""
import json,math
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
from components import P,W,H,blank,progress,alpha,puttext,text_tile

FONT='D:/SKILL/font-check/SourceHanSerifSC-Bold.otf'
def put(out,im,x,y,op=1):out.alpha_composite(alpha(im,op),(round(x),round(y)))
@lru_cache(maxsize=64)
def asset(path):return Image.open(P/path).convert('RGBA')
def fit(im,w,h):return im.resize((max(1,round(w)),max(1,round(h))),Image.Resampling.LANCZOS)
def base_grid():
 im=Image.new('RGBA',(W,H),'#030708');d=ImageDraw.Draw(im)
 for x in range(4,W,8):
  for y in range(3,H,8):d.ellipse((x,y,x+1,y+1),fill='#1b2020')
 return im
def matte(c,n):return Image.open(P/c['matteFrames']/f'{n:04d}.png').convert('RGBA')

def visual(family,raw,n,c):
 v=c['visual'];e=c['events'];out={}
 if family=='V04':
  bg=base_grid();q=progress(n,*e['collage']);tile=asset(v['collage']);tile=fit(tile,W,H);put(bg,tile,0,(1-q)*H,q)
  if v.get('photo'):
   photo=asset(v['photo'])
   for j,(x,y,w,h,ang) in enumerate([(-8,9,154,167,-7),(143,5,152,189,6),(-6,221,162,191,5),(150,223,145,189,-6)]):
    im=fit(photo,w,h).rotate(ang,Image.Resampling.BICUBIC,expand=True);put(bg,im,x,y+(1-progress(n,e['collage'][0]+j*3,e['collage'][1]+j*3))*90,q*.7)
  fg=matte(c,n);a=fg.getchannel('A');stroke=a.filter(ImageFilter.MaxFilter(9));rim=Image.new('RGBA',(W,H),'#fffffa');rim.putalpha(stroke);rim.alpha_composite(fg)
  return {'background':bg,'outlinedPresenter':rim}
 if family=='V05':
  bg=base_grid();history=blank();q=progress(n,*e['history']);im=fit(asset(v['history']),108,126);put(history,im,177-23*q,44-29*q,1-progress(n,*e['historyOut']))
  papers=blank();N=len(v['documents'])
  for j,path in enumerate(v['documents']):
   age=n-e['stairs'][0]-j*e.get('stagger',5);q=progress(age,0,8)
   if age<0:continue
   w=134;h=172;im=fit(asset(path),w,h);x=12+j*28;y=48+j*48+(1-q)*130;put(papers,im,x,y,1-progress(n,*e['focus']))
  # One focus paper takes over; continuous geometry rather than a jump-cut thumbnail.
  q=progress(n,*e['focus']);q=1-(1-q)**3;paper=fit(asset(v['documents'][-1]),108+118*q,140+144*q);put(papers,paper,159-130*q,223-23*q,progress(n,e['focus'][0]-2,e['focus'][0]+2))
  return {'background':bg,'history':history,'documents':papers}
 if family=='V09':
  out['background']=raw.convert('RGBA').filter(ImageFilter.GaussianBlur(5*progress(n,*e['blur'])))
  q=progress(n,*e['page']);q=1-(1-q)**3;im=asset(v['document']);w=190*q;h=278*q
  paper=blank()
  if q>0:
   full=fit(im,max(2,w),max(2,h));py=92+(1-q)*70
   # Row-strip cylindrical curl: lower paper narrows and lifts to reveal its shaded back.
   curl=44*(1-progress(n,e['page'][0]+7,e['page'][1]+7));ch=round(full.height)
   for yy in range(0,ch,3):
    row=full.crop((0,yy,full.width,min(ch,yy+3)));f=progress(yy,ch-curl,ch);inset=round(f*f*curl*.5);row=fit(row,max(2,full.width-inset*2),row.height);put(paper,row,142-row.width/2,py+yy-f*f*curl*.25)
   if curl>2:
    d=ImageDraw.Draw(paper);y=py+h-curl*.25;d.polygon([(142-w/2+curl*.2,y-curl*.4),(142+w/2-curl*.2,y-curl*.7),(142+w/2-curl*.5,y),(142-w/2+curl*.5,y+curl*.2)],fill='#d8d8cc')
  return dict(out,document=paper)
 if family=='V12':
  layer=blank();q=progress(n,*e['symbol']);im=asset(v['symbol'])
  for x,y,size,delay in [(51,60,79,0),(244,111,53,2),(153,28,34,4)]:
   t=progress(n-delay,*e['symbol']);s=size*(.08+1.05*t if t<.85 else 1+.05*(1-progress(t,.85,1)));put(layer,fit(im,s,s),x-s/2,y-s/2,progress(t,0,.15))
  ban=blank();q=progress(n,*e['ban']);im=asset(v['ban'])
  if q>0:
   for x,y,size in [(51,60,88),(244,111,60)]:put(ban,fit(im,size*q,size*q),x-size*q/2,y-size*q/2)
  return {'symbols':layer,'prohibition':ban}
 if family=='V11':
  # Normal caption is placed inside the scaled coordinate system, not registered as a subtitle family.
  inner=raw.convert('RGBA');ordinary_caption(inner,n,c)
  q=progress(n,*e['shrink']);s=1-(1-v['scale'])*(1-(1-q)**3);im=fit(inner,W*s,H*s);bg=Image.new('RGBA',(W,H),'black');put(bg,im,(W-im.width)/2,(H-im.height)/2)
  return {'completeInset':bg}
 raise ValueError(family)

def ordinary_caption(out,n,c):
 for cue in c.get('ordinaryCues',[]):
  if cue['in']<=n<cue['out']:puttext(out,cue['text'],cue['style'],142,cue.get('y',335))

def subtitle(family,n,c):
 if family!='T04':raise ValueError(family)
 s=c['evidenceText'];e=c['events'];layer=blank();overlay=blank()
 # Shared document focus marker/zoom implementation for staircase and curl families.
 q=progress(n,*e['marker']);x,y,w,h=s['markerRect'];d=ImageDraw.Draw(layer);d.rectangle((x,y,x+w*q,y+h),fill=(242,204,40,165))
 if n>=e['zoom'][0]:
  q=progress(n,*e['zoom']);q=1-(1-q)**3;z=Image.new('RGBA',(W,H));zx,zy,zw,zh=s['zoomRect'];panel=Image.new('RGBA',(round(zw),round(zh)),'#fafbf7');highlight=Image.new('RGBA',panel.size);d=ImageDraw.Draw(highlight);d.rectangle((5,7,5+(zw-10)*progress(n,e['zoom'][1],e['zoom'][1]+10),28),fill=(247,211,39,135));panel.alpha_composite(highlight);puttext(panel,s['documentTitle'],s['documentStyle'],zw/2,8);put(z,panel,zx,zy+(1-q)*32,q);layer.alpha_composite(z)
 for line in s['headline']:
  if n>=line['in']:puttext(overlay,line['text'],line['style'],line.get('cx',142),line['y']+12*(1-progress(n,line['in'],line['in']+5)),progress(n,line['in']-1,line['in']+2))
 return {'documentMarker':layer,'conclusion':overlay}

def support(family,n,c):
 if family!='ordinary-caption':raise ValueError(family)
 layer=blank();ordinary_caption(layer,n,c);return {'speech':layer}
