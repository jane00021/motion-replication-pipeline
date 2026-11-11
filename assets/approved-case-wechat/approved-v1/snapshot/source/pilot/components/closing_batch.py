from .common import *
from .visual import head_matte
import round2_render
from .detail_tools import glyph_tile,place_text
FONT='C:/Windows/Fonts/Noto Sans SC Bold (TrueType).otf'

def _rect(c,n):
 keys=c['visual']['keyframes'];lo=max((k for k in keys if k['frame']<=n),key=lambda k:k['frame']);hi=next((k for k in keys if k['frame']>n),lo);t=0 if hi==lo else (n-lo['frame'])/(hi['frame']-lo['frame']);return [core.mix(x,y,t) for x,y in zip(lo['rect'],hi['rect'])]

def render(component_id,raw,frame,parameters,disabled=()):
 c=parameters;n=frame;raw=raw.convert('RGBA')
 if component_id=='v08':
  x0,y0,x1,y1=map(round,_rect(c,n));inset=Image.new('RGBA',(286,508));small=raw.resize((max(1,x1-x0),max(1,y1-y0)),Image.Resampling.LANCZOS);put(inset,small,x0,y0)
  # The real new presenter is restored above the title through a new-input matte.
  fg=Image.open(P/c['matteFrames']/f'{n:04d}.png').convert('RGBA') if c.get('matteFrames') else raw.copy()
  if not c.get('matteFrames'):fg.putalpha(head_matte(raw))
  foreground=Image.new('RGBA',(286,508));put(foreground,fg.resize(small.size,Image.Resampling.LANCZOS),x0,y0)
  return {'stage':Image.new('RGBA',(286,508),'#050607'),'inset':inset,**({} if 'occlusion' in disabled else {'presenterForeground':foreground})}
 if component_id=='v09':
  x0,y0,x1,y1=map(round,_rect(c,n));out=Image.new('RGBA',(286,508),'#050607');put(out,raw.resize((max(1,x1-x0),max(1,y1-y0)),Image.Resampling.LANCZOS),x0,y0);return {'presenter':out}
 raise ValueError(component_id)

@lru_cache(maxsize=64)
def giant(text,width,height):
 tile,m=text_tile(text,96,'#f9f9f5',FONT);tile=tile.crop((8,8,round(m['inkWidth'])+9,round(m['inkHeight'])+11));tile=tile.resize((width,height),Image.Resampling.LANCZOS)
 # Measured source has forward-slanted heavy sans glyphs with tight black lower shadow.
 tile=tile.transform((width+20,height),Image.Transform.AFFINE,(1,-.20,14,0,1,0),Image.Resampling.BICUBIC)
 out=Image.new('RGBA',(tile.width+6,tile.height+7));s=Image.new('RGBA',tile.size,'#17191d');s.putalpha(tile.getchannel('A'));put(out,s,2,4,.85,.35);put(out,tile,0,0);return out

def render_subtitle(component_id,frame,parameters,disabled=()):
 c=parameters;n=frame
 if 'text' in disabled:return {}
 if component_id=='t04':return {'text':core.rgba(load(P/c['subtitle']['parameterPath']),n)}
 if component_id=='t15':return {'text':round2_render.text_layer(c['subtitle'],n)}
 if c.get('calibratedRoles') and component_id in ('t13','t14'):return calibrated_subtitle(component_id,n,c)
 if component_id=='t13':
  out=Image.new('RGBA',(286,508));s=c['subtitle'];end=s['exit'];fade=1-prog(n,end[0],end[1]);clock=s['rows']
  for i,row in enumerate(clock):
   q=prog(n,row['entry'],row['settle']);drift=(1-q)*row['drift']
   # Source uses two separated oversized glyphs straddling the face, not repeated words.
   for j,ch in enumerate(row['text']):
    tile=giant(ch,row.get('glyphInkWidth',85),row['inkHeight']);anchor=row.get('glyphX',[-7,194])[j]
    dx=drift if j==0 else -drift
    put(out,tile,anchor+dx,row['y'],prog(n,row['entry']-1,row['entry']+3)*fade,2*(1-q))
  cap=Image.new('RGBA',(286,508));tile,m=text_tile(s['caption'],13);put(cap,tile,(286-m['inkWidth'])/2-8,430-8,fade)
  return {'behindTitle':out,'speechCaption':cap}
 if component_id=='t14':
  out=Image.new('RGBA',(286,508));s=c['subtitle'];fade=1-prog(n,*s['exit'])
  for phrase in s['phrases']:
   q=prog(n,*phrase['plateIn'])
   if q<=0:continue
   x,y,w,h=phrase['rect'];plate=Image.new('RGBA',(w,h));ImageDraw.Draw(plate).rounded_rectangle((0,0,w-1,h-1),radius=4,fill=(105,109,110,145));put(out,plate,x,y,q*fade)
   text=phrase['text'];role=copy.deepcopy(s['style']);tile,m=core.ink(text,role);glyphWidth=m['inkWidth'];xtext=x+(w-glyphWidth)/2
   advances=[];total=0
   for ch in text:
    t,meta=core.ink(ch,role);advances.append((t,meta,total));total+=meta['advance']
   for j,(t,meta,offset) in enumerate(advances):
    age=n-phrase['textStart']-j*phrase['stagger'];v=prog(age,-1,4)
    if age<0:continue
    sx=.07+.93*(1-(1-v)**2);scaled=t.resize((max(1,round(t.width*sx)),t.height),Image.Resampling.BICUBIC)
    # Positions are native real ink coordinates, independent of plate geometry.
    put(out,scaled.resize((max(1,round(scaled.width/4)),round(scaled.height/4)),Image.Resampling.LANCZOS),xtext+offset-8+(1-sx)*meta['inkWidth']/2,y+(h-meta['inkHeight'])/2-8,v*fade,1.3*(1-v))
  return {'phrasePlates':out}
 raise ValueError(component_id)


def calibrated_subtitle(component_id,n,c):
 s=c['subtitle'];fade=1-prog(n,*s['exit']);out=Image.new('RGBA',(286,508))
 if component_id=='t13':
  for row in s['rows']:
   q=prog(n,row['entry'],row['settle']);ease=1-(1-q)**3
   for j,ch in enumerate(row['text']):
    spec=row['style'];tile,(w,h)=glyph_tile(ch,json.dumps(spec,sort_keys=True));skew=row.get('skew',.15)
    tile=tile.transform((tile.width+round(h*skew),tile.height),Image.Transform.AFFINE,(1,skew,-h*skew,0,1,0),Image.Resampling.BICUBIC)
    x=row['glyphX'][j]+row['drift']*(1-ease)*(1 if j==0 else -1)
    put(out,tile,x-6,row['y']-6,prog(n,row['entry']-1,row['entry']+3)*fade,1.8*(1-q))
  cap=Image.new('RGBA',(286,508));spec=s['captionStyle'];place_text(cap,s['caption'],spec,143,spec['inkY'],99,op=fade)
  return {'behindTitle':out,'speechCaption':cap}
 for phrase in s['phrases']:
  q=prog(n,*phrase['plateIn'])
  if q<=0:continue
  x,y,w,h=phrase['rect'];plate=Image.new('RGBA',(w,h));ImageDraw.Draw(plate).rounded_rectangle((0,0,w-1,h-1),radius=3,fill=(105,109,110,145));put(out,plate,x,y,q*fade)
  st=phrase['style'];chars=list(phrase['text']);gw=st['inkWidth'];gh=st['inkHeight'];spacing=phrase.get('tracking',0);total=len(chars)*gw+(len(chars)-1)*spacing;xtext=x+(w-total)/2
  for j,ch in enumerate(chars):
   age=n-phrase['textStart']-j*phrase['stagger']
   if age<0:continue
   a=prog(age,0,4);tile,bb=glyph_tile(ch,json.dumps(st,sort_keys=True));sx=.06+.94*(1-(1-a)**2);tile=tile.resize((max(1,round(tile.width*sx)),tile.height),Image.Resampling.BICUBIC)
   put(out,tile,xtext+j*(gw+spacing)-6+(1-sx)*gw/2,y+(h-gh)/2-6,prog(age,-1,3)*fade,1.1*(1-a))
 return {'phrasePlates':out}
