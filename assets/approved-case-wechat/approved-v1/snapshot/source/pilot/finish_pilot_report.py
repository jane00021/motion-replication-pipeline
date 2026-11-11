from pathlib import Path
import json,subprocess,hashlib
P=Path(__file__).resolve().parents[2]
def write(p,v):
    q=P/p;q.parent.mkdir(exist_ok=True,parents=True);q.write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf-8')
def read(p):return json.loads((P/p).read_text('utf-8'))
for group in ['cg06','cg09']:
    result=subprocess.run(['python','-X','utf8',str(P/'.pipeline/motion_pipeline.py'),'validate-video','--project',str(P),'--video',f'render/pilot/{group}-candidate.mp4'],check=True,capture_output=True,text=True,encoding='utf-8')
    write(f'reviews/{group}-video-validation.json',json.loads(result.stdout))
raw=P/'observations/manual-review/adjustments.json'
assert hashlib.sha256(raw.read_bytes()).hexdigest()=='ad019b72bf6d8488083dad54865249365ea5f989d5d1519abe1019c7669afed8'
unknowns=[
 {'id':'cg06-motion-match','sourceFrames':[301,312,331,342,360,365],'finding':'已经真实重建逐字和亮条动作，但字号/字形、逐字移动/缩放、纵向模糊展开与发光幅度仍有可见差异，尚不能作为合格原素材基准。','evidence':['reviews/cg06-browser.png','render/pilot/cg06-comparison.png','measurements/evidence/text-300.jpg','measurements/evidence/text-324.jpg']},
 {'id':'original-font','finding':'参考是低分辨率栅格成片，无法证明系统宋体就是原字体；当前候选显式记录字体近似。','evidence':['measurements/fonts.json','source/pilot/parameters.json']},
 {'id':'repaired-original-media','finding':'仅有烧字成片；cg06胸口/领口用无字邻帧对齐修补，cg09被人物窗遮挡的案例视频区域用修补填充。可见原人物和案例运动得以保留，但修补稳定性、圆环遮罩边缘与原素材一致性未通过。','evidence':['source/pilot/asset-provenance.json','reviews/cg09-browser.png','render/pilot/cg09-comparison.png']},
 {'id':'audio-and-handoff-review','finding':'原混合音轨按原时钟裁出，解码检查通过；尚无实际连续听审，以及带相邻独立组的完整交接复审，不能将ASR/播放至结束冒充声画质量验收。','evidence':['reviews/pilot-browser-qa.json','reviews/pilot-decodes.json','measurements/evidence/speech-asr.json']}
]
write('reviews/pilot-review.json',{'stage':'03-pilot','status':'needs-revision-not-accepted','scope':['cg06:t04 subtitle-only','cg09:v07 visual-only'],'reference':'wechat-0a5c43 male source at8766','fullDecode':True,'browserPlayAndSeek':True,'realLayerSource':True,'visualInspectionMethod':'native comparison images, source per-frame strips, browser captured frames; no claim of continuous human audiovisual review','audioListeningApproved':False,'unresolved':unknowns,'baselineApproved':False,'replacementVersionsGenerated':False,'rejectedPseudoAssetsUsed':False,'humanFeedbackRawPreserved':True})
write('reports/03-pilot.json',{'stage':'03-pilot','unresolved':[x['finding'] for x in unknowns],'artifacts':[{'role':'editable-source','path':'source/pilot'},{'role':'comparison-video','path':'render/pilot/cg06-compare.mp4'},{'role':'comparison-video','path':'render/pilot/cg09-compare.mp4'},{'role':'pilot-review','path':'reviews/pilot-review.json'},{'role':'pilot-review-page','path':'render/pilot/index.html'}],'checks':[{'id':'actual-layer-composition','passed':True,'method':'independent-crop-assets-plus-text-vector-mask-composition-and-in-memory-parameter-tests','finding':'渲染器使用独立动态图层，重新排版文字、圆形遮罩、横线和圆环；改变文字、字体和人物窗位置确实改变像素。真实源工程与提取修补记录可查；不复用隔离的伪复刻。','evidence':['source/pilot/render_pilot.py','source/pilot/parameters.json','source/pilot/asset-provenance.json','reviews/pilot-layer-tests.json']},{'id':'encoded-playback-and-scrub','passed':True,'method':'ffprobe-count-frames+ffmpeg-full-decode+real-chrome-video-controls','finding':'两组候选66/67帧以及两条并排对照完整解码；浏览器四个视频均播放到结束，逐帧与拖动有效，无JS错误。仅证明媒体和控件可用。','evidence':['reviews/pilot-decodes.json','reviews/pilot-browser-qa.json','reviews/cg06-video-validation.json','reviews/cg09-video-validation.json']},{'id':'fidelity-gate','passed':False,'method':'source-frame-versus-rebuilt-frame-visual-comparison-and-unresolved-evidence-review','finding':'字体、亮条/发光过程、局部修补、圆环边缘及声音/交接听审未通过；禁止将候选记为合格baseline，禁止accept03或进入04。','evidence':['reviews/pilot-review.json','reviews/cg06-browser.png','reviews/cg09-browser.png']}],'notes':'按用户授权执行到03；01通过人类最终边界和机制验收，02通过可实施配方与显式未知范围；03已有真实分层候选但质量门禁未过，必须保持active并记录blocker。未生成换内容/字体视频，未占用07正式preview。','applied_lessons':['分层源码、原素材基准合格、用户认可三个状态分别记录。','不以HTTP200、抽帧、ASR、视频能播放或参数有变化替代复刻质量验收。']})
(P/'source/pilot/README.md').write_text('''# 代表组参考重建试验（未验收）

只处理男生视频 cg06（字幕组）与 cg09（画面组）。

运行：
```
python source/pilot/render_pilot.py --prepare --render
python source/pilot/pilot_server.py --port 8768
python source/pilot/check_pilot.py
```

先启动本地服务器再执行浏览器检查。现有8766拆解页不变。

`parameters.json` 是源工程参数。渲染器读取分离并修补的动态图层，不把成片参考作为最终播放器或合成输出。
`--prepare` 从参考抽取移动人物/案例素材并记录修补；不会使用rejected目录。
每个候选原内容与人物保持参考；当前使用系统宋体候选，原作者字体未识别。修补胸口/领口及被人物窗遮挡的案例像素属于近似。

本页是03试验复审页，不是07正式展示面板。不产生换内容或换字体版。
`reports/03-pilot.json` 和 `reviews/pilot-review.json` 列出尚未通过的质量项，不能将候选视为已认可baseline。
''','utf-8')
print(json.dumps({'pilotStatus':'needs-revision-not-accepted','candidates':2,'rawFeedbackUnchanged':True},ensure_ascii=False))
