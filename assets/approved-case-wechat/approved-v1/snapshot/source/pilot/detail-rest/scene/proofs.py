import sys,json,copy,subprocess
from pathlib import Path
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'))
from components.common import *
from components.detail_tools import place_text,glyph_tile
from components.scene_batch import render_subtitle
S=P/'source/pilot/detail-rest/scene';R=P/'reviews/detail-rest/scene'
# Same words, measured role boxes. Reference top/bottom, editable layers below.
for id,words in [('cg07',{'title':'很多人习惯','left':'跟风消费','right':'盲目扩张'}),('cg08',{'first':'透支负债前行','second':'跟风盲目炒股'})]:
 c=load(S/f'{id}-input.json');c['text']=words;sf,ef=c['sourceRange'];N=ef-sf
 if id=='cg07':c['clock'].update(title=16,leftLabel=25,rightLabel=60);c['typeRoles']['left']['inkWidth']=80;c['typeRoles']['right']['inkWidth']=80
 else:c['clock'].update(firstText=0,secondText=28,secondPanel=[25,38])
 save=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8');save(R/f'{id}-same-word-input.json',c)
 sheet=Image.new('RGB',(1430,1040),'#20252c');d=ImageDraw.Draw(sheet)
 for k,n in enumerate([0,N//5,N*2//5,N*3//5,N-1]):
  ref=Image.open(P/f'observations/frame-audit/frames/{sf+n+1:04d}.jpg');sheet.paste(ref,(k*286,22));layers=render_subtitle(c['subtitleFamily'],n,c);bg=Image.new('RGBA',(286,508),'#20252c');bg.alpha_composite(layers['text']);sheet.paste(bg.convert('RGB'),(k*286,530));d.text((k*286+4,6),f'source/local {sf+n}/{n}',fill='white')
 sheet.save(R/f'{id}-same-word-process.jpg')
# Native ink bbox arithmetic independent of visual effect opacity.
checks=[]
for id in ['cg07','cg08','cg09']:
 c=load(S/f'{id}-input.json')
 for role,s in c['typeRoles'].items():
  text=c['text'].get(role,c.get('captions',[{'text':'普通字幕'}])[0]['text']);tile,(w,h)=glyph_tile(text,json.dumps(s,sort_keys=True));x=s['anchorX']-w/2;checks.append({'occurrence':id,'role':role,'text':text,'inkBox':[x,s['inkY'],x+w,s['inkY']+h],'center':s['anchorX'],'insideWidth':x>=0 and x+w<=286,'font':s['path']})
(R/'ink-layout-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
# Hair/finger before/after comparison, original only used for proof.
from components.scene_batch import matte
sheet=Image.new('RGB',(6*220,430),'#183a51');d=ImageDraw.Draw(sheet)
for i,n in enumerate([0,35,145]):
 raw=Image.open(R/f'raw-f{n:03d}.jpg');old=matte(raw.resize((286,508))).resize((220,392));new=Image.open(R/f'matte-f{n:03d}.png').resize((220,392))
 for j,im in enumerate([old,new]):
  bg=Image.new('RGBA',(220,392),'#183a51');bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),((i*2+j)*220,28));d.text(((i*2+j)*220+4,7),f'{"old GrabCut" if j==0 else "new RVM"} f{n}',fill='white')
sheet.save(R/'matte-before-after.jpg')
