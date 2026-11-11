"""03 draft: one v04 scene and five subtitle families; recipes own sequencing.

No reference image/video is loaded by the component entrypoints. Evidence slots are
explicit media inputs. All text comes from font outlines and semantic role data.
"""
from .common import *
from PIL import ImageChops
from .detail_tools import place_text,glyph_tile
from .media_source import source_frame
import hashlib

W,H=286,508
FONT='C:/Windows/Fonts/Source Han Serif SC Heavy (TrueType).ttf'
NUMBER='C:/Windows/Fonts/impact.ttf'

def blank():return Image.new('RGBA',(W,H))

@lru_cache(maxsize=512)
def glyph(text,size,color,font,style_digest):
 return text_tile(text,size,color,font)[0]

def tile(text,size=24,color='#f3f1eb',font=FONT):
 style_digest=hashlib.sha256((P/'source/pilot/complete01-02/shared-text-style.json').read_bytes()).hexdigest()
 return glyph(text,size,color,font,style_digest).copy()

def text(out,text,size,xy,color='#f3f1eb',age=20,duration=5,mode='rise',font=FONT,center=False,max_width=None):
 if age<0:return
 im=tile(text,size,color,font);q=prog(age,0,duration);ease=1-(1-q)**3;x,y=xy
 if max_width and im.width-16>max_width:
  im=im.resize((max_width+16,im.height),Image.Resampling.LANCZOS)
 if center:x-=(im.width-16)/2
 if mode=='rise':y+=(1-ease)*20
 elif mode=='right':x+=(1-ease)*80
 elif mode=='left':x-=(1-ease)*80
 elif mode=='scale':
  s=.2+ease*.9 if q<.7 else 1+.1*(1-prog(q,.7,1))
  im=im.resize((max(1,round(im.width*s)),max(1,round(im.height*s))),Image.Resampling.BICUBIC)
 put(out,im,x-8,y-8,prog(age,-1,2),2*(1-q))

@lru_cache(maxsize=4)
def grid_background(color='#1d1e1d'):
 yy,xx=np.mgrid[:H,:W];r=np.sqrt(((xx-143)/240)**2+((yy-250)/390)**2)
 light=np.clip(1-r,0,1)*5;noise=np.random.default_rng(4004).normal(0,.9,(H,W))
 a=np.zeros((H,W,4),np.uint8)
 for k,base in enumerate(Image.new('RGB',(1,1),color).getpixel((0,0))):a[:,:,k]=np.clip(base+light+noise,0,255)
 a[:,:,3]=255;im=Image.fromarray(a);d=ImageDraw.Draw(im)
 for x in range(0,W,7):d.line((x,0,x,H),fill=(34,35,33,255),width=1)
 for y in range(0,H,7):d.line((0,y,W,y),fill=(34,35,33,255),width=1)
 return im

def render(component_id,raw,frame,parameters,disabled=()):
 if component_id!='v04':raise ValueError(component_id)
 c=parameters;n=frame;v=c['visual'];out={'background':grid_background(v.get('background','#1d1e1d')).copy()}
 if 'presenter' not in disabled:
  x,y,w,h=v.get('window',[66,87,154,154]);crop=v.get('presenterCrop',[55,76,231,252])
  presenter=raw.crop(crop).resize((w,h),Image.Resampling.LANCZOS).convert('RGBA')
  mask=Image.new('L',(w*4,h*4));ImageDraw.Draw(mask).ellipse((3,3,w*4-4,h*4-4),fill=255)
  presenter.putalpha(mask.resize((w,h),Image.Resampling.LANCZOS))
  layer=blank();d=ImageDraw.Draw(layer);d.ellipse((x-3,y-3,x+w+3,y+h+3),fill='#fcfcf8');layer.alpha_composite(presenter,(x,y));out['presenterWindow']=layer
 if v.get('evidence') and 'evidence' not in disabled:
  e=v['evidence'];age=n-e['start'];end=e.get('end',c['frames'])
  if age>=0 and n<end:
   im=source_frame(e['source'],n,c.get('fps',30)) if e.get('source') else Image.open(P/e['path']).convert('RGBA')
   if e.get('transparent',False):im=im.crop(im.getchannel('A').getbbox())
   w,h=e['size'];im=im.resize((w,h),Image.Resampling.LANCZOS)
   if not e.get('transparent',False):
    mask=Image.new('L',im.size);ImageDraw.Draw(mask).rounded_rectangle((0,0,w,h),radius=8,fill=255);im.putalpha(mask)
   q=prog(age,0,8);s=.75+.3*q if q<.7 else 1+.05*(1-prog(q,.7,1));im=im.resize((round(w*s),round(h*s)),Image.Resampling.LANCZOS)
   layer=blank();x,y=e['xy'];put(layer,im,x+(w-im.width)/2,y+(h-im.height)/2,prog(age,-1,3)*(1-prog(n,end-5,end)),2*(1-q));out['evidence']=layer
 return out

def torn_backing(w,h):
 rng=random.Random(9);im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im)
 points=[(x,rng.randint(0,13)) for x in range(0,w,10)]+[(w,rng.randint(0,7)),(w,h-4)]+[(x,h-rng.randint(0,13)) for x in range(w,0,-10)]+[(0,h-5)]
 d.polygon(points,fill=(154,156,150,215));inner=[(x+6,y+8 if y<h/2 else y-8) for x,y in points];d.polygon(inner,fill=(3,4,4,255))
 for x in [4,27,63,111]:d.polygon([(x,12),(x+9,1),(x+16,17),(x+7,21)],fill=(179,180,173,190))
 return im

@lru_cache(maxsize=12)
def number_tile(number,style_digest):
 im=tile(number,150,'#fffef9',NUMBER);bbox=im.getchannel('A').getbbox();im=im.crop(bbox)
 # Font-generated editable number with reusable racing/slash material; original font unknown.
 width={'1':77,'2':99,'3':94}.get(number,90);height=123
 im=im.resize((width,height),Image.Resampling.LANCZOS)
 skew=.22;im=im.transform((width+28,height),Image.Transform.AFFINE,(1,skew,-height*skew,0,1,0),Image.Resampling.BICUBIC)
 alpha=im.getchannel('A');cut=Image.new('L',im.size,255);d=ImageDraw.Draw(cut);d.line((0,107,width+20,47),fill=0,width=3);im.putalpha(ImageChops.multiply(alpha,cut))
 return im

def red_warning(size):
 # Metal-warning asset is shared with existing v02. Recoloring is a material variant.
 from .visual import icon
 im=icon();a=np.array(im);gold=(a[:,:,0].astype(int)-a[:,:,2].astype(int)>60)&(a[:,:,3]>0)
 for k,factor in [(0,1.03),(1,.25),(2,.45)]:a[:,:,k]=np.where(gold,np.clip(a[:,:,k]*factor,0,255),a[:,:,k])
 im=Image.fromarray(a);im=im.crop(im.getchannel('A').getbbox());return im.resize((size,size),Image.Resampling.LANCZOS).rotate(-13,Image.Resampling.BICUBIC,expand=True)

def arrow(out,a,b,amount):
 if amount<=0:return
 scale=4;layer=Image.new('RGBA',(W*scale,H*scale));d=ImageDraw.Draw(layer)
 x1,y1=a;x2,y2=b;x=x1+(x2-x1)*amount;y=y1+(y2-y1)*amount
 d.line((x1*scale,y1*scale,x*scale,y*scale),fill='#f0f0eb',width=round(2.5*scale))
 if amount>.92:
  ang=math.atan2(y2-y1,x2-x1);length=14
  for off in [-.55,.55]:d.line((x2*scale,y2*scale,(x2-length*math.cos(ang+off))*scale,(y2-length*math.sin(ang+off))*scale),fill='#f0f0eb',width=round(2.5*scale))
 out.alpha_composite(layer.resize((W,H),Image.Resampling.LANCZOS))

def render_subtitle(component_id,frame,parameters,disabled=()):
 if 'text' in disabled:return {}
 c=parameters;n=frame;s=c['subtitle'];e=s['events'];t=s['text'];back=blank();front=blank();fade=1-prog(n,e.get('exitStart',c['frames']+1),e.get('clear',c['frames']+2))
 if c.get('detailRest') and component_id in ('t08','t10','t11','t12'):
  return detail_subtitle(component_id,n,c,fade)
 if component_id=='t08':
  # Quantity first, then reflow the two glyphs apart to expose the named subject.
  age=n-e['quantity'];q=prog(n,e['reflow'],e['reflow']+7)
  text(front,t['left'],78,(49-20*q,279-39*q),'#efeeea',age,8,'rise')
  text(front,t['right'],78,(150+44*q,279+17*q),'#efeeea',age,8,'rise')
  text(front,t['subject'],33,(76,311),'#9b0926',n-e['subject'],5,'right',max_width=145)
 elif component_id=='t09':
  age=n-e['number'];q=prog(age,0,7)
  # Display-number remains behind the circular presenter, a single variant input.
  if age>=0:
   if c.get('numberRole'):
    role=c['numberRole'];im,_=glyph_tile(t['number'],json.dumps(role,sort_keys=True));cut=Image.new('L',im.size,255);dd=ImageDraw.Draw(cut);dd.line((3,im.height-15,im.width-2,35),fill=0,width=2);im.putalpha(ImageChops.multiply(im.getchannel('A'),cut));put(back,im,role['anchorX']-6,role['inkY']-6+(1-q)*22,prog(age,-1,3),2*(1-q))
   else:
    dig=number_tile(t['number'],hashlib.sha256((P/'source/pilot/complete01-02/shared-text-style.json').read_bytes()).hexdigest());put(back,dig,30,43+(1-(1-(1-q)**3))*22,prog(age,-1,3),2*(1-q))
  tag=t['tag'];ti=tile(tag,16,'#fff');w=ti.width-16
  if n>=e['tag']:
   if c.get('tagRole'):
    role=c['tagRole'];iw=role['inkWidth'];ImageDraw.Draw(front).rounded_rectangle((role['anchorX']-iw/2-6,role['inkY']-4,role['anchorX']+iw/2+6,role['inkY']+role['inkHeight']+4),radius=3,fill='#030404');place_text(front,tag,role,role['anchorX'],role['inkY'],n-e['tag'],3)
   else:
    ImageDraw.Draw(front).rounded_rectangle((172,232,181+w,254),radius=3,fill='#030404');put(front,ti,176-8,236-8,prog(n,e['tag']-1,e['tag']+3))
  if not s.get('markerOnly'):
   if s.get('backing') and n>=e['first']:
    if c.get('tornAsset'):
     strip=Image.open(P/c['tornAsset']).convert('RGBA').resize((151,100),Image.Resampling.LANCZOS);put(front,strip,0,260,prog(n,e['first']-1,e['first']+4))
    else:
     strip=torn_backing(148,82);put(front,strip,0,270,prog(n,e['first']-1,e['first']+4))
   first=blank()
   if c.get('detailProfile'):
    role=c['typeRoles']['first'];place_text(first,t['first'],role,role['anchorX'],role['inkY'],n-e['first'],6,dx=32)
   else:text(first,t['first'],s.get('firstSize',26),(s.get('firstX',31),s.get('firstY',307)),s.get('firstColor','#f5f2e9'),n-e['first'],6,'right',max_width=241)
   if s.get('replaceFirst'):first=core.opacity(first,1-prog(n,e['second']-3,e['second']+1))
   front.alpha_composite(first)
   if t.get('second'):
    if c.get('detailProfile'):
     role=c['typeRoles']['second'];place_text(front,t['second'],role,role['anchorX'],role['inkY'],n-e['second'],6,dx=22)
    else:text(front,t['second'],s.get('secondSize',23),(s.get('secondX',109),s.get('secondY',352)),s.get('secondColor','#f5f2e9'),n-e['second'],6,'right',max_width=167)
 elif component_id=='t10':
  text(back,t['title'],65,(143,40),'#fffef9',n-e['title'],5,'rise',center=True,max_width=240)
  text(front,'?' if t['question']=='？' else t['question'],115,(143,284),'#b30829',n-e['question'],6,'scale',font='C:/Windows/Fonts/timesbd.ttf',center=True)
  text(front,t['left'],31,(72,280),'#f7f3ed',n-e['left'],5,'left',center=True,max_width=90)
  text(front,t['right'],31,(220,337),'#f7f3ed',n-e['right'],5,'right',center=True,max_width=100)
 elif component_id=='t11':
  age=n-e['warning'];q=prog(age,0,7)
  if age>=0:
   im=red_warning(max(3,round(89*(.2+.9*q if q<.7 else 1+.1*(1-prog(q,.7,1))))));put(back,im,17,48,prog(age,-1,3))
  text(front,t['warning'],39,(143,238),'#9e0827',n-e['warningText'],7,'scale',center=True,max_width=235)
  if t.get('prefix'):text(front,t['prefix'],20,(33,313),'#f4f1e7',n-e['context'],0,'rise')
  prefix=tile(t.get('prefix',''),20);x=33+max(0,prefix.width-16)
  text(front,t['context'],25,(x,309),'#dac565',n-e['context'],0,'rise',max_width=250-x)
 elif component_id=='t12':
  text(front,t['lead'],25,(143,269),'#fffef8',n-e['lead'],4,'rise',center=True,max_width=245)
  arrow(front,(128,302),(74,352),prog(n,e['leftArrow'],e['leftArrow']+6));arrow(front,(155,302),(209,352),prog(n,e['rightArrow'],e['rightArrow']+6))
  text(front,t['left'],27,(64,365),'#fffdf4',n-e['left'],5,'rise',center=True,max_width=116)
  text(front,t['right'],27,(216,365),'#fffdf4',n-e['right'],5,'rise',center=True,max_width=116)
 else:raise ValueError(component_id)
 return {'backMark':core.opacity(back,fade),'foregroundText':core.opacity(front,fade)}

def detail_subtitle(component_id,n,c,fade):
 """Optional ink-measured roles for the same families; cg13's accepted route is unchanged."""
 back=blank();front=blank();s=c['subtitle'];e=s['events'];t=s['text'];roles=c['typeRoles']
 def role(out,key,event=None,dx=0,dy=0,op=1):
  spec=roles[key];age=n-e.get(event or key,-9);return place_text(out,t[key],spec,spec['anchorX']+dx,spec['inkY']+dy,age,spec.get('entryFrames',6),spec.get('align','center'),dx=spec.get('entryDx',0),op=op)
 if component_id=='t08':
  age=n-e['quantity'];q=prog(n,e['reflow'],e['reflow']+7);q=q*q*(3-2*q)
  for key in ['left','right']:
   spec=roles[key];target=spec['reflowXY'];dx=(target[0]-spec['anchorX'])*q;dy=(target[1]-spec['inkY'])*q
   # Quantity emerges from blurred vertical compression before its spatial reflow.
   layer=blank();role(layer,key,'quantity',dx,dy)
   if age<6 and age>=0:layer=layer.filter(ImageFilter.GaussianBlur((1-prog(age,0,6))*3))
   front.alpha_composite(layer)
  role(front,'subject','subject')
 elif component_id=='t10':
  role(back,'title');role(front,'question');role(front,'left');role(front,'right')
 elif component_id=='t11':
  age=n-e['warning'];q=prog(age,0,6)
  if age>=0:
   asset=Image.open(P/c['warningAsset']).convert('RGBA');asset=asset.crop(asset.getchannel('A').getbbox());scale=.04+1.06*q if q<.85 else 1+.1*(1-prog(q,.85,1));w=round(83*scale);h=round(91*scale);asset=asset.resize((max(1,w),max(1,h)),Image.Resampling.LANCZOS)
   put(back,asset,21+(83-w)/2,47+(91-h)/2,prog(age,-1,2))
  role(front,'warning','warningText');role(front,'prefix','context');role(front,'context','context')
 elif component_id=='t12':
  role(front,'lead');arrow(front,(128,302),(74,352),prog(n,e['leftArrow'],e['leftArrow']+6));arrow(front,(155,302),(209,352),prog(n,e['rightArrow'],e['rightArrow']+6));role(front,'left');role(front,'right')
 return {'backMark':core.opacity(back,fade),'foregroundText':core.opacity(front,fade)}

def compose(raw,frame,c):
 out=render('v04',raw,frame,c);sub=render_subtitle(c['subtitleFamily'],frame,c);canvas=blank()
 for key in ['background','backMark','presenterWindow','evidence','foregroundText']:
  if key in out:canvas.alpha_composite(out[key])
  elif key in sub:canvas.alpha_composite(sub[key])
 return canvas
