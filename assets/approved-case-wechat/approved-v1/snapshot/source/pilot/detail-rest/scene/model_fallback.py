import urllib.request
from pathlib import Path
urls=[('selfie.tflite','https://storage.googleapis.com/mediapipe-assets/selfie_segmentation.tflite'),('rvm.onnx','https://ghfast.top/https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx')]
for name,url in urls:
 try:
  with urllib.request.urlopen(url,timeout=20) as r: data=r.read()
  Path('source/pilot/detail-rest/scene/models',name).write_bytes(data);print(name,len(data),flush=True)
 except Exception as e:print(name,type(e).__name__,e,flush=True)
