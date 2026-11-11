"""Editable transparent t04: right-anchored phrase reveal, per-glyph streaks,
overshoot, two-color luminous emphasis, hold and shared fade. Native 3x raster."""
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
import math
def clamp(x):return max(0.,min(1.,x))
def alpha(im,k):
    im=im.copy();im.putalpha(im.getchannel('A').point(lambda a:round(a*clamp(k))));return im
def render(p,f,font_path,canvas=(286,508)):
    s=3;out=Image.new('RGBA',(canvas[0]*s,canvas[1]*s))
    fade=1-clamp((f-p['fadeStartFrame'])/max(1,p['fadeEndFrame']-p['fadeStartFrame']))
    if fade<=0:return out.resize(canvas,Image.Resampling.LANCZOS)
    def label(text,size,colors):
        font=ImageFont.truetype(font_path,round(size*s));width=round(font.getlength(text))+s*8
        im=Image.new('RGBA',(width,round(size*s*1.6)));d=ImageDraw.Draw(im)
        x=3*s
        for k,ch in enumerate(text):
            bb=font.getbbox(ch);d.text((round(x),round(3*s-bb[1])),ch,font=font,fill=colors(k),stroke_width=0 if 'Heavy' in font_path else 2,stroke_fill=colors(k))
            x+=font.getlength(ch)
        return im
    first=p['firstLine'];size=p['firstFontSize'];entries=p['glyphEntryFrames'];x,y=p['firstLineXY']
    # Reveal phrase from its fixed right edge while the masked left boundary travels left.
    im=label(first,size,lambda k:'#ffffff');right=im.width-3*s
    elapsed=clamp((f-min(entries)+1)/max(1,max(entries)-min(entries)+1))
    if elapsed>0:
        mask=Image.new('L',im.size);d=ImageDraw.Draw(mask);d.rectangle((round(right*(1-elapsed)),0,im.width,im.height),fill=255)
        im.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
        out.alpha_composite(alpha(im,fade),(round(x*s),round(y*s)))
    start=p['streakFrame'];age=f-start
    if age>=0:
        size=p['secondFontSize'];text=p['secondLine'];font=ImageFont.truetype(font_path,round(size*s))
        spans=p.get('emphasisRanges',[[p.get('goldFromCharacter',len(text)),len(text)]])
        emphasized=lambda k:any(a<=k<b for a,b in spans)
        # Local delay only during entry: each glyph stretches vertically, never a block of pixels.
        row=Image.new('RGBA',(canvas[0]*s,round(size*s*3.5)))
        emphasis_row=Image.new('RGBA',row.size)
        cursor=0
        for k,ch in enumerate(text):
            glyph=label(ch,size,lambda j:'#f0d36b' if emphasized(k) else '#ffffff')
            phase=age-k*.16;a=clamp((phase+1)/3)
            stretch=1+2.5*(1-clamp(phase/4))
            overshoot=1+.13*math.sin(clamp(phase/8)*math.pi) if phase<8 else 1
            width_factor=.12+.88*clamp(phase/3)
            gw=round(glyph.width*overshoot*width_factor);gh=round(glyph.height*stretch*overshoot)
            stretched=glyph.resize((max(1,gw),max(1,gh)),Image.Resampling.BICUBIC)
            blur=max(0,3.5*(1-clamp(phase/6)))*s
            if blur:stretched=stretched.filter(ImageFilter.GaussianBlur(blur))
            row.alpha_composite(alpha(stretched,a),(round(cursor+(glyph.width-gw)/2),round((row.height-gh)/2)))
            if emphasized(k):emphasis_row.alpha_composite(alpha(stretched,a),(round(cursor+(glyph.width-gw)/2),round((row.height-gh)/2)))
            cursor+=font.getlength(ch)
        # A short luminous peak on both white and gold glyphs, then clean solid hold.
        glow_strength=clamp((age-1)/3)*(1-clamp((age-7)/5))
        xx,yy=p['secondLineXY'];pos=(round(xx*s),round((yy+size*.3)*s-(row.height-size*s)/2))
        if glow_strength:
            for radius,k in [(5,.9),(2.3,1.4),(.8,1.2)]:
                out.alpha_composite(alpha(emphasis_row.filter(ImageFilter.GaussianBlur(radius*s)),glow_strength*k*fade),pos)
        out.alpha_composite(alpha(row,fade),pos)
    return out.resize(canvas,Image.Resampling.LANCZOS)
