"""User-requested new-input trial, within reopened03. Never reads repaired reference assets."""
from pathlib import Path
import json,subprocess,copy,hashlib
import numpy as np
import cv2
from PIL import Image,ImageDraw
import render_pilot as engine
P=engine.P;S=P/'source/pilot';O=P/'render/pilot/migration';O.mkdir(exist_ok=True)
manifest=engine.read(S/'new-input/manifest.json');SRC=manifest['path']
W,H=628,1118
def run(cmd):return subprocess.run(cmd,check=True,capture_output=True)
def extract(start,duration):
    result=run(['ffmpeg','-v','error','-ss',str(start),'-i',SRC,'-t',str(duration),'-vf','fps=30,scale=628:1118','-f','rawvideo','-pix_fmt','rgb24','pipe:1'])
    return np.frombuffer(result.stdout,np.uint8).reshape(-1,H,W,3)
def encode(path,frames,audio):
    proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','628x1118','-r','30','-i','pipe:0','-i',str(audio),'-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart',str(path)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    for im in frames:proc.stdin.write(np.asarray(im,dtype=np.uint8).tobytes())
    proc.stdin.close();err=proc.stderr.read();rc=proc.wait()
    if rc:raise RuntimeError(err.decode(errors='replace'))
def audio(name,start,duration):
    p=O/f'{name}.wav';run(['ffmpeg','-v','error','-y','-ss',str(start),'-i',SRC,'-t',str(duration),'-vn','-ac','1',str(p)]);return p

def main():
    assert engine.read(P/'.pipeline/state.json')['stages'][3]['status']=='active'
    p=engine.read(S/'parameters.json');p=copy.deepcopy(p)
    # Reuse exactly the subtitle entry/glow/exit mechanism with new text, clocks and sizing.
    p['cg06'].update(firstLine='打工就是拿时间去换工资',secondLine='天花板就在这',firstFontSize=20,firstLineXY=[24,346],secondFontSize=29,secondLineXY=[85,373],goldFromCharacter=2,glyphEntryFrames=[12-k for k in range(11)],streakFrame=63,settleFrame=75,fadeStartFrame=91,fadeEndFrame=96)
    p['cg06'].pop('goldFromCharacter',None)
    p['cg06']['emphasisRanges']=[[0,3]]
    p['cg06']['semanticRoles']=[{'text':'天花板','range':[0,3],'role':'核心限制结论','style':'gold-emphasis-with-entry-glow'},{'text':'就在这','range':[3,6],'role':'辅助指代','style':'white-support'}]
    O.joinpath('alpha').mkdir(exist_ok=True)
    raw=extract(19.4,3.2);assert len(raw)==96
    subtitle=[];alpha_stats=[]
    for i,a in enumerate(raw):
        transparent=engine.render_frame('cg06',0,p,base_override=Image.new('RGBA',(286,508)),clock_frame=i)
        alpha=np.array(transparent)[:,:,3]
        disabled=engine.render_frame('cg06',0,p,disable=['text'],base_override=Image.new('RGBA',(286,508)),clock_frame=i)
        assert np.max(np.array(disabled)[:,:,3])==0
        scaled=transparent.resize((W,H),Image.Resampling.LANCZOS)
        im=Image.fromarray(a).convert('RGBA');im.alpha_composite(scaled);subtitle.append(im.convert('RGB'))
        if i in [0,12,64,70,79,90,95]:
            scaled.save(O/f'alpha/{i:04d}.png');im.save(O/f'subtitle-{i}.png')
        alpha_stats.append({'frame':i,'nontransparent':int((alpha>0).sum()),'disabledAlphaMax':0,'cornerAlpha':[int(alpha[y,x]) for x,y in [(0,0),(285,0),(0,507),(285,507)]]})
    aud=audio('subtitle',19.4,3.2)
    encode(O/'subtitle-raw.mp4',[Image.fromarray(a) for a in raw],aud);encode(O/'subtitle-applied.mp4',subtitle,aud)
    # Same v07 geometry; both video slots use the new raw input, not any old composite.
    raw2=extract(17.5,2.5);assert len(raw2)==75;visual=[]
    for i,a in enumerate(raw2):
        base=Image.new('RGBA',(286,508),'#18191a');d=ImageDraw.Draw(base)
        for x in range(0,286,8):d.line((x,0,x,508),fill='#1c1d1e')
        for y in range(0,508,8):d.line((0,y,286,y),fill='#1c1d1e')
        broll=Image.fromarray(a).resize((286,509),Image.Resampling.LANCZOS).crop((0,115,286,296))
        base.alpha_composite(broll.convert('RGBA'),(0,162))
        d=ImageDraw.Draw(base)
        geom=p['cg09'];cx,cy=geom['circleCenter'];r=geom['ringRadius']-1
        for y in geom['rulesY']:d.rectangle((0,y,286,y+geom['rulesThickness']-1),fill='white')
        # Native raw face-centered crop includes forehead through chin, not just hair.
        face=Image.fromarray(a).crop((110,230,510,630)).resize((99,99),Image.Resampling.LANCZOS).convert('RGBA')
        mask=Image.new('L',(99,99));ImageDraw.Draw(mask).ellipse((1,1,97,97),fill=255);face.putalpha(mask)
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill='white');base.alpha_composite(face,(cx-49,cy-49))
        text='但风险全在自己身上' if i<40 else '好几年都翻不过身'
        glyph=engine.text_layer(text,18,font_path=p['font']);engine.paste(base,glyph,((286-glyph.width)/2,370))
        final=base.resize((W,H),Image.Resampling.LANCZOS).convert('RGB');visual.append(final)
        if i==40:final.save(O/'visual-40.png')
    aud2=audio('visual',17.5,2.5)
    encode(O/'visual-raw.mp4',[Image.fromarray(a) for a in raw2],aud2);encode(O/'visual-applied.mp4',visual,aud2)
    # Standalone alpha sequence is genuine RGBA with no presenter/background pixels.
    engine.write(O/'alpha-qa.json',{'frames':alpha_stats,'textDisabledFullyTransparent':True,'backgroundOrRepairRead':False})
    engine.write(S/'migration-parameters.json',{'input':manifest,'subtitleParameters':p['cg06'],'visualParameters':p['cg09'],'subtitleRange':[19.4,22.6],'visualRange':[17.5,20.0],'timingSource':'local ASR hypothesis; listening not approved','visualSlots':'presenter and example window both use new raw clip; same-person duplication is disclosed functional slot test, not semantically appropriate final broll','scopeAuthorization':'用户明确要求用这条未剪辑口播验证迁移；作为03输入验证试验，不提前验收05。'})
    engine.write(O/'manifest.json',{'status':'new-input-migration-trial-not-accepted','inputSha256':manifest['sha256'],'oldRepairedAssetsUsed':False,'sourceRenderer':'source/pilot/render_migration.py','sharedSubtitleEngine':'source/pilot/render_pilot.py:render_frame(base_override,clock_frame)','outputs':[{'id':'subtitle','raw':'subtitle-raw.mp4','applied':'subtitle-applied.mp4','frames':96},{'id':'visual','raw':'visual-raw.mp4','applied':'visual-applied.mp4','frames':75}],'limits':['font and motion fidelity remain pending','new script transcription/timing requires listening','example slot uses same raw presenter for mechanical validation only']})
    # Preserve history; replace the official pilot entry with the new-input trial.
    page=P/'render/pilot/index.html';old=page.read_text('utf-8')
    history=P/'reviews/pilot-page-before-migration.html'
    if not history.exists():history.write_text(old,'utf-8')
    old=history.read_text('utf-8')
    old=old.replace('男生参考视频｜代表组复刻试验·未验收','未剪辑口播｜动效迁移试验·未验收')
    old=old.replace('先检验两组机制，再决定是否扩展','用未剪辑口播检验动效迁移')
    start=old.index('<p>男生参考视频');end=old.index('<article',start)
    old=old[:start]+'''<p>新输入：灰衣男生未剪辑口播。<a href="http://127.0.0.1:8766/observations/decomposition-preview/index.html?revision=final-feedback">原参考拆解页</a></p><div class="notice">字幕组直接叠加到新底片，没有清字、补背景或矩形底板。可下载<a href="migration/alpha/0079.png">透明字幕PNG</a>检查。画面组两处视频输入均来自新片，案例窗暂用同一人物做输入测试；尚未验证为合格完整复刻。</div>'''+old[end:]
    old=old.replace('cg06 · 解释口播与重点词字幕','字幕机制迁移 · 解释句与金色重点句').replace('cg09 · 横线框景与人物窗','画面机制迁移 · 横线框景与新人物窗')
    old=old.replace('data-frames="66"','data-frames="96"').replace('max="65"','max="95"').replace('/ 65 帧','/ 95 帧').replace('data-frames="67"','data-frames="75"').replace('max="66"','max="74"').replace('/ 66 帧','/ 74 帧')
    old=old.replace('../../observations/accepted-review/cg06/reference-clip.mp4','migration/subtitle-raw.mp4').replace('cg06-candidate.mp4','migration/subtitle-applied.mp4').replace('../../observations/accepted-review/cg09/reference-clip.mp4','migration/visual-raw.mp4').replace('cg09-candidate.mp4','migration/visual-applied.mp4')
    old=old.replace('原片参考','新口播原片').replace('独立文字重建候选 · 未通过','字幕应用结果 · 待复审').replace('独立图层重建候选 · 未通过','画面应用结果 · 待复审')
    old=old.replace('仅字幕动效 t04｜来源 00:10.000–00:12.200｜源帧 [300,366)，终帧不包含','仅字幕机制 t04｜新片 00:19.400–00:22.600｜96帧，终帧不包含').replace('仅画面动效 v07｜普通口播主字幕不另计字幕动效｜来源 00:17.700–00:19.933｜源帧 [531,598)','画面机制 v07｜新片 00:17.500–00:20.000｜75帧，终帧不包含')
    old=old.replace('保留原人物动态；文字区域用无字参考帧对齐修补。','直接保留新口播原始底片，关闭字幕即恢复原画面。').replace('「单纯埋头打工」','「打工就是拿时间去换工资」').replace('「只能维持生活」','「天花板就在这」').replace('白色与金色分区。','金色重点句。').replace('修补区域时序稳定性','新语句时间匹配').replace('独立提取的静态暗纹背景。','程序绘制暗纹背景。').replace('案例视频活动矩形图层。','案例窗输入新口播（同人物重复，仅作输入验证）。').replace('独立活动人物窗、圆形遮罩与白色圆环。','从新片裁取活动人物窗；圆形遮罩、圆环独立绘制。').replace('被原人物窗遮挡的案例区域修补','独立素材窗裁切与新台词匹配')
    old=old.replace('source/pilot/parameters.json','source/pilot/migration-parameters.json').replace('cg06-compare.mp4','migration/subtitle-applied.mp4').replace('cg09-compare.mp4','migration/visual-applied.mp4').replace('并排对照 MP4','迁移结果 MP4').replace('cg06-comparison.png','migration/alpha/0079.png').replace('参考 / 候选 / 隐去字幕组件','透明字幕层 PNG').replace('cg09-comparison.png','migration/visual-40.png').replace('参考 / 候选 / 隐去人物窗与横线','新片应用帧').replace('source/pilot/asset-provenance.json','source/pilot/new-input/manifest.json').replace('素材提取和修补记录','新输入来源记录')
    old=add_reference_panels(old)
    old=old.replace('金色重点句。','“天花板”是核心限制结论：金色重点；“就在这”是辅助指代：白色。')
    old=old.replace('<li>发光消退后停留，再退场。</li>','<li>强调光效绑定“天花板”，不按第几个字固定着色；发光消退后停留，再共同退场。</li>')
    old=old.replace('migration/subtitle-applied.mp4','migration/subtitle-applied.mp4?revision=semantic-emphasis-v3')
    old=old.replace('待改：字形与笔画、光晕强度、揭字过程、新语句时间匹配；需实际听审。','设计对照：原片“只能”白色、“维持生活”金色；新片“天花板”金色、“就在这”白色。字体材质、描边阴影与字距仍待与对标校准；当前未验收。')
    page.write_text(old,'utf-8')
    print(json.dumps({'newInputApplied':True,'subtitleFrames':96,'visualFrames':75,'noRepairedBackground':True},ensure_ascii=False))
def add_reference_panels(html):
    for group,tc in [('cg06','00:10.000–00:12.200'),('cg09','00:17.700–00:19.933')]:
        start=html.index(f'<article data-group="{group}"')
        at=html.index('<div class="columns">',start)+len('<div class="columns">')
        html=html[:at]+f'<section class="pane"><label>原对标动效组 · 参考成片</label><video class="original-reference" controls muted playsinline preload="auto" src="../../observations/accepted-review/{group}/reference-clip.mp4"></video><small>对标来源 {tc}｜独立播放，保留原速度</small></section>'+html[at:]
    html=html.replace("card.querySelectorAll('video')","card.querySelectorAll('video:not(.original-reference)')")
    html=html.replace('>同步播放</button>','>同步播放新片与结果</button>')
    return html
if __name__=='__main__':main()
