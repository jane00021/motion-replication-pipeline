"""Actual native browser playback checks; no claim of audiovisual perception."""
import json,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright
P=Path(__file__).resolve().parents[2];R=P/'reviews/last-four/integration'
def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf-8')
def main():
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',args=['--autoplay-policy=no-user-gesture-required'])
  page=browser.new_page(viewport={'width':1280,'height':1040});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto('http://127.0.0.1:8768/render/pilot/index.html?revision=last-four-v1',wait_until='domcontentloaded');cards=page.locator('article[data-batch]');assert cards.count()==4
  records=[]
  for card in cards.all():
   card.scroll_into_view_if_needed();oid=card.get_attribute('id');videos=card.locator('video');assert videos.count()==2
   videos.evaluate_all('async vs=>{for(const v of vs){v.preload="auto";v.muted=true;if(v.readyState<2){v.load();await Promise.race([new Promise((r,j)=>{v.addEventListener("loadeddata",r,{once:true});v.addEventListener("error",()=>j(Error("video error")),{once:true})}),new Promise((r,j)=>setTimeout(()=>j(Error("load timeout")),25000))])}}}')
   card.locator('button').first.click();page.wait_for_timeout(650)
   start=videos.evaluate_all('vs=>vs.map(v=>({current:v.currentTime,paused:v.paused,width:v.videoWidth,height:v.videoHeight,error:!!v.error}))');assert all(v['current']>.1 and not v['paused'] and not v['error'] for v in start),(oid,start)
   videos.evaluate_all('vs=>vs.forEach(v=>{v.currentTime=Math.max(0,v.duration-.45)})');page.wait_for_timeout(900)
   assert videos.evaluate_all('vs=>vs.every(v=>v.ended&&!v.error)'),oid
   videos.evaluate_all('vs=>vs.forEach(v=>{v.currentTime=v.duration*.5;v.pause()})');page.wait_for_timeout(120)
   assert videos.evaluate_all('vs=>vs.every(v=>v.currentTime>0&&!v.error)'),oid
   if oid in ['cg01','cg02','cg09','cg19']:card.screenshot(path=str(R/(oid+'-browser.png')))
   records.append({'occurrence':oid,'players':2,'loadedDimensions':[v['width'] for v in start],'playFromStart':True,'playToEndAfterTailSeek':True,'seekMidpoint':True,'scope':'native browser technical playback; not continuous full perceptual watching or listening'})
  for value,count in [('opening',2),('scene',1),('closing',1)]:
   page.select_option('#batch',value);assert page.locator('article[data-batch]:visible').count()==count
  page.select_option('#batch','');assert page.locator('article[data-batch]:visible').count()==4
  assert not errors,errors
  page.screenshot(path=str(R/'browser-overview.png'))
  browser.close()
 dump(R/'browser.json',{'groups':records,'jsErrors':errors,'batchFilters':True,'actualBrowser':True,'perceptualOrAudioApproval':False})
 print(json.dumps({'browserGroups':len(records),'players':len(records)*2,'jsErrors':errors}))
if __name__=='__main__':main()
