"""Probe + decode + browser playback + editable-layer checks. No listening claim."""
from pathlib import Path
import json, subprocess, copy, importlib.util, hashlib
import numpy as np
from playwright.sync_api import sync_playwright

P=Path(__file__).resolve().parents[2];out=P/'reviews';out.mkdir(exist_ok=True)
URL='http://127.0.0.1:8768/render/pilot/index.html'
def read(p):return json.loads(p.read_text('utf-8'))
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')
decode=[]
for group,n in [('cg06',66),('cg09',67)]:
    for kind,w in [('candidate',286),('compare',572)]:
        path=P/f'render/pilot/{group}-{kind}.mp4'
        cmd=['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=codec_name,width,height,nb_read_frames,duration','-of','json',str(path)]
        stream=json.loads(subprocess.run(cmd,check=True,capture_output=True).stdout)['streams'][0]
        assert int(stream['nb_read_frames'])==n and stream['width']==w and stream['height']==508
        dec=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True)
        assert dec.returncode==0 and not dec.stderr,dec.stderr
        decode.append({'path':path.relative_to(P).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'stream':stream,'fullDecode':True})
write(out/'pilot-decodes.json',decode)

spec=importlib.util.spec_from_file_location('pilot_renderer',P/'source/pilot/render_pilot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
params=read(P/'source/pilot/parameters.json')
layer_tests=[]
for g,i in [('cg06',38),('cg09',22)]:
    base=np.array(m.render_frame(g,i,params));p=copy.deepcopy(params)
    if g=='cg06':p[g]['firstLine']='单纯埋头学习'
    else:p[g]['circleCenter']=[190,130]
    diff=np.any(base!=np.array(m.render_frame(g,i,p)),2)
    assert diff.sum()>50
    layer_tests.append({'id':g,'parameterChangesPixels':int(diff.sum()),'method':'in-memory source parameter mutation; no replacement version exported'})
p=copy.deepcopy(params);p['font']='C:/Windows/Fonts/msyhbd.ttc'
diff=int(np.any(np.array(m.render_frame('cg06',38,params))!=np.array(m.render_frame('cg06',38,p)),2).sum())
assert diff>50
layer_tests.append({'id':'font-input','parameterChangesPixels':diff,'method':'in-memory glyph rasterization, no font variant exported'})
write(out/'pilot-layer-tests.json',layer_tests)

with sync_playwright() as pl:
    browser=pl.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',args=['--autoplay-policy=no-user-gesture-required'])
    page=browser.new_page(viewport={'width':1440,'height':1100});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(URL);page.wait_for_selector('article video')
    results=[]
    for group,total in [('cg06',66),('cg09',67)]:
        card=page.locator(f'article[data-group="{group}"]');videos=card.locator('video')
        for v in videos.all():v.evaluate('(v)=>new Promise((r,j)=>{if(v.readyState>=2)r();else{v.addEventListener("loadeddata",r,{once:true});v.addEventListener("error",()=>j(v.error?.message),{once:true});}})')
        card.locator('[data-action="play"]').click();page.wait_for_timeout(650)
        progress=videos.evaluate_all('(vs)=>vs.map(v=>({time:v.currentTime,playing:!v.paused,decoded:v.getVideoPlaybackQuality().totalVideoFrames}))')
        assert all(v['time']>.3 and v['playing'] and v['decoded']>5 for v in progress)
        page.wait_for_timeout(2200)
        ended=videos.evaluate_all('(vs)=>vs.map(v=>({ended:v.ended,time:v.currentTime,decoded:v.getVideoPlaybackQuality().totalVideoFrames}))')
        assert all(v['ended'] and v['decoded']>=total-2 for v in ended)
        slider=card.locator('input');slider.evaluate('(el,n)=>{el.value=n;el.dispatchEvent(new Event("input",{bubbles:true}));}',total//2);page.wait_for_timeout(250)
        sought=videos.evaluate_all('(vs)=>vs.map(v=>v.currentTime)')
        assert all(abs(t-(total//2+.15)/30)<.04 for t in sought),{'group':group,'sought':sought,'expected':(total//2+.15)/30}
        card.locator('[data-action="next"]').click();page.wait_for_timeout(120)
        after=videos.evaluate_all('(vs)=>vs.map(v=>v.currentTime)')
        assert all(abs(a-b-1/30)<.005 for a,b in zip(after,sought))
        card.screenshot(path=str(out/f'{group}-browser.png'))
        results.append({'group':group,'bothVideosPlayback':progress,'bothReachedEnd':ended,'sliderSeek':sought,'singleFrameStep':after})
    assert not errors
    page.screenshot(path=str(out/'pilot-browser.png'),full_page=True)
    write(out/'pilot-browser-qa.json',{'url':URL,'checks':results,'javascriptErrors':errors,'audioListeningApproved':False,'note':'Real headless Chrome decoded/playback/seek check; does not certify perceptual match or audio listening.'})
    browser.close()
print(json.dumps({'fullDecode':True,'layerTests':layer_tests,'browserPlayback':True,'audioListeningApproved':False},ensure_ascii=False))
