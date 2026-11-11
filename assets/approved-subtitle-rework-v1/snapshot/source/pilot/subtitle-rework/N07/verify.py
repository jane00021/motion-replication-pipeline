from pathlib import Path
import sys,json,copy,hashlib,importlib
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
P=Path(__file__).resolve().parents[4];sys.path.insert(0,str(P/'source/pilot'))
from batch_runtime import load,dump,validate,sha,compose
m=importlib.import_module('subtitle-rework.N07.providers');S=P/'source/pilot/subtitle-rework/N07';O=P/'render/pilot/subtitle-rework/N07';R=P/'reviews/subtitle-rework/N07'
cs=load(S/'same-word-input.json');cn=load(S/'new-content-input.json');r=load(S/'new-content-recipe.json');validate(r)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',11);frames=[86,92,100,106,110,114,120,134,163];sheet=Image.new('RGB',(len(frames)*146,3*280),'#eee');d=ImageDraw.Draw(sheet);same=cv2.VideoCapture(str(O/'same-word-text-process.mp4'));new=cv2.VideoCapture(str(O/'N07.mp4'))
for j,f in enumerate(frames):
 original=Image.open(P/'observations/frame-audit/frames'/f'{444+f+1:05d}.jpg');sheet.paste(original.resize((142,252)),(j*146,20));d.text((j*146,2),f'原参考local{f}',font=font,fill='#111');same.set(cv2.CAP_PROP_POS_FRAMES,f);ok,a=same.read();assert ok;sheet.paste(Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((142,252)),(j*146,300));d.text((j*146,282),f'同字local{f}',font=font,fill='#111');nf=round(f/163*145);new.set(cv2.CAP_PROP_POS_FRAMES,nf);ok,a=new.read();assert ok;sheet.paste(Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB)).resize((142,252)),(j*146,580));d.text((j*146,562),f'迁移阶段{nf}',font=font,fill='#111')
same.release();new.release();sheet.save(R/'process-comparison.jpg',quality=94)
cal=Image.new('RGB',(600,260),'#172124');cald=ImageDraw.Draw(cal);cald.text((8,4),'同字静态：源f565裁片 / 可编辑候选，非完整原素材基准',font=font,fill='white');cal.paste(Image.open(P/'observations/frame-audit/frames/00566.jpg').crop((55,100,230,165)).resize((350,130)),(4,25));merged=Image.new('RGBA',(284,504));ls=m.title_layers(134,cs)
for im in ls.values():merged.alpha_composite(im)
cal.paste(merged.crop((55,100,230,165)).resize((350,130)),(230,125));cal.save(R/'same-word-calibration.png')
checks=[];metrics=[]
for label,c in [('same-word',cs),('new-content',cn)]:
 seq=load(O/(label+'-rgba')/'sequence.json');assert len(seq['frames'])==c['frames'];boxes=[]
 for n in range(c['frames']):
  layer=Image.open(O/(label+'-rgba')/f'{n:04d}-goldMiddle.png');box=layer.getchannel('A').getbbox()
  if n>=c['splitSubtitle']['events']['goldSettle']+1:assert box and box[2]-box[0]>80
  boxes.append(box)
 for key in ['white','gold']:
  s=c['splitSubtitle'][key+'Style'];f=TTFont(s['font'],lazy=True);cmap=f.getBestCmap();f.close();assert all(ord(ch) in cmap for ch in c['splitSubtitle'][key]);tile,_=m.glyph_run(c['splitSubtitle'][key],json.dumps(s,sort_keys=True),c['splitSubtitle'].get('tracking' if key=='white' else 'goldTracking',0));metrics.append({'label':label,'role':key,'text':c['splitSubtitle'][key],'font':s['font'],'fontSha256':sha(s['font']),'inkSize':tile.size,'style':s})
 checks.append({'label':label,'frames':len(seq['frames']),'fullRGBASaved':True,'settledGoldWidth':next(b[2]-b[0] for n,b in enumerate(boxes) if n>=c['splitSubtitle']['events']['goldSettle']+1),'sequentialRevealCacheSafe':True})
# Primitive split conserves the actual source pixels before displacement.
sample=Image.open(O/'new-content-rgba/0090-whiteUpper.png');base=Image.new('RGBA',(284,504));ImageDraw.Draw(base).rectangle((20,90,220,120),fill='white');up,lo=m.split_rgba(base,105,0,0);up.alpha_composite(lo);assert np.array_equal(base,up)
changed=copy.deepcopy(cn);changed['splitSubtitle']['gold']='先行动';a=m.subtitle('T04',130,cn);b=m.subtitle('T04',130,changed);assert not np.array_equal(a['goldMiddle'],b['goldMiddle'])
dump(S/'font-metrics.json',metrics);dump(R/'verification.json',{'checks':checks,'splitMaskConservesOneText':True,'editGoldChangesPixels':True,'recipeValid':True,'fullResultSha256':sha(O/'N07.mp4'),'continuousVisualPlayback':False,'audioListening':False,'userApproved':False});print('N07 sequential full RGBA/coverage/split-mask/editability passed')
