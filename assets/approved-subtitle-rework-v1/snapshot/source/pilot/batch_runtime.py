"""Shared deterministic pilot runtime: independent providers, source/input hashes, streaming encode."""
from pathlib import Path
import json,hashlib,importlib,subprocess,sys,copy,argparse
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[2];sys.path.insert(0,str(P/'source/pilot'))
W,H=284,504

def load(path):return json.loads(Path(path).read_text('utf-8-sig'))
def dump(path,obj):path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def absolute(path):path=Path(path);return path if path.is_absolute() else P/path

def bind(recipe,input_path):
 r=copy.deepcopy(recipe);r['input']=str(Path(input_path).resolve().relative_to(P)).replace('\\','/');r['inputSha256']=sha(input_path)
 for ref in r['components']:ref['sha256']=sha(absolute(ref['source']))
 r.setdefault('supportBindings',{})['source/pilot/batch_runtime.py']=sha(__file__)
 return r

def validate(recipe):
 if sha(absolute(recipe['input']))!=recipe['inputSha256']:raise ValueError('Input changed; bind and recheck')
 for ref in recipe['components']:
  if ref['kind'] not in ('visual','subtitle'):raise ValueError('Invalid component kind')
  if sha(absolute(ref['source']))!=ref['sha256']:raise ValueError('Component changed: '+ref['id'])
 for path,digest in recipe.get('supportBindings',{}).items():
  if sha(absolute(path))!=digest:raise ValueError('Support dependency changed: '+path)
 return True

def layers(recipe,raw,n,c):
 out={}
 for ref in recipe['components']:
  module,fn=ref['entrypoint'].split(':');fun=getattr(importlib.import_module(module),fn);params=c.get(ref['inputKey'],c) if ref.get('inputKey') else c
  result=fun(ref['id'],raw,n,params) if ref['kind']=='visual' else fun(ref['id'],n,params)
  prefix=ref.get('prefix',ref.get('slotPrefix',ref['kind']))
  for slot,im in result.items():
   key=prefix+'.'+slot
   if key in out:raise ValueError('Duplicate layer '+key+'; choose unique prefix')
   if im.mode!='RGBA' or im.size!=(W,H):raise ValueError('Expected native full-frame RGBA: '+key)
   out[key]=im
 if set(out)-set(recipe['layerOrder']):raise ValueError('Uncomposed produced slots '+str(set(out)-set(recipe['layerOrder'])))
 return out

def compose(recipe,raw,n,c):
 out=Image.new('RGBA',(W,H));ls=layers(recipe,raw,n,c)
 for key in recipe['layerOrder']:
  if key in ls:out.alpha_composite(ls[key])
 return out

def run_group(recipe,input_config=None,output=None,**kwargs):
 # Accept either file paths or dicts. Persist explicit input/recipe paths before calling.
 rp=Path(recipe) if isinstance(recipe,(str,Path)) else None;r=load(rp) if rp else recipe
 c=load(absolute(r['input'])) if input_config is None else load(input_config) if isinstance(input_config,(str,Path)) else input_config
 validate(r)
 state=load(P/'.pipeline/state.json');assert state['stages'][3]['status']=='active','03 must be active'
 N=int(c.get('frameCount',c.get('frames')));fps=int(c.get('fps',30));start=c.get('rawRange',[c.get('rawStart',0)])[0];source=c.get('rawSource',c.get('source'))
 if not source:source='C:/Users/Administrator/.codex/skills/motion-replication-pipeline/assets/migration-demo/talking-head-raw.mp4'
 source=absolute(source);output=absolute(output or c['output']);output.parent.mkdir(parents=True,exist_ok=True)
 dec=subprocess.Popen(['ffmpeg','-v','error','-threads','1','-ss',str(start),'-i',str(source),'-frames:v',str(N),'-vf',f'fps={fps},scale={W}:{H}','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
 enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-s',f'{W}x{H}','-pix_fmt','rgb24','-r',str(fps),'-i','pipe:0','-ss',str(start),'-i',str(source),'-t',str(N/fps),'-map','0:v','-map','1:a:0?','-vf',f'scale={W*2}:{H*2}:flags=lanczos','-c:v','libx264','-threads','2','-crf','16','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(output)],stdin=subprocess.PIPE)
 samples={0,min(6,N-1),N//4,N//2,N*3//4,N-1};proof=output.parent/(output.stem+'-proof');proof.mkdir(exist_ok=True);alpha_dir=output.parent/(output.stem+'-rgba');alpha_dir.mkdir(exist_ok=True);alphas=[]
 try:
  for n in range(N):
   data=dec.stdout.read(W*H*3)
   if len(data)!=W*H*3:raise RuntimeError('Raw frame missing '+str(n))
   raw=Image.frombytes('RGB',(W,H),data);ls=layers(r,raw,n,c);im=Image.new('RGBA',(W,H))
   for key in r['layerOrder']:
    if key in ls:im.alpha_composite(ls[key])
   enc.stdin.write(im.convert('RGB').tobytes())
   if n in samples:
    im.save(proof/f'{n:04d}.png')
    check=compose(r,raw,n,c);assert np.array_equal(np.asarray(im),np.asarray(check)),'Non-deterministic providers'
    for ref in r['components']:
     if ref['kind']=='subtitle':
      prefix=ref.get('prefix',ref.get('slotPrefix','subtitle'))
      for key,tile in ls.items():
       if key.startswith(prefix+'.'):tile.save(alpha_dir/f'{n:04d}-{key}.png');alphas.append({'frame':n,'slot':key,'alphaBBox':tile.getchannel('A').getbbox()})
 finally:
  enc.stdin.close()
 if enc.wait()!=0 or dec.wait()!=0:raise RuntimeError('Encode/decode failed')
 subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(output),'-f','null','-'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 info=load_json_probe(output);assert int(info['nb_read_frames'])==N
 source_conf=load(P/'project.json')['references'][0]['path'];oid=r['occurrence'];catalog=load(P/'observations/group-catalog.json');o=next(x for x in catalog['occurrences'] if x['id']==oid);refpath=output.parent/(oid+'-reference.mp4')
 subprocess.run(['ffmpeg','-v','error','-y','-i',source_conf,'-vf',f'trim=start_frame={o["startFrame"]}:end_frame={o["endFrame"]},setpts=PTS-STARTPTS','-an','-c:v','libx264','-threads','2','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(refpath)],check=True)
 record={'occurrence':oid,'name':o['name'],'file':str(output.relative_to(P)).replace('\\','/'),'referenceFile':str(refpath.relative_to(P)).replace('\\','/'),'recipe':str(rp.resolve().relative_to(P)).replace('\\','/') if rp else None,'input':r['input'],'frameCount':N,'rawRange':[start,start+N/fps],'sourceRange':[o['startFrame'],o['endFrame']],'visualFamily':o['visual'],'subtitleFamily':o['subtitle'],'visualComponents':o.get('visualComponents',[o['visual']] if o['visual'] else []),'subtitleComponents':o.get('subtitleComponents',[o['subtitle']] if o['subtitle'] else []),'sha256':sha(output),'verificationState':'trial-awaiting-user-review','limitations':c.get('limitations',['原字体身份、声音词点与完整视觉效果待复审']),'technical':{'fullDecode':True,'frames':N,'deterministicLayerRecomposition':True,'alphaSamples':alphas,'audioListeningApproved':False}}
 dump(output.with_suffix('.verification.json'),record);return record

def load_json_probe(path):return json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,width,height','-of','json',str(path)]))['streams'][0]

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--recipe',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();print(json.dumps(run_group(a.recipe,output=a.output),ensure_ascii=False))
