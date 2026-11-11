from pathlib import Path
import json,subprocess,copy
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
import round2_render as rr
P=rr.P;O=rr.O
def load(p):return json.loads(Path(p).read_text('utf-8'))
def main():
 results=[]
 for name,frames in [('subtitle-applied.mp4',78),('visual-applied.mp4',34),('subtitle-same.mp4',46)]:
  path=O/name;probe=json.loads(subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=width,height,nb_read_frames','-of','json',str(path)],check=True,capture_output=True).stdout)['streams'][0]
  assert int(probe['nb_read_frames'])==frames
  d=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True);assert d.returncode==0 and not d.stderr
  results.append({'file':name,'sha256':rr.core.file_sha(path),'frames':frames,'fullDecode':True})
 cfg=load(rr.S/'subtitle-input.json');rr.core.ink(cfg['phrases']['first']['text'],cfg['styles']['first'])
 checks=[]
 for n in range(78):
  im=Image.open(O/'subtitle-rgba'/f'{n:04d}.png');assert im.mode=='RGBA';bb=im.getchannel('A').getbbox();assert not bb or (bb[0]>=0 and bb[2]<286 and bb[1]>0 and bb[3]<508)
 checks.append({'RGBAFrames':78,'endStillVisibleAsReference':True,'noRectangleBackground':True})
 same=copy.deepcopy(cfg);same['phrases']=cfg['sameWord']['phrases'];ns=[0,3,6,12,20,23,29,40];out=Image.new('RGB',(4*572,2*220),'#19202a')
 for j,n in enumerate(ns):
  x=j%4*572;y=j//4*220;ref=Image.open(P/'observations/frame-audit/frames'/f'{1173+n:04d}.jpg').crop((0,325,286,420));bg=Image.new('RGBA',(286,508),'#263036');bg.alpha_composite(rr.text_layer(same,n));cand=bg.convert('RGB').crop((0,325,286,420))
  out.paste(ref,(x,y+20));out.paste(cand,(x+286,y+20));ImageDraw.Draw(out).text((x+3,y+3),f'local{n}: reference / same text',fill='white')
 out.save(P/'reviews/round2-subtitle-comparison.jpg',quality=95)
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe');page=b.new_page(viewport={'width':1180,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8768/render/pilot/index.html?revision=skill-round2')
  assert page.locator('article').count()==2
  for card in page.locator('article').all():
   assert card.locator('video').count()==2
   card.locator('video').evaluate_all('async vs=>{for(const v of vs){if(v.readyState<2)await new Promise(r=>v.addEventListener("loadeddata",r,{once:true}));}}')
   card.locator('button').first.click();page.wait_for_timeout(350);assert card.locator('video').evaluate_all('vs=>vs.every(v=>!v.paused&&v.currentTime>0)')
   page.wait_for_timeout(2700);assert card.locator('video').evaluate_all('vs=>vs.every(v=>v.ended)')
   card.locator('video').evaluate_all('vs=>vs.forEach(v=>v.currentTime=v.duration/2)');page.wait_for_timeout(150);assert card.locator('video').evaluate_all('vs=>vs.every(v=>v.currentTime>0&&!v.error)')
  assert not errors;page.screenshot(path=str(P/'reviews/round2-browser.png'),full_page=True);b.close()
 rr.core.dump(P/'reviews/round2-qa.json',{'decoded':results,'alpha':checks,'browserPlayers':4,'browserPlayEndSeek':True,'jsErrors':errors,'visualInspection':'source/native process stills and same-word frame board; browser is technical playback, no audio-listening approval','skillVersionEvidence':'reviews/skill-calibration-update.json','priorApprovedSample':'reviews/t04-user-approval.json','remaining':['字幕字体身份与逐帧速度仍需人眼复审','整体放大几何拟合约2px误差，未包含原片t14字幕组件','新片声音未连续听审'],'stageAccepted':False})
 report=load(P/'reports/03-pilot.json');rr.core.dump(P/'reviews/report03-before-round2.json',report)
 report.update(unresolved=['第二轮t15字幕与v09画面新代表组等待真实对照复审；不能将上一组用户认可沿用。','字体身份、精确动作速度/几何以及新片听审仍未通过。'],artifacts=[{'role':'editable-source','path':'source/pilot/round2_render.py'},{'role':'comparison-video','path':'render/pilot/round2/subtitle-applied.mp4'},{'role':'comparison-video','path':'render/pilot/round2/visual-applied.mp4'},{'role':'pilot-review','path':'reviews/round2-qa.json'}],checks=[{'id':'updated-skill-and-new-trials','passed':True,'method':'skill-validate+fresh-init-check+render+full-decode+same-word-process+real-browser','finding':'全局skill与新init读取新校准方法；已选择不同t15与v09，读取用户最终边界，实际渲染新输入。每组只展示原对标/新口播结果。字幕单独RGBA；画面只重建v09整体回放大，不冒称附带t14字幕已实现。','evidence':['reviews/skill-calibration-update.json','reviews/round2-subtitle-comparison.jpg','reviews/round2-qa.json','source/pilot/round2/subtitle-input.json','source/pilot/round2/visual-input.json']}],notes='用户认可上一t04阴影版范围单独保存到reviews/t04-user-approval.json；新两组是下一轮待检验，不自动accept03或进入04。')
 rr.core.dump(P/'reports/03-pilot.json',report)
 ctx=load(P/'workflow-context.json');ctx['currentRequest']='沉淀当前字幕方法到skill后，再挑选一字幕组、一画面组复刻供用户检验；范围在03。';rr.core.dump(P/'workflow-context.json',ctx)
 print(json.dumps({'newGroups':2,'browserPlayers':4,'fullDecode':True,'userReviewPending':True}))
if __name__=='__main__':main()
