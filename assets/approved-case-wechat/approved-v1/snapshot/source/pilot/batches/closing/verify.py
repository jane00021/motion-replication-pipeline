from pathlib import Path
import sys,json,subprocess,copy
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from components.common import *
from components import closing_batch as b
from components.runtime import validate_recipe,compose
from components.pairing import check
S=P/'source/pilot/batches/closing';R=P/'reviews/batches/closing';O=P/'render/pilot/batches/closing'
def raw_at(start):
 path=load(P/'source/pilot/new-input/manifest.json')['path'];r=subprocess.run(['ffmpeg','-v','error','-ss',str(start),'-i',path,'-frames:v','1','-vf','scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True);return Image.frombytes('RGB',(286,508),r.stdout).convert('RGBA')
rows=[]
for id in ['cg06','cg17','cg18','cg19']:
 c=load(S/(id+'-input.json'));recipe=load(S/(id+'-recipe.json'))
 # Parent owns runtime changes, current recipe is rebound after finalized source snapshot.
 for ref in recipe['components'].values():ref['sha256']=core.file_sha(P/ref['source'])
 recipe['runtimeSha256']=core.file_sha(P/'source/pilot/components/runtime.py');core.dump(S/(id+'-recipe.json'),recipe)
 validate_recipe(recipe);check(recipe,c,P);raw=raw_at(c['rawRange'][0]);n=min(c['frameCount']-1,30);im=compose(recipe,raw,n,c);im.save(R/(id+'-recipe-frame.png'))
 layer=b.render_subtitle(c['subtitleFamily'],n,c);disabled=b.render_subtitle(c['subtitleFamily'],n,c,['text']);assert not disabled
 if id!='cg06':
  revised=copy.deepcopy(c)
  if id=='cg17':revised['subtitle']['rows'][0]['text']='本领'
  elif id=='cg18':revised['subtitle']['phrases'][0]['text']='需踏实'
  else:revised['subtitle']['phrases']['first']['text']='选对方式'
  edit=b.render_subtitle(c['subtitleFamily'],n,revised);assert any(np.any(np.array(edit[k])!=np.array(layer[k])) for k in layer)
 rows.append({'occurrence':id,'runtimeValidation':True,'pairingStructuralCheck':True,'textDisabledTransparent':True,'textEditablePixelIntervention':id!='cg06','separateComponentsRecomposed':True})
manifest=load(O/'manifest.json');boards=[]
for row in manifest['groups']:
 id=row['occurrence'];count=row['frameCount'];f=P/row['file'];samples=[0,3,min(8,count-1),min(12,count-1),count//2,count-7,count-1]
 board=Image.new('RGB',(286*7,540*2));d=ImageDraw.Draw(board)
 for i,n in enumerate(samples):
  # Actual encoded output, phase-mapped source evidence is marked separately.
  r=subprocess.run(['ffmpeg','-v','error','-ss',str(n/30),'-i',str(f),'-frames:v','1','-vf','scale=286:508','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True);im=Image.frombytes('RGB',(286,508),r.stdout);board.paste(im,(i*286,540));d.text((i*286+3,1050),f'encoded local f{n}',fill='white')
  ref0,ref1=load(S/(id+'-input.json'))['sourceFrames'];source=round(ref0+(ref1-ref0-1)*n/max(1,count-1));ref=Image.open(P/f'observations/frame-audit/frames/{source+1:04d}.jpg');board.paste(ref,(i*286,0));d.text((i*286+3,510),f'source f{source}; normalized duration',fill='white')
 board.save(R/(id+'-encoded-phase-comparison.jpg'));boards.append(str(R/(id+'-encoded-phase-comparison.jpg')))
core.dump(R/'component-verification.json',{'checks':rows,'method':'real runtime composition, independent subtitle intervention, output decode phase evidence','stageAccepted':False,'continuousVisualPlayback':False,'audioListening':False})
# Static original-word candidate calibration is intentionally evidence, not the main review gallery.
canvas=Image.new('RGB',(286*4,540*2),'#30363b');d=ImageDraw.Draw(canvas)
for i,(id,fn,n) in enumerate([('cg17',1119,16),('cg18',1152,17),('cg19',1210,42),('cg06',350,50)]):
 c=load(S/(id+'-input.json'));raw=Image.new('RGBA',(286,508),'#30363b')
 if id=='cg17':c['subtitle']['rows'][0]['text']='认知';c['subtitle']['rows'][1]['text']='筛选'
 elif id=='cg18':c['subtitle']['phrases'][0]['text']='不跟风';c['subtitle']['phrases'][1]['text']='不浮躁';n=33
 elif id=='cg19':c['subtitle']['phrases']=c['subtitle']['sameWord']['phrases']
 else:c['subtitle']['parameterPath']='source/pilot/t04/input-same.json'
 for layer in b.render_subtitle(c['subtitleFamily'],n,c).values():raw.alpha_composite(layer)
 canvas.paste(Image.open(P/f'observations/frame-audit/frames/{fn+1:04d}.jpg'),(i*286,0));canvas.paste(raw.convert('RGB'),(i*286,540));d.text((i*286+3,510),id+' source original words',fill='white');d.text((i*286+3,1050),'candidate editable glyphs; no source pixels',fill='white')
canvas.save(R/'same-word-static-candidates.jpg')
print(json.dumps({'verified':4,'encodedBoards':boards},ensure_ascii=False))
