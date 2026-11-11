"""Shared still/vector/video source; container motion belongs to family components.
Legacy string paths preserve current image behavior. Structured slots opt into playback.
"""
from pathlib import Path
from functools import lru_cache
import json,math,subprocess,hashlib,io,base64
from PIL import Image,ImageOps
from .common import P
IMAGE_EXT={'.png','.jpg','.jpeg','.webp','.bmp','.tif','.tiff'}
VIDEO_EXT={'.mp4','.mov','.mkv','.webm','.m4v','.avi'}

def normalize(slot):
 s={'path':slot} if isinstance(slot,str) else dict(slot)
 if not s.get('path'):raise ValueError('Media source path missing')
 path=Path(s['path']);path=path if path.is_absolute() else P/path
 if not path.is_file():raise FileNotFoundError(path)
 ext=path.suffix.lower();kind=s.get('type','auto')
 if kind=='auto':kind='svg' if ext=='.svg' else 'video' if ext in VIDEO_EXT else 'image' if ext in IMAGE_EXT else None
 if kind not in ('image','video','svg'):raise ValueError('Unsupported media type/extension')
 s.update(path=str(path),type=kind)
 if s.get('fit','contain') not in ('cover','contain','stretch'):raise ValueError('Invalid media fit')
 if s.get('endBehavior','hold') not in ('hold','loop','transparent'):raise ValueError('Invalid video endBehavior')
 if float(s.get('speed',1))<=0:raise ValueError('Video speed must be positive')
 if s.get('audio','mute')!='mute':raise ValueError('Material audio requires explicit shared-timeline mixing; this visual source does not mix it')
 return s

def stamp(path):
 p=Path(path);st=p.stat();return (str(p),st.st_mtime_ns,st.st_size)

@lru_cache(maxsize=32)
def _image(key):
 with Image.open(key[0]) as im:return ImageOps.exif_transpose(im).convert('RGBA')

@lru_cache(maxsize=8)
def _probe(key):
 data=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=duration,avg_frame_rate,width,height:format=duration','-of','json',key[0]]))
 stream=data['streams'][0];num,den=map(float,stream.get('avg_frame_rate','30/1').split('/'));fps=num/den if den and num else 30
 duration=float(stream.get('duration',data.get('format',{}).get('duration',0)))
 if duration<=0:raise ValueError('Video duration unknown')
 return duration,fps

@lru_cache(maxsize=48)
def _video(key,second):
 # ffmpeg accurate seeking, decoded frame by source time, not a frozen poster.
 data=subprocess.check_output(['ffmpeg','-v','error','-threads','1','-ss',f'{second:.9f}','-i',key[0],'-frames:v','1','-f','image2pipe','-c:v','png','-threads','1','pipe:1'])
 if not data:raise ValueError('Video source produced no frame')
 return Image.open(io.BytesIO(data)).convert('RGBA')

@lru_cache(maxsize=8)
def _svg(key,scale):
 from playwright.sync_api import sync_playwright
 encoded=base64.b64encode(Path(key[0]).read_bytes()).decode('ascii')
 # SVG loaded as an image; no inline script execution or raster stand-in identity.
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe')
  page=b.new_page(viewport={'width':512,'height':512},device_scale_factor=scale,java_script_enabled=True)
  page.route('http://**/*',lambda r:r.abort());page.route('https://**/*',lambda r:r.abort())
  page.set_content('<style>html,body{margin:0;background:transparent}img{display:block;max-width:none}</style><img src="data:image/svg+xml;base64,'+encoded+'">')
  page.wait_for_function('document.images[0].complete && document.images[0].naturalWidth>0')
  data=page.locator('img').screenshot(omit_background=True);b.close()
 return Image.open(io.BytesIO(data)).convert('RGBA')

def source_frame(slot,frame=0,fps=30):
 s=normalize(slot);key=stamp(s['path'])
 if s['type']=='image':im=_image(key).copy()
 elif s['type']=='svg':
  if s.get('rasterPath'):
   p=Path(s['rasterPath']);p=p if p.is_absolute() else P/p
   if s.get('sourceSha256')!=hashlib.sha256(Path(s['path']).read_bytes()).hexdigest():raise ValueError('SVG cache lacks matching sourceSha256')
   im=_image(stamp(p)).copy()
  else:im=_svg(key,float(s.get('rasterScale',4))).copy()
 else:
  duration,source_fps=_probe(key);begin=float(s.get('sourceIn',0));end=float(s.get('sourceOut',duration));start=int(s.get('timelineStartFrame',0))
  if not 0<=begin<end<=duration+.001:raise ValueError('Video source range invalid')
  if frame<start:return Image.new('RGBA',(1,1))
  t=begin+(frame-start)/fps*float(s.get('speed',1));behavior=s.get('endBehavior','hold')
  if t>=end:
   if behavior=='transparent':return Image.new('RGBA',(1,1))
   t=begin+(t-begin)%(end-begin) if behavior=='loop' else max(begin,end-1/source_fps)
  im=_video(key,round(min(t,max(begin,duration-1/source_fps)),9)).copy()
 if s.get('crop'):im=im.crop(tuple(s['crop']))
 if s.get('trimAlpha',False):
  bb=im.getchannel('A').getbbox()
  if bb:im=im.crop(bb)
 return im

def fit_frame(slot,frame,size,fps=30,default_fit='contain'):
 s=normalize(slot);im=source_frame(s,frame,fps);size=tuple(map(int,size));fit=s.get('fit',default_fit);anchor=s.get('anchor',[.5,.5])
 if len(anchor)!=2 or any(not 0<=float(x)<=1 for x in anchor):raise ValueError('Anchor must be normalized [x,y]')
 if fit=='stretch':return im.resize(size,Image.Resampling.LANCZOS)
 if fit=='cover':return ImageOps.fit(im,size,method=Image.Resampling.LANCZOS,centering=tuple(anchor))
 im.thumbnail(size,Image.Resampling.LANCZOS);out=Image.new('RGBA',size);out.alpha_composite(im,(round((size[0]-im.width)*anchor[0]),round((size[1]-im.height)*anchor[1])));return out
