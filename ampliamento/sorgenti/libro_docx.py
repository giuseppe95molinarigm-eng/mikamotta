#!/usr/bin/env python3
"""Word impaginato come il libro (6 x 9 in), pulito, da consegnare all'autrice.
Uso: python3 libro_docx.py  ->  out/libro_6x9.docx"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FONT = 'Garamond'
GRIGIO = RGBColor(0x55, 0x55, 0x55)

def set_font(style_or_run, size=None, italic=None, color=None, bold=None, caps=False, spacing=None):
    f = style_or_run.font
    f.name = FONT
    rpr = style_or_run.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rf.set(qn(a), FONT)
    for a in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
        if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]
    if size: f.size = Pt(size)
    if italic is not None: f.italic = italic
    if bold is not None: f.bold = bold
    if color is not None: f.color.rgb = color
    if caps: f.small_caps = True
    if spacing is not None:
        sp = OxmlElement('w:spacing'); sp.set(qn('w:val'), str(spacing)); rpr.append(sp)

def field(run, instr):
    for t, txt in (('begin', None), (None, instr), ('end', None)):
        if t:
            e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'), t); run._r.append(e)
        else:
            e = OxmlElement('w:instrText'); e.set(qn('xml:space'), 'preserve'); e.text = txt; run._r.append(e)

def main():
    sez = build.parse()
    d = Document()
    # impostazioni pagina 6x9, margini a specchio, intestazioni pari/dispari diverse
    s0 = d.sections[0]
    s0.page_width, s0.page_height = Inches(6), Inches(9)
    s0.top_margin, s0.bottom_margin = Inches(0.75), Inches(0.8)
    s0.left_margin, s0.right_margin = Inches(0.8), Inches(0.6)   # interno / esterno
    s0.header_distance, s0.footer_distance = Inches(0.4), Inches(0.4)
    st = d.settings.element
    for tag in ('w:mirrorMargins', 'w:evenAndOddHeaders'):
        st.append(OxmlElement(tag))
    lang = OxmlElement('w:themeFontLang'); lang.set(qn('w:val'), 'it-IT'); st.append(lang)
    auto = OxmlElement('w:autoHyphenation'); st.append(auto)

    # stili
    normal = d.styles['Normal']
    set_font(normal, size=11.5)
    rpr = normal.element.get_or_add_rPr(); lg = OxmlElement('w:lang'); lg.set(qn('w:val'), 'it-IT'); rpr.append(lg)
    pf = normal.paragraph_format
    pf.space_before = Pt(0); pf.space_after = Pt(0); pf.line_spacing = 1.18
    pf.first_line_indent = Inches(0.18); pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.widow_control = True
    h1 = d.styles['Heading 1']; set_font(h1, size=19, bold=False, color=RGBColor(0x11, 0x11, 0x11), italic=False)
    h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h1.paragraph_format.space_before = Pt(0); h1.paragraph_format.space_after = Pt(30)
    h1.paragraph_format.first_line_indent = Inches(0); h1.paragraph_format.keep_with_next = True
    h2 = d.styles['Heading 2']; set_font(h2, size=11.5, bold=True, color=RGBColor(0x11, 0x11, 0x11), italic=False)
    h2.paragraph_format.space_before = Pt(12); h2.paragraph_format.space_after = Pt(4)
    h2.paragraph_format.first_line_indent = Inches(0); h2.paragraph_format.keep_with_next = True

    def p(text='', indent=True, align=None, size=None, italic=None, color=None, before=None, after=None,
          page_break=False, caps=False, spacing=None, keep=False):
        par = d.add_paragraph()
        if text:
            parts = [text]
            for s_ in build.ITALICI:
                nxt = []
                for part in parts:
                    if isinstance(part, tuple): nxt.append(part); continue
                    bits = part.split(s_)
                    for k, bit in enumerate(bits):
                        if bit: nxt.append(bit)
                        if k < len(bits) - 1: nxt.append((s_,))
                parts = nxt
            for part in parts:
                r = par.add_run(part[0] if isinstance(part, tuple) else part)
                set_font(r, size=size, italic=True if isinstance(part, tuple) else italic, color=color, caps=caps, spacing=spacing)
        f = par.paragraph_format
        if not indent: f.first_line_indent = Inches(0)
        if align is not None: f.alignment = align
        if before is not None: f.space_before = Pt(before)
        if after is not None: f.space_after = Pt(after)
        if page_break: f.page_break_before = True
        if keep: f.keep_with_next = True
        return par

    def lines_par(lines, italic=False, left=0.35, after=9):
        par = d.add_paragraph(); f = par.paragraph_format
        f.first_line_indent = Inches(0); f.left_indent = Inches(left); f.alignment = WD_ALIGN_PARAGRAPH.LEFT
        f.space_after = Pt(after); f.keep_together = True
        for k, l in enumerate(lines):
            r = par.add_run(l); set_font(r, italic=italic)
            if k < len(lines) - 1: r.add_break()
        return par

    C = WD_ALIGN_PARAGRAPH.CENTER
    # ---- pagine iniziali
    p(build.TITOLO.upper(), indent=False, align=C, size=12, before=170, spacing=40)
    p('', page_break=True)                                   # pagina 2 bianca
    p(build.AUTRICE.upper(), indent=False, align=C, size=11, before=110, after=40, spacing=40, page_break=True)
    p('La Radioterapista', indent=False, align=C, size=28)
    p('Invisibile', indent=False, align=C, size=28, after=16)
    p(build.SOTTOTITOLO, indent=False, align=C, size=13, italic=True)
    col = [build.TITOLO + ' – ' + build.SOTTOTITOLO, '© 2026 ' + build.AUTRICE + '. Tutti i diritti riservati.',
           'Nuova edizione ampliata, 2026.']
    first = True
    for t in col:
        p(t, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, size=9, after=6, before=380 if first else None, page_break=first); first = False
    p(build.DISCLAIMER, indent=False, align=WD_ALIGN_PARAGRAPH.LEFT, size=9, italic=True)

    def heading(s):
        k = s['kind']
        if k == 'capitolo':
            p('Capitolo %d' % s['num'], indent=False, align=C, size=10, color=GRIGIO, before=60, after=8, page_break=True, caps=True, spacing=30, keep=True)
            d.add_heading(s['title'], level=1)
        elif k == 'prologo':
            p('Prologo', indent=False, align=C, size=10, color=GRIGIO, before=60, after=8, page_break=True, caps=True, spacing=30, keep=True)
            d.add_heading('“%s”' % s['title'], level=1)
        else:
            h = p(s['title'], indent=False, align=C, size=16, italic=True, before=60, after=26, page_break=True, keep=True)

    for s in sez:
        heading(s)
        first = True
        for b in s['blocks']:
            t = b['t']
            if t == 'p':
                if s['kind'] == 'nota':
                    p(b['text'], indent=False, align=C, italic=True)
                else:
                    p(b['text'], indent=not first)
                first = False
            elif t in ('poesia', 'citazione'):
                st_, stanzas = [], []
                for l in b['lines'] + ['']:
                    if l.strip(): st_.append(l)
                    elif st_: stanzas.append(st_); st_ = []
                for x in stanzas:
                    lines_par(x, italic=(t == 'citazione'), left=0.5 if t == 'poesia' else 0.3, after=10 if t == 'poesia' else 6)
                first = True
            elif t == 'lista':
                for k, l in enumerate([l for l in b['lines'] if l.strip()]):
                    par = p(('%d. ' % (k + 1) if b['numbered'] else '– ') + l, indent=False)
                    par.paragraph_format.left_indent = Inches(0.3)
                first = True
            elif t == 'riquadro':
                body = ' '.join(l.strip() for l in b['lines'] if l.strip()).lstrip('~ ').strip()
                p(b['title'], indent=False, size=10, before=12, after=3, caps=True, spacing=20, keep=True)
                p(body, indent=False, size=10, after=12)
                first = True
            elif t == 'sezione':
                d.add_heading(b['text'], level=2); first = True
            elif t == 'sottotitolo':
                p(b['text'], indent=False, align=C, italic=True, after=18); first = True
            elif t == 'stacco':
                p('*', indent=False, align=C, before=8, after=8); first = True
            elif t == 'img':
                par = p('', indent=False, align=C, before=14, after=8)
                par.add_run().add_picture(os.path.join(build.BASE, 'img', b['file']), width=Inches(min(b['w'], 4.5)))
                first = True
            elif t == 'gloss':
                p(b['term'], indent=False, keep=True, before=5).runs[0].font.bold = True
                p(b['def'], indent=False)

    # intestazioni e numeri di pagina (pari: autrice; dispari: titolo); prima pagina senza
    s0.different_first_page_header_footer = True
    for hdr, txt in ((s0.header, build.TITOLO), (s0.even_page_header, build.AUTRICE)):
        par = hdr.paragraphs[0]; par.alignment = C; par.paragraph_format.first_line_indent = Inches(0)
        r = par.add_run(txt.upper()); set_font(r, size=8, color=GRIGIO, spacing=24)
    for ftr in (s0.footer, s0.even_page_footer):
        par = ftr.paragraphs[0]; par.alignment = C; par.paragraph_format.first_line_indent = Inches(0)
        r = par.add_run(); set_font(r, size=9.5); field(r, 'PAGE')

    out = os.path.join(build.OUT, 'libro_6x9.docx')
    d.core_properties.title = build.TITOLO; d.core_properties.author = build.AUTRICE
    d.save(out); print(out)

if __name__ == '__main__':
    main()
