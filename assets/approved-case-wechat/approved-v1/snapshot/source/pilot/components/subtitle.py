from .common import *
from .detail_tools import place_text

def title_tile(text,c):
 spec=c['title'];font=ImageFont.truetype(spec['font'],280)
 bb=font.getbbox(text);mask=Image.new('L',(bb[2]-bb[0]+24,bb[3]-bb[1]+24));ImageDraw.Draw(mask).text((12-bb[0],12-bb[1]),text,font=font,fill=255)
 mask=mask.crop(mask.getbbox()).resize((spec['inkWidth']*3,spec['inkHeight']*3),Image.Resampling.LANCZOS)
 pad=18;size=(mask.width+pad*2,mask.height+pad*2);full=Image.new('L',size);full.paste(mask,(pad,pad));out=Image.new('RGBA',size)
 shadow=Image.new('L',size);shadow.paste(mask,(pad+5,pad+8));color=Image.new('RGBA',size,'#635f30');color.putalpha(shadow.filter(ImageFilter.GaussianBlur(3)));out.alpha_composite(color)
 rim=Image.new('RGBA',size,'#c3a94d');rim.putalpha(full.filter(ImageFilter.MaxFilter(5)));out.alpha_composite(rim)
 yy=np.linspace(0,1,size[1]);arr=np.zeros((size[1],size[0],4),np.uint8)
 for y,t in enumerate(yy):arr[y,:,:3]=[round(255-7*t),round(254-51*t),round(173-99*t)]
 arr[:,:,3]=np.array(full);out.alpha_composite(Image.fromarray(arr))
 # Small inward top highlight, independent of background or the source glyph pixels.
 shifted=Image.new('L',size);shifted.paste(full,(1,2));edge=np.clip(np.asarray(full,dtype=int)-np.asarray(shifted,dtype=int),0,255).astype(np.uint8)
 light=Image.new('RGBA',size,'#fffed4');light.putalpha(Image.fromarray(edge));out.alpha_composite(core.opacity(light,.65))
 return out.resize((round(size[0]/3),round(size[1]/3)),Image.Resampling.LANCZOS)

def render(component_id, frame, parameters, disabled=()):
 n=frame;c=parameters;layers={}
 if component_id=='t01':
  if 'text' in disabled:return layers
  clock=c['clock'];fade=1-prog(n,*clock['allExit']);layer=Image.new('RGBA',(286,508))
  if c.get('typeRoles'):
   for role,event in [('first','firstText'),('second','secondText'),('question','questionAndResult'),('result','questionAndResult')]:
    spec=c['typeRoles'][role];age=n-clock[event][0];place_text(layer,c['text'][role],spec,spec['anchorX'],spec['inkY'],age,spec.get('duration',7),spec.get('align','center'),spec.get('entryDx',0))
  else:
   styles=c.get('textLayout',{})
   first=styles.get('first',{'size':26,'xy':[34,321]});second=styles.get('second',{'size':24,'xy':[34,355]})
   reveal(layer,c['text']['first'],first['size'],first['xy'],n-clock['firstText'][0]);reveal(layer,c['text']['second'],second['size'],second['xy'],n-clock['secondText'][0])
   age=n-clock['questionAndResult'][0]
   if age>=0:
    q=styles.get('question',{'size':43,'xy':[62,305],'fill':'#b70923'});r=styles.get('result',{'size':28,'xy':[105,326],'fill':'#fffff5'})
    reveal(layer,c['text']['question'],q['size'],q['xy'],age,q['fill'],duration=9);reveal(layer,c['text']['result'],r['size'],r['xy'],age,r['fill'],duration=9,dx=35)
  layers['questionText']=core.opacity(layer,fade)
 elif component_id=='t02':
  t=c['clock']
  if n>=t['titleStart'] and 'title' not in disabled:
   tile=title_tile(c['text']['title'],c);age=n-t['titleStart'];entry=prog(n,t['titleStart'],t['titleOvershoot']);settle=prog(n,t['titleOvershoot'],t['titleSettle'])
   y=core.mix(-90,16,1-(1-entry)**3) if n<t['titleOvershoot'] else core.mix(16,c['title']['inkY'],settle)
   title=Image.new('RGBA',(286,508));put(title,tile,c['title']['inkX']-6,y-6,prog(age,-1,3),3*(1-prog(age,0,6)));layers['behindTitle']=title
  if 'text' not in disabled:
   line=c['text']['first'] if n<t['captionChange'] else c['text']['second'];caption=Image.new('RGBA',(286,508))
   if c.get('typeRoles'):
    spec=c['typeRoles']['caption'];place_text(caption,line,spec,spec['anchorX'],spec['inkY'],99)
   else:
    tile,m=text_tile(line,c.get('captionSize',12),'#ffffff');put(caption,tile,(286-m['inkWidth'])/2-8,374-8)
   layers['speechCaption']=caption
 else:raise ValueError('Unknown subtitle component '+component_id)
 return layers
