import sys,json
from pathlib import Path
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'))
from components.detail_tools import *
fonts=load(P/'source/pilot/detail-two/fonts.json');R=P/'reviews/detail-two';R.mkdir(exist_ok=True)
rows=[('context','经济环境',(22,64,136,96),'0238.jpg'),('statement','彻底改变',(19,105,158,152),'0238.jpg'),('conclusion','永远优先',(59,316,225,358),'0853.jpg')]
sheet=Image.new('RGB',(900,780),'#303943');d=ImageDraw.Draw(sheet);f=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
for i,(role,words,bb,frame) in enumerate(rows):
 ref=Image.open(P/'observations/frame-audit/frames'/frame).crop(bb);sheet.paste(ref.resize((ref.width*2,ref.height*2)),(10,i*255+25));d.text((10,i*255+3),'原片 '+words,font=f,fill='white')
 for j,key in enumerate(['serif-heavy','serif-bold','yansong','sans-bold','youshe']):
  s={'path':fonts[key],'size':40,'inkWidth':bb[2]-bb[0]-8,'inkHeight':bb[3]-bb[1]-7,'outlinePx':1.3 if role=='statement' else 0}
  im,meta=glyph_tile(words,json.dumps(s,sort_keys=True));x=285+j%3*205;y=i*255+20+j//3*100
  d.text((x,y),key,font=f,fill='white');sheet.paste(im.convert('RGB').resize((im.width*1,im.height*1)),(x,y+25))
sheet.save(R/'same-word-font-candidates.jpg')
