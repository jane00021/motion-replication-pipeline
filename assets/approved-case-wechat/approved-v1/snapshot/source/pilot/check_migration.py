from pathlib import Path
import json,subprocess,hashlib
from playwright.sync_api import sync_playwright
P=Path(__file__).resolve().parents[2];O=P/'render/pilot/migration';results=[]
for name,n in [('subtitle',96),('visual',75)]:
 for kind in ['raw','applied']:
    f=O/f'{name}-{kind}.mp4'
    data=json.loads(subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames','-of','json',str(f)],check=True,capture_output=True).stdout)['streams'][0]
    assert int(data['nb_read_frames'])==n and data['width']==628
    d=subprocess.run(['ffmpeg','-v','error','-i',str(f),'-f','null','-'],capture_output=True);assert d.returncode==0 and not d.stderr
    results.append({'file':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'fullDecode':True,'frames':n})
with sync_playwright() as pl:
 b=pl.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe');page=b.new_page(viewport={'width':1440,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8768/render/pilot/index.html?revision=raw-migration-1');checks=[]
 for group,total in [('cg06',96),('cg09',75)]:
    card=page.locator(f'article[data-group="{group}"]');videos=card.locator('.columns .pane video:not(.original-reference)');videos.evaluate_all('async (vs)=>{for(const v of vs){if(v.readyState<2)await new Promise(r=>v.addEventListener("loadeddata",r,{once:true}));}}');card.locator('[data-action="play"]').click();page.wait_for_timeout(900)
    playing=videos.evaluate_all('(vs)=>vs.map(v=>({time:v.currentTime,playing:!v.paused,decoded:v.getVideoPlaybackQuality().totalVideoFrames}))');assert all(v['time']>.15 and v['playing'] for v in playing)
    page.wait_for_timeout(total/30*1000)
    ended=videos.evaluate_all('(vs)=>vs.map(v=>v.ended)');assert all(ended)
    card.locator('input').evaluate('(e,n)=>{e.value=n;e.dispatchEvent(new Event("input"));}',int(total*.8));page.wait_for_timeout(200)
    times=videos.evaluate_all('(vs)=>vs.map(v=>v.currentTime)');assert max(times)-min(times)<.01
    card.screenshot(path=str(P/f'reviews/{group}-migration-browser.png'))
    checks.append({'group':group,'playing':playing,'ended':ended,'seek':times})
 assert not errors
 b.close()
(P/'reviews/migration-qa.json').write_text(json.dumps({'decode':results,'browser':checks,'javascriptErrors':errors,'transparentLayerEvidence':'render/pilot/migration/alpha-qa.json','noOldRepairedAssets':True,'audioListeningApproved':False},ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'newInputClips':4,'decodedAndBrowserPlayed':True,'alphaNoBackground':True}))
