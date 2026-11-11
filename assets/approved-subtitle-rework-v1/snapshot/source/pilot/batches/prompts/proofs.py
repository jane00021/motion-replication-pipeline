import sys,json,copy,cv2
from pathlib import Path
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'));import batch_runtime as rt,components
from batches.prompts import providers as pr
from PIL import Image,ImageDraw
from fontTools.ttLib import TTFont
S=P/'source/pilot/batches/prompts';R=P/'reviews/pilot/batches/prompts';O=P/'render/pilot/batches/prompts';m=rt.load(O/'manifest.json');catalog={o['id']:o for o in rt.load(P/'observations/group-catalog.json')['occurrences']}
allproof=[]
same={'N03':('就会开始','焦虑'),'N05':('一个','昼夜节律'),'N09':('钟表时间','最标准'),'N10':('睡满8小时才算','标准睡眠'),'N21':('就能够','精神焕发'),'N22':('才能','充满活力'),'N23':('所以最终要','精神好'),'N24':('白天','不犯困')}
for g in m['groups']:
 id=g['occurrence'];c=rt.load(P/g['input']);r=rt.load(P/g['recipe']);N=c['frames'];sf,ef=g['sourceRange'];o=catalog[id];stages=[0,N//4,N//2,N*3//4,N-1];sheet=Image.new('RGB',(1420,1032),'#20252a');d=ImageDraw.Draw(sheet);cap=cv2.VideoCapture(str(P/g['file']))
 for k,n in enumerate(stages):
  f=sf+round(n/max(1,N-1)*(ef-sf-1));ref=Image.open(P/f'observations/frame-audit/frames/{f+1:05d}.jpg').resize((284,504));sheet.paste(ref,(k*284,20));cap.set(cv2.CAP_PROP_POS_FRAMES,n);ok,a=cap.read();assert ok;new=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((284,504));sheet.paste(new,(k*284,528));d.text((k*284+4,4),f'ref {f} / new {n} phase',fill='white')
 cap.release();sheet.save(R/f'{id}-encoded-compare.jpg');cc=copy.deepcopy(c);cc['frames']=ef-sf;cc['frameCount']=cc['frames'];cc.pop('t01Cues',None)
 if id in same:cc['subtitle'].update(prefix=same[id][0],emphasis=same[id][1],bodyIn=1,emphasisIn=[max(3,cc['frames']//3),max(3,cc['frames']//3)+6])
 if id=='N12':cc['rollLines']=['那为什么','我们总感觉睡不够'];cc['rollClock']=[10,20]
 if id=='N13':cc['headline']='真正作用';cc['headlineStyle']['size']=37
 rt.dump(R/f'{id}-same-word-input.json',cc);sheet=Image.new('RGB',(1420,1032),'#20252a');d=ImageDraw.Draw(sheet)
 for k,n in enumerate([0,cc['frames']//4,cc['frames']//2,cc['frames']*3//4,cc['frames']-1]):
  ref=Image.open(P/f'observations/frame-audit/frames/{sf+n+1:05d}.jpg').resize((284,504));sheet.paste(ref,(k*284,20));out=Image.new('RGBA',(284,504),'#20252a')
  for refcomp in r['components']:
   if refcomp['kind']!='subtitle':continue
   mod,fun=refcomp['entrypoint'].split(':');fn=getattr(__import__(mod,fromlist=[fun]),fun);ls=fn(refcomp['id'],n,cc)
   for im in ls.values():out.alpha_composite(im)
  sheet.paste(out.convert('RGB'),(k*284,528));d.text((k*284+4,4),f'source/local {sf+n}/{n}',fill='white')
 sheet.save(R/f'{id}-same-word-process.jpg');allproof.append({'occurrence':id,'encodedFullDecode':True,'phaseComparison':f'{id}-encoded-compare.jpg','sameWordInput':f'{id}-same-word-input.json','sameWordProcess':f'{id}-same-word-process.jpg'})
# Font coverage reads exact selected paths and actual candidate strings.
fonts={};checks=[]
for g in m['groups']:
 c=rt.load(P/g['input']);texts=[]
 def visit(x):
  if isinstance(x,dict):
   for k,v in x.items():
    if k in ['prefix','emphasis','headline','caption'] and isinstance(v,str):texts.append(v)
    elif k in ['rollLines'] and isinstance(v,list):texts.extend(v)
    visit(v)
  elif isinstance(x,list):
   for y in x:visit(y)
 visit(c)
 for st in [c['subtitle']['bodyStyle'],c['subtitle']['focusStyle']]+([c['questionStyle']] if 'questionStyle' in c else [])+([c['headlineStyle']] if 'headlineStyle' in c else []):
  path=st['font']
  if path not in fonts:
   f=TTFont(path,fontNumber=0);fonts[path]=set(f.getBestCmap());f.close()
  relevant=['?'] if path.endswith('arialbd.ttf') else texts;missing=sorted({ch for text in relevant for ch in text if ord(ch) not in fonts[path]});checks.append({'occurrence':g['occurrence'],'font':path,'sha256':rt.sha(path),'missing':missing})
rt.dump(R/'checks.json',{'groups':allproof,'fontCoverage':checks,'fullDecode':True,'continuousVisualWatching':False,'audioListeningApproved':False})
rt.dump(R/'review.json',{'scope':[g['occurrence'] for g in m['groups']],'status':'03-trial-not-user-approved','familyReuse':{'T01':'直接调用components.subtitle；多短句仅薄时钟适配，不复制渲染','V01':'直接调用components.visual','V07':['N09','N17','N20'],'N12':['T07','T10'],'N17':['V15','V07']},'iterations':[{'found':['N10先句被下一句替换，丢掉双行接力','N13金色强调缺少红色影层'],'changed':['N10保持第一行并在其下出现第二行','N13新增独立红色阴影轮廓后真实重编码']}],'largest3':{'N03':['新口播采用办公动态视频两段示意，未冒充原失眠/疲倦素材','人物圆窗几何与源图有差异','新词时钟为语义概括未听审'],'N04':['圆窗扩张缓动近似','源片圆角遮罩形变需更多测量','新人物裁切与源不同'],'N05':['手形光标为自绘矢量轮廓','点击节奏和重点词摆位近似','字体身份未确认'],'N09':['时钟与右侧清单为新语义提示','钟表运动和源人物贴图不同','重点词仍需感官校准'],'N10':['双行接力按新台词重定时','重点字形和泛光仍候选','朗读词点需听审'],'N12':['3问号新排布和原源略有区别','滚动窗口没有原字逐词测量','词钟未听审'],'N13':['红影与金字材质近似','暗角复用仅指定新输入试验','标题时长伸长需复审'],'N17':['整体放大轨迹近似','旋涡为自绘动图变体','普通字幕仅语义概括'],'N20':['风险警示替代疲惫漫画按语义改变','图形进入退场近似','源漫画材质不复用'],'N21':['新重点词语义变化','候选字形和泛光差异','词钟未听审'],'N22':['新句长度与源不同','自然字号未按固定宽强压缩','词钟未听审'],'N23':['新强调词由精神好转为踏实','候选字体仍不同','原音效未重建'],'N24':['两句语义先后保留但时长延长','原重点词与新词不同','淡出/词钟未听审']},'proofScope':'实际查看源boundary图、编码抽帧与技术完整解码；未声称连续视觉观看或声音认可'})
(S/'PURPOSE.md').write_text('# 13个完整组｜参考机制迁移试作\n\n'+ '\n\n'.join('## '+g['occurrence']+'\n'+catalog[g['occurrence']]['purpose']+'\n新片范围 '+str(g['rawRange'])+'；组件 '+str(catalog[g['occurrence']].get('visualComponents') or [g['visualFamily']])+' × '+str(catalog[g['occurrence']].get('subtitleComponents') or [g['subtitleFamily']])+'。' for g in m['groups'])+'\n\n先由人物解释，再以贴图/圆窗/重点词承接新语义。原片睡眠内容不机械沿用到工作口播；片段可重用但不把同一真人重复充当案例证据。N03办公实拍动态视频两个不同源时段仅语境示意，不称财务证据。所有配方为03候选，未推进04。',encoding='utf-8')
print(len(m['groups']),'proofs')
