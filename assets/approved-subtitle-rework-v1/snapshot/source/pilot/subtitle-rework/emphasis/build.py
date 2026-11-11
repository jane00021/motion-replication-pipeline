import sys,json,copy,subprocess
from pathlib import Path
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'));import batch_runtime as rt
S=P/'source/pilot/subtitle-rework/emphasis';O=P/'render/pilot/subtitle-rework/emphasis';R=P/'reviews/pilot/subtitle-rework/emphasis'
font='D:/SKILL/font-check/SourceHanSerifSC-Bold.otf'
for id in ['N13','N17']:
 c=rt.load(P/f'source/pilot/batches/prompts/{id}-input.json');r=rt.load(P/f'source/pilot/batches/prompts/{id}-recipe.json');r['components']=[x for x in r['components'] if x['kind']=='visual'];r['layerOrder']=[x for x in r['layerOrder'] if not x.startswith('subtitle.')]
 if id=='N13':
  c['text']={'headline':'思路更重要','english':'Mindset matters'}
  c['roles']={'headline':{'font':font,'size':52,'inkWidth':235,'inkHeight':53,'outline':.5,'top':[255,237,116],'bottom':[192,155,45],'shadow':{'dx':1,'dy':2,'blur':.6,'opacity':.95}},'english':{'font':'C:/Windows/Fonts/georgiab.ttf','size':19,'top':[167,12,19],'bottom':[110,5,10],'shadow':{'dx':1,'dy':1,'blur':.3,'opacity':.85}}}
  # Source local0..7 actual faint-small -> clear larger; new time extends hold, entry remains seven frames.
  c['motion']={'keys':[{'frame':0,'scale':.75,'opacity':.12,'blur':2.5,'y':265},{'frame':2,'scale':.84,'opacity':.62,'blur':1.15,'y':264},{'frame':4,'scale':.94,'opacity':.94,'blur':.45,'y':261},{'frame':7,'scale':1,'opacity':1,'blur':0,'y':258},{'frame':c['frames']-1,'scale':1,'opacity':1,'blur':0,'y':258}],'englishY':304};fam='T08';order=['subtitle.english','subtitle.headline']
 else:
  c['text']={'sentence':'别陷在焦虑里抱怨没钱'};c['roles']={'sentence':{'font':font,'size':18.5,'top':[249,228,100],'bottom':[180,143,30],'outline':.45,'shadow':{'dx':.8,'dy':1.4,'blur':.4,'opacity':.95}}};c['motion']={'y':401,'amplitude':3.2,'period':25,'phaseStep':.58,'rotation':4,'tracking':.25,'start':0};fam='gold-wave';order=['subtitle.goldSentence']
 c['limitations']=['原字体未知，采用思源宋Bold候选；具体字形及压缩特征仍有差异','动态参数依据逐帧观测近似，未声称轨迹逐像素一致','保留新口播原声，词级听审和原片音效未完成']
 ip=S/f'{id}-input.json';rp=S/f'{id}-recipe.json';rt.dump(ip,c);r['components'].append({'kind':'subtitle','id':fam,'entrypoint':'subtitle-rework.emphasis.providers:subtitle','source':'source/pilot/subtitle-rework/emphasis/providers.py'});r['layerOrder']+=order;r['supportBindings']={'source/pilot/components.py':rt.sha(P/'source/pilot/components.py'),'source/pilot/batches/prompts/providers.py':rt.sha(P/'source/pilot/batches/prompts/providers.py')}
 for role in c['roles'].values():r['supportBindings'][role['font']]=rt.sha(role['font'])
 rt.dump(rp,rt.bind(r,ip))
if __name__=='__main__':
 groups=[]
 for id in ['N13','N17']:
  print(id,flush=True);g=rt.run_group(S/f'{id}-recipe.json',output=O/f'{id}.mp4');groups.append(g);rt.dump(O/'manifest.json',{'groups':groups,'status':'subtitle-rework-trial'})
