import sys,json
from pathlib import Path
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'));from components import scene_batch as m
from components.common import load
from PIL import Image,ImageDraw
S=P/'source/pilot/batches/scene';R=P/'reviews/batches/scene'
sets=[('cg04','t03',['经济环境','彻底改变','工资暴富'],[0,31,63,94,125]),('cg07','t05',['很多人习惯','跟风消费','盲目扩张'],[0,20,40,60,82]),('cg08','t06',['透支负债前行','跟风盲目炒股'],[0,17,34,51,68])]
for id,fam,words,frames in sets:
 c=load(S/(id+'-input.json'));sf=c['sourceRange'][0];N=c['sourceRange'][1]-sf
 if fam=='t03':c['text']=dict(zip(['context','change','result'],words));c['clock'].update(context=0,change=31,result=80,returnStart=120,returnEnd=126)
 elif fam=='t05':c['text']=dict(zip(['title','left','right'],words));c['clock'].update(title=16,leftLabel=25,rightLabel=60)
 else:c['text']=dict(zip(['first','second'],words));c['clock'].update(firstText=0,secondText=28,secondPanel=[25,38])
 sheet=Image.new('RGB',(5*286,1060),'#20252a');d=ImageDraw.Draw(sheet)
 for k,n in enumerate(frames):
  ref=Image.open(P/f'observations/frame-audit/frames/{sf+n+1:04d}.jpg').convert('RGB');sheet.paste(ref,(k*286,26));alpha=m.render_subtitle(fam,n,c)['text'];bg=Image.new('RGBA',(286,508),'#25282c');bg.alpha_composite(alpha);sheet.paste(bg.convert('RGB'),(k*286,550));d.text((k*286+4,6),f'source f{sf+n} / local {n}',fill='white')
 sheet.save(R/(id+'-same-word-process.jpg'))
 (R/(id+'-same-word-parameters.json')).write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
report={'scope':'03 scene batch trial, not accepted','actualChecks':['实际观察4份原片process-evidence.jpg','实际查看4组编码过程图','同字3字体候选图比对','圆窗嘴部截断问题修复后重编码','cg08从宋体改用粗黑候选后重编码','真实MP4完整解码和帧数检查','输出透明字幕与人物图层PNG','共用runtime独立调用及源码摘要核对'],'notPerformed':['未完成连续视觉观看','未试听台词词点与声音','未证明原字体身份','未通过用户感官验收'],'largestDifferences':{'cg04':['原片主句是压缩黑体，本次粗黑候选字形仍非原字体','城市与工作素材更换后明暗/构图不同','斜切撕边采用数学边线，纸纹与缓动仍近似'],'cg07':['人物圆窗的缩入轨迹/变形时长须与原动作精校','标签字重与卡片裁切和原片不同','新台词延长后双卡错时需要听审'],'cg08':['原片数字雨为细竖线纵深，本次程序数字密度与流速近似','GrabCut抠像双手/发丝存在粗边','第二面板的峰值比例和弹性需精校'],'cg09':['案例输入目前为静态实拍轻移，缺乏原片案例内部运动','圆窗与横线尺寸仍有像素差','普通口播字幕词点未经听审']},'iterations':[{'round':1,'found':['圆窗下巴嘴部裁断','cg08误用宋体'],'fix':['共享圆窗裁切更改为[51,82,239,300]','cg08独立body字体输入改Noto Sans Bold']},{'round':2,'found':['cg04返回人物尾帧仍混合','字体参数不是每角色真实入口'],'fix':['返回在末帧之前完成','body/statement/labels均驱动渲染']}]}
(R/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
