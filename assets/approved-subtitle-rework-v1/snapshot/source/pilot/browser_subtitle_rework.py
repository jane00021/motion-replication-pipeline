from pathlib import Path
import json
from playwright.sync_api import sync_playwright
P=Path.cwd();R=P/'reviews/pilot/subtitle-rework'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe');page=b.new_page(viewport={'width':1280,'height':1040});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8767/render/pilot/index.html?revision=subtitle-mechanisms-v2');assert page.locator('article:visible').count()==6;records=[]
 for card in page.locator('article:visible').all():
  card.scroll_into_view_if_needed();oid=card.get_attribute('id');vs=card.locator('video');assert vs.count()==2
  vs.evaluate_all('async vs=>{for(const v of vs){v.muted=true;v.preload="auto";if(v.readyState<2){v.load();await new Promise((r,j)=>{v.addEventListener("loadeddata",r,{once:true});v.addEventListener("error",j,{once:true})})}}}')
  card.locator('button').first.click();page.wait_for_timeout(350);assert vs.evaluate_all('vs=>vs.every(v=>v.currentTime>.1&&!v.error&&!v.paused)'),oid
  vs.evaluate_all('vs=>vs.forEach(v=>v.currentTime=Math.max(0,v.duration-.3))');page.wait_for_timeout(650);assert vs.evaluate_all('vs=>vs.every(v=>v.ended&&!v.error)'),oid
  vs.evaluate_all('vs=>vs.forEach(v=>{v.pause();v.currentTime=v.duration*.7})');page.wait_for_timeout(150);card.screenshot(path=str(R/(oid+'-browser.png')));records.append({'occurrence':oid,'twoPlayers':True,'fromStart':True,'seekAndEnd':True,'continuousPerceptualReview':False,'listening':False})
 page.select_option('#scope','all');assert page.locator('article:visible').count()==24;page.select_option('#scope','rework');assert not errors;b.close()
(R/'browser.json').write_text(json.dumps({'groups':records,'jsErrors':errors,'filters':True},ensure_ascii=False,indent=2),'utf-8');print('Six pairs checked; all24 filter checked')
