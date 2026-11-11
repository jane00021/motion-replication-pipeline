"""Measured closing captions: split-line handoff, diagonal handoff, typewriter relay.
Independent editable glyphs and material roles, never reads reference pixels.
"""
from pathlib import Path
import json,copy,math,importlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
from . import core as shared
W,H=284,504;S=4

def q(n,a,b):return max(0.,min(1.,(n-a)/max(1.,b-a)))
def ease(t):return 1-(1-t)**3

def tile(text,style):
 f=ImageFont.truetype(style['font'],round(style['size']*S));bb=f.getbbox(text);mask=Image.new('L',(bb[2]-bb[0]+20,bb[3]-bb[1]+20));ImageDraw.Draw(mask).text((10-bb[0],10-bb[1]),text,font=f,fill=255);mask=mask.crop(mask.getbbox());w,h=mask.size;pad=24;out=Image.new('RGBA',(w+48,h+48));m=Image.new('L',out.size);m.paste(mask,(pad,pad));sh=style['shadow'];sm=Image.new('L',out.size);sm.paste(mask,(pad+round(sh['x']*S),pad+round(sh['y']*S)));layer=Image.new('RGBA',out.size,sh['color']);layer.putalpha(sm.filter(ImageFilter.GaussianBlur(sh['blur']*S)).point(lambda v:round(v*sh['opacity'])));out.alpha_composite(layer)
 if style.get('outline',0):
  r=round(style['outline']*S);border=m.filter(ImageFilter.MaxFilter(2*r+1));layer=Image.new('RGBA',out.size,style.get('outlineColor','#4b3b11'));layer.putalpha(border);out.alpha_composite(layer)
 layer=Image.new('RGBA',mask.size,style['fill']);layer.putalpha(mask);out.alpha_composite(layer,(pad,pad))
 return out,{'width':w/S,'height':h/S,'advance':f.getlength(text)/S,'fontAscent':f.getmetrics()[0]/S}

def place(out,im,x,y,op=1,sx=1,sy=1,blur=0):
 if op<=0:return
 if sx!=1 or sy!=1:im=im.resize((max(1,round(im.width*sx)),max(1,round(im.height*sy))),Image.Resampling.BICUBIC)
 if blur:im=im.filter(ImageFilter.GaussianBlur(blur*S))
 if op<1:im=im.copy();im.putalpha(im.getchannel('A').point(lambda v:round(v*max(0,min(1,op)))))
 out.alpha_composite(im,(round(x*S),round(y*S)))

def phrase(out,text,style,cx,y,op=1,sx=1,sy=1,blur=0):
 im,m=tile(text,style);place(out,im,cx-m['width']*sx/2-6*sx,y-6*sy,op,sx,sy,blur);return m

def subtitle(family,n,c):
 s=c['subtitle'];out=Image.new('RGBA',(W*S,H*S));mode=s['mode'];white=s['styles']['white'];gold=s['styles']['gold'];clock=s['clock'];y=s.get('y',332);fade=1-q(n,*clock['exit']) if clock.get('exit') else 1
 if mode=='split-line':
  im,m=tile(s['setup'],white);t=ease(q(n,*clock['split']));x=142-m['width']/2-6
  # One real line split through its glyph ink: no duplicate whole sentence.
  layer=Image.new('RGBA',(W*S,H*S));place(layer,im,x,y-6,fade)
  from .split_title import split_rgba
  primitive=split_rgba
  native=layer.resize((W,H),Image.Resampling.LANCZOS);upper,lower=primitive(native,y+m['height']/2,dy=t*s['splitDistance'])
  out.alpha_composite(upper.resize(out.size,Image.Resampling.LANCZOS));out.alpha_composite(lower.resize(out.size,Image.Resampling.LANCZOS))
  a=q(n,*clock['takeover']);phrase(out,s['conclusion'],gold,142,y-(gold['size']-white['size'])/2,fade*a,sx=.68+.32*ease(a),sy=1.12-.12*a,blur=1.5*(1-a))
 elif mode=='diagonal-line':
  a=s['setupParts'];ma=tile(a[0],white)[1];mb=tile(a[1],white)[1];t=ease(q(n,*clock['split']));start=142-(ma['width']+mb['width'])/2
  phrase(out,a[0],white,start+ma['width']/2-s['splitX']*t,y-s['splitY']*t,fade);phrase(out,a[1],white,start+ma['width']+mb['width']/2+s['splitX']*t,y+s['splitY']*t,fade)
  a=q(n,*clock['takeover']);phrase(out,s['conclusion'],gold,142,y-(gold['size']-white['size'])/2,fade*a,sx=.7+.3*ease(a),sy=1.1-.1*a,blur=1.6*(1-a))
 elif mode=='typed-relay':
  first=s['first'];firstStyle=s.get('firstStyle',gold);entry=clock['first'];clear=clock['firstClear'];count=sum(n>=v for v in entry)
  if n<clear and count:
   # Keep the original full phrase anchor while each real character is revealed.
   _,m=tile(first,firstStyle);cursor=142-m['width']/2
   for i,ch in enumerate(first):
    im,mm=tile(ch,firstStyle)
    if n>=entry[i]:place(out,im,cursor-6,y-6,fade)
    cursor+=mm['advance']
  if n>=clock['secondStart']:
   age=n-clock['secondStart'];a=ease(q(age,0,clock['secondSettle']-clock['secondStart']));parts=s['second'];widths=[tile(seg['text'],s['styles'][seg['role']])[1]['width'] for seg in parts];cursor=142-sum(widths)/2
   for seg,w in zip(parts,widths):
    st=s['styles'][seg['role']];im,mm=tile(seg['text'],st);place(out,im,cursor-6,y-6,fade*q(age,-1,3),blur=(1-a)*2.4);cursor+=w
 else:raise ValueError(mode)
 return {'closingText':out.resize((W,H),Image.Resampling.LANCZOS)}
