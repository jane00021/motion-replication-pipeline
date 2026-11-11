from pathlib import Path
import json,math,copy,random
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance
import t04_render as core
import render_migration as media
P=core.P
def load(p):return json.loads(Path(p).read_text('utf-8'))

def prog(n,a,b):return core.clamp((n-a)/max(1,b-a))

def text_tile(text,size,fill='#ffffff',font=None,shadow=True):
 style=copy.deepcopy(load(P/'source/pilot/complete01-02/shared-text-style.json'));style.update(size=size,fill=fill)
 if font:style['path']=font
 from fontTools.ttLib import TTFont
 f=TTFont(style['path'],fontNumber=0,lazy=True);cmap=f.getBestCmap();f.close()
 if any(ord(ch) not in cmap for ch in text):style['path']='C:/Windows/Fonts/simsun.ttc'
 if not shadow:style['shadow']['opacity']=0
 im,m=core.ink(text,style)
 return im.resize((round(im.width/4),round(im.height/4)),Image.Resampling.LANCZOS),m

def put(base,tile,x,y,op=1,blur=0):
 if blur:tile=tile.filter(ImageFilter.GaussianBlur(blur))
 if op!=1:tile=core.opacity(tile,op)
 base.alpha_composite(tile,(round(x),round(y)))

def reveal(base,text,size,xy,age,fill='#fff',duration=6,dx=0):
 if age<0:return
 tile,m=text_tile(text,size,fill);t=core.clamp(age/max(1,duration));x,y=xy
 if t<1:
  # Horizontal compression -> expanded real glyph, not a generic opacity transition.
  sx=max(.05,t);tile=tile.resize((max(1,round(tile.width*sx)),tile.height),Image.Resampling.BICUBIC)
 put(base,tile,x-8+dx*(1-t),y-8,prog(age,-1,3),2*(1-t))
