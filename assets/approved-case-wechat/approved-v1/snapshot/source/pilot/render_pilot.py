"""Actual layered reference reconstruction trials. Original font/assets are not claimed.

python source/pilot/render_pilot.py --prepare --render
The final compositor reads isolated, repaired moving assets, never a finished reference clip.
"""
from pathlib import Path
import argparse, json, subprocess, hashlib, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

P=Path(__file__).resolve().parents[2]
S=P/'source/pilot';A=S/'assets';OUT=P/'render/pilot'
W,H,FPS=286,508,30
FONT='C:/Windows/Fonts/Source Han Serif SC Heavy (TrueType).ttf'
def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf-8')
def read(p): return json.loads(p.read_text('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def original_frame(n):return Image.open(P/'observations/frame-audit/frames'/f'{n+1:04d}.jpg').convert('RGB')
def run(cmd):return subprocess.run(cmd,check=True,capture_output=True)
def clamp(x):return max(0,min(1,x))
def opacity(frame,a,b):return clamp((frame-a)/max(1,b-a))

def prepare():
    A.mkdir(parents=True,exist_ok=True)
    provenance=[]
    donor=np.array(original_frame(365))
    for n in range(300,366):
        a=np.array(original_frame(n));mask=np.zeros((H,W),np.uint8)
        # Remove the whole glow footprint, not just bright glyph cores.
        # A nearby text-free moving-source frame supplies the covered shirt. This is a repair.
        if n>300:
            cv2.rectangle(mask,(18,339),(182,380),255,-1)
        if n>=331:
            cv2.rectangle(mask,(65,353),(273,419),255,-1)
        rough=cv2.inpaint(a,mask,5,cv2.INPAINT_TELEA)
        flow=cv2.calcOpticalFlowFarneback(cv2.cvtColor(rough,cv2.COLOR_RGB2GRAY),cv2.cvtColor(donor,cv2.COLOR_RGB2GRAY),None,.5,3,25,3,5,1.2,0)
        yy,xx=np.mgrid[:H,:W].astype('float32')
        warped=cv2.remap(donor,xx+flow[:,:,0],yy+flow[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
        weight=cv2.GaussianBlur(mask,(9,9),2).astype(float)/255
        # Inside every original lettering region use only the text-free donor.
        weight=np.maximum(weight,mask/255.)
        clean=np.clip(a*(1-weight[:,:,None])+warped*weight[:,:,None],0,255).astype('uint8')
        d=A/'cg06/clean-presenter';d.mkdir(parents=True,exist_ok=True)
        Image.fromarray(clean).save(d/f'{n-300:04d}.png')
        if n in [300,312,338,360]:
            md=A/'cg06/repair-evidence';md.mkdir(parents=True,exist_ok=True)
            Image.fromarray(mask).save(md/f'mask-{n}.png')
        provenance.append({'frame':n,'asset':'cg06/clean-presenter','repair':'text/glow footprint removed; optical-flow aligned text-free source f365 supplies chest/collar; approximate underlying detail','pixelsRepaired':int((mask>0).sum())})
    for n in range(531,598):
        a=np.array(original_frame(n))
        broll=a[162:343].copy();mask=np.zeros(broll.shape[:2],np.uint8)
        cv2.circle(mask,(223,149-162),55,255,-1)
        clean=cv2.inpaint(broll,mask,5,cv2.INPAINT_TELEA)
        d=A/'cg09/broll';d.mkdir(parents=True,exist_ok=True)
        Image.fromarray(clean).save(d/f'{n-531:04d}.png')
        d=A/'cg09/presenter';d.mkdir(parents=True,exist_ok=True)
        # Source circle contains live presenter motion. Original white border is excluded.
        crop=Image.fromarray(a).crop((174,100,273,199)).convert('RGBA')
        m=Image.new('L',(99,99));ImageDraw.Draw(m).ellipse((1,1,97,97),fill=255)
        crop.putalpha(m);crop.save(d/f'{n-531:04d}.png')
        provenance.append({'frame':n,'asset':'cg09/broll+presenter','repair':'circle-overlap pixels in broll repaired; presenter extracted inside ring; mask/rules/background independently rebuilt'})
    src=Path(read(P/'project.json')['references'][0]['path'])
    for name,a,b in [('cg06',300,366),('cg09',531,598)]:
        run(['ffmpeg','-v','error','-y','-i',str(src),'-vn','-af',f'atrim=start={a/30}:end={b/30},asetpts=PTS-STARTPTS','-ar','44100','-ac','1',str(A/f'{name}-mix.wav')])
    # Visible static grid is extracted as its own background, with foreground removed.
    bg=np.array(original_frame(550));mask=np.zeros((H,W),np.uint8)
    cv2.rectangle(mask,(0,156),(285,349),255,-1);cv2.circle(mask,(223,149),56,255,-1)
    glyphmask=np.zeros((H,W),np.uint8)
    glyphmask[364:401,55:233]=(bg[364:401,55:233].min(2)>120).astype('uint8')*255
    glyphmask=cv2.dilate(glyphmask,np.ones((3,3),np.uint8))
    mask=np.maximum(mask,glyphmask)
    bg=cv2.inpaint(bg,mask,5,cv2.INPAINT_TELEA)
    Image.fromarray(bg).save(A/'cg09/background.png')
    write(S/'asset-provenance.json',{'source':str(src),'sourceSha256':sha(src),'status':'reference-derived visible moving regions; not original isolated media','frames':provenance,'repairsDisclosed':True,'rejectedAssetsUsed':False})
    write(S/'parameters.json',{'canvas':[W,H],'fps':FPS,'font':FONT,'fontIdentity':'system candidate, original unconfirmed','cg06':{'firstLine':'单纯埋头打工','secondLine':'只能维持生活','glyphEntryFrames':[310,308,306,304,302,301],'firstLineXY':[27,346],'firstFontSize':23,'secondLineXY':[77,366],'secondFontSize':30,'goldFromCharacter':2,'streakFrame':331,'settleFrame':342,'fadeStartFrame':360,'fadeEndFrame':365},'cg09':{'circleCenter':[223,149],'innerRadius':49,'ringRadius':53,'ringWidth':3,'brollXY':[0,162],'rulesY':[160,344],'rulesThickness':2,'captions':[{'text':'最后本金受损','entry':532,'settle':535,'exitStart':561,'end':565,'xy':[84,370]},{'text':'生活压力越来越大','entry':565,'settle':570,'exitStart':598,'end':598,'xy':[62,370]}]}})

def text_layer(text,size,fill='white',stroke=1,font_path=FONT):
    font=ImageFont.truetype(font_path,size*3)
    b=font.getbbox(text);w=math.ceil(font.getlength(text))+12
    im=Image.new('RGBA',(w,size*3+18));d=ImageDraw.Draw(im)
    d.text((6,3-b[1]),text,font=font,fill=fill,stroke_width=stroke,stroke_fill=fill)
    return im.resize((math.ceil(w/3),size+6),Image.Resampling.LANCZOS)

def paste(base,layer,xy,alpha=1):
    if alpha<=0:return
    if alpha<1:
        layer=layer.copy();layer.putalpha(layer.getchannel('A').point(lambda p:round(p*alpha)))
    base.alpha_composite(layer,(round(xy[0]),round(xy[1])))

def background():
    if (A/'cg09/background.png').exists():return Image.open(A/'cg09/background.png').convert('RGBA')
    yy,xx=np.mgrid[:H,:W];r=np.sqrt(((xx-143)/200)**2+((yy-240)/350)**2)
    val=np.clip(29-15*r,11,30)
    val+=((xx%8==0)|(yy%8==0))*2
    val+=((xx%48==0)|(yy%48==0))*1
    arr=np.repeat(np.clip(val,0,255).astype(np.uint8)[:,:,None],3,2)
    im=Image.fromarray(arr).convert('RGBA')
    ImageDraw.Draw(im).polygon([(9,500),(271,500),(277,505),(3,505)],fill=(24,45,53,255))
    return im

def render_frame(group,i,params,disable=None,base_override=None,clock_frame=None):
    disable=set(disable or [])
    if group=='cg06':
        f=i+300 if clock_frame is None else clock_frame;p=params['cg06'];base=base_override.copy().convert('RGBA') if base_override is not None else Image.open(A/f'cg06/clean-presenter/{i:04d}.png').convert('RGBA')
        from subtitle_motion import render as subtitle_render
        if 'text' not in disable:base.alpha_composite(subtitle_render(p,f,params['font']))
        return base if base_override is not None else base.convert('RGB')
    p=params['cg09'];f=i+531;base=background()
    if 'broll' not in disable:
        broll=Image.open(A/f'cg09/broll/{i:04d}.png').convert('RGBA');paste(base,broll,p['brollXY'])
    if 'rules' not in disable:
        d=ImageDraw.Draw(base)
        for y in p['rulesY']:d.rectangle((0,y,W,y+p['rulesThickness']-1),fill='white')
    if 'presenter' not in disable:
        cx,cy=p['circleCenter'];r=p['ringRadius']-1;ImageDraw.Draw(base).ellipse((cx-r,cy-r,cx+r,cy+r),fill='white')
        presenter=Image.open(A/f'cg09/presenter/{i:04d}.png');paste(base,presenter,(cx-49,cy-49))
    if 'caption' not in disable:
        for caption in p['captions']:
            a=opacity(f,caption['entry']-1,caption['settle'])
            if caption['end']>caption['exitStart']:a*=1-opacity(f,caption['exitStart'],caption['end'])
            glyph=text_layer(caption['text'],18,font_path=params['font'])
            paste(base,glyph,caption['xy'],a)
    return base.convert('RGB')

def encode(group,params):
    total=66 if group=='cg06' else 67
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/f'{group}-candidate.mp4'
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','pipe:0','-i',str(A/f'{group}-mix.wav'),'-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart',str(path)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    for i in range(total):proc.stdin.write(render_frame(group,i,params).tobytes())
    proc.stdin.close();error=proc.stderr.read();rc=proc.wait()
    if rc:raise RuntimeError(error.decode(errors='replace'))
    ref=P/f'observations/accepted-review/{group}/reference-clip.mp4'
    compare=OUT/f'{group}-compare.mp4'
    run(['ffmpeg','-v','error','-y','-i',str(ref),'-i',str(path),'-filter_complex','[0:v][1:v]hstack=inputs=2[v]','-map','[v]','-map','0:a','-c:v','libx264','-crf','18','-preset','fast','-c:a','aac','-shortest','-movflags','+faststart',str(compare)])
    # A true ablation demonstrates parameters alter independently rebuilt components.
    n=38 if group=='cg06' else 22
    full=np.array(render_frame(group,n,params));hidden=np.array(render_frame(group,n,params,['text'] if group=='cg06' else ['rules','presenter']))
    Image.fromarray(full).save(OUT/f'{group}-candidate-frame.png')
    Image.fromarray(hidden).save(OUT/f'{group}-layers-disabled.png')
    refim=original_frame(n+(300 if group=='cg06' else 531))
    sheet=Image.new('RGB',(W*3,H+25),'#161616');d=ImageDraw.Draw(sheet)
    for j,(im,title) in enumerate([(refim,'reference'),(Image.fromarray(full),'layered candidate'),(Image.fromarray(hidden),'component disabled')]):
        sheet.paste(im,(j*W,25));d.text((j*W+8,5),title,fill='white')
    sheet.save(OUT/f'{group}-comparison.png')
    return {'id':group,'frames':total,'candidate':path.relative_to(P).as_posix(),'comparison':compare.relative_to(P).as_posix(),'sha256':sha(path),'ablationChangedPixels':int(np.any(full!=hidden,2).sum()),'referenceReplayUsedByCompositor':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--render',action='store_true');args=ap.parse_args()
    assert read(P/'.pipeline/state.json')['stages'][3]['status']=='active','03 must be active before any reconstruction output'
    if args.prepare:prepare()
    if args.render:
        params=read(S/'parameters.json');rows=[encode(group,params) for group in ['cg06','cg09']]
        write(OUT/'manifest.json',{'status':'layered-pilot-candidates-not-accepted','groups':rows,'limitations':['original font unconfirmed; system Songti candidate','source chest/circle-overlap repairs are approximate','procedural dark grid approximates reference','audio mixed source retained; no listening approval'],'source':'source/pilot/render_pilot.py','parameterFile':'source/pilot/parameters.json'})
        print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
