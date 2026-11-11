"""Recipe runtime owns compositing, not the component implementations."""
import hashlib,json,importlib
from PIL import Image
from . import visual,subtitle
from .common import P,load
def passthrough(component_id,raw,frame,inputs,disabled=()):
 if component_id is not None:raise ValueError('Passthrough is not a visual family')
 return {'presenter':raw.convert('RGBA')}

REGISTRY={'components.visual:render':visual.render,'components.subtitle:render':subtitle.render,
 'components.runtime:passthrough':passthrough}
BATCH_MODULES=('scene_batch','circle_batch','closing_batch')

def resolve(entrypoint):
 if entrypoint not in REGISTRY:
  module,function=entrypoint.split(':',1)
  if module not in {'components.'+name for name in BATCH_MODULES} or function not in ('render','render_subtitle'):
   raise ValueError('Unknown entrypoint: '+entrypoint)
  REGISTRY[entrypoint]=getattr(importlib.import_module(module),function)
 return REGISTRY[entrypoint]

def component_source(kind,ref):
 expected='source/pilot/'+ref['entrypoint'].split(':')[0].replace('.','/')+'.py'
 supplied=ref.get('source',expected)
 if supplied.replace('\\','/')!=expected:raise ValueError('Source and entrypoint mismatch')
 return P/supplied

def validate_recipe(recipe):
 for kind,ref in recipe['components'].items():
  path=component_source(kind,ref)
  if hashlib.sha256(path.read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('Component source changed: rebind recipe and invalidate review')
 for path,field in [(P/'source/pilot/components/common.py','commonSha256'),(P/recipe['sharedStyle'],'sharedStyleSha256')]:
  if hashlib.sha256(path.read_bytes()).hexdigest()!=recipe[field]:raise ValueError('Common source/style changed: invalidate dependent recipe review')
 for ref in recipe['components'].values():
  resolve(ref['entrypoint'])
 for path,sha in recipe.get('supportBindings',{}).items():
  if hashlib.sha256((P/path).read_bytes()).hexdigest()!=sha:raise ValueError('Dependency changed: '+path)
 return True
def layers(recipe,raw,frame,parameters,disabled=()):
 result={}
 for kind,ref in recipe['components'].items():
  fun=resolve(ref['entrypoint'])
  output=fun(ref['id'],raw,frame,parameters,disabled) if kind=='visual' else fun(ref['id'],frame,parameters,disabled)
  result.update({kind+'.'+slot:tile for slot,tile in output.items()})
 return result
def compose(recipe,raw,frame,parameters,disabled=()):
 output=layers(recipe,raw,frame,parameters,disabled);unknown=set(output)-set(recipe['layerOrder'])
 if unknown:raise ValueError('Recipe forgot produced layers: '+str(unknown))
 canvas=Image.new('RGBA',(286,508))
 for name in recipe['layerOrder']:
  if name in output:canvas.alpha_composite(output[name])
 return canvas
