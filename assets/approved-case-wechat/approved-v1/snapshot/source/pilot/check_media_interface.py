from pathlib import Path
import json,copy,sys,hashlib
import numpy as np
from PIL import Image
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'))
from components.media_source import source_frame,fit_frame
from components.scene_batch import render
R=P/'reviews/media-interface';R.mkdir(exist_ok=True)
def load(p):return json.loads(Path(p).read_text('utf-8-sig'))
video=load(P/'source/pilot/new-input/manifest.json')['path']
inputs={'jpeg':{'type':'image','path':'source/pilot/batches/scene/assets/city.jpg','fit':'cover'},'png-alpha':{'type':'image','path':'source/pilot/detail-rest/scene/assets/skill.png','fit':'contain','trimAlpha':True},'svg':{'type':'svg','path':'source/pilot/detail-rest/scene/assets/skill.svg','fit':'contain','trimAlpha':True},'video':{'type':'video','path':video,'sourceIn':3,'sourceOut':5,'timelineStartFrame':0,'speed':1,'endBehavior':'hold','fit':'cover','audio':'mute'}}
checks=[]
for key,slot in inputs.items():
 im=fit_frame(slot,20,(252,136));assert im.size==(252,136) and im.mode=='RGBA';im.save(R/(key+'.png'));checks.append({'type':key,'rgba':True,'fittedSize':[252,136]})
# Real moving footage, source trim, timeline start and EOF policies.
v=inputs['video'];a=np.array(source_frame(v,0));b=np.array(source_frame(v,30));assert np.any(a!=b)
assert np.array_equal(np.asarray(source_frame(v,300)),np.asarray(source_frame(v,350)))
assert source_frame(dict(v,endBehavior='transparent'),300).getchannel('A').getbbox() is None
assert np.array_equal(np.asarray(source_frame(dict(v,endBehavior='loop'),0)),np.asarray(source_frame(dict(v,endBehavior='loop'),60)))
assert source_frame(dict(v,timelineStartFrame=10),0).getchannel('A').getbbox() is None
# Multi-format inputs reach the SAME current v06 full component, not just a detached loader.
c=load(P/'source/pilot/detail-rest/scene/cg08-input.json');raw=Image.new('RGBA',(286,508),'#101820')
for key in ['jpeg','png-alpha','svg','video']:
 q=copy.deepcopy(c);q['assets']['top']=inputs[key];q['assets']['second']=inputs[key]
 out=render('v06',raw,100,q);assert 'topPanel' in out and 'secondPanel' in out
 frame=Image.new('RGBA',(286,508))
 for name in ['background','presenter','topPanel','secondPanel']:frame.alpha_composite(out[name])
 frame.save(R/f'v06-{key}-frame.png')
q=copy.deepcopy(c);q['assets']['top']=v;x=render('v06',raw,20,q)['topPanel'];y=render('v06',raw,100,q)['topPanel'];assert np.any(np.array(x)!=np.array(y))
# Alpha-bearing image remains transparent at source, no baked preview backdrop.
assert source_frame(inputs['png-alpha']).getchannel('A').getextrema()[0]==0
# Preserve existing displayed/approved media hashes.
approval=load(P/'reviews/detail-two/user-approval.json')
for g in approval['groups']:assert hashlib.sha256((P/g['file']).read_bytes()).hexdigest()==g['sha256']
receipt={'formats':checks,'realVideoChangesWithTime':True,'holdLoopTransparentChecked':True,'timelineStartChecked':True,'v06SameComponentAllFourTypes':True,'v06VideoPanelMoves':True,'alphaPreserved':True,'displayedApprovedMediaUnchanged':True,'scope':'RGBA frame tests only; no new group render, no perceptual approval, no full-library multi-format certification','sourceInputs':inputs}
(R/'verification.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),'utf-8')
print('4 types, video clocks/EOF policies and same v06 slot verified; no media replaced')
