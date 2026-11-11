from pathlib import Path
import sys,json,copy,math
P=Path(__file__).resolve().parents[4];sys.path.insert(0,str(P/'source/pilot'))
from batch_runtime import *
from components import text_tile
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
S=P/'source/pilot/batches/evidence';O=P/'render/pilot/batches/evidence';R=P/'reviews/pilot/batches/evidence';A=S/'assets'
RAW='C:/Users/Administrator/.codex/skills/motion-replication-pipeline/assets/migration-demo/talking-head-raw.mp4';FONT='D:/SKILL/font-check/SourceHanSerifSC-Bold.otf'
def style(size=16,fill='#fffef5',**kw):return dict(font=FONT,size=size,fill=fill,shadowX=.7,shadowY=1,shadowBlur=.4,**kw)
def assets():
 # Original diagrams and notes explicitly identify their illustrative status.
 for j,title in enumerate(['少一点空想','学一门本事','记录踩过的坑','先了解风险']):
  svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="240" height="320" viewBox="0 0 240 320"><rect width="240" height="320" rx="4" fill="#f6f5eb"/><rect x="0" y="0" width="240" height="28" fill="#273f45"/><text x="15" y="19" font-size="12" fill="white">学习笔记 · 示意 / {j+1:02d}</text><text x="15" y="55" font-size="20" font-weight="bold">{title}</text><path d="M15 68H222" stroke="#656a62"/><text x="15" y="91" font-size="11">只作内容可视化，不是研究论文或事实证据</text><g stroke="#8a8f85" stroke-width="2">'''+''.join(f'<path d="M15 {y}H{222-(i%3)*24}"/>' for i,y in enumerate(range(115,280,13)))+'''</g><rect x="16" y="292" width="208" height="2" fill="#8f948b"/></svg>'''
  (A/f'note-{j}.svg').write_text(svg,'utf-8')
 (A/'skill-collage.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="284" height="504"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#22393e"/><stop offset="1" stop-color="#0b1018"/></linearGradient></defs><rect width="284" height="504" fill="url(#g)"/><g stroke="#6b8e8d" fill="#31434b"><path d="M0 40L130 0V160L0 204Z"/><path d="M142 18L284 0V192L142 216Z"/><path d="M0 230L136 197V410L0 440Z"/><path d="M148 231L284 206V504H148Z"/></g><g fill="#a9c5bb" font-family="sans-serif"><text x="10" y="90" font-size="25">时间</text><text x="158" y="91" font-size="22">工资</text><text x="10" y="287" font-size="23">经验</text><text x="158" y="285" font-size="22">本事</text></g><g stroke="#6c7f81" opacity=".4">'''+''.join(f'<path d="M0 {y}H284"/>' for y in range(0,504,12))+'''</g><text x="9" y="490" fill="#bfc9c3" font-size="10">工作与技能语境 · 原创图形示意</text></svg>''','utf-8')
 (A/'money-temptation.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="180" height="180"><defs><radialGradient id="g"><stop stop-color="#fff4b3"/><stop offset=".65" stop-color="#e4bb4b"/><stop offset="1" stop-color="#7f5720"/></radialGradient></defs><circle cx="90" cy="90" r="76" fill="url(#g)" stroke="#f9dc85" stroke-width="7"/><circle cx="90" cy="90" r="64" fill="none" stroke="#a97b2a" stroke-width="3"/><text x="90" y="123" fill="#684919" font-size="94" font-family="serif" font-weight="bold" text-anchor="middle">¥</text></svg>''','utf-8')
 (A/'prohibition.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><defs><linearGradient id="r" x2="1" y2="1"><stop stop-color="#ff3957"/><stop offset=".5" stop-color="#be0634"/><stop offset="1" stop-color="#800926"/></linearGradient></defs><circle cx="100" cy="100" r="85" stroke="#35020d" stroke-width="19" fill="none" transform="translate(2 3)"/><circle cx="100" cy="100" r="85" stroke="url(#r)" stroke-width="16" fill="none"/><path d="M39 39L161 161" stroke="url(#r)" stroke-width="17"/><path d="M43 35L166 157" stroke="#ff8b9c" stroke-width="2" opacity=".7"/></svg>''','utf-8')
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe');page=b.new_page(device_scale_factor=3)
  for svg in A.glob('*.svg'):
   page.set_content('<style>html,body{margin:0;background:transparent}</style>'+svg.read_text('utf-8'));page.locator('svg').screenshot(path=str(svg.with_suffix('.png')),omit_background=True)
  b.close()
def ref(kind,id,module='batches.evidence.providers',prefix=None):return dict(kind=kind,id=id,entrypoint=module+':'+('visual' if kind=='visual' else 'subtitle'),source='source/pilot/'+module.replace('.','/')+'.py',prefix=prefix or kind)
def configs(id):
 ranges={'N06':[19.48,22.54],'N07':[24.48,29.34],'N14':[34.42,37.56],'N18':[29.34,32.06],'N16':[17.56,19.48]};start,end=ranges[id];N=round((end-start)*30);c={'id':id,'rawSource':RAW,'rawRange':[start,end],'frameCount':N,'frames':N,'fps':30,'canvas':[284,504],'visual':{},'events':{},'limitations':['原字体身份未确认，原声效未独立重建；新词点尚未人工听审','图形/文档为原创示意，不能冒称论文证据','人物matte只验证当前口播，头发/手指边缘仍待视觉复审']};parts=[];order=[]
 if id=='N06':
  c['matteFrames']='source/pilot/batches/evidence/matte-N06';c['visual']={'collage':(A/'skill-collage.png').relative_to(P).as_posix(),'photo':(A/'work-keyboard.jpg').relative_to(P).as_posix()};c['events']={'collage':[18,37]};c['subtitle']=load(P/'source/pilot/N02-input.json')['subtitle'];c['subtitle'].update(title='天花板',titleClock=[37,45,51],titleY=48,cues=[{'in':0,'out':63,'white':'打工就是拿时间换','gold':'工资'},{'in':63,'out':N,'white':'收入存在','gold':'天花板'}]);parts=[ref('visual','V04'),ref('subtitle','T02','components')];order=['visual.background','subtitle.behindTitle','visual.outlinedPresenter','subtitle.speech'];c['purpose']='时间换工资带来上限；工作实拍拼贴铺垫，人物白边保持主体，大标题在身后接管限制判断。'
 elif id in ['N07','N14']:
  parts=[ref('visual','V05' if id=='N07' else 'V09'),ref('subtitle','T04')];order=['visual.background']+(['visual.history','visual.documents'] if id=='N07' else ['visual.document'])+['subtitle.documentMarker','subtitle.conclusion']
  if id=='N07':
   c['visual']={'history':(A/'note-0.png').relative_to(P).as_posix(),'documents':[(A/f'note-{j}.png').relative_to(P).as_posix() for j in range(4)]};c['events']={'history':[0,12],'historyOut':[28,40],'stairs':[8,40],'stagger':6,'focus':[42,59],'marker':[63,76],'zoom':[77,88]};c['evidenceText']={'markerRect':[42,245,185,17],'zoomRect':[29,235,226,51],'documentTitle':'学一门能落地的本事','documentStyle':style(17,'#181b18',inkWidth=205,inkHeight=23),'headline':[{'text':'别陷在焦虑里', 'in':55,'y':100,'style':style(22,inkWidth=216,inkHeight=27)},{'text':'学个落地的本事','in':79,'y':132,'style':style(24,'#e7cb5b',inkWidth=230,inkHeight=30)}]};c['purpose']='从焦虑转到行动：学习笔记铺垫、多页阶段递进、重点笔记接管，标记“落地的本事”；不捏造历史/科研证据。'
  else:
   c['visual']={'document':(A/'note-2.png').relative_to(P).as_posix()};c['events']={'blur':[0,7],'page':[5,26],'marker':[32,42],'zoom':[43,54]};c['evidenceText']={'markerRect':[58,127,169,16],'zoomRect':[40,167,204,57],'documentTitle':'先了解别人踩过的坑','documentStyle':style(17,'#191c18',inkWidth=185,inkHeight=20),'headline':[]};c['purpose']='先了解风险再少走弯路：人物虚化、学习笔记卷页展开、局部标题放大并标记；不是Nature论文或科学结论。'
 else:
  c['ordinaryCues']=[{'text':'好几年都翻不过身' if id=='N16' else '别相信快速赚钱','in':0,'out':N,'style':style(17),'y':336}]
  if id=='N16':c['visual']={'scale':.94};c['events']={'shrink':[0,5]};parts=[ref('visual','V11')];order=['visual.completeInset'];c['purpose']='风险可能长期影响生活，整体缩小与黑边强调整句；字幕与人物在同一坐标系缩小。'
  else:
   c['matteFrames']='source/pilot/batches/evidence/matte-N18';c['visual']={'dim':[0,1],'brightness':1,'symbol':(A/'money-temptation.png').relative_to(P).as_posix(),'ban':(A/'prohibition.png').relative_to(P).as_posix()};c['events']={'symbol':[0,7],'ban':[13,20]};parts=[ref('visual','V14','components','base'),ref('visual','V12')];parts.append({'kind':'subtitle','id':'ordinary-caption','entrypoint':'batches.evidence.providers:support','source':'source/pilot/batches/evidence/providers.py','prefix':'support'});order=['base.background','visual.symbols','visual.prohibition','base.foreground','support.speech'];c['purpose']='短期赚钱诱惑先出现，再由禁止符号明确否定；钱币替代病毒，但保留两个阶段和人物前后遮挡。'
 c['visualComponents']={'N06':['V04'],'N07':['V05'],'N14':['V09'],'N18':['V12','V14'],'N16':['V11']}[id]
 r={'schema':1,'occurrence':id,'status':'03-pilot-trial','components':parts,'layerOrder':order,'verificationState':'trial','completeGroupValidated':False,'supportBindings':{'source/pilot/components.py':sha(P/'source/pilot/components.py')}};return c,r
def main():
 assets();rows=[]
 for id in ['N06','N07','N14','N18','N16']:
  c,r=configs(id);ip=S/f'{id}-input.json';dump(ip,c);r=bind(r,ip)
  for file in A.glob('*'):r['supportBindings'][file.relative_to(P).as_posix()]=sha(file)
  for file in (P/c.get('matteFrames','__missing__')).glob('*.json'):r['supportBindings'][file.relative_to(P).as_posix()]=sha(file)
  rp=S/f'{id}-recipe.json';dump(rp,r);row=run_group(rp,output=O/f'{id}.mp4');rows.append(row);dump(O/'manifest.json',{'groups':rows,'status':'03-trial-awaiting-user'});print(id,flush=True)
if __name__=='__main__':main()
