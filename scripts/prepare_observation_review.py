"""Install reference-only manual review UI without overwriting human feedback."""
import argparse,json,shutil,subprocess
from pathlib import Path
from fractions import Fraction

def prepare(project,assets):
    config=json.loads((project/'project.json').read_text('utf-8'))
    source=Path(config['references'][0]['path'])
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=avg_frame_rate,r_frame_rate,nb_frames,duration','-of','json',str(source)],text=True))['streams'][0]
    fps=float(Fraction(probe['r_frame_rate']))
    decoded=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(source)],text=True))['frames']
    times=[float(f['best_effort_timestamp_time']) for f in decoded]
    if not times or any(b<=a for a,b in zip(times,times[1:])):
        raise SystemExit('帧时间戳缺失或不严格递增，需要先检查源视频。')
    total=len(times)
    folder=project/'observations/decomposition-preview';folder.mkdir(parents=True,exist_ok=True)
    for name in ['index.html','review.js','review_server.py']:
        shutil.copyfile(assets/name,folder/name)
    shutil.copyfile(source,folder/'reference-source.mp4')
    # Original stays immutable; H.264 is only a browser playback copy.
    browser_source=folder/'reference-browser.mp4'
    if not browser_source.exists():
        subprocess.run(['ffmpeg','-v','error','-i',str(source),'-c:v','libx264','-crf','18','-preset','fast','-c:a','aac','-movflags','+faststart','-y',str(browser_source)],check=True)
    target=folder/'metadata.json' 
    metadata=json.loads(target.read_text('utf-8')) if target.exists() else {'title':'仅拆解，不是复刻','mode':'decomposition-only','completeGroups':[],'visualFamilies':[],'subtitleFamilies':[]}
    metadata.update(playbackSource='reference-browser.mp4',referenceSource='reference-source.mp4',fps=fps,totalFrames=total,projectKey=str(project),frameTimes=times+[float(probe['duration'])],timeBasis='decoded-frame-PTS')
    target.write_text(json.dumps(metadata,ensure_ascii=False,indent=2),'utf-8')
    return folder

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);a=p.parse_args()
    here=Path(__file__).resolve()
    assets=here.parent/'assets/decomposition-preview' if here.parent.name=='.pipeline' else here.parents[1]/'assets/decomposition-preview'
    folder=prepare(a.project.resolve(),assets)
    print(json.dumps({'page':str(folder/'index.html'),'server':str(folder/'review_server.py'),'note':'Fill metadata.completeGroups with observed candidates; no baseline/variant rendering.'}))
