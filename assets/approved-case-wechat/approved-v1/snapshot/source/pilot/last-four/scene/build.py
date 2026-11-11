from pathlib import Path
import sys,json,subprocess,copy
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'))
from components.common import core,load
from components.runtime import compose,validate_recipe,layers
from components.pairing import check
from components.media_source import fit_frame
S=P/'source/pilot/last-four/scene';O=P/'render/pilot/last-four/scene';R=P/'reviews/last-four/scene'
def sha(p):return core.file_sha(p)
def dump(p,v):core.dump(p,v)
c=load(P/'source/pilot/detail-rest/scene/cg09-input.json');c['assets']['example']={'type':'video','path':'source/pilot/last-four/scene/assets/experience-review.mp4','sourceIn':4,'sourceOut':4+94/30,'timelineStartFrame':0,'speed':1,'endBehavior':'hold','fit':'cover','anchor':[.5,.5],'audio':'mute'}
# Ordinary speech captions retain font aspect ratio; each cue has its own natural width.
role=c['typeRoles']['caption'];role.pop('inkWidth',None);role.pop('inkHeight',None);role['size']=14;role['layoutPolicy']='natural-font-metrics';role['anchorX']=143
c['purpose']='别人踩过的坑提前了解，少走很多弯路。案例窗以真实办公复盘视频承接经验学习，人物圆窗解释，框景和主字幕保持原机制；内部素材运动由视频时钟真实读取。';c['assetMeaning']='真实办公实拍示意，不称画中人物为讲述者或真实案例证据';dump(S/'cg09-input.json',c)
r=load(P/'source/pilot/detail-rest/scene/cg09-recipe.json');r.update(input='source/pilot/last-four/scene/cg09-input.json',verificationState='trial',completeGroupValidated=False)
for ref in r['components'].values():ref['sha256']=sha(P/ref['source'])
deps=['source/pilot/components/common.py','source/pilot/components/media_source.py','source/pilot/components/detail_tools.py','source/pilot/components/runtime.py','source/pilot/components/pairing.py','source/pilot/t04_render.py','source/pilot/last-four/scene/cg09-input.json','source/pilot/last-four/scene/assets/provenance.json','source/pilot/last-four/scene/assets/experience-review.mp4']
r['supportBindings']={x:sha(P/x) for x in deps};dump(S/'cg09-recipe.json',r);validate_recipe(r);check(r,c,P)
N=c['frames'];src=load(P/'source/pilot/new-input/manifest.json')['path'];dec=subprocess.Popen(['ffmpeg','-v','error','-ss',str(c['rawRange'][0]),'-i',src,'-frames:v',str(N),'-vf','fps=30,scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE);fp=O/'cg09.mp4'
enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-s','286x508','-pix_fmt','rgb24','-r','30','-i','pipe:0','-ss',str(c['rawRange'][0]),'-i',src,'-t',str(N/30),'-map','0:v','-map','1:a:0','-vf','scale=572:1016:flags=lanczos','-c:v','libx264','-threads','2','-crf','15','-preset','fast','-c:a','aac','-pix_fmt','yuv420p','-movflags','+faststart',str(fp)],stdin=subprocess.PIPE)
for n in range(N):
 data=dec.stdout.read(286*508*3);assert len(data)==286*508*3;raw=Image.frombytes('RGB',(286,508),data);im=compose(r,raw,n,c);enc.stdin.write(im.convert('RGB').tobytes())
 if n in [0,10,30,50,70,93]:im.save(R/f'cg09-{n:03d}.png')
enc.stdin.close();assert enc.wait()==dec.wait()==0
subprocess.run(['ffmpeg','-v','error','-i',str(fp),'-f','null','-'],check=True)
# Show internal video changes with the SAME presenter frame and all other inputs frozen.
fixed=Image.new('RGBA',(286,508),'#151e29');a=layers(r,fixed,10,c)['visual.example'];b=layers(r,fixed,70,c)['visual.example'];changed=int(np.any(np.asarray(a)!=np.asarray(b),2).sum());assert changed>100
x=compose(r,fixed,45,c);parts=layers(r,fixed,45,c);z=Image.new('RGBA',(286,508))
for key in r['layerOrder']:
 if key in parts:z.alpha_composite(parts[key])
assert np.array_equal(np.asarray(x),np.asarray(z))
# Actual encoded comparison and motion crops.
frames=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(fp),'-vf','scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1']),np.uint8).reshape(-1,508,286,3);assert len(frames)==N
board=Image.new('RGB',(5*292,1060),'#192634');d=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',12)
for j,n in enumerate([0,20,40,65,93]):
 sf=531+round(n/93*66);ref=Image.open(P/'observations/frame-audit/frames'/f'{sf+1:04d}.jpg');board.paste(ref,(j*292,25));board.paste(Image.fromarray(frames[n]),(j*292,548));d.text((j*292,3),f'原f{sf}／新f{n} 阶段对齐',font=font,fill='white')
board.save(R/'cg09-encoded-comparison.jpg')
limitations=['案例窗已换真实动态办公视频，动作内容与原片捂脸/闹钟案例不同；属于新口播语义替换，不称同一素材','原字体身份未确认，圆窗与框景几何保持当前校准范围','素材原音轨静音，仅保留新口播；词点与独立音效未听审']
g={'occurrence':'cg09','name':'横线框景＋动态经验案例视频','file':fp.relative_to(P).as_posix(),'referenceFile':'observations/accepted-review/cg09/reference-clip.mp4','recipe':'source/pilot/last-four/scene/cg09-recipe.json','input':'source/pilot/last-four/scene/cg09-input.json','frameCount':N,'rawRange':c['rawRange'],'sourceRange':[531,598],'visualFamily':'v07','subtitleFamily':None,'sha256':sha(fp),'limitations':limitations,'verificationState':'trial'}
dump(O/'manifest.json',{'groups':[g],'stage':'03-pilot','accepted':False});dump(R/'verification.json',{'fullDecode':True,'frames':N,'internalMotionChangedPixels':changed,'fixedPresenterMotionTest':True,'independentLayerRecompositionExact':True,'videoSlotActuallyDecoded':True,'staticSVGReplaced':True,'limitations':limitations,'sha256':sha(fp)});print('cg09 dynamic video complete',changed)
