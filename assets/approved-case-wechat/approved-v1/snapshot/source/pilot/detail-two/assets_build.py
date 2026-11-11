from pathlib import Path
import json
P=Path.cwd();S=P/'source/pilot/detail-two';A=S/'assets';A.mkdir(exist_ok=True)
start='<svg xmlns="http://www.w3.org/2000/svg" width="286" height="508" viewBox="0 0 286 508">'
defs='''<defs><linearGradient id="sky" x2="0" y2="1"><stop stop-color="#6591b0"/><stop offset="1" stop-color="#dfedf0"/></linearGradient><linearGradient id="glass"><stop stop-color="#163546"/><stop offset=".48" stop-color="#71a0b7"/><stop offset=".53" stop-color="#274758"/><stop offset="1" stop-color="#a1b9c5"/></linearGradient><linearGradient id="paper" x2=".2" y2="1"><stop stop-color="#ffffef"/><stop offset=".5" stop-color="#e7ead5"/><stop offset="1" stop-color="#aabda9"/></linearGradient><linearGradient id="teal" x2="1" y2="1"><stop stop-color="#719c91"/><stop offset="1" stop-color="#244f52"/></linearGradient><filter id="sh" x="-.4" y="-.4" width="1.8" height="1.8"><feDropShadow dx="1.4" dy="2.4" stdDeviation="1.2" flood-color="#08171b" flood-opacity=".52"/></filter></defs>'''
svg=start+defs+'<path fill="url(#sky)" d="M0 0H286V508H0z"/><path fill="#e5eff0" opacity=".3" d="M-20 99Q80 60 140 95T310 73V91Q180 132 100 100T-20 125z"/>'
for x,y,w,h in [(-18,110,77,400),(54,153,60,355),(93,47,81,461),(180,76,78,432),(246,186,61,322)]:
 svg+=f'<g><path fill="url(#glass)" stroke="#cad9da" stroke-width="1.1" d="M{x} {y+12}l{w/2} -12 {w/2} 12V508H{x}Z"/>'
 for k in range(1,7):svg+=f'<path d="M{x+k*w/7} {y+12}V508" stroke="#c1d2d8" stroke-width=".65" opacity=".8"/>'
 for yy in range(y+22,508,11):svg+=f'<path d="M{x} {yy}h{w}" stroke="#142c3b" stroke-width="1.3" opacity=".65"/>'
 svg+='</g>'
svg+='<path d="M133 5v45m-7-11h14M195 36v42" stroke="#e0ded2" stroke-width="2"/><path d="M0 470L286 431V508H0z" fill="#3b545e" opacity=".4"/></svg>'
(A/'business-skyline.svg').write_text(svg,'utf-8')
svg=start+defs+'<path fill="#c8d7d4" d="M0 0H286V508H0z"/><path fill="#e6e6d8" d="M0 0H286V312H0z"/>'
for xx in range(18,285,57):svg+=f'<path d="M{xx} 25v250m-20-135h53" stroke="#94b2b3" stroke-width="3"/>'
svg+='<path fill="#b49a76" d="M0 354l286-15v169H0z"/><g transform="translate(18 284) rotate(-6)" filter="url(#sh)"><path d="M0 0h160v112H0z" fill="#2f454b" stroke="#ebf3ef" stroke-width="3"/><path d="M7 7h146v91H7z" fill="#688d91"/><path d="M24 20h80m-80 12h110m-110 12h95m-95 12h115" stroke="#bfd4cd" stroke-width="3"/><path d="M0 112h160l23 31H-21z" fill="#bdc6c1" stroke="#e7ece3"/><path d="M8 118h147l11 15H-3z" fill="#6d8282"/></g><g transform="translate(140 369) rotate(8)" filter="url(#sh)"><path d="M0 0h116v114H0z" fill="url(#paper)"/><path d="M12 13h53m-53 15h90m-90 12h90m-90 12h90m-90 12h90m-90 12h90" stroke="#7a9587" stroke-width="2"/><path d="M56 98l13-25 15 10 13-36" fill="none" stroke="#a53e37" stroke-width="4"/></g><g transform="translate(235 296)" filter="url(#sh)"><path d="M0 0h30v49H0z" fill="#e5d9b2"/><path d="M30 9q21 0 12 20H30" fill="none" stroke="#e5d9b2" stroke-width="5"/><path d="M-6 49h43" stroke="#647f77" stroke-width="2"/></g></svg>'
(A/'business-risk-desk.svg').write_text(svg,'utf-8')
# Freestanding, editable vector objects; no opaque photographic rectangle.
svg=start+defs
svg+='''<g filter="url(#sh)"><g transform="translate(37 254) rotate(-24 56 36)"><path d="M0 0h112v70H0z" fill="url(#paper)" stroke="#7b9682" stroke-width="1.2"/><path d="M6 6h100v58H6z" fill="none" stroke="#8fa48b"/><path d="M15 17h27m-27 9h34m-34 10h27m-27 9h34m-34 10h27" stroke="#7e9984" stroke-width="1.5"/><circle cx="78" cy="35" r="22" fill="#b3c5aa" stroke="#7f9f89"/><path d="M65 35l9 9 19-22" fill="none" stroke="#356b5e" stroke-width="6"/></g>
<g transform="translate(106 282) rotate(17 59 38)"><path d="M0 0h120v78H0z" fill="url(#paper)" stroke="#759180"/><path d="M7 7h106v64H7z" fill="none" stroke="#8ca58c"/><path d="M18 20h32m-32 10h26m-26 11h32m-32 10h22" stroke="#7c9787" stroke-width="2"/><path d="M81 22l-13 16 13 15m17-31 13 16-13 15m-7-34-9 37" fill="none" stroke="#3e7167" stroke-width="3"/></g>
<g transform="translate(36 326) rotate(-11 58 39)"><path d="M0 0q29-9 58 0 29-9 58 0v68q-29-8-58 0-29-8-58 0z" fill="url(#paper)" stroke="#748f7a" stroke-width="1.5"/><path d="M58 1v65" stroke="#668776" stroke-width="2"/><path d="M10 14q19-4 36 0m-36 11q19-4 36 0m-36 11q19-4 36 0m-36 11q19-4 36 0m20-33q19-4 36 0m-36 11q19-4 36 0m-36 11q19-4 36 0m-36 11q19-4 36 0" fill="none" stroke="#8fa38c"/></g>
<g transform="translate(112 367) rotate(14 64 33)"><path d="M0 0h126v66H0z" fill="url(#paper)" stroke="#78927e"/><path d="M7 7h112v52H7z" fill="none" stroke="#98ac90"/><circle cx="33" cy="33" r="18" fill="#b8c6ac" stroke="#839e87"/><path d="M24 34l7 7 12-15" fill="none" stroke="#527b66" stroke-width="4"/><path d="M61 21h47m-47 9h37m-37 9h47m-47 9h31" stroke="#8b9e81" stroke-width="2"/></g></g></svg>'''
(A/'practical-skills-spread.svg').write_text(svg,'utf-8')
print('3 editable SVG sources created')
