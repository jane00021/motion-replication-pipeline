from pathlib import Path
import json,subprocess,hashlib,wave
import numpy as np
from faster_whisper import WhisperModel
P=Path(__file__).resolve().parents[2]
src=Path('C:/Users/Administrator/文档/xwechat_files/wxid_rfsxn410awad12_0c48/msg/video/2026-11/aebcf42c0e2e7155065def1be4bc39b7.mp4')
out=P/'source/pilot/new-input';out.mkdir(exist_ok=True)
probe=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(src)],capture_output=True,check=True).stdout)
(out/'manifest.json').write_text(json.dumps({'path':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'role':'user-authorized-unedited-migration-input','probe':probe},ensure_ascii=False,indent=2),'utf-8')
wav=out/'speech.wav';subprocess.run(['ffmpeg','-v','error','-y','-i',str(src),'-vn','-ac','1','-ar','16000',str(wav)],check=True)
with wave.open(str(wav),'rb') as f:audio=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
m=WhisperModel('base',device='cpu',compute_type='int8',cpu_threads=2,local_files_only=True)
segments,info=m.transcribe(audio,language='zh',word_timestamps=True,beam_size=3,vad_filter=False)
rows=[]
for s in segments:
    row={'start':s.start,'end':s.end,'text':s.text,'words':[{'text':w.word,'start':w.start,'end':w.end} for w in s.words or []]};rows.append(row);print(s.start,s.end,s.text,flush=True)
(out/'asr.json').write_text(json.dumps({'method':'local ASR hypothesis, not listening approval','segments':rows},ensure_ascii=False,indent=2),'utf-8')
