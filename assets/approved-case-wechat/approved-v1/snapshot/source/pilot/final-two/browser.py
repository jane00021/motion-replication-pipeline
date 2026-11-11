from pathlib import Path
from playwright.sync_api import sync_playwright
import json
P=Path.cwd();R=P/'reviews/final-two';checks=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe');page=b.new_page(viewport={'width':1300,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8768/render/pilot/index.html?revision=final-two-v1')
 assert page.locator('article').count()==2
 for card in page.locator('article').all():
  card.scroll_into_view_if_needed();vs=card.locator('video');assert vs.count()==2
  vs.evaluate_all('async vs=>{for(const v of vs){v.muted=true;v.preload="auto";v.load();await new Promise((r,j)=>{v.addEventListener("loadeddata",r,{once:true});v.addEventListener("error",j,{once:true})})}}')
  card.locator('button').first.click();page.wait_for_timeout(500);assert vs.evaluate_all('vs=>vs.every(v=>v.currentTime>.1&&!v.paused)')
  duration=vs.evaluate_all('vs=>Math.max(...vs.map(v=>v.duration))');page.wait_for_timeout(round(duration*1000)+150);assert vs.evaluate_all('vs=>vs.every(v=>v.ended&&!v.error)')
  vs.evaluate_all('vs=>vs.forEach(v=>{v.currentTime=v.duration*.7;v.pause()})');page.wait_for_timeout(200);card.screenshot(path=str(R/(card.get_attribute('id')+'-browser.png')))
  checks.append({'occurrence':card.get_attribute('id'),'twoPlayers':True,'technicalPlayToEnd':True,'seek':True,'continuousPerceptualWatching':False,'listening':False})
 assert not errors;page.screenshot(path=str(R/'browser.png'));b.close()
(R/'browser.json').write_text(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2),'utf-8');print('browser 2 cards, 4 players checked')
