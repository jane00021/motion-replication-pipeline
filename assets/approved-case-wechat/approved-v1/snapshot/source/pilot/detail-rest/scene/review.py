from pathlib import Path
import json,cv2
from PIL import Image,ImageDraw
P=Path.cwd();R=P/'reviews/detail-rest/scene';O=P/'render/pilot/detail-rest/scene';m=json.loads((O/'manifest.json').read_text('utf-8'))
for g in m['groups']:
 id=g['occurrence'];N=g['frameCount'];frames=[0,N//5,N*2//5,N*3//5,N-1];sheet=Image.new('RGB',(1430,1044),'#20252a');d=ImageDraw.Draw(sheet);cap=cv2.VideoCapture(str(P/g['file']))
 for k,n in enumerate(frames):
  sf=g['sourceRange'][0]+round(n/(N-1)*(g['sourceRange'][1]-g['sourceRange'][0]-1));ref=Image.open(P/f'observations/frame-audit/frames/{sf+1:04d}.jpg');sheet.paste(ref,(k*286,24));cap.set(cv2.CAP_PROP_POS_FRAMES,n);ok,a=cap.read();assert ok;im=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((286,508));sheet.paste(im,(k*286,536));d.text((k*286+4,6),f'ref {sf} / new {n} stage aligned',fill='white')
 cap.release();sheet.save(R/f'{id}-encoded-stage-compare.jpg')
report={'stage':'03 trial not accepted','groups':['cg07','cg08','cg09'],'method':'沿用已认可detail-two方法：角色字体/墨迹盒居中、独立描边阴影、真实SVG输入、共享family引用配方、编码后阶段对照','iterations':[{'round':1,'found':['07标题固定左坐标导致视觉偏心','07/08/09矩形照片无法表达新语义','08固定GrabCut截掉食指并硬切肩膀'],'changes':['改typeRoles字面中心定位','新建5份原创透明物件SVG和4x缓存，卡片结构仍按原family保留','RVM MobileNetV3原分辨率连续抠像，12帧预热，柔边RGBA缓存；实际对照0/1/2/35/145帧'] }],'actualChecks':['3组实际编码完成并完整解码','实际查看新渲染关键帧','同字过程图对照 cg07/cg08','07标题和双标签、08双标题、09普通字幕墨迹盒居中计算','RVM前后发丝/肩膀/食指对照和连续0/1/2帧视觉检查'],'notDone':['未试听新口播逐词时点','未通过用户视觉认可','未确认原字体身份','未声称CG09内部案例视频已经还原'],'largestDifferences':{'cg07':['圆窗缩入轨迹和遮罩变形细节仍近似','原片标签与卡片不同，现为新语义SVG变体','宋体候选字形、笔画仍有差异'],'cg08':['数字雨密度纵深与原片不同','RVM已保留食指和肩线，但细发和手指贴脸处仍可能有软边泄漏','面板内部改为SVG语义插画，原片动态视频内容未复刻'],'cg09':['原案例窗内有实拍视频运动，现在SVG为静态语义场景，明确保留差异','人物窗/字幕与原片大小仍需感官确认','新口播普通字幕时点未听审']},'matting':{'method':'RobustVideoMatting MobileNetV3 ONNX CPU recurrent','inputResolution':[628,1118],'normalized':'RGB float32 [0,1] NCHW','downsampleRatio':.35,'warmupFrames':12,'output':'RGBA straight alpha, fgr and pha from model','temporalReviewFrames':[0,1,2,35,145],'knownLimits':'native soft alpha保留；贴脸手指与发丝可有柔边，未精修到像素级人工轮廓'} }
(R/'review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
