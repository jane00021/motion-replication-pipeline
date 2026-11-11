import json,hashlib
from pathlib import Path
P=Path.cwd();S=P/'source/pilot/batches/scene'
for id in ['cg04','cg07','cg08','cg09']:
 p=S/(id+'-recipe.json');r=json.loads(p.read_text('utf-8'));ip=S/(id+'-input.json');c=json.loads(ip.read_text('utf-8'))
 deps={str(ip.relative_to(P)).replace('\\','/'):ip,**{v:P/v for v in c['assets'].values()},**{role['path']:Path(role['path']) for role in c['fontRoles'].values()}}
 r['supportBindings'].update({k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in deps.items()});p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
