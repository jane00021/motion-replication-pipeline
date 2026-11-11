import sys,json,copy,subprocess,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[3];sys.path.insert(0,str(P/'source/pilot'))
from components.common import *
from components.runtime import compose,validate_recipe
from components.pairing import check
S=P/'source/pilot/detail-two';O=P/'render/pilot/detail-two';R=P/'reviews/detail-two';O.mkdir(exist_ok=True)
fonts=load(S/'fonts.json');src=load(P/'source/pilot/new-input/manifest.json')['path']
def dump(p,v):core.dump(p,v)
def sha(p):return core.file_sha(p)
def style(font,w,h,x,y,outline=0,fill='#fffef7'):
 return {'path':fonts[font],'size':44,'inkWidth':w,'inkHeight':h,'anchorX':x,'inkY':y,'align':'center','fill':fill,'outlinePx':outline,'outline':'#111319','shadow':{'dx':.85,'dy':1.3,'blur':.4,'opacity':.85}}
c4=load(P/'source/pilot/batches/scene/cg04-input.json');c4.update(detailProfile='measured-ink-roles-svg-v1',presenterCrop=[31,76,255,300],presenterWindow=[163,29,102],diagonalTravel=420)
c4['assets']={'background':'source/pilot/detail-two/assets/business-skyline.png','example':'source/pilot/detail-two/assets/business-risk-desk.png'}
c4['typeRoles']={'context':style('serif-bold',109,26,79,64),'statement':style('sans-bold',128,39,85,109,1.5),'result':style('serif-bold',114,27,195,343)}
c4['typeRoles']['statement']['weightPx']=1.05
c4['text']={'context':'生意风光','change':'风险自担','result':'亏损难翻身'}
c4['clock'].update(diagonalIn=[69,115]);c4['typeRoles']['statement']['entryDx']=8
c13=load(P/'source/pilot/batches/circle/cg13-input.json');c13.update(detailProfile='measured-ink-roles-svg-v1')
c13['visual']['presenterCrop']=[31,76,255,300];c13['visual']['evidence']={'path':'source/pilot/detail-two/assets/practical-skills-spread.png','svgSource':'source/pilot/detail-two/assets/practical-skills-spread.svg','transparent':True,'start':10,'end':75,'xy':[22,249],'size':[242,178]}
c13['subtitle']['text'].update(first='与其空想',second='本事落地');c13['subtitle']['events'].update(first=5,second=34);c13['typeRoles']={'first':style('serif-heavy',143,34,143,316,fill='#a00b29'),'second':style('serif-bold',148,34,143,326)}
c13['typeRoles']['second']['weightPx']=.25
c13['semanticBindings']['purpose']='与其空想，不如学个能落地的本事：红色铺垫让位给白色结论；书本、技能证书和代码矢量素材支撑行动表达。标题按真实字面中心对齐，不保留旧照片背景。'
for id,c in [('cg04',c4),('cg13',c13)]:
 if id=='cg04':c['frames']=c['frameCount']
 else:c['frameCount']=c['frames']
 dump(S/f'{id}-input.json',c)
 old=P/('source/pilot/batches/scene/cg04-recipe.json' if id=='cg04' else 'source/pilot/batches/circle/cg13-recipe.json');r=load(old)
 r.update(input=f'source/pilot/detail-two/{id}-input.json',verificationState='trial',completeGroupValidated=False)
 if id=='cg04':r['layerOrder']=['visual.background','visual.example','visual.tornEdge','visual.presenter','visual.returnPresenter','subtitle.text']
 for ref in r['components'].values():ref['sha256']=sha(P/ref['source'])
 r['supportBindings']={dep:sha(P/dep) for dep in ['source/pilot/t04_render.py','source/pilot/components/runtime.py','source/pilot/components/pairing.py','source/pilot/components/detail_tools.py']}
 for p in list((S/'assets').glob('*')):
  if p.is_file():r['supportBindings'][p.relative_to(P).as_posix()]=sha(p)
 r['supportBindings'][f'source/pilot/detail-two/{id}-input.json']=sha(S/f'{id}-input.json')
 dump(S/f'{id}-recipe.json',r)
 validate_recipe(r);check(r,c,P)
 # Encode at 2x native, streaming all frames, no reference pixels.
 N=c['frames'];dec=subprocess.Popen(['ffmpeg','-v','error','-threads','2','-ss',str(c['rawRange'][0]),'-i',src,'-frames:v',str(N),'-vf','fps=30,scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
 out=O/f'{id}.mp4';enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','286x508','-r','30','-i','pipe:0','-ss',str(c['rawRange'][0]),'-i',src,'-t',str(N/30),'-map','0:v','-map','1:a:0','-vf','scale=572:1016:flags=lanczos','-c:v','libx264','-threads','2','-crf','15','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for n in range(N):
  data=dec.stdout.read(286*508*3);assert len(data)==286*508*3
  raw=Image.frombytes('RGB',(286,508),data);im=compose(r,raw,n,c);enc.stdin.write(im.convert('RGB').tobytes())
  if n in [0,6,round(N*.3),round(N*.5),round(N*.7),N-8,N-1]:im.save(R/f'{id}-f{n:03d}.png')
 enc.stdin.close();assert enc.wait()==0;assert dec.wait()==0
 subprocess.run(['ffmpeg','-v','error','-i',str(out),'-f','null','-'],check=True)
 print(id,sha(out),flush=True)
