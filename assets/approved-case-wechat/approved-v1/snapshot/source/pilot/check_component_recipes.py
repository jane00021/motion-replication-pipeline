"""Execution evidence for independent entries and shared implementation, not visual acceptance."""
from pathlib import Path
import json,copy,subprocess,hashlib
import numpy as np
from PIL import Image
from components import visual,subtitle,common
from components.runtime import compose,layers,validate_recipe,REGISTRY
import complete_groups as g
P=g.P;S=g.S;R=P/'reviews/complete01-02/component-proof';R.mkdir(exist_ok=True)
def run(args):return subprocess.run(args,capture_output=True,check=True,text=True,encoding='utf-8')
def main():
 records=[]
 for i,n in [('01',130),('02',70)]:
  recipe=g.load(S/f'recipes/{i}.json');c=g.load(P/recipe['input']);assert validate_recipe(recipe)
  rawPath=R/f'raw-{i}.png'
  subprocess.run(['ffmpeg','-v','error','-y','-ss',str(c['rawStart']+n/30),'-i',g.media.SRC,'-frames:v','1','-vf','scale=286:508',str(rawPath)],check=True)
  im=Image.open(rawPath).convert('RGB')
  base=['python','-X','utf8',str(P/'source/pilot/component_entry.py')]
  calls=[]
  for kind in ['visual','subtitle','recipe']:
   cmd=base+['--kind',kind,'--input',str(S/f'recipes/{i}.json' if kind=='recipe' else P/recipe['input']),'--frame',str(n),'--output',str(R/i/kind)]
   if kind!='recipe':cmd+=['--id',recipe['components'][kind]['id']]
   if kind!='subtitle':cmd+=['--raw-frame',str(rawPath)]
   out=run(cmd);calls.append(json.loads(out.stdout))
  # Recombine independently rendered files strictly by recipe layer order.
  combined=Image.new('RGBA',(286,508))
  for name in recipe['layerOrder']:
   kind,slot=name.split('.');path=R/i/kind/(slot+'.png')
   if path.exists():combined.alpha_composite(Image.open(path).convert('RGBA'))
  cli=Image.open(R/i/'recipe/complete.png');assert np.array_equal(np.array(cli),np.array(combined))
  direct=compose(recipe,im,n,c);assert np.array_equal(np.array(cli),np.array(direct))
  # Real edit: mutate content and shadow source once, without creating alternate implementations.
  edited=copy.deepcopy(c);key='result' if i=='01' else 'title';edited['text'][key]='检验改字';different=int(np.any(np.array(compose(recipe,im,n,edited))!=np.array(direct),2).sum());assert different>0
  tamper=copy.deepcopy(recipe);tamper['components']['subtitle']['sha256']='0'*64
  try:validate_recipe(tamper);raise AssertionError('stale dependency accepted')
  except ValueError:pass
  records.append({'id':i,'componentCli':calls,'cliLayersRecomposeExactly':True,'sameCallable':REGISTRY[recipe['components']['subtitle']['entrypoint']] is subtitle.render,'changedTextPixels':different,'staleSourceRejected':True})
 # Shared shadow source affects BOTH subtitle components; no copied material per recipe.
 original=common.load;style=g.load(S/'shared-text-style.json')
 def altered(path):
  if Path(path).name=='shared-text-style.json':
   d=copy.deepcopy(style);d['shadow']['dx']=4;d['shadow']['dy']=5;d['shadow']['opacity']=1;return d
  return original(path)
 shadow=[]
 for id,i,n,slot in [('t01','01',130,'questionText'),('t02','02',70,'speechCaption')]:
  c=g.load(S/f'input-{i}.json');before=subtitle.render(id,n,c)[slot];common.load=altered
  try:after=subtitle.render(id,n,c)[slot]
  finally:common.load=original
  diff=int(np.any(np.array(before)!=np.array(after),2).sum());assert diff>0;shadow.append({'component':id,'oneSharedStyleChangePixels':diff})
 # Reusable bounds are explicit about current local geometry and unknown semantic/audio facts.
 contracts={'status':'03-pilot-source-and-recipe-draft','canvas':[286,508],'fps':30,'sourceRoot':'source/pilot/components','entryCLI':'python source/pilot/component_entry.py --kind visual|subtitle|recipe --input <json> --frame <n> [--id <id>] [--raw-frame <png>] --output <folder>','components':[
 {'id':'v01','entrypoint':'components.visual:render','responsibility':'attention focus and work-context image','inputs':['new raw frame','image asset path','clock.vignetteIn/photoIn/allExit','photoBrightness'],'outputSlots':['presenter','focus','workPhoto'],'occupiedSpace':'focus whole canvas; image y355..508 soft top45px','conflicts':['important chart at image/boundary','presenter outside fixed focus'],'tested':'current input only'},
 {'id':'t01','entrypoint':'components.subtitle:render','responsibility':'setup lines -> result-question takeover -> shared exit','inputs':['text first/second/question/result','semanticRoles','textLayout size/xy/fill','shared-text-style.json','clock.firstText/secondText/questionAndResult/allExit'],'outputSlots':['questionText'],'occupiedSpace':'lower 305..395 native px; actual glyph changes require bounds check','conflicts':['photo detail or face at same area','too long result obscures setup'],'tested':'current short text'},
 {'id':'v02','entrypoint':'components.visual:render','responsibility':'presenter geometry, foreground separation, batch symbol motion','inputs':['new raw frame','presenterReframe scale/cropXY','symbol.assetPath/count/seed/sizeRange/speedRange/spinRange/nearBlur/farBlur','clock.symbolFirst/symbolSpawnEnd/symbolExitEnd/titleStart'],'outputSlots':['presenter','presenterForeground','symbols'],'occupiedSpace':'symbols traverse full canvas; fixed head seeds around143,153','conflicts':['off-center new head','no valid matte','dense/large motifs obscure reading or face'],'tested':'gray-shirt input; seeded matte approximate'},
 {'id':'t02','entrypoint':'components.subtitle:render','responsibility':'speech progression -> oversized background conclusion','inputs':['text first/second/title','semanticRoles','title font/inkWidth/inkHeight/inkX/inkY','captionSize','shared-text-style.json','clock.captionChange/titleStart/titleOvershoot/titleSettle'],'outputSlots':['behindTitle','speechCaption'],'occupiedSpace':'title ink x6..280,y11..89; speech y374','conflicts':['missing foreground alpha','too long caption','unfitting risk/wealth metaphor'],'tested':'current four-character title'}],
 'pairingRules':[{'if':'recipe01','requires':['setup before question takeover','shared exit of v01/t01','image semantic purpose matches labor'],'adjust':['focus ellipse for subject','photo size/brightness','textLayout for actual ink'],'why':'work context supports inquiry; emphasis takes over rather than competing'}, {'if':'recipe02','requires':['background title before presenterForeground in layerOrder','symbols in foreground','title onset after motif setup','symbol asset meaning matches conclusion'],'adjust':['density/size after icon change','input head matte seeds','title ink bounds for actual typeface'],'why':'motif introduces temptation/risk; giant title organizes conclusion and presenter stays readable'}],
 'acceptanceBoundary':'No official04 library, no new pairing this turn. Component test pass does not assert full expression fidelity or audio correctness. New combinations wait until these complete groups are inspected and04 activated.'}
 g.core.dump(P/'contracts/component-recipe-draft.json',contracts)
 architecture=g.load(P/'contracts/composition-architecture.json');architecture['status']='03-real-entries-and-reference-recipes-draft';architecture['notes']='real components and recipes exist; quality and official04 pending';
 for kind,ids in [('visualLibrary',['v01','v02']),('subtitleLibrary',['t01','t02'])]:
  architecture[kind]['status']='pilot-source-draft'
  for item,id in zip(architecture[kind]['components'],ids):item.update(entrypoint='components.'+('visual' if kind=='visualLibrary' else 'subtitle')+':render',validated=False,implementationTest='reviews/complete01-02/component-proof/verification.json')
 for recipe in architecture['recipes']:
  i='01' if recipe['sourceOccurrence']=='cg01' else '02';recipe['recipeFile']=f'source/pilot/complete01-02/recipes/{i}.json';recipe['independentLibraryEntryImplemented']=True;recipe['status']='trial-not-approved'
 g.core.dump(P/'contracts/composition-architecture.json',architecture)
 g.core.dump(R/'verification.json',{'groups':records,'sharedShadowStyle':shadow,'formalLibraryAccepted':False,'newCombinationAttempted':False,'sources':{str(f.relative_to(P)):g.core.file_sha(f) for f in [P/'source/pilot/components/visual.py',P/'source/pilot/components/subtitle.py',P/'source/pilot/components/common.py',P/'source/pilot/components/runtime.py',S/'shared-text-style.json']}})
 print(json.dumps({'groups':2,'independentCLI':True,'identicalLayerRecomposition':True,'sharedShadow':shadow,'officialLibraryAccepted':False}))
if __name__=='__main__':main()
