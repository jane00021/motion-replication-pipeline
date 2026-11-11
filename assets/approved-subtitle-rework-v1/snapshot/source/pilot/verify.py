from pathlib import Path
import sys,json,copy,subprocess
from PIL import Image,ImageDraw,ImageFont
import numpy as np
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'));import components as e
S=P/'source/pilot';R=P/'reviews/pilot';O=P/'render/pilot'
def load(p):return json.loads(Path(p).read_text('utf-8'))
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),'utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',12);checks=[]
for oid,start,end in [('N01',0,52),('N02',54,111)]:
 c=load(S/f'{oid}-input.json');r=load(S/f'{oid}-recipe.json');N=c['frames'];data=subprocess.check_output(['ffmpeg','-v','error','-i',str(O/(oid+'-applied.mp4')),'-vf','scale=284:504','-f','rawvideo','-pix_fmt','rgb24','pipe:1']);frames=np.frombuffer(data,np.uint8).reshape(-1,504,284,3);assert len(frames)==N
 # Source same-word clock uses measured original frame events, neutral backdrop kept out of subtitle.
 same=copy.deepcopy(c);same['frames']=end-start
 if oid=='N01':same['subtitle'].update(prefix='你是不是也听说过',emphasis='这句话',bodyIn=4,emphasisIn=[32,39]);same['subtitle']['bodyStyle']['size']=16;same['subtitle']['focusStyle']['size']=21
 else:same['subtitle'].update(cues=[{'in':4,'out':57,'white':'每天','gold':'必须睡满'}],title='8小时',titleClock=[35,40,44]);same['subtitle']['titleStyle'].update(inkWidth=250,inkHeight=86,skew=-.18)
 dump(S/f'{oid}-same-word.json',same)
 enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-s','284x504','-pix_fmt','rgb24','-r','30','-i','pipe:0','-an','-c:v','libx264','-threads','2','-crf','15','-pix_fmt','yuv420p',str(O/(oid+'-same-word.mp4'))],stdin=subprocess.PIPE)
 for n in range(same['frames']):
  out=Image.new('RGBA',(284,504),'#34404b')
  for layer in e.subtitle(r['subtitleFamily'],n,same).values():out.alpha_composite(layer)
  enc.stdin.write(out.convert('RGB').tobytes())
 enc.stdin.close();assert enc.wait()==0
 board=Image.new('RGB',(6*288,1065),'#18232e');d=ImageDraw.Draw(board)
 for j,n in enumerate(np.linspace(0,N-1,6,dtype=int)):
  sf=start+round(n/(N-1)*(end-start-1));ref=Image.open(P/'observations/frame-audit/frames'/f'{sf+1:05d}.jpg');board.paste(ref,(j*288,25));board.paste(Image.fromarray(frames[n]),(j*288,551));d.text((j*288+2,3),f'原f{sf}／新f{n} 阶段对照',font=font,fill='white')
 board.save(R/f'{oid}-encoded-comparison.jpg')
 raw=Image.new('RGBA',(284,504),'#385064');n=round(N*.8);out=e.compose(r,raw,n,c);parts={**{'visual.'+k:v for k,v in e.visual(r['visualFamily'],raw,n,c).items()},**{'subtitle.'+k:v for k,v in e.subtitle(r['subtitleFamily'],n,c).items()}};re=Image.new('RGBA',(284,504))
 for k in r['layerOrder']:
  if k in parts:re.alpha_composite(parts[k])
 assert np.array_equal(np.array(out),np.array(re))
 changed=copy.deepcopy(c)
 if oid=='N01':changed['subtitle']['emphasis']='测试重点'
 else:changed['subtitle']['title']='测试字'
 px=int(np.any(np.array(out)!=np.array(e.compose(r,raw,n,changed)),2).sum());assert px>0
 difference=['原字体身份未确认；宋体字形及重点词泛光曲线仍为近似','新口播按语义重定时，参考和新片不是相同台词/时长','未人工听审，不推导原音效与词点通过'] if oid=='N01' else ['背字字体/材质/斜度仍是候选，未声称原字形一致','RVM前景发丝和手指局部柔边仍需用户视觉检验','新片天花板为新语义；字幕词点、独立音效未听审']
 checks.append({'occurrence':oid,'frames':N,'fullDecode':True,'layerRecompositionExact':True,'textEditPixels':px,'sameWordOutput':'render/pilot/'+oid+'-same-word.mp4','sameWordScope':'text mechanisms on neutral backdrop, not original-material complete baseline','remainingLargestThree':difference,'userApproved':False})
# Side-by-side same-word glyph comparison, natural text ratio and visible material.
board=Image.new('RGB',(900,450),'#25323c');d=ImageDraw.Draw(board)
for j,(oid,sf) in enumerate([('N01',45),('N02',100)]):
 ref=Image.open(P/'observations/frame-audit/frames'/f'{sf+1:05d}.jpg');same=load(S/f'{oid}-same-word.json');out=Image.new('RGBA',(284,504),'#34404b')
 for tile in e.subtitle('T01' if oid=='N01' else 'T02',sf if oid=='N01' else sf-54,same).values():out.alpha_composite(tile)
 ref=ref.crop((0,45 if oid=='N02' else 310,284,160 if oid=='N02' else 360));candidate=out.crop((0,45 if oid=='N02' else 310,284,160 if oid=='N02' else 360));board.paste(ref,(5,j*210+30));board.paste(candidate.convert('RGB'),(330,j*210+30));d.text((5,j*210+5),oid+' 原片同字／候选字形与材质',font=font,fill='white')
board.save(R/'same-word-static.jpg');dump(R/'verification.json',{'groups':checks,'perceptualAudioApproval':False,'stageAccepted':False,'scope':'only first2; all other groups untouched'})
print('same-word, encoded comparisons and editable layers verified')
