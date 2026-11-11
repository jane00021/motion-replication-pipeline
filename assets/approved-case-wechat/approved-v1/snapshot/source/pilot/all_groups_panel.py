from pathlib import Path
import sys,json,hashlib,subprocess,html
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'));import integrate_batches as ui
R=P/'reviews/all-groups';R.mkdir(exist_ok=True)
def load(p):return json.loads(Path(p).read_text('utf-8-sig'))
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),'utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Explicit precedence: current corrections beat all old batch candidates.
selected={}
for path in ['render/pilot/batches/closing/manifest.json','render/pilot/detail-two/metadata.json','render/pilot/detail-rest/metadata.json','render/pilot/final-two/metadata.json','render/pilot/last-four/metadata.json']:
 for g in load(P/path)['groups']:selected[g['occurrence']]=g
cat=load(P/'observations/group-catalog.json');assert set(selected)=={o['id'] for o in cat['occurrences']}
approved={}
for path in ['reviews/detail-two/user-approval.json','reviews/final-two/user-approval.json']:
 for a in load(P/path)['groups']:approved[a['occurrence']]=a['sha256']
a=load(P/'reviews/t04-user-approval.json');approved['cg06']=a['sha256']
rows=[];checks=[];families={kind:{f['id']:{'name':f['name'],'occurrences':[]} for f in cat['families'][kind]} for kind in ['visual','subtitle']}
for o in cat['occurrences']:
 g=dict(selected[o['id']]);g.update(name=o['name'],visualFamily=o['visual'],subtitleFamily=o['subtitle'],sourceRange=[o['startFrame'],o['endFrame']],sourceTimecode=o['timecode'],variantMembers=o['members'],compositionMode=o['compositionMode'])
 assert (P/g['file']).is_file() and (P/g['referenceFile']).is_file()
 g['sha256']=sha(P/g['file']);g['limitations']=g.get('limitations',g.get('differences',[]));g['batch']='approved' if approved.get(o['id'])==g['sha256'] else 'review'
 g['verificationState']='user-approved-specific-media' if g['batch']=='approved' else 'awaiting-current-version-review'
 if o['id']=='cg09':
  current=load(P/'render/pilot/last-four/scene/manifest.json')['groups'][0];assert current['sha256']==g['sha256'],'09 must use natural-font correction'
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,width,height','-of','json',str(P/g['file'])]))['streams'][0];assert int(info['nb_frames'])==g.get('frameCount',int(info['nb_frames']))
 checks.append({'occurrence':o['id'],'file':g['file'],'sha256':g['sha256'],'metadataFrames':int(info['nb_frames']),'status':g['verificationState']})
 for kind in families:
  fid=g[kind+'Family']
  if fid:families[kind][fid]['occurrences'].append(o['id'])
 rows.append(g)
ui.NAMES={'approved':'已有明确认可记录','review':'本版待核验'}
m={'schema':1,'stage':'03-pilot','groups':rows,'families':families,'formalStageAccepted':False,'selection':'latest occurrence-specific media;09 natural-font correction; approved versions SHA-checked'}
dump(P/'render/pilot/all-groups-metadata.json',m);dump(R/'selection.json',{'groups':checks,'count':len(rows),'latest09Corrected':True})
old=P/'render/pilot/index.html';(R/'previous-panel.html').write_text(old.read_text('utf-8'),'utf-8');ui.render_page(m)
s=old.read_text('utf-8').replace('完整动效组 · 分批复现待复核','全部17组 · 原对标与新口播对比').replace('完整动效组 · 分批复现','全部17组 · 原对标与新口播对比').replace('17 个完整 occurrence：已有 2 组＋3 个并行工作包的 15 组。每组保留原对标与新口播完整结果。当前为 03 试作待复核，技术检查与用户视觉认可分别记录。','按最终拆解目录展示17个完整动效组，共34个播放器。左侧原对标，右侧各组最新新口播完整结果；09已使用动态视频和自然字形字幕修正版。所有组均有实现结果，整个03节点仍未正式验收。').replace('工作包 <select','核验状态 <select')
for g in rows:
 label='已认可该视频版本' if g['batch']=='approved' else '本版待核验'
 s=s.replace(f'{ui.NAMES[g["batch"]]} · 03待复核',f'{ui.NAMES[g["batch"]]} · {label}')
nav='<nav style="display:flex;flex-wrap:wrap;gap:10px;margin:20px 0">'+''.join(f'<a href="#{g["occurrence"]}">{g["occurrence"][2:]}</a>' for g in rows)+'</nav>'
s=s.replace('<details><summary>共用 family',nav+'<details><summary>共用 family',1);old.write_text(s,'utf-8')
print(json.dumps({'groups':len(rows),'players':len(rows)*2,'explicitApproved':sum(g['batch']=='approved' for g in rows),'latest09':next(g['sha256'] for g in rows if g['occurrence']=='cg09')},ensure_ascii=False))
