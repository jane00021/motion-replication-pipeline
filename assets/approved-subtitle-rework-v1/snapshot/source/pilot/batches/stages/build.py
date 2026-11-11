from pathlib import Path
import sys,json,hashlib,copy
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'))
import batch_runtime as R
S=P/'source/pilot/batches/stages';O=P/'render/pilot/batches/stages';Q=P/'reviews/pilot/batches/stages';S.mkdir(exist_ok=True)
source='C:/Users/Administrator/.codex/skills/motion-replication-pipeline/assets/migration-demo/talking-head-raw.mp4'
cases=[
 {'id':'N08','matteFrames':'source/pilot/batches/stages/matte-N08','frameCount':287,'rawRange':[0,287/30],'visual':{'sunIn':[10,35],'moonIn':[213,239],'cardIn':[110,155,207]},'subtitle':{'columns':[{'text':'加班','x':22,'y':186,'entry':6},{'text':'找出路','x':214,'y':59,'entry':12}],'captions':[{'in':0,'out':55,'text':'加班熬到半夜'},{'in':55,'out':175,'text':'工资到手也剩不了多少'},{'in':175,'out':287,'text':'想做别的，又怕亏本'}]},'purpose':'日夜舞台把反复加班具象化，底部小卡依次给出“工作→学习→行动”的可能出路，竖排主题字围住工作舞台。'},
 {'id':'N11','frameCount':76,'rawRange':[26.82,26.82+76/30],'visual':{'panelIn':[5,20]},'subtitle':{'tags':[{'in':36,'text':'先学能落地的本事','rect':[95,263,180,35]}],'caption':'与其空想，不如学个本事'},'purpose':'人物让位到圆窗，一张自主练习计划透视旋入；小标签把注意力定在“落地”职责上，不伪造工厂/理财证明。'},
 {'id':'N15','frameCount':203,'rawRange':[32.06,32.06+203/30],'visual':{},'ordinaryCaptions':[{'in':0,'out':70,'text':'合适的方法需要打磨'},{'in':70,'out':135,'text':'提前了解别人踩过的坑'},{'in':135,'out':203,'text':'一步一步，少走弯路'}],'purpose':'用固定圆角视窗连续推进“了解→练习→积累”的原创示意，人物圆窗保留讲述。它是学习过程示意，不是脑科学或收益证据。'},
 {'id':'N19','frameCount':580,'rawRange':[24.48,24.48+580/30],'visual':{'cardIn':[7,202,405]},'subtitle':{'times':[7,202,405],'labels':['学本事','避开坑','一步步'],'english':['Learn a skill','Avoid pitfalls','Step by step'],'captions':['与其焦虑，不如学习','提前了解别人的坑','踏实比求快更重要']},'purpose':'同一图卡舞台持续承载学技能、避坑、踏实行动三职责；三标签随新项增加向下让位，而非三份重复机制。'}]
catalog=R.load(P/'observations/group-catalog.json');rows=[]
for c in cases:
 oid=c['id'];g=next(g for g in catalog['completeGroups'] if g['id']==oid);c.update(fps=30,canvas=[284,504],rawSource=source,sourceRange=[g['startFrame'],g['endFrame']],members=g.get('members',[oid]),limitations=['原字体身份未确认，选用真实字体近似并留同字证据','原创工作/学习示意替换原睡眠素材，素材风格不等同原资产','新口播时点尚未人工听审，音效未独立还原','03试作，不代表正式库通过'])
 refs=[{'kind':'visual','id':g['visual'],'entrypoint':'batches.stages.providers:visual','source':'source/pilot/batches/stages/providers.py'}]
 if g['subtitle']:refs.append({'kind':'subtitle','id':g['subtitle'],'entrypoint':'batches.stages.providers:subtitle','source':'source/pilot/batches/stages/providers.py'})
 if oid=='N08':order=['visual.background','visual.stage','subtitle.type']
 elif oid=='N11':order=['visual.background','visual.panel','visual.presenter','subtitle.annotations']
 elif oid=='N15':order=['visual.background','visual.viewport','visual.presenter','visual.normalCaption']
 else:order=['visual.background','visual.cards','visual.presenter','subtitle.labels']
 inp=S/(oid+'-input.json');rp=S/(oid+'-recipe.json');R.dump(inp,c);r=R.bind({'occurrence':oid,'components':refs,'layerOrder':order,'verificationState':'trial','supportBindings':{'source/pilot/components.py':R.sha(P/'source/pilot/components.py')}},inp);R.dump(rp,r)
 if '--prepare-only' in sys.argv:continue
 if '--skip-N08' in sys.argv and oid=='N08':continue
 row=R.run_group(rp,output=O/(oid+'-applied.mp4'));row['components']=r['components'];row['members']=c['members'];rows.append(row);R.dump(O/'manifest.json',{'groups':rows,'stage':'03-pilot','accepted':False});print(oid+' ready',flush=True)
