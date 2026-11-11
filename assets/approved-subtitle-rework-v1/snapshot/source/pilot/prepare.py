from pathlib import Path
import json,hashlib
P=Path.cwd();S=P/'source/pilot';K=Path('C:/Users/Administrator/.codex/skills/motion-replication-pipeline');raw=K/'assets/migration-demo/talking-head-raw.mp4'
fonts=json.loads((P/'measurements/fonts.json').read_text('utf-8'))
def style(size,fill='#fffef4'):return {'font':fonts['bodyCandidate'],'size':size,'fill':fill,'shadowX':.6,'shadowY':.85,'shadowBlur':.35}
configs=[{'id':'N01','frames':112,'rawStart':0,'purpose':'前句询问加班与收入处境，工资是表达核心；暗角聚焦+句末重点词放大泛光接管。','visual':{'center':[142,195],'radii':[143,230],'opacity':.82,'exit':[100,111]},'subtitle':{'prefix':'你是不是也在为','emphasis':'工资发愁','bodyIn':4,'emphasisIn':[62,70],'y':332,'bodyStyle':style(16),'focusStyle':style(21,'#e4c64d')}}, {'id':'N02','frames':93,'rawStart':19.48,'purpose':'打工以时间换工资形成限制判断；背景压暗让位，人物保留在前，天花板巨字在人后强化核心限制。','matteFrames':'source/pilot/matte-N02','visual':{'dim':[57,65],'brightness':.46},'subtitle':{'cues':[{'in':0,'out':63,'white':'打工就是拿时间去换','gold':'工资'},{'in':63,'out':93,'white':'这就是收入的','gold':'天花板'}],'bodyStyle':style(15),'goldStyle':style(18,'#e4c64d'),'y':332,'title':'天花板','titleClock':[57,65,72],'titleY':63,'titleStyle':dict(style(66),inkWidth=250,inkHeight=86,skew=-.18,shadowX=1.5,shadowY=2.0)}}]
for c in configs:
 c['rawSource']=str(raw);c['fps']=30;c['canvas']=[284,504];(S/(c['id']+'-input.json')).write_text(json.dumps(c,ensure_ascii=False,indent=2),'utf-8')
 v,t=('V01','T01') if c['id']=='N01' else ('V14','T02');order=['visual.presenter','visual.focus','subtitle.speech'] if c['id']=='N01' else ['visual.background','subtitle.behindTitle','visual.foreground','subtitle.speech']
 r={'occurrence':c['id'],'visualFamily':v,'subtitleFamily':t,'visualEntry':'components:visual','subtitleEntry':'components:subtitle','source':'source/pilot/components.py','sourceSha256':hashlib.sha256((S/'components.py').read_bytes()).hexdigest(),'input':'source/pilot/'+c['id']+'-input.json','inputSha256':hashlib.sha256((S/(c['id']+'-input.json')).read_bytes()).hexdigest(),'layerOrder':order,'status':'pilot-trial-not-approved'};(S/(c['id']+'-recipe.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2),'utf-8')
print('two recipes written')
