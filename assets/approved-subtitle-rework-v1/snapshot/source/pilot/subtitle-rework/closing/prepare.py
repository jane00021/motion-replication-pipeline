from pathlib import Path
import sys,importlib,json,copy
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'));R=importlib.import_module('batch_runtime');V=importlib.import_module('subtitle-rework.closing.provider')
from PIL import Image,ImageDraw
S=P/'source/pilot/subtitle-rework/closing';Q=P/'reviews/pilot/subtitle-rework/closing'
font='D:/SKILL/font-check/SourceHanSerifSC-Bold.otf';sh={'x':.7,'y':1.,'blur':.4,'color':'#211e17','opacity':.85}
styles={'white':{'font':font,'size':16,'fill':'#fffdf0','shadow':sh},'gold':{'font':font,'size':21,'fill':'#dcc34b','shadow':sh,'outline':.18,'outlineColor':'#4b3d14'}}
same={
 'N21':{'mode':'split-line','setup':'有的人睡五六个小时','conclusion':'就能够精神焕发','splitDistance':10,'clock':{'split':[1,7],'takeover':[3,8],'exit':[40,43]}},
 'N22':{'mode':'diagonal-line','setupParts':['而有的人','要睡9个小时'],'conclusion':'才能充满活力','splitX':8,'splitY':11,'clock':{'split':[0,7],'takeover':[1,6]}},
 'N24':{'mode':'typed-relay','first':'白天不犯困','second':[{'text':'那就是','role':'white'},{'text':'适合你的睡眠','role':'gold'}],'clock':{'first':[0,2,5,8,10],'firstClear':30,'secondStart':31,'secondSettle':40,'exit':[82,89]}}}
for oid,s in same.items():
 s['styles']=copy.deepcopy(styles);s['y']=332
 if oid in ('N21','N22'):s['styles']['white']['size']=18;s['styles']['gold']['size']=22
 else:s['styles']['white']['size']=18;s['styles']['gold']['size']=22;s['firstStyle']=copy.deepcopy(s['styles']['gold']);s['firstStyle']['size']=18
 if oid=='N21':s['styles']['gold']['size']=25
 if oid in ('N21','N22'):s['styles']['gold']['font']='C:/Windows/Fonts/Source Han Serif SC Heavy (TrueType).ttf'
same['N21']['clock']['exit']=[39,41]
same['N24']['clock']['first']=[0,2,4,7,9]
same['N24']['clock']['secondSettle']=40
for oid in same:
 old=R.load(P/f'source/pilot/batches/prompts/{oid}-input.json');c=copy.deepcopy(old);c['subtitle']=copy.deepcopy(same[oid]);N=c['frameCount']
 if oid=='N21':c['subtitle'].update(setup='合适的方式要慢慢',conclusion='打磨出来');c['subtitle']['clock']={'split':[20,31],'takeover':[25,35],'exit':[N-7,N-2]}
 if oid=='N22':c['subtitle'].update(setupParts=['提前了解','别人踩过的坑'],conclusion='少走弯路');c['subtitle']['clock']={'split':[27,39],'takeover':[33,45]}
 if oid=='N24':c['subtitle'].update(first='一步一步来',second=[{'text':'生活才能','role':'white'},{'text':'慢慢变好','role':'gold'}]);c['subtitle']['clock']={'first':[4,8,12,16,20],'firstClear':43,'secondStart':43,'secondSettle':53}
 c['purpose']='语义重点绑定结论，保留参考让位/接管，不再套T01放大';c['limitations']=['原字体身份与精确材质仍未确认，采用同字校准候选','动作依据源过程观察重建，精确曲线仍近似','新台词时点需人工听审；未获得本轮用户认可']
 R.dump(S/(oid+'-input.json'),c);sc=copy.deepcopy(c);sc['frameCount']=same[oid]['clock'].get('exit',[45,45])[-1]+1 if oid!='N22' else 41;sc['subtitle']=same[oid];sc['frameCount']={'N21':45,'N22':41,'N24':95}[oid];R.dump(S/(oid+'-same-word.json'),sc)
# Font candidates same text & measured roles, no imported AH font assumptions.
b=Image.new('RGBA',(852,600),'#27323b');d=ImageDraw.Draw(b)
for j,fp in enumerate([font,'C:/Windows/Fonts/Source Han Serif SC Heavy (TrueType).ttf','C:/Windows/Fonts/simsun.ttc']):
 for i,t in enumerate(['有的人睡五六个小时','才能充满活力','白天不犯困']):
  st=copy.deepcopy(styles['white' if i==0 else 'gold']);st['font']=fp;tile,m=V.tile(t,st);tile=tile.resize((round(tile.width/4),round(tile.height/4)),Image.Resampling.LANCZOS);b.alpha_composite(tile,(round(i*284+142-m['width']/2-6),j*190+30));d.text((i*284+2,j*190+90),Path(fp).name[:34],fill='white')
b.convert('RGB').save(Q/'same-word-font-candidates.jpg');R.dump(Q/'same-word-layout.json',{oid:{'styles':same[oid]['styles'],'originalFontConfirmed':False} for oid in same})
print('inputs ready')
