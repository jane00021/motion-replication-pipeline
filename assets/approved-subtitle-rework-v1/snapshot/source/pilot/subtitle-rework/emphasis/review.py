import sys,json,copy,importlib
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
from fontTools.ttLib import TTFont
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'));import batch_runtime as rt
pr=importlib.import_module('subtitle-rework.emphasis.providers');S=P/'source/pilot/subtitle-rework/emphasis';R=P/'reviews/pilot/subtitle-rework/emphasis';O=P/'render/pilot/subtitle-rework/emphasis'
# Same word static roles on source crop and rendered candidate.
sheet=Image.new('RGB',(852,420),'#25272c');d=ImageDraw.Draw(sheet)
for row,(id,f) in enumerate([('N13',1433),('N17',1887)]):
 c=rt.load(R/f'{id}-same-word-input.json');crop=Image.open(P/f'observations/frame-audit/frames/{f+1:05d}.jpg').crop((0,245 if id=='N13' else 385,284,335 if id=='N13' else 450));sheet.paste(crop,(0,row*210+28));d.text((4,row*210+8),f'{id} source f{f}',fill='white')
 ls=pr.subtitle('T08' if id=='N13' else 'gold-wave',12,c);a=Image.new('RGBA',(284,504),'#25272c')
 for name in ['english','headline','goldSentence']:
  if name in ls:a.alpha_composite(ls[name])
 crop=a.crop((0,245 if id=='N13' else 385,284,335 if id=='N13' else 450));sheet.paste(crop,(284,row*210+28));d.text((288,row*210+8),'editable candidate same words',fill='white')
 alt=copy.deepcopy(c)
 if id=='N13':alt['roles']['headline']['font']='C:/Windows/Fonts/simsun.ttc'
 else:alt['roles']['sentence']['font']='C:/Windows/Fonts/simsun.ttc'
 ls=pr.subtitle('T08' if id=='N13' else 'gold-wave',12,alt);a=Image.new('RGBA',(284,504),'#25272c')
 for name in ['english','headline','goldSentence']:
  if name in ls:a.alpha_composite(ls[name])
 sheet.paste(a.crop((0,245 if id=='N13' else 385,284,335 if id=='N13' else 450)),(568,row*210+28));d.text((572,row*210+8),'SimSun alternate, thinner strokes',fill='white')
sheet.save(R/'same-word-static-font-comparison.jpg')
checks=[]
for id in ['N13','N17']:
 c=rt.load(S/f'{id}-input.json');fam='T08' if id=='N13' else 'gold-wave'
 for role,s in c['roles'].items():
  text=c['text']['headline' if role=='headline' else 'english' if role=='english' else 'sentence'];f=TTFont(s['font'],fontNumber=0);cm=f.getBestCmap();f.close();assert all(ord(ch) in cm for ch in text);tile,(w,h)=pr.tile(text,json.dumps(s,sort_keys=True));checks.append({'id':id,'role':role,'font':s['font'],'sha256':rt.sha(s['font']),'inkWidth':w,'inkHeight':h,'missing':[]})
 a=pr.subtitle(fam,12,c);off=copy.deepcopy(c)
 for s in off['roles'].values():s['shadow']['opacity']=0
 b=pr.subtitle(fam,12,off);assert any(a[k].tobytes()!=b[k].tobytes() for k in a)
 r=rt.load(S/f'{id}-recipe.json');rt.validate(r)
rt.dump(R/'font-shadow-checks.json',checks)
review={'scope':['N13','N17'],'status':'03-subtitle-trial','referenceObservations':{'N13':{'observedFrames':list(range(1421,1443)),'finding':'金中文与红英文是两个独立文字角色，红英文The real function不是红色投影。金字初始虚淡、小字，前7帧增大清晰；稳定字面约190x53，中文顶约258，英文约304。末帧仍保留，下一镜硬切，不能增加淡出。','clock':'local0低透明模糊；2可见；4接近稳定；7至21阅读保持。颜色阈值测量仅辅助、衣物误检已说明。'},'N17':{'observedFrames':list(range(1863,1911,2)),'finding':'整句金字及暗描边投影，逐字有起伏/倾斜；随原整体放大在画面下方约y400，不能因普通字幕类别丢掉材质。','measurement':'逐字波浪近似振幅3.2px，周期25帧，错相0.58rad，角度约±4°；未声称原曲线精确反推。'}},'AH-S07Scope':'读取HANDOFF、render.py和same-word/process-1/process-2。借鉴独立角色、实际字面、同字编码过程返工；不复制其年份/背字动作或把已认可效果等同原字体确认。','iterations':[{'round':1,'largest':['N13将英文误作红影','N13旧动作从大缩小，源实际由小增大','N17白色12px静态字幕丢失金色整句与字级波浪'],'fix':['独立可编辑English角色','参数关键帧0.75→1放大，blur2.5→0前7帧','金色渐变/描边/阴影，按单字公共基线+错相位移旋转']},{'round':2,'largest':['同字对照英文太小','N17候选金字字面较源窄'],'fix':['Georgia Bold英文15→19','金句17→18.5自然字号，不按整句固定宽拉伸']}],'largest3Remaining':{'N13':['原中文/英文字体身份未知，思源宋Bold/Georgia Bold仍有轮廓差异','金属高光与中文压缩比例近似','精确透明度、放大曲线和英中层相位未逐像素匹配'],'N17':['波浪参数为逐帧近似，未恢复原速度曲线','候选字形/描边厚度与源不同','新句长度和节奏改变，语音听审未完成']},'verification':{'fullDecode':True,'completeNewVideos':2,'sameWordEncodedCalibration':2,'fullRGBAFrames':128,'oldVisualUnchanged':True,'newProviderEditableRoles':True,'fontCoverage':True,'visibleShadowPixelDifference':True,'continuousVisualWatching':False,'audioListening':False,'accepted03':False}}
rt.dump(R/'review.json',review)
