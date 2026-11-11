"""Scene families: independent visual and subtitle providers; composition lives in recipes."""
from .common import *
from PIL import ImageOps
from .detail_tools import place_text
from .media_source import source_frame,fit_frame
W,H=286,508
FONT='C:/Windows/Fonts/Source Han Serif SC Heavy (TrueType).ttf'
def canvas():return Image.new('RGBA',(W,H))
def ease(x):return 1-(1-core.clamp(x))**3
@lru_cache(maxsize=24)
def photo(path):return Image.open(P/path).convert('RGBA')
def cover(im,size):return ImageOps.fit(im,size,method=Image.Resampling.LANCZOS)
def grid():
 im=Image.new('RGBA',(W,H),'#292b2c');d=ImageDraw.Draw(im)
 for x in range(0,W,12):d.line((x,0,x,H),fill='#323435')
 for y in range(0,H,12):d.line((0,y,W,y),fill='#323435')
 return im

def circle(raw,diameter,crop=None):
 # New source has face x70..217,y92..277; crop eyes through neck, live every frame.
 im=cover(raw.crop(crop or (51,82,239,300)),(diameter,diameter)).convert('RGBA');m=Image.new('L',im.size);ImageDraw.Draw(m).ellipse((1,1,diameter-2,diameter-2),fill=255);im.putalpha(m)
 return im

def window(raw,box,ring=2,crop=None):
 out=canvas();x,y,sz=box;ImageDraw.Draw(out).ellipse((x-ring,y-ring,x+sz+ring,y+sz+ring),fill='#fffde9');out.alpha_composite(circle(raw,sz,crop),(round(x),round(y)));return out

def rounded(im,box,radius=8,border=2):
 x,y,w,h=map(round,box);tile=cover(im,(max(1,w),max(1,h)));m=Image.new('L',tile.size);ImageDraw.Draw(m).rounded_rectangle((0,0,w-1,h-1),radius=radius,fill=255);tile.putalpha(m);out=canvas();out.alpha_composite(tile,(x,y));ImageDraw.Draw(out).rounded_rectangle((x,y,x+w-1,y+h-1),radius=radius,outline='#fffde2',width=border);return out

def matte(raw):
 a=np.array(raw.convert('RGB'));mask=np.full((508,286),cv2.GC_BGD,np.uint8)
 cv2.ellipse(mask,(143,180),(88,109),0,0,360,cv2.GC_PR_FGD,-1);cv2.rectangle(mask,(30,274),(267,507),cv2.GC_PR_FGD,-1)
 cv2.ellipse(mask,(147,193),(52,69),0,0,360,cv2.GC_FGD,-1);cv2.rectangle(mask,(78,312),(209,506),cv2.GC_FGD,-1)
 bg=np.zeros((1,65),np.float64);fg=bg.copy();cv2.grabCut(a,mask,None,bg,fg,2,cv2.GC_INIT_WITH_MASK)
 alpha=np.uint8(((mask==1)|(mask==3))*255);im=raw.convert('RGBA');im.putalpha(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(.4)));return im
@lru_cache(maxsize=16)
def rain(phase):
 im=Image.new('RGBA',(W,H),'#10222c');d=ImageDraw.Draw(im);rng=random.Random(108)
 for x in range(0,W,7):
  for k in range(12):
   y=(rng.randrange(508)+phase*3)%540-24;val=rng.randrange(35,140);d.text((x,y),str(rng.randrange(10)),font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',7),fill=(70,val,min(230,val+40),255))
 return im

def vector_panel(path,box,frame=0,fps=30):
 x,y,w,h=map(round,box);out=canvas();d=ImageDraw.Draw(out);d.rounded_rectangle((x,y,x+w,y+h),radius=9,fill='#122733',outline='#0a1119',width=3)
 if isinstance(path,dict):
  art=fit_frame(path,frame,(max(1,w-6),max(1,h-6)),fps,default_fit='cover');out.alpha_composite(art,(x+3,y+3))
 else:
  art=photo(path).copy();art=art.crop(art.getbbox());art.thumbnail((round(w*.92),round(h*.89)),Image.Resampling.LANCZOS);out.alpha_composite(art,(round(x+(w-art.width)/2),round(y+(h-art.height)/2)))
 return out

def render(component_id,raw,frame,parameters,disabled=()):
 n=frame;c=parameters;t=c['clock'];layers={};assets=c.get('assets',{})
 if component_id=='v03':
  bg=cover(source_frame(assets['background'],n,c.get('fps',30)) if isinstance(assets['background'],dict) else photo(assets['background']),(W,H));layers['background']=bg;layers['presenter']=window(raw,tuple(c.get('presenterWindow',[169,28,91])),crop=c.get('presenterCrop'))
  q=ease(prog(n,*t['diagonalIn']));asset=cover(source_frame(assets['example'],n,c.get('fps',30)) if isinstance(assets['example'],dict) else photo(assets['example']),(W,H));m=Image.new('L',(W,H));md=ImageDraw.Draw(m)
  # Irregular diagonal travelling up-left; photo and torn-edge share the same geometry.
  edge=670-q*c.get('diagonalTravel',520);pts=[]
  for y in range(0,509,8):pts.append((round(edge-y*.52+math.sin(y*1.1)*2),y))
  md.polygon(pts+[(286,508),(286,0)],fill=255);asset.putalpha(m);layers['example']=asset;line=canvas();ImageDraw.Draw(line).line(pts,fill='#f6f3dd',width=3);layers['tornEdge']=line
  if n>=t['returnStart']:
   a=prog(n,t['returnStart'],t['returnEnd']);layers['returnPresenter']=core.opacity(raw.convert('RGBA'),a)
 elif component_id=='v05':
  layers['background']=grid();q=ease(prog(n,*t['presenterShrink']));win=c.get('presenterWindow',[65,37,156]);diam=round(286*(1-q)+win[2]*q);x=round(win[0]*q);y=round(win[1]*q)
  box=np.array([0,0,286,508])*(1-q)+np.array(c.get('presenterCrop',[31,76,255,300]))*q;tile=cover(raw.crop(tuple(box)),(diam,round(508*(1-q)+win[2]*q))).convert('RGBA');m=Image.new('L',tile.size);ImageDraw.Draw(m).rounded_rectangle((0,0,tile.width-1,tile.height-1),radius=round(q*diam/2),fill=255);tile.putalpha(m);p=canvas();p.alpha_composite(tile,(x,y));ImageDraw.Draw(p).rounded_rectangle((x,y,x+tile.width-1,y+tile.height-1),radius=round(q*diam/2),outline='#fffeeb',width=2 if q else 0);layers['presenter']=p
  for i,key in enumerate(['left','right']):
   a=prog(n,*t[key+'Card']);e=ease(a)
   if a>0:
    box=c.get('cardBoxes',[[5,244,133,170],[153,244,128,170]])[i];x,y,w,h=box;y+=(1-e)*90;card=canvas();d=ImageDraw.Draw(card);d.rounded_rectangle((x,y,x+w,y+h),radius=8,fill='#222b32',outline='#eee8cf',width=2)
    if isinstance(assets[key],dict):
     art=fit_frame(assets[key],n,(round(w-4),round(h-4)),c.get('fps',30),default_fit='cover');card.alpha_composite(art,(round(x+2),round(y+2)))
    else:
     art=photo(assets[key]);bb=art.getbbox();art=art.crop(bb);art.thumbnail((round(w*.94),round(h*.65)),Image.Resampling.LANCZOS);card.alpha_composite(art,(round(x+(w-art.width)/2),round(y+h-art.height-13)))
    layers[key+'Card']=core.opacity(card,a)
 elif component_id=='v06':
  layers['background']=rain(n)
  if 'presenter' not in disabled:
   if c.get('matteFrames'):
    person=Image.open(P/c['matteFrames']/f'{n:04d}.png').convert('RGBA')
   else:person=matte(raw)
   bounds=c.get('presenterBox',[-3,271,139,247]);person=person.resize(tuple(bounds[2:]),Image.Resampling.LANCZOS);p=canvas();p.alpha_composite(person,tuple(bounds[:2]));layers['presenter']=p
  box=c.get('topPanelBox',[17,40,252,136]);layers['topPanel']=vector_panel(assets['top'],box,n,c.get('fps',30))
  a=prog(n,*t['secondPanel']);scale=1+.18*math.sin(a*math.pi)*math.exp(-a*1.2);box=c.get('secondPanelBox',[0,156,286,164]);x,y,w,h=box;y+=(1-ease(a))*190
  if a>0:layers['secondPanel']=vector_panel(assets['second'],(x+(w-w*scale)/2,y,w*scale,h*scale),n,c.get('fps',30))
 elif component_id=='v07':
  layers['background']=grid();box=c.get('exampleBox',[0,156,286,184]);x,y,w,h=box;panel=canvas();art=fit_frame(assets['example'],n,(round(w),round(h)),c.get('fps',30),default_fit='cover') if isinstance(assets['example'],dict) else photo(assets['example']).copy();bb=art.getbbox();art=art.crop(bb) if bb else art;art.thumbnail((round(w),round(h)),Image.Resampling.LANCZOS);panel.alpha_composite(art,(round(x+(w-art.width)/2),round(y+(h-art.height)/2)));ImageDraw.Draw(panel).rectangle((0,y,285,y+2),fill='white');ImageDraw.Draw(panel).rectangle((0,y+h-2,285,y+h),fill='white');layers['example']=panel;layers['presenter']=window(raw,tuple(c.get('presenterWindow',[174,98,97])),crop=c.get('presenterCrop'));layers['ordinaryCaption']=ordinary_caption(n,c)
 else:raise ValueError(component_id)
 if 'pictures' in disabled:
  layers={k:v for k,v in layers.items() if k not in ['example','leftCard','rightCard','topPanel','secondPanel']}
 return layers

def line(out,text,size,xy,age,color='#ffffff',duration=7,font=None):
 if font is None:return reveal(out,text,size,xy,age,color,duration=duration,dx=14)
 if age<0:return
 tile,m=text_tile(text,size,color,font=font);a=prog(age,0,duration);tile=tile.resize((max(1,round(tile.width*max(.05,a))),tile.height),Image.Resampling.BICUBIC);put(out,tile,xy[0]-8+14*(1-a),xy[1]-8,prog(age,-1,3),2*(1-a))
def render_subtitle(component_id,frame,parameters,disabled=()):
 if 'text' in disabled:return {}
 n=frame;c=parameters;t=c['clock'];txt=c['text'];out=canvas()
 if component_id=='t03' and c.get('detailProfile'):
  for role,txtkey,clockkey in [('context','context','context'),('statement','change','change'),('result','result','result')]:
   spec=c['typeRoles'][role];place_text(out,txt[txtkey],spec,spec['anchorX'],spec['inkY'],n-t[clockkey],spec.get('duration',7),spec.get('align','center'),spec.get('entryDx',14))
  out=core.opacity(out,1-prog(n,t['returnStart'],t['returnEnd']))
 elif component_id=='t03':
  line(out,txt['context'],23,(13,67),n-t['context'],font=c['fontRoles']['body']['path']);line(out,txt['change'],30,(13,113),n-t['change'],font=c['fontRoles']['statement']['path']);line(out,txt['result'],24,(152,345),n-t['result'],font=c['fontRoles']['body']['path'])
  out=core.opacity(out,1-prog(n,t['returnStart'],t['returnEnd']))
 elif component_id=='t05':
  if c.get('typeRoles'):
   for role,key,clock in [('title','title','title'),('left','left','leftLabel'),('right','right','rightLabel')]:
    spec=c['typeRoles'][role];place_text(out,txt[key],spec,spec['anchorX'],spec['inkY'],n-t[clock],spec.get('duration',7),'center',spec.get('entryDx',14))
  else:
   line(out,txt['title'],30,(38,197),n-t['title'],font=c['fontRoles']['body']['path'])
   for i,key in enumerate(['left','right']):line(out,txt[key],20,(14+148*i,259),n-t[key+'Label'],'#fff4b7',font=c['fontRoles']['labels']['path'])
 elif component_id=='t06':
  if c.get('typeRoles'):
   for role,key,event in [('first','first','firstText'),('second','second','secondText')]:
    spec=c['typeRoles'][role];y=spec['inkY']+(1-ease(prog(n,*t['secondPanel'])))*190 if role=='second' else spec['inkY'];place_text(out,txt[key],spec,spec['anchorX'],y,n-t[event],spec.get('duration',7),'center',spec.get('entryDx',0))
  else:
   line(out,txt['first'],30,(39,90),n-t['firstText'],font=c['fontRoles']['body']['path'])
   if n>=t['secondText']:
    a=prog(n,*t['secondPanel']);line(out,txt['second'],29,(39,211+(1-ease(a))*190),n-t['secondText'],font=c['fontRoles']['body']['path'])
 else:raise ValueError(component_id)
 return {'text':out}

def ordinary_caption(frame,parameters):
 # Ordinary spoken caption belongs to the v07 complete recipe, not a new effect family.
 c=parameters;out=canvas();n=frame
 for cue in c['captions']:
  if cue['in']<=n<cue['out']:
   
   if c.get('typeRoles'):
    spec=c['typeRoles']['caption'];place_text(out,cue['text'],spec,spec['anchorX'],spec['inkY'],99)
   else:
    tile,m=text_tile(cue['text'],14,font=c['fontRoles']['body']['path']);put(out,tile,(286-tile.width)/2,370)
 return out
