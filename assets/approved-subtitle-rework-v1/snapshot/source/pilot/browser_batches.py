from pathlib import Path
import json
from playwright.sync_api import sync_playwright
P=Path.cwd();R=P/'reviews/pilot/integration';records=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe');page=b.new_page(viewport={'width':1280,'height':1040});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8767/render/pilot/index.html?revision=all24-parallel-v1',wait_until='domcontentloaded');cards=page.locator('article');assert cards.count()==24
 for card in cards.all():
  card.scroll_into_view_if_needed();oid=card.get_attribute('id');vs=card.locator('video');assert vs.count()==2
  vs.evaluate_all('async vs=>{for(const v of vs){v.muted=true;if(v.readyState<2){v.preload="auto";v.load();await Promise.race([new Promise((r,j)=>{v.addEventListener("loadeddata",r,{once:true});v.addEventListener("error",j,{once:true})}),new Promise((r,j)=>setTimeout(()=>j(Error("timeout")),20000))])}}}')
  card.locator('button').first.click();page.wait_for_timeout(350);assert vs.evaluate_all('vs=>vs.every(v=>v.currentTime>.1&&!v.error&&!v.paused)'),oid
  vs.evaluate_all('vs=>vs.forEach(v=>v.currentTime=Math.max(0,v.duration-.35))');page.wait_for_timeout(650);assert vs.evaluate_all('vs=>vs.every(v=>v.ended&&!v.error)'),oid
  vs.evaluate_all('vs=>vs.forEach(v=>{v.pause();v.currentTime=v.duration*.7})');page.wait_for_timeout(80)
  if oid in ['N03','N06','N08','N12','N15','N18','N19']:card.screenshot(path=str(R/(oid+'-browser.png')))
  records.append({'occurrence':oid,'twoPlayers':True,'playFromStart':True,'seekTailAndPlaybackEnd':True,'seekMiddle':True,'perceptualReview':False,'listening':False})
 for batch,count in [('pilot',2),('prompts',13),('evidence',5),('stages',4)]:page.select_option('#batch',batch);assert page.locator('article:visible').count()==count
 page.select_option('#batch','');assert page.locator('article:visible').count()==24;assert not errors;page.screenshot(path=str(R/'overview.png'));b.close()
(R/'browser.json').write_text(json.dumps({'groups':records,'jsErrors':errors,'filters':True,'totalPlayers':48},ensure_ascii=False,indent=2),'utf-8');print('24 cards /48 players checked')
