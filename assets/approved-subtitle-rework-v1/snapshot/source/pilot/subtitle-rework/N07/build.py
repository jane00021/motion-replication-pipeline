from pathlib import Path
import sys,json,copy,subprocess,hashlib
P=Path(__file__).resolve().parents[4];sys.path.insert(0,str(P/'source/pilot'))
from batch_runtime import *
from components import *
from PIL import ImageChops
import importlib.util
S=P/'source/pilot/subtitle-rework/N07';O=P/'render/pilot/subtitle-rework/N07';R=P/'reviews/subtitle-rework/N07'
spec=importlib.util.spec_from_file_location('n07providers',S/'providers.py');provider=importlib.util.module_from_spec(spec);spec.loader.exec_module(provider)
FONT='D:/SKILL/font-check/SourceHanSerifSC-Bold.otf'
def style(size,color):return {'font':FONT,'size':size,'fill':color,'shadowX':.6,'shadowY':.85,'shadowBlur':.35}
def config(same=False):
 c=load(P/'source/pilot/batches/evidence/N07-input.json');c.pop('evidenceText');N=164 if same else c['frameCount'];ratio=N/164
 c['splitSubtitle']={'white':'古人的睡觉' if same else '学个落地本事','gold':'根本不是一觉到天亮' if same else '不如行动起来','cx':142,'whiteY':120,'tracking':1.8 if same else .2,'goldTracking':.2,'splitRatio':.49,'splitDistance':15,'goldY':128,'whiteStyle':style(26,'#fffef8'),'goldStyle':style(17,'#dec55a'),'setupStyle':style(16,'#fffef8'),'setupY':332,'entryOrder':[0,2,4,1,3] if same else [0,2,4,1,3,5],'glyphStagger':2,'events':{k:round(v*ratio) for k,v in {'entryStart':86,'entrySettle':101,'splitStart':107,'splitSettle':112,'goldStart':113,'goldSettle':121}.items()},'marker':{'rect':[42,245,185,17],'clock':[round(86*ratio),round(101*ratio)]},'setupCues':[{'text':'有位历史学家翻阅' if same else '别总陷在焦虑里','in':7,'out':round(42*ratio)},{'text':'几百份文件发现' if same else '与其空想','in':round(42*ratio),'out':round(86*ratio)}]}
 c['subtitleReworkPurpose']='白色同一句先完整揭晓，再沿字面水平切为上下两半分别让位，夹缝金句补充结论；不重复两条完整白句。'
 if same:
  c['frames']=c['frameCount']=164;c['rawRange']=[24.48,24.48+164/30]
 return c
def recipe(c,label):
 r=load(P/'source/pilot/batches/evidence/N07-recipe.json');r['components'][1].update(entrypoint='subtitle-rework.N07.providers:subtitle',source='source/pilot/subtitle-rework/N07/providers.py');r['layerOrder']=['visual.background','visual.history','visual.documents','subtitle.documentMarker','subtitle.whiteUpper','subtitle.whiteLower','subtitle.goldMiddle','subtitle.setupSpeech'];r['supportBindings']={p:sha(P/p) for p in ['source/pilot/components.py','source/pilot/batches/evidence/providers.py']};return bind(r,S/f'{label}-input.json')
def rgba(c,label):
 folder=O/(label+'-rgba');folder.mkdir(exist_ok=True);rows=[];proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','284x504','-r','30','-i','pipe:0','-an','-c:v','libx264','-threads','2','-crf','15','-pix_fmt','yuv420p',str(O/(label+'-text-process.mp4'))],stdin=subprocess.PIPE)
 for n in range(c['frames']):
  layers=provider.subtitle('T04',n,c);combined=blank()
  for key,im in layers.items():combined.alpha_composite(im);im.save(folder/f'{n:04d}-{key}.png')
  combined.save(folder/f'{n:04d}.png');rows.append({'frame':n,'sha256':hashlib.sha256(combined.tobytes()).hexdigest(),'alphaBBox':combined.getchannel('A').getbbox()});bg=Image.new('RGBA',(284,504),'#101819');bg.alpha_composite(combined);proc.stdin.write(bg.convert('RGB').tobytes())
 proc.stdin.close();assert proc.wait()==0;dump(folder/'sequence.json',{'fps':30,'canvas':[284,504],'fullRGBA':True,'roles':['whiteUpper','whiteLower','goldMiddle','documentMarker','setupSpeech'],'frames':rows})
def main():
 for label in ['same-word','new-content']:
  c=config(label=='same-word');dump(S/f'{label}-input.json',c);r=recipe(c,label);dump(S/f'{label}-recipe.json',r);rgba(c,label)
 row=run_group(S/'new-content-recipe.json',output=O/'N07.mp4');row['comparisonEvidence']='reviews/subtitle-rework/N07/process-comparison.jpg';dump(O/'manifest.json',{'groups':[row],'status':'03-subtitle-rework-trial'})
if __name__=='__main__':main()
