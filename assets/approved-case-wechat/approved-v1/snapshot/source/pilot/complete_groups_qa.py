from pathlib import Path
import json,copy,subprocess
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
import complete_groups as g
P=g.P;O=g.O;R=P/'reviews/complete01-02';R.mkdir(exist_ok=True)
def load(p):return json.loads(Path(p).read_text('utf-8'))
def decode(p,w=286,h=508):
 d=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-vf','scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True)
 assert not d.stderr;return np.frombuffer(d.stdout,np.uint8).reshape(-1,h,w,3)
def main():
 manifest=load(O/'manifest.json');decodeRows=[]
 for group in manifest['groups']:
  path=P/group['file'];frames=decode(path);assert len(frames)==group['frameCount'];decodeRows.append({'id':group['id'],'frames':len(frames),'sha256':g.core.file_sha(path),'fullDecode':True})
  source=group['sourceRange'];sourceFrames=source[1]-source[0];ns=[0,6,12,18,30,42,50,60,65]
  sheet=Image.new('RGB',(3*572,3*310),'#161c26');d=ImageDraw.Draw(sheet)
  for j,n in enumerate(ns):
   dest=round(n/(sourceFrames-1)*(len(frames)-1));ref=Image.open(P/'observations/frame-audit/frames'/f'{source[0]+n+1:04d}.jpg').resize((143,254));candidate=Image.fromarray(frames[dest]).resize((143,254));x=j%3*572;y=j//3*310
   sheet.paste(ref,(x,y+40));sheet.paste(candidate,(x+165,y+40));d.text((x+3,y+3),f'reference local{n} / new local{dest}',fill='white');d.text((x+3,y+22),'phase alignment; different durations',fill='#b4caff')
  sheet.save(R/f'group{group["id"]}-decoded-process.jpg',quality=94)
 # Independent transparent component evidence: alpha without presenter image is not a screenshot.
 c=load(g.S/'input-01.json');alpha=g.group1(Image.new('RGBA',(286,508)),130,c,['vignette','photo']);alpha.save(R/'01-text-alpha.png');assert alpha.getchannel('A').getpixel((0,0))==0
 c2=load(g.S/'input-02.json');sym=g.symbols(30,c2);sym.save(R/'02-symbols-alpha.png');assert sym.getchannel('A').getpixel((0,0))==0
 # Mapped content/layers and every start/advance/handoff/exit are kept in records, not in page alone.
 clock={'01':{'source':{'absoluteFrames':[0,66],'vignette':[6,12],'workImage':[3,12],'openingText':[6,21],'questionAndResult':[42,51],'exit':[57,66]},'new':c['clock'],'layersBackToFront':['new-presenter-video','vignette','work-photo-soft-top','opening-lines','question','result-emphasis'],'handoff':'image and vignette establish labor context; result-question takes over late; all exit together','semanticMapping':{'reference':'为什么／越努力上班／越存不到钱','new':'加班／熬到半夜／存不下钱'},'note':'new headline summarizes0–5.8s, not a claimed verbatim transcript'},'02':{'source':{'absoluteFrames':[108,174],'symbols':[1,57],'captionChange':6,'titleEntry':[42,51],'titleHold':[51,66]},'new':c2['clock'],'layersBackToFront':['new-presenter-video','falling-spinning-warning-symbols','speech-caption','gold-title'],'handoff':'warning motifs establish risk and keep moving while caption advances; large warning title takes expression lead; symbols clear while title holds','semanticMapping':{'reference':'coin money motif -> 财富真相','new':'warning motif -> 警惕快钱'},'iconSubstitutionIsSameMechanism':True}}
 g.core.dump(g.S/'layer-clock-mapping.json',clock)
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe');page=b.new_page(viewport={'width':1280,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8768/render/pilot/index.html?revision=complete01-02-r2');cards=page.locator('article');assert cards.count()==2
  checks=[]
  for card in cards.all():
   videos=card.locator('video');assert videos.count()==2
   videos.evaluate_all('async vs=>{for(const v of vs){if(v.readyState<2)await new Promise(r=>v.addEventListener("loadeddata",r,{once:true}));}}');card.locator('button').first.click();page.wait_for_timeout(450);assert videos.evaluate_all('vs=>vs.every(v=>v.currentTime>.1&&!v.paused)');dur=videos.evaluate_all('vs=>Math.max(...vs.map(v=>v.duration))');page.wait_for_timeout(round(dur*1000)+200);assert videos.evaluate_all('vs=>vs.every(v=>v.ended)');videos.evaluate_all('vs=>vs.forEach(v=>v.currentTime=v.duration*.75)');page.wait_for_timeout(150);assert videos.evaluate_all('vs=>vs.every(v=>v.currentTime>0&&!v.error)');checks.append({'players':2,'playEndSeek':True})
  assert not errors;page.screenshot(path=str(R/'browser.png'),full_page=True);b.close()
 remaining=['新图标的下落轨迹和新标题材质为机制重建近似，未声明与金币像素级一致','01工作图片是替换素材；原字体身份、问句压叠排版和原图遮罩仍需用户复审','新片句时点按机器转录选取；未完成连续听审，不把技术播放称试听','02标题与原片前后遮挡关系尚未逐帧达到相同，当前为完整组件试作而非已验收库']
 g.core.dump(R/'qa.json',{'decode':decodeRows,'browser':checks,'jsErrors':errors,'components':manifest['groups'],'allRequestedComponentsPresent':True,'sharedClock':True,'newInputOnlyPresenter':True,'alphaEvidence':['01-text-alpha.png','02-symbols-alpha.png'],'actualVisualReview':'native source and decoded phase boards / captured browser stills; no claim of continuous perceptual audiovisual approval','remaining':remaining,'stageAccepted':False})
 report=load(P/'reports/03-pilot.json');g.core.dump(R/'prior-report03.json',report)
 report.update(unresolved=remaining,artifacts=[{'role':'editable-source','path':'source/pilot/complete_groups.py'},{'role':'comparison-video','path':'render/pilot/complete01-02/group-01.mp4'},{'role':'comparison-video','path':'render/pilot/complete01-02/group-02.mp4'},{'role':'pilot-review','path':'reviews/complete01-02/qa.json'}],checks=[{'id':'complete-group-01-02','passed':True,'method':'frozen-catalog+shared-clock-component-ablation+full-decode+actual-browser','finding':'严格映射cg01/cg02最终完整组：01含v01+t01，02含v02+t02；独立参数、同时间轴，画面与字幕齐备。用户允许图标语义替换，02金币换风险符号，保留运动与标题接管。缺字问号已切换可覆盖字体。完整解码、播放、拖动及组件禁用输出差异通过；视觉保真尚未验收。','evidence':['source/pilot/complete01-02/layer-clock-mapping.json','source/pilot/complete01-02/input-01.json','source/pilot/complete01-02/input-02.json','reviews/complete01-02/qa.json']}],notes='当前任务替换上一轮t15/v09测试范围，只处理用户指定01和02完整动效组，停03，不进入04/05。')
 g.core.dump(P/'reports/03-pilot.json',report);g.core.dump(P/'reviews/pilot-review.json',{'current':'complete01-02','report':'reviews/complete01-02/qa.json','stageAccepted':False})
 ctx=load(P/'workflow-context.json');ctx['currentRequest']='用户明确要求最终拆解目录01和02完整组，用未剪辑口播选合适片段；图标允许按新语义替换，核心保留机制与组合。';g.core.dump(P/'workflow-context.json',ctx)
 print(json.dumps({'completeGroups':2,'allComponents':True,'browserPlayers':4,'decoded':decodeRows,'needsReview':True}))
if __name__=='__main__':main()
