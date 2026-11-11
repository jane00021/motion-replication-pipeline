"""Calibrated text-only t04. All glyphs generated from independent font roles.
No original video, reference glyph pixels or inpaint inputs are read by rgba()."""
from pathlib import Path
import argparse,json,math,hashlib,subprocess,copy
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
from fontTools.ttLib import TTFont
P=Path(__file__).resolve().parents[2];S=P/'source/pilot/t04';O=P/'render/pilot/t04'
S.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
SCALE=4;W,H=286,508
def clamp(x):return min(1.,max(0.,x))
def mix(a,b,t):return a+(b-a)*t
def file_sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,data):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')
def opacity(im,a):
 im=im.copy();im.putalpha(im.getchannel('A').point(lambda v:round(v*clamp(a))));return im
def ink(text,style):
 font=ImageFont.truetype(style['path'],round(style['size']*SCALE),index=style.get('face',0))
 weight=round(style['weightPx']*SCALE);bb=font.getbbox(text,stroke_width=weight)
 mask=Image.new('L',(bb[2]-bb[0]+16,bb[3]-bb[1]+16));ImageDraw.Draw(mask).text((8-bb[0],8-bb[1]),text,font=font,fill=255,stroke_width=weight)
 bbox=mask.getbbox();mask=mask.crop(bbox)
 mask=mask.resize((max(1,round(mask.width*style['scaleX'])),max(1,round(mask.height*style['scaleY']))),Image.Resampling.LANCZOS)
 pad=32;out=Image.new('RGBA',(mask.width+2*pad,mask.height+2*pad))
 shadow=style['shadow'];sm=Image.new('L',out.size);sm.paste(mask,(pad+round(shadow['dx']*SCALE),pad+round(shadow['dy']*SCALE)))
 layer=Image.new('RGBA',out.size,shadow['color']);layer.putalpha(sm.filter(ImageFilter.GaussianBlur(shadow['blur']*SCALE)).point(lambda v:round(v*shadow.get('opacity',.4))));out.alpha_composite(layer)
 if style['outlinePx']:
  r=round(style['outlinePx']*SCALE);border=Image.new('L',out.size);border.paste(mask,(pad,pad));border=border.filter(ImageFilter.MaxFilter(2*r+1));layer=Image.new('RGBA',out.size,style['outline']);layer.putalpha(border);out.alpha_composite(layer)
 body=Image.new('RGBA',mask.size,style['fill']);body.putalpha(mask);out.alpha_composite(body,(pad,pad))
 return out,{'inkWidth':mask.width/SCALE,'inkHeight':mask.height/SCALE,'pad':pad,'advance':font.getlength(text)*style['scaleX']/SCALE}
def place(base,tile,x,y,sx=1,sy=1,op=1,blur=0):
 if op<=0:return
 if sx!=1 or sy!=1:tile=tile.resize((max(1,round(tile.width*sx)),max(1,round(tile.height*sy))),Image.Resampling.BICUBIC)
 if blur:tile=tile.filter(ImageFilter.GaussianBlur(blur*SCALE))
 base.alpha_composite(opacity(tile,op),(round(x),round(y)))
def validate(c):
 for role,style in c['roles'].items():
  f=TTFont(style['path'],fontNumber=style.get('face',0),lazy=True);cmap=f.getBestCmap();f.close()
  texts=[c['text']['body']] if role=='body' else [s['text'] for s in c['text']['second'] if s['role']==role]
  missing=[ch for text in texts for ch in text if ord(ch) not in cmap]
  if missing:raise ValueError(f'{role}: missing {missing}')
 for text,role in [(c['text']['body'],'body')]+[(s['text'],s['role']) for s in c['text']['second']]:
  _,meta=ink(text,c['roles'][role])
  if meta['inkWidth']>258:raise ValueError('text exceeds supported width')
 return True
def rgba(c,n):
 out=Image.new('RGBA',(W*SCALE,H*SCALE));e=c['events'];pos=c['layout']
 if n>=e['clear']:return out.resize((W,H),Image.Resampling.LANCZOS)
 fade=1-clamp((n-e['fadeStart'])/(e['clear']-e['fadeStart']))
 # Prefix appears progressively from right to left, but the phrase has its own center clock.
 body=c['text']['body'];elapsed=0 if n<=e['bodyStart'] else clamp((n-e['bodyStart']+1)/(e['bodySettle']-e['bodyStart']+1))
 if elapsed>0:
  tile,meta=ink(body,c['roles']['body']);left=round((1-elapsed)*meta['inkWidth']*SCALE)
  crop=Image.new('L',tile.size);ImageDraw.Draw(crop).rectangle((32+left,0,tile.width,tile.height),fill=255)
  tile.putalpha(ImageChops.multiply(tile.getchannel('A'),crop))
  shift=clamp((n-e['bodyMoveStart'])/(e['bodyMoveEnd']-e['bodyMoveStart']))
  x=mix(pos['bodyInitialX'],pos['bodyFinalX'],shift)
  # The visible suffix starts near a fixed left reveal slot; its right edge expands.
  # Source f301=工 nearx68, f306=埋头打工 nearx67, f312=full line nearx73.
  x-=meta['inkWidth']*(1-elapsed)
  x-=7*(1-elapsed)
  place(out,tile,x*SCALE-32,pos['bodyY']*SCALE-32,op=fade)
 # Second phrase: each glyph is a layer, with independently selected semantic material.
 age=n-e['secondStart'];tiles=[];width=0
 for segment in c['text']['second']:
  style=c['roles'][segment['role']]
  for ch in segment['text']:
   t,m=ink(ch,style);tiles.append((t,m,segment['role'],width,ch));width+=m['advance']+pos['letterSpacing']
 if age>=0:
  x0=pos['secondRight']-width
  for k,(tile,meta,role,offset,ch) in enumerate(tiles):
   z=age-k*e['glyphStagger'];entry=clamp((z+1)/3)
   # Current source has narrow vertical strokes, expansion, a small scale peak then recovery.
   if z<2:sx=mix(.035,.09,clamp(z/2));sy=mix(1.45,1.2,clamp(z/2))
   elif z<3:sx=mix(.09,1,(z-2));sy=mix(1.2,1,(z-2))
   elif z<5:sx=sy=mix(1,1.05,(z-3)/2)
   else:sx=sy=mix(1.05,1,clamp((z-5)/5))
   bl=1.2*(1-clamp(z/5));px=(x0+offset)*SCALE-32;py=pos['secondY']*SCALE-32
   dx=(tile.width*(1-sx))/2;dy=(tile.height*(1-sy))/2
   peak=clamp((z-2)/5)*(1-clamp((z-7)/4))
   if peak>0:
    # Light peak brightens the glyph core and suppresses shadow; not a glowing outline.
    style=copy.deepcopy(c['roles'][role]);rgb=Image.new('RGB',(1,1),style['fill']).getpixel((0,0))
    target=(255,253,204) if role=='emphasis' else (255,255,255)
    q=peak*.65;style['fill']=tuple(round(mix(a,b,q)) for a,b in zip(rgb,target));style['shadow']['opacity']=style['shadow'].get('opacity',.4)*(1-.55*peak)
    tile,_=ink(ch,style)
   if peak>0:
    # Glow applies to source phrase roles; semantic emphasis remains its gold fill.
    strength=c['roles'][role]['glow']
    for radius,a in [(4,.6),(2,.5)]:
     # Blur coverage, then tint. Blurring transparent RGB creates dark fringes and loses light.
     gm=tile.getchannel('A').filter(ImageFilter.GaussianBlur(radius*SCALE))
     gm=gm.point(lambda v:round(min(255,v*2.2)))
     gl=Image.new('RGBA',tile.size,'#fff1a8' if role=='emphasis' else '#ffffff');gl.putalpha(gm)
     place(out,gl,px+dx,py+dy,sx,sy,peak*a*strength*fade)
   place(out,tile,px+dx,py+dy,sx,sy,entry*fade,bl)
 return out.resize((W,H),Image.Resampling.LANCZOS)
def init_configs():
 font='C:/Windows/Fonts/Source Han Serif SC Heavy (TrueType).ttf'
 def style(size,fill):return {'path':font,'face':0,'size':size,'weightPx':0,'scaleX':1.,'scaleY':1.,'fill':fill,'outlinePx':0,'outline':'#26241c','shadow':{'dx':.6,'dy':1.,'blur':.45,'color':'#191a1d'},'glow':1.}
 c={'id':'t04-same-text','frames':66,'fps':30,'previewBackground':'#263036','text':{'body':'单纯埋头打工','second':[{'text':'只能','role':'support'},{'text':'维持生活','role':'emphasis'}]},'roles':{'body':style(22,'#efefec'),'support':style(29.5,'#fffef3'),'emphasis':style(29.5,'#e9cc67')},'layout':{'bodyInitialX':73,'bodyFinalX':29,'bodyY':348,'secondRight':257,'secondY':365,'letterSpacing':0},'events':{'bodyStart':0,'bodySettle':11,'bodyMoveStart':27,'bodyMoveEnd':33,'secondStart':31,'glyphStagger':.05,'fadeStart':59,'clear':65},'reference':{'sourceFrames':[300,366],'timeConvention':'local zero-based, end-exclusive','nativeCanvas':[286,508]},'fontOriginalIdentityConfirmed':False}
 dump(S/'input-same.json',c)
 a=copy.deepcopy(c);a['id']='t04-A-content';a['frames']=96;a['text']={'body':'打工就是拿时间去换工资','second':[{'text':'天花板','role':'emphasis'},{'text':'就在这','role':'support'}]};a['roles']['body']['size']=20;a['layout'].update(bodyInitialX=33,bodyFinalX=24,bodyY=348,secondY=373,secondRight=262);a['events'].update(bodyStart=0,bodySettle=12,bodyMoveStart=57,bodyMoveEnd=63,secondStart=63,fadeStart=90,clear=95)
 dump(S/'input-A.json',a);b=copy.deepcopy(a);b['id']='t04-B-font-only'
 for role,path in {'body':'C:/Windows/Fonts/Noto Sans SC Medium (TrueType).otf','support':'C:/Windows/Fonts/msyhbd.ttc','emphasis':'C:/Windows/Fonts/simhei.ttf'}.items():b['roles'][role]['path']=path
 dump(S/'input-B.json',b)
def encode(c,out):
 validate(c);folder=out.parent/(out.stem+'-rgba');folder.mkdir(exist_ok=True);rows=[]
 proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','286x508','-r','30','-i','pipe:0','-an','-c:v','libx264','-crf','15','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 for n in range(c['frames']):
  layer=rgba(c,n);path=folder/f'{n:04d}.png';layer.save(path);rows.append({'frame':n,'file':path.name,'sha256':file_sha(path),'alphaBBox':layer.getchannel('A').getbbox()})
  bg=Image.new('RGBA',(W,H),c['previewBackground']);bg.alpha_composite(layer);proc.stdin.write(bg.convert('RGB').tobytes())
 proc.stdin.close();err=proc.stderr.read();rc=proc.wait()
 if rc:raise RuntimeError(err.decode())
 dump(folder/'sequence.json',{'width':W,'height':H,'fps':30,'alpha':'straight RGBA PNG','frames':rows})
 return {'file':str(out.relative_to(P)),'sha256':file_sha(out),'frames':c['frames'],'lastFrameAlphaEmpty':rows[-1]['alphaBBox'] is None}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--init',action='store_true');ap.add_argument('--input');args=ap.parse_args()
 if args.init:init_configs()
 if args.input:
  path=Path(args.input);c=json.loads(path.read_text('utf-8'));r=encode(c,O/(path.stem+'.mp4'));dump(O/(path.stem+'-receipt.json'),dict(r,inputSha256=file_sha(path),sourceSha256=file_sha(__file__),fonts={r:s['path'] for r,s in c['roles'].items()}));print(json.dumps(r))
if __name__=='__main__':main()
