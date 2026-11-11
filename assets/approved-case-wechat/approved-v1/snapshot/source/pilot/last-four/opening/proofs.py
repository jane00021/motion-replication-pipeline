import sys,json,copy,cv2
from pathlib import Path
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'))
from components.common import *
from components.subtitle import render,title_tile
from components.runtime import compose,validate_recipe
from components.detail_tools import glyph_tile
S=P/'source/pilot/last-four/opening';R=P/'reviews/last-four/opening';O=P/'render/pilot/last-four/opening'
for id in ['cg01','cg02']:
 c=load(S/f'{id}-input.json');sf,ef=c['sourceRange'];N=ef-sf;sheet=Image.new('RGB',(1430,1044),'#20252a');d=ImageDraw.Draw(sheet)
 if id=='cg01':
  c['text'].update(first='为什么',second='越努力上班',result='越存不到钱');c['clock'].update(firstText=[9,14],secondText=[15,24],questionAndResult=[43,48],allExit=[55,66]);c['typeRoles']['second']['inkWidth']=104;c['typeRoles']['result'].update(inkWidth=112,anchorX=197)
 else:c['text']['title']='财富真相';c['clock'].update(titleStart=45,titleOvershoot=50,titleSettle=56);c['title'].update(inkWidth=274,inkHeight=76,inkX=6,inkY=7)
 core.dump(R/f'{id}-same-word-input.json',c)
 for k,n in enumerate([0,N//5,N*2//5,N*3//5,N-1]):
  ref=Image.open(P/f'observations/frame-audit/frames/{sf+n+1:04d}.jpg');sheet.paste(ref,(k*286,24));out=Image.new('RGBA',(286,508),'#20252a');ls=render(c['components']['subtitle'],n,c)
  for im in ls.values():out.alpha_composite(im)
  sheet.paste(out.convert('RGB'),(k*286,536));d.text((k*286+4,6),f'source {sf+n} / local {n}',fill='white')
 sheet.save(R/f'{id}-same-word-process.jpg')
 m=load(O/'manifest.json');g=next(x for x in m['groups'] if x['occurrence']==id);N=g['frameCount'];cap=cv2.VideoCapture(str(P/g['file']));sheet=Image.new('RGB',(1430,1044),'#20252a');d=ImageDraw.Draw(sheet)
 for k,n in enumerate([0,N//5,N*2//5,N*3//5,N-1]):
  f=sf+round(n/(N-1)*(ef-sf-1));ref=Image.open(P/f'observations/frame-audit/frames/{f+1:04d}.jpg');sheet.paste(ref,(k*286,24));cap.set(cv2.CAP_PROP_POS_FRAMES,n);ok,a=cap.read();assert ok;out=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((286,508));sheet.paste(out,(k*286,536));d.text((k*286+4,6),f'ref {f} / new {n},stage aligned',fill='white')
 cap.release();sheet.save(R/f'{id}-encoded-compare.jpg')
# precise layer recomposition determinism and editable strings
checks=[]
for id in ['cg01','cg02']:
 c=load(S/f'{id}-input.json');r=load(S/f'{id}-recipe.json');validate_recipe(r);cap=cv2.VideoCapture(load(P/'source/pilot/new-input/manifest.json')['path']);cap.set(cv2.CAP_PROP_POS_MSEC,c['rawStart']*1000);ok,a=cap.read();cap.release();raw=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((286,508));n=130 if id=='cg01' else 70;im=compose(r,raw,n,c);im2=compose(r,raw,n,c);assert im.tobytes()==im2.tobytes();p=copy.deepcopy(c);p['text']['result' if id=='cg01' else 'title']='编辑验证';assert compose(r,raw,n,p).tobytes()!=im.tobytes();checks.append({'occurrence':id,'deterministic':True,'editableTextChangesPixels':True,'fullDecode':True})
core.dump(R/'checks.json',checks)
core.dump(R/'review.json',{'stage':'03 trial','scope':['cg01','cg02'],'method':'同family组件新增角色墨迹盒/材质入口，01保留真实图片，02已有风险SVG复用；共享配方时钟，RVM预计算RGBA使巨字在人与手之后','actualChecks':['原片process-evidence实际观察','两组真实编码及全解码','编码新片/原片阶段对照','同字过程图与原文参数','runtime确定性重组、改字改变像素','独立RGBA字幕序列258帧'],'notDone':['未连续视觉观看','未声音听审','未证明原字体身份','未通过用户视觉认可'],'largest3':{'cg01':['暗角聚焦中心与原片仍有几何差异','工作照片为可替换真实键盘图片，与源素材取景不同','正文宋体候选字形、问句接管间隔按新口播延长'],'cg02':['警示SVG代替金币，轮廓材质与源不同','字体巨字已顶部撑满并在人后，具体字形/金属高光仍近似','RVM局部发丝柔边和下落符号疏密仍需用户复审']},'iteration':{'found':['前轮固定字面定位不随角色校准','前轮粗GrabCut只抠头不能可靠保护手','前轮警示图标质量较低'],'fix':['角色化typeRoles真实墨迹盒+独立阴影描边','RVM全人物递归RGBA覆盖头发/肩膀/手','复用已存在精制红警示SVG、按alpha裁图，深度旋转下落保留']}})
