import sys,json,copy
from pathlib import Path
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'))
import batch_runtime as rt
S=P/'source/pilot/batches/prompts';O=P/'render/pilot/batches/prompts';R=P/'reviews/pilot/batches/prompts'
base=rt.load(P/'source/pilot/N01-input.json');catalog=rt.load(P/'observations/group-catalog.json');groups={o['id']:o for o in catalog['occurrences']}
font=base['subtitle']['bodyStyle']['font'];gold=base['subtitle']['focusStyle'];provider='source/pilot/batches/prompts/providers.py'
specs=[('N03',5.833333,11.5,'V02','T01','又想做点别的却','不敢尝试'),('N04',11.5,11.933333,'V03',None,'',''),('N05',22.533333,24.466667,None,'T03','拼的不是体力','是思路'),('N09',19.466667,21.6,'V07','T01','打工就是拿时间','换工资'),('N10',26.8,29.333333,None,'T01','与其空想不如学个','落地本事'),('N12',5.833333,7.233333,None,'T07','',''),('N13',22.533333,24.466667,'V01','T08','',''),('N17',24.466667,26.8,'V07',None,'',''),('N20',29.333333,32.066667,'V07',None,'',''),('N21',32.066667,34.433333,None,'T01','合适的方式要慢慢','打磨出来'),('N22',34.433333,37.566667,None,'T01','提前了解别人踩过的坑','少走弯路'),('N23',38.8,40.533333,None,'T01','比起求快更重要的是','踏实'),('N24',40.533333,43.8,None,'T01','选对方式再','一步一步来')]
def ref(kind,id,entry,source=provider,prefix=None):
 d={'kind':kind,'id':id,'entrypoint':entry,'source':source}
 if prefix:d['prefix']=prefix
 return d
for id,start,end,v,t,prefix,emph in specs:
 c=copy.deepcopy(base);c.update(id=id,frames=round((end-start)*30),rawStart=start,rawRange=[start,end],frameCount=round((end-start)*30),purpose='语义迁移概括：新口播的生活/工作判断，复用参考完整表达关系。');c['subtitle'].update(prefix=prefix,emphasis=emph,bodyIn=2,emphasisIn=[round(c['frames']*.4),round(c['frames']*.4)+7],y=333)
 # Natural font-size, no inkWidth forced by character count.
 c['subtitle']['bodyStyle']['size']=16;c['subtitle']['focusStyle']['size']=21;c['captionStyle']=copy.deepcopy(c['subtitle']['bodyStyle']);c['captionStyle']['size']=12
 refs=[];order=[]
 if v=='V01':refs+=[ref('visual','V01','components:visual','source/pilot/components.py')];order+=['visual.presenter','visual.focus'];c['visual']['exit']=[c['frames']-7,c['frames']]
 elif v=='V07':
  if id=='N17':refs+=[ref('visual','V15','batches.prompts.providers:visual',prefix='zoom')];order+=['zoom.zoomedPresenter']
  else:refs+=[ref('visual','raw','batches.prompts.providers:visual',prefix='base')];order+=['base.presenter']
  refs+=[ref('visual','V07','batches.prompts.providers:visual')];order+=['visual.sticker'];c['sticker']={'N09':'clock','N17':'swirl','N20':'warning'}[id];c['stickerCenter']=[142,48];c['caption']={'N09':'打工就是拿时间去换工资','N17':'别陷在焦虑里抱怨没钱','N20':'别相信短期快速赚钱'}[id]
 elif v:
  refs+=[ref('visual',v,'batches.prompts.providers:visual')];order+=['visual.stage' if v=='V02' else 'visual.expandingPresenter']
 else:refs+=[ref('visual','raw','batches.prompts.providers:visual',prefix='base')];order+=['base.presenter']
 if id=='N03':c['sceneAssets']=[{'path':'D:/SKILL/动效复刻项目/社会观察对标_20261109/groups/G01/assets/night-work-pexels-3140468.mp4','start':0},{'path':'D:/SKILL/动效复刻项目/社会观察对标_20261109/groups/G01/assets/night-work-pexels-3140468.mp4','start':5}];c['sceneChange']=round(c['frames']*.52);c['subtitle']['y']=145;c['captionStyle']['size']=12;c['t01Cues']=[{'in':0,'out':92,'subtitle':{'prefix':'想做又不敢','emphasis':'怕亏本','bodyIn':3,'emphasisIn':[35,42]}},{'in':92,'out':c['frames'],'subtitle':{'prefix':'一年又一年','emphasis':'没起色','bodyIn':1,'emphasisIn':[16,23]}}]
 if t=='T01':
  multi=id in ['N03','N10','N24']
  if id=='N10':c['t01Cues']=[{'in':0,'out':c['frames'],'subtitle':{'prefix':'与其空想','emphasis':'不如行动','bodyIn':0,'emphasisIn':[10,16],'y':321}},{'in':c['frames']//2,'out':c['frames'],'subtitle':{'prefix':'学个本事','emphasis':'能落地','bodyIn':0,'emphasisIn':[10,16],'y':352}}]
  if id=='N24':c['t01Cues']=[{'in':0,'out':43,'subtitle':{'prefix':'选对方式','emphasis':'一步一步来','bodyIn':0,'emphasisIn':[12,19]}},{'in':43,'out':c['frames'],'subtitle':{'prefix':'生活才能','emphasis':'慢慢变好','bodyIn':0,'emphasisIn':[12,19]}}]
  refs+=[ref('subtitle','T01','batches.prompts.providers:t01' if multi else 'components:subtitle',provider if multi else 'source/pilot/components.py')];order+=['subtitle.speech']
 elif t:
  refs+=[ref('subtitle',t,'batches.prompts.providers:subtitle')];order+=[{'T03':'subtitle.cursorText','T07':'subtitle.questions','T08':'subtitle.headline'}[t]]
  if t=='T03':c['subtitle'].update(keywordIn=10,cursorIn=17,y=324)
  if t=='T07':
   c.update(questionStyle={**gold,'font':'C:/Windows/Fonts/arialbd.ttf','size':30},rollClock=[14,25],rollLines=['想做点别的','又不敢尝试']);refs+=[ref('subtitle','T10','batches.prompts.providers:subtitle',prefix='rolling')];order+=['rolling.rollingSpeech']
  if t=='T08':c.update(headline='思路更重要',headlineStyle={**gold,'size':33,'fill':'#e6c34c','shadowX':1.5,'shadowY':2,'shadowBlur':.6})
 elif id in ['N17','N20']:
  refs+=[ref('subtitle','ordinary','batches.prompts.providers:subtitle')];order+=['subtitle.speech']
 c['limitations']=['原字体身份和声音落点未确认；新台词为语义概括，词钟需听审','只验证本次输入的完整组合，不称任意迁移均通过']
 if id=='N03':c['limitations']+=['两段不同时间的真实办公视频示意加班/工作语境，不冒称原失眠素材；语义为新口播概括']
 if id in ['N09','N17','N20']:c['limitations']+=['头顶图形按新口播换语义素材；材质与原时钟/漫画不同']
 ip=S/f'{id}-input.json';rp=S/f'{id}-recipe.json';rt.dump(ip,c);r={'schema':1,'occurrence':id,'components':refs,'layerOrder':order,'canvas':[284,504],'fps':30,'status':'03-trial','sourceRange':[groups[id]['startFrame'],groups[id]['endFrame']],'supportBindings':{'source/pilot/components.py':rt.sha(P/'source/pilot/components.py')}}
 for f in c.get('sceneAssets',[]):
  path=f['path'] if isinstance(f,dict) else f;r['supportBindings'][path]=rt.sha(P/path)
 rt.dump(rp,rt.bind(r,ip))
if __name__=='__main__':
 records=[]
 for id,*_ in specs:
  print('render',id,flush=True);records.append(rt.run_group(S/f'{id}-recipe.json',output=O/f'{id}.mp4'));rt.dump(O/'manifest.json',{'groups':records,'status':'03 trial'})
