import urllib.request
from pathlib import Path
u='https://huggingface.co/Xenova/modnet/resolve/main/onnx/model.onnx'
p=Path('source/pilot/detail-rest/scene/models/modnet.onnx')
try:
 with urllib.request.urlopen(u,timeout=25) as r,p.open('wb') as f:
  while True:
   data=r.read(1024*1024)
   if not data:break
   f.write(data)
 print(p.stat().st_size,flush=True)
except Exception as e:print(type(e).__name__,e,flush=True)
