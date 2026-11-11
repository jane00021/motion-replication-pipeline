from pathlib import Path
p=Path('source/pilot/components/scene_batch.py');s=p.read_text('utf-8');start=s.index(" elif component_id=='v05':");end=s.index(" else:raise ValueError(component_id)",start)
s=s[:start]+''' elif component_id=='v05':
  layers['background']=grid();q=ease(prog(n,*t['presenterShrink']));win=c.get('presenterWindow',[65,37,156]);diam=round(286*(1-q)+win[2]*q);x=round(win[0]*q);y=round(win[1]*q)
  box=np.array([0,0,286,508])*(1-q)+np.array(c.get('presenterCrop',[31,76,255,300]))*q;tile=cover(raw.crop(tuple(box)),(diam,round(508*(1-q)+win[2]*q))).convert('RGBA');m=Image.new('L',tile.size);ImageDraw.Draw(m).rounded_rectangle((0,0,tile.width-1,tile.height-1),radius=round(q*diam/2),fill=255);tile.putalpha(m);p=canvas();p.alpha_composite(tile,(x,y));ImageDraw.Draw(p).rounded_rectangle((x,y,x+tile.width-1,y+tile.height-1),radius=round(q*diam/2),outline='#fffeeb',width=2 if q else 0);layers['presenter']=p
  for i,key in enumerate(['left','right']):
   a=prog(n,*t[key+'Card']);e=ease(a)
   if a>0:
    box=c.get('cardBoxes',[[5,244,133,170],[153,244,128,170]])[i];x,y,w,h=box;y+=(1-e)*90;card=canvas();d=ImageDraw.Draw(card);d.rounded_rectangle((x,y,x+w,y+h),radius=8,fill='#222b32',outline='#eee8cf',width=2)
    art=photo(assets[key]);bb=art.getbbox();art=art.crop(bb);art.thumbnail((round(w*.94),round(h*.65)),Image.Resampling.LANCZOS);card.alpha_composite(art,(round(x+(w-art.width)/2),round(y+h-art.height-13)));layers[key+'Card']=core.opacity(card,a)
 elif component_id=='v06':
  layers['background']=rain(n)
  if 'presenter' not in disabled:
   if c.get('matteFrames'):
    person=Image.open(P/c['matteFrames']/f'{n:04d}.png').convert('RGBA')
   else:person=matte(raw)
   bounds=c.get('presenterBox',[-3,271,139,247]);person=person.resize(tuple(bounds[2:]),Image.Resampling.LANCZOS);p=canvas();p.alpha_composite(person,tuple(bounds[:2]));layers['presenter']=p
  box=c.get('topPanelBox',[17,40,252,136]);layers['topPanel']=vector_panel(assets['top'],box)
  a=prog(n,*t['secondPanel']);scale=1+.18*math.sin(a*math.pi)*math.exp(-a*1.2);box=c.get('secondPanelBox',[0,156,286,164]);x,y,w,h=box;y+=(1-ease(a))*190
  if a>0:layers['secondPanel']=vector_panel(assets['second'],(x+(w-w*scale)/2,y,w*scale,h*scale))
 elif component_id=='v07':
  layers['background']=grid();box=c.get('exampleBox',[0,156,286,184]);x,y,w,h=box;panel=canvas();art=photo(assets['example']);bb=art.getbbox();art=art.crop(bb);art.thumbnail((round(w),round(h)),Image.Resampling.LANCZOS);panel.alpha_composite(art,(round(x+(w-art.width)/2),round(y+(h-art.height)/2)));ImageDraw.Draw(panel).rectangle((0,y,285,y+2),fill='white');ImageDraw.Draw(panel).rectangle((0,y+h-2,285,y+h),fill='white');layers['example']=panel;layers['presenter']=window(raw,tuple(c.get('presenterWindow',[174,98,97])),crop=c.get('presenterCrop'));layers['ordinaryCaption']=ordinary_caption(n,c)
''' +s[end:]
insert=s.index('\ndef render(component_id')
s=s[:insert]+'''
def vector_panel(path,box):
 x,y,w,h=map(round,box);out=canvas();d=ImageDraw.Draw(out);d.rounded_rectangle((x,y,x+w,y+h),radius=9,fill='#122733',outline='#0a1119',width=3)
 art=photo(path).copy();art=art.crop(art.getbbox());art.thumbnail((round(w*.92),round(h*.89)),Image.Resampling.LANCZOS);out.alpha_composite(art,(round(x+(w-art.width)/2),round(y+(h-art.height)/2)));return out
''' +s[insert:]
start=s.index(" elif component_id=='t05':");end=s.index(" else:raise ValueError(component_id)",start)
s=s[:start]+''' elif component_id=='t05':
  if c.get('typeRoles'):
   for role,key,clock in [('title','title','title'),('left','left','leftLabel'),('right','right','rightLabel')]:
    spec=c['typeRoles'][role];place_text(out,txt[key],spec,spec['anchorX'],spec['inkY'],n-t[clock],spec.get('duration',7),'center',spec.get('entryDx',14))
  else:
   line(out,txt['title'],30,(38,197),n-t['title'],font=c['fontRoles']['body']['path'])
   for i,key in enumerate(['left','right']):line(out,txt[key],20,(14+148*i,259),n-t[key+'Label'],'#fff4b7',font=c['fontRoles']['labels']['path'])
 elif component_id=='t06':
  if c.get('typeRoles'):
   for role,key,event in [('first','first','firstText'),('second','second','secondText')]:
    spec=c['typeRoles'][role];y=spec['inkY']+(1-ease(prog(n,*t['secondPanel'])))*190 if role=='second' else spec['inkY'];place_text(out,txt[key],spec,spec['anchorX'],y,n-t[event],spec.get('duration',7),'center',spec.get('entryDx',0))
  else:
   line(out,txt['first'],30,(39,90),n-t['firstText'],font=c['fontRoles']['body']['path'])
   if n>=t['secondText']:
    a=prog(n,*t['secondPanel']);line(out,txt['second'],29,(39,211+(1-ease(a))*190),n-t['secondText'],font=c['fontRoles']['body']['path'])
''' +s[end:]
s=s.replace("tile,m=text_tile(cue['text'],14,font=c['fontRoles']['body']['path']);put(out,tile,(286-tile.width)/2,370)","\n   if c.get('typeRoles'):\n    spec=c['typeRoles']['caption'];place_text(out,cue['text'],spec,spec['anchorX'],spec['inkY'],99)\n   else:\n    tile,m=text_tile(cue['text'],14,font=c['fontRoles']['body']['path']);put(out,tile,(286-tile.width)/2,370)")
p.write_text(s,encoding='utf-8')
