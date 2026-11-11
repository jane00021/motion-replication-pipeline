import sys,json
from pathlib import Path
P=Path.cwd();sys.path.insert(0,str(P/'source/pilot'))
from components.scene_batch import *
from PIL import ImageDraw
R=P/'reviews/batches/scene'
items=[('cg04',237,(10,35,156,170),'经济环境'),('cg07',429,(16,192,270,245),'很多人习惯'),('cg08',513,(26,75,260,135),'透支负债前行')]
fonts=[FONT,'C:/Windows/Fonts/simsun.ttc','C:/Windows/Fonts/Noto Sans SC Bold (TrueType).otf']
sheet=Image.new('RGB',(1100,360),'#23282c');d=ImageDraw.Draw(sheet)
for row,(id,f,box,word) in enumerate(items):
 im=Image.open(P/f'observations/frame-audit/frames/{f+1:04d}.jpg').crop(box);im.thumbnail((270,100));sheet.paste(im,(0,row*120+18));d.text((4,row*120+2),f'{id} source f{f}',fill='white')
 for j,font in enumerate(fonts):
  tile,m=text_tile(word,30,font=font);sheet.paste(tile,(285+j*270,row*120+36),tile);d.text((285+j*270,row*120+2),['Source Han Serif Heavy','SimSun','Noto Sans Bold'][j],fill='white')
sheet.save(R/'same-word-font-candidates.jpg')
