import urllib.request,json
from pathlib import Path
p=Path('source/pilot/batches/scene/assets')
items={'city':'photo-1486406146926-c627a92ad1ab','office':'photo-1497366216548-37526070297c','desk':'photo-1454165804606-c3d57bc86b40','meeting':'photo-1517245386807-bb43f82c33c4','laptop':'photo-1516321318423-f06f85e504b3'}
for name,id in items.items():
 url='https://images.unsplash.com/'+id+'?w=1000&q=88&fit=crop'
 try:
  urllib.request.urlretrieve(url,p/(name+'.jpg'));print(name,'ok')
 except Exception as e:print(name,e)
(p/'provenance.json').write_text(json.dumps({k:{'url':'https://images.unsplash.com/'+v,'use':'editorial illustrative stock photo, not financial evidence'} for k,v in items.items()},indent=2),encoding='utf-8')
