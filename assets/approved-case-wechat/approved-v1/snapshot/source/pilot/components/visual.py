from .common import *

def vignette(op):
 yy,xx=np.mgrid[:508,:286];r=np.sqrt(((xx-143)/148)**2+((yy-205)/215)**2)
 a=np.clip((r-.68)/.42,0,1)*op
 rgba=np.zeros((508,286,4),np.uint8);rgba[:,:,3]=np.uint8(a*255)
 return Image.fromarray(rgba)

def icon():
 s=512;yy,xx=np.mgrid[:s,:s].astype(float)
 mask=Image.new('L',(s,s));d=ImageDraw.Draw(mask);d.polygon([(256,35),(479,439),(33,439)],fill=255)
 # Rounded cast-metal perimeter, modelled from distance to its own silhouette.
 smooth=np.asarray(mask.filter(ImageFilter.GaussianBlur(8)))
 alpha=np.clip((smooth.astype(float)-96)*3,0,255).astype(np.uint8)
 solid=(alpha>127).astype(np.uint8);dist=cv2.distanceTransform(solid,cv2.DIST_L2,5)
 nx=cv2.Sobel(dist,cv2.CV_32F,1,0,ksize=3);ny=cv2.Sobel(dist,cv2.CV_32F,0,1,ksize=3)
 normal=np.sqrt(nx*nx+ny*ny+1e-4);lighting=np.clip((-nx*.65-ny*.9)/normal,-1,1)
 arr=np.zeros((s,s,4),np.uint8);t=yy/s
 body=np.stack([245-23*t,190-70*t,60-48*t],axis=2)
 bevel=dist<13;shine=np.clip((lighting+1)/2,0,1)
 highlight=np.exp(-((yy-xx*.25-125)/25)**2)*42
 for k in range(3):
  values=body[:,:,k]+highlight*(1 if k<2 else .6)
  edge=np.array([252,215,119])[k]*shine+np.array([98,57,18])[k]*(1-shine)
  values=np.where(bevel,edge,values)
  arr[:,:,k]=np.clip(values,0,255).astype(np.uint8)
 arr[:,:,3]=alpha;front=Image.fromarray(arr)
 im=Image.new('RGBA',(s,s))
 # Extruded dark edge and tight ambient shadow, visibly different from a flat emoji.
 edge=Image.new('RGBA',(s,s),'#73461c');edge.putalpha(Image.fromarray(alpha))
 for off in range(11,0,-1):im.alpha_composite(edge,(off,off))
 im.alpha_composite(front)
 # Inset channel separates rim and enamel; white enamel punctuation has a dark recess.
 inset=Image.fromarray(np.uint8((dist>20)*190));line=Image.fromarray(np.uint8(((dist>17)&(dist<20))*155));channel=Image.new('RGBA',(s,s),'#845414');channel.putalpha(line);im.alpha_composite(channel)
 mark=Image.new('L',(s,s));md=ImageDraw.Draw(mark);md.rounded_rectangle((234,151,278,296),radius=14,fill=255);md.ellipse((234,323,278,367),fill=255)
 shadow=Image.new('L',(s,s));shadow.paste(mark,(3,5));black=Image.new('RGBA',(s,s),'#57300f');black.putalpha(shadow.filter(ImageFilter.GaussianBlur(2)));im.alpha_composite(black)
 white=Image.new('RGBA',(s,s),'#fff5d7');white.putalpha(mark);im.alpha_composite(white)
 return im

def symbols(n,c):
 out=Image.new('RGBA',(286,508));rng=random.Random(c['symbol']['seed']);tile=Image.open(P/c['symbol']['assetPath']).convert('RGBA') if c['symbol'].get('assetPath') else icon();tile=tile.crop(tile.getbbox())
 for j in range(c['symbol']['count']):
  start=rng.uniform(c['clock'].get('symbolFirst',1),c['clock']['symbolSpawnEnd']);x=rng.uniform(0,286);radius=rng.uniform(*c['symbol'].get('sizeRange',[24,65]));speed=rng.uniform(*c['symbol'].get('speedRange',[12,21]));spin=rng.uniform(*c['symbol'].get('spinRange',[9,19]));phase=rng.uniform(0,6.28);age=n-start
  if age<0:continue
  y=-90+age*speed
  if y>600:continue
  flip=max(.13,abs(math.cos(age*.22+phase)));h=round(radius);w=max(3,round(h*flip));im=tile.resize((w,h),Image.Resampling.LANCZOS).rotate(age*spin,resample=Image.Resampling.BICUBIC,expand=True)
  blur=c['symbol'].get('nearBlur',1.6) if radius>47 else c['symbol'].get('farBlur',.4)
  alpha=1-prog(n,c['clock']['symbolExitEnd']-8,c['clock']['symbolExitEnd'])
  put(out,im,x-im.width/2,y-im.height/2,alpha,blur)
 return out

def reframe_presenter(raw,c):
 r=c.get('presenterReframe')
 if not r:return raw.convert('RGBA')
 s=r['scale'];im=raw.resize((round(286*s),round(508*s)),Image.Resampling.LANCZOS);x,y=r['cropXY'];return im.crop((x,y,x+286,y+508)).convert('RGBA')

def head_matte(raw):
 a=np.array(raw.convert('RGB'));h,w=a.shape[:2]
 # Explicit foreground/background seeds on the new presenter's head; no mask from old source.
 mask=np.full((h,w),cv2.GC_BGD,np.uint8)
 ellipse=np.zeros((h,w),np.uint8);cv2.ellipse(ellipse,(143,153),(94,125),0,0,360,255,-1);mask[ellipse>0]=cv2.GC_PR_BGD
 probable=np.zeros_like(ellipse);cv2.ellipse(probable,(143,153),(77,110),0,0,360,255,-1);mask[probable>0]=cv2.GC_PR_FGD
 sure=np.zeros_like(ellipse);cv2.ellipse(sure,(143,162),(45,71),0,0,360,255,-1);cv2.ellipse(sure,(143,100),(40,30),0,0,360,255,-1);mask[sure>0]=cv2.GC_FGD
 bg=np.zeros((1,65),np.float64);fg=np.zeros((1,65),np.float64);cv2.grabCut(a,mask,None,bg,fg,3,cv2.GC_INIT_WITH_MASK)
 matte=np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD),255,0).astype(np.uint8)
 matte=cv2.medianBlur(matte,3)
 return Image.fromarray(matte).filter(ImageFilter.GaussianBlur(.45))

def render(component_id, raw, frame, parameters, disabled=()):
 n=frame;c=parameters;layers={}
 if component_id=='v01':
  layers['presenter']=raw.convert('RGBA');clock=c['clock'];fade=1-prog(n,*clock['allExit'])
  if 'vignette' not in disabled:layers['focus']=vignette(prog(n,*clock['vignetteIn'])*fade)
  if 'photo' not in disabled:
   photo=Image.open(P/c['asset']).resize((286,153),Image.Resampling.LANCZOS).convert('RGBA')
   photo=ImageEnhance.Brightness(photo).enhance(c.get('photoBrightness',.62))
   yy=np.arange(153)[:,None];a=np.repeat(np.clip(yy/45,0,1),286,axis=1)*255
   photo.putalpha(Image.fromarray(a.astype(np.uint8)));q=prog(n,*clock['photoIn']);layer=Image.new('RGBA',(286,508));put(layer,photo,0,355+(1-q)*75,q*fade);layers['workPhoto']=layer
 elif component_id=='v02':
  presenter=reframe_presenter(raw,c);layers['presenter']=presenter
  if n>=c['clock']['titleStart'] and 'occlusion' not in disabled:
   
   if c.get('matteFrames'):
    fg=Image.open(P/c['matteFrames']/f'{n:04d}.png').convert('RGBA');fg=reframe_presenter(fg,c)
   else:
    fg=presenter.copy();fg.putalpha(head_matte(presenter))
   layers['presenterForeground']=fg
  if 'symbols' not in disabled:layers['symbols']=symbols(n,c)
 else:raise ValueError('Unknown visual component '+component_id)
 return layers
