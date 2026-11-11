from pathlib import Path
from playwright.sync_api import sync_playwright
P=Path.cwd();A=P/'source/pilot/detail-two/assets'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe');page=b.new_page(viewport={'width':286,'height':508},device_scale_factor=4)
 for svg in A.glob('*.svg'):
  page.set_content('<style>html,body{margin:0;background:transparent}</style>'+svg.read_text('utf-8'))
  page.locator('svg').screenshot(path=str(svg.with_suffix('.png')),omit_background=True)
 b.close()
print('SVG raster caches, 4x alpha, regenerated from vector sources')
