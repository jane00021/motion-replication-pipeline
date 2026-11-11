"""Glyph-bound placement. Logical ink boxes exclude shadows; editable fonts, outline, tracking."""
from .common import *
from PIL import ImageChops
SCALE=4
@lru_cache(maxsize=256)
def glyph_tile(text,spec_json):
 s=json.loads(spec_json);font=ImageFont.truetype(s['path'],round(s.get('size',40)*4))
 ascent,descent=font.getmetrics();tracking=s.get('tracking',0)*4
 width=math.ceil(sum(font.getlength(ch) for ch in text)+max(0,len(text)-1)*tracking)+24
 m=Image.new('L',(width,ascent+descent+24));d=ImageDraw.Draw(m);x=12
 for ch in text:d.text((x,12+ascent),ch,font=font,anchor='ls',fill=255,stroke_width=round(s.get('weightPx',0)*4));x+=font.getlength(ch)+tracking
 bb=m.getbbox()
 if bb is None:raise ValueError('No glyph coverage: '+text)
 m=m.crop(bb);w=round(s.get('inkWidth',m.width/4)*4);h=round(s.get('inkHeight',m.height/4)*4)
 m=m.resize((w,h),Image.Resampling.LANCZOS)
 pad=24;out=Image.new('RGBA',(w+pad*2,h+pad*2));placed=Image.new('L',out.size);placed.paste(m,(pad,pad))
 sh=s.get('shadow',{'dx':1,'dy':1.5,'blur':.5,'opacity':.8});sm=Image.new('L',out.size);sm.paste(m,(pad+round(sh['dx']*4),pad+round(sh['dy']*4)));sm=sm.filter(ImageFilter.GaussianBlur(sh['blur']*4)).point(lambda a:round(a*sh['opacity']));layer=Image.new('RGBA',out.size,sh.get('color','#111217'));layer.putalpha(sm);out.alpha_composite(layer)
 radius=round(s.get('outlinePx',0)*4)
 if radius:
  layer=Image.new('RGBA',out.size,s.get('outline','#111217'));layer.putalpha(placed.filter(ImageFilter.MaxFilter(radius*2+1)));out.alpha_composite(layer)
 layer=Image.new('RGBA',out.size,s.get('fill','#fffef7'));layer.putalpha(placed);out.alpha_composite(layer)
 return out.resize((round(out.width/4),round(out.height/4)),Image.Resampling.LANCZOS),(w/4,h/4)

def place_text(out,text,s,anchor,y,age=99,duration=6,align='center',dx=0,op=1):
 if age<0:return None
 im,(w,h)=glyph_tile(text,json.dumps(s,sort_keys=True));q=prog(age,0,duration);q=1-(1-q)**3
 x=anchor-w/2 if align=='center' else anchor if align=='left' else anchor-w
 if q<1:im=im.filter(ImageFilter.GaussianBlur((1-q)*1.4))
 put(out,im,x-6+dx*(1-q),y-6,op*prog(age,-1,2))
 return [x,y,x+w,y+h]
