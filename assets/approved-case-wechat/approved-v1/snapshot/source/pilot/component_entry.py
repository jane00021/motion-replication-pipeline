"""Independently render/edit component inputs to RGBA layers, or compose by recipe."""
import argparse,json
from pathlib import Path
from PIL import Image
from components import visual,subtitle
from components.runtime import compose,validate_recipe,resolve
from components.common import P,load
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--kind',choices=['visual','subtitle','recipe'],required=True);ap.add_argument('--id');ap.add_argument('--entrypoint');ap.add_argument('--input',required=True);ap.add_argument('--raw-frame');ap.add_argument('--frame',type=int,required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
 out=Path(args.output);out.mkdir(exist_ok=True,parents=True);inputPath=Path(args.input);c=json.loads(inputPath.read_text('utf-8'))
 raw=Image.open(args.raw_frame).convert('RGBA').resize((286,508)) if args.raw_frame else None
 if args.kind=='recipe':
  validate_recipe(c)
  from components.pairing import check
  check(c,load(P/c['input']),P)
  if raw is None:raise ValueError('recipe requires raw-frame')
  outputs={'complete':compose(c,raw,args.frame,load(P/c['input']))}
 elif args.kind=='visual':
  if raw is None:raise ValueError('visual requires raw-frame')
  outputs=resolve(args.entrypoint or 'components.visual:render')(args.id,raw,args.frame,c)
 else:outputs=resolve(args.entrypoint or 'components.subtitle:render')(args.id,args.frame,c)
 for name,im in outputs.items():im.save(out/(name+'.png'))
 print(json.dumps({'kind':args.kind,'layers':list(outputs),'rgba':True}))
if __name__=='__main__':main()
