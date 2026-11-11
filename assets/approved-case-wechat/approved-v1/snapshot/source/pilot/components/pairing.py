"""Current two draft recipes only; rules reject unsupported combinations instead of guessing."""
from pathlib import Path
import json
def check(recipe,inputs,root):
 ids={k:v['id'] for k,v in recipe['components'].items()};clock=inputs.get('clock',{})
 if ids=={'visual':'v01','subtitle':'t01'}:
  if not Path(root/inputs['asset']).is_file():raise ValueError('work-context image missing')
  if inputs.get('importantEdgeEvidence',False):raise ValueError('vignette conflicts with critical edge evidence')
  if not clock['firstText'][0]<clock['questionAndResult'][0]<clock['allExit'][0]:raise ValueError('setup/takeover/read/exit order invalid')
  if clock['questionAndResult'][1]+10>clock['allExit'][0]:raise ValueError('insufficient reading hold')
 elif ids=={'visual':'v02','subtitle':'t02'}:
  order=recipe['layerOrder']
  if not order.index('subtitle.behindTitle')<order.index('visual.presenterForeground')<order.index('visual.symbols'):raise ValueError('background title/presenter/foreground motif order invalid')
  if not clock['symbolFirst']<clock['titleStart']<clock['titleSettle']<clock['titleHoldEnd']:raise ValueError('motif/title handoff invalid')
  if not clock['titleSettle']+10<=clock['titleHoldEnd']:raise ValueError('title reading hold too short')
  sym=inputs['symbol']
  if not Path(root/sym['assetPath']).is_file():raise ValueError('semantic symbol input missing')
  if not 1<=sym['count']<=18:raise ValueError('symbol density exceeds currently tested range')
  if max(sym.get('sizeRange',[24,65]))>70:raise ValueError('new size needs occlusion revalidation')
  if not inputs.get('semanticRoles',{}).get('conclusion'):raise ValueError('new semantic conclusion not assigned')
  t=inputs['title']
  if t['inkX']<0 or t['inkX']+t['inkWidth']>286 or t['inkHeight']>100:raise ValueError('title spatial envelope exceeded')
 else:
  # Observed catalogue pairings are authorized 03 trials, never approved reusable combinations.
  allowed={'cg04':('v03','t03'),'cg06':(None,'t04'),'cg07':('v05','t05'),
   'cg08':('v06','t06'),'cg09':('v07',None),'cg10':('v04','t08'),
   'cg11':('v04','t09'),'cg12':('v04','t10'),'cg13':('v04','t09'),
   'cg14':('v04','t11'),'cg15':('v04','t12'),'cg16':('v04','t09'),
   'cg17':('v08','t13'),'cg18':('v09','t14'),'cg19':(None,'t15')}
  occurrence=recipe.get('occurrence')
  actual=(ids.get('visual'),ids.get('subtitle'))
  if occurrence not in allowed or actual!=allowed[occurrence]:raise ValueError('Pairing not in frozen observed catalogue')
  if recipe.get('completeGroupValidated',False):raise ValueError('Batch trial cannot claim complete-group approval')
  if recipe.get('verificationState','trial') not in ('trial','trial-not-approved','user-approved-scoped-media','pending','source-draft'):
   raise ValueError('Trial verification state requires explicit review')
  if not recipe.get('layerOrder'):raise ValueError('Missing complete layer composition')
  if len(recipe['layerOrder'])!=len(set(recipe['layerOrder'])):raise ValueError('Duplicate composition slots')
  # Do not infer readability, semantics or safe occlusion from this structural check.

 return True
