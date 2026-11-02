#!/usr/bin/env python3
"""Costruisce da testo/*.txt: HTML per la stampa (paged.js), HTML per EPUB, DOCX di revisione e DOCX pulito."""
import re, os, html, sys, json, glob

BASE = os.path.dirname(os.path.abspath(__file__))
TESTO = os.path.join(BASE, 'testo')
OUT = os.path.join(BASE, 'out')
os.makedirs(OUT, exist_ok=True)

TITOLO = 'La Radioterapista Invisibile'
SOTTOTITOLO = 'Appunti clinici e emozionali da un bunker'
AUTRICE = 'Micaela Motta'
DISCLAIMER = ('Ogni riferimento a fatti e persone realmente esistenti è da considerarsi puramente casuale. '
              'L’autrice declina ogni responsabilità in caso di coincidenze. L’opera è frutto di fantasia.')
ITALICI = ['Amare Tradire Capire', 'Leucanthemum vulgare', 'Faust',
           'Grazie, dottoressa Valli TVB. Grazie per esserci, anche quando non si vede.']

# ---------------------------------------------------------------- parsing
def parse():
    righe = []
    for f in sorted(glob.glob(os.path.join(TESTO, '*.txt'))):
        righe += open(f, encoding='utf-8').read().split('\n') + ['']
    sezioni = []          # liste di dict
    cur = None
    i = 0
    n_cap = 0
    def para_flush(buf):
        if not buf: return
        t = ' '.join(buf).strip()
        mark = None
        if t.startswith('+ '): mark, t = 'new', t[2:]
        elif t.startswith('~ '): mark, t = 'rev', t[2:]
        cur['blocks'].append({'t': 'p', 'text': t, 'mark': mark})
    buf = []
    while i < len(righe):
        r = righe[i].rstrip()
        if r.startswith('@'):
            para_flush(buf); buf = []
            cmd, _, arg = r[1:].partition(' ')
            if cmd in ('nota', 'prologo', 'capitolo', 'inserto', 'glossario'):
                cur = {'kind': cmd, 'title': arg.strip(), 'blocks': []}
                if cmd == 'capitolo':
                    n_cap += 1; cur['num'] = n_cap
                sezioni.append(cur)
                if cmd == 'glossario':
                    i += 1
                    while not righe[i].startswith('@fine'):
                        if righe[i].strip():
                            line = righe[i].strip(); mark = None
                            if line.startswith('+'): mark, line = 'new', line[1:]
                            elif line.startswith('~'): mark, line = 'rev', line[1:]
                            term, _, d = line.partition('|')
                            cur['blocks'].append({'t': 'gloss', 'term': term.strip(), 'def': d.strip(), 'mark': mark})
                        i += 1
            elif cmd in ('poesia', 'citazione', 'lista', 'riquadro'):
                lines = []
                i += 1
                while not righe[i].startswith('@fine'):
                    lines.append(righe[i].rstrip()); i += 1
                b = {'t': cmd, 'lines': lines}
                if cmd == 'lista': b['numbered'] = (arg.strip() == 'numerata')
                if cmd == 'riquadro': b['title'] = arg.strip()
                cur['blocks'].append(b)
            elif cmd in ('sezione', 'sottotitolo'):
                cur['blocks'].append({'t': cmd, 'text': arg.strip()})
            elif cmd == 'stacco':
                cur['blocks'].append({'t': 'stacco'})
            elif cmd == 'immagine':
                f, w = arg.split()
                cur['blocks'].append({'t': 'img', 'file': f, 'w': float(w)})
        elif r.strip() == '':
            para_flush(buf); buf = []
        else:
            buf.append(r.strip())
        i += 1
    para_flush(buf)
    return sezioni

# ---------------------------------------------------------------- inline
def inline_html(t):
    t = html.escape(t, quote=False)
    for s in ITALICI:
        t = t.replace(html.escape(s, quote=False), '<em>%s</em>' % html.escape(s, quote=False))
    return t

def sec_id(s):
    if s['kind'] == 'capitolo': return 'cap%d' % s['num']
    return re.sub(r'[^a-z0-9]+', '-', s['title'].lower()).strip('-')[:40]

def label(s):
    return {'capitolo': 'Capitolo %d' % s.get('num', 0)}.get(s['kind'], '')

# ---------------------------------------------------------------- HTML (stampa ed epub)
def blocks_html(s, for_epub=False):
    out = []
    first = True
    for b in s['blocks']:
        t = b['t']
        if t == 'p':
            cls = ' class="first"' if first else ''
            out.append('<p%s>%s</p>' % (cls, inline_html(b['text'])))
            first = False
        elif t == 'poesia':
            stanzas, st = [], []
            for l in b['lines'] + ['']:
                if l.strip(): st.append(inline_html(l))
                elif st: stanzas.append(st); st = []
            out.append('<div class="poesia">' + ''.join('<p class="strofa">%s</p>' % '<br/>'.join(x) for x in stanzas) + '</div>')
            first = True
        elif t == 'citazione':
            out.append('<blockquote class="citazione"><p>%s</p></blockquote>' % '<br/>'.join(inline_html(l) for l in b['lines'] if l.strip()))
            first = True
        elif t == 'lista':
            tag = 'ol' if b['numbered'] else 'ul'
            out.append('<%s class="lista">%s</%s>' % (tag, ''.join('<li>%s</li>' % inline_html(l) for l in b['lines'] if l.strip()), tag))
            first = True
        elif t == 'riquadro':
            body = ' '.join(l.strip() for l in b['lines'] if l.strip()).lstrip('~ ').strip()
            out.append('<div class="riquadro"><p class="riq-tit">%s</p><p>%s</p></div>' % (inline_html(b['title']), inline_html(body)))
            first = True
        elif t == 'sezione':
            out.append('<h3>%s</h3>' % inline_html(b['text'])); first = True
        elif t == 'sottotitolo':
            out.append('<p class="sottotitolo">%s</p>' % inline_html(b['text'])); first = True
        elif t == 'stacco':
            out.append('<p class="stacco">*</p>'); first = True
        elif t == 'img':
            src = ('img/' if for_epub else '../img/') + b['file']
            out.append('<figure class="ill" style="width:%.2fin"><img src="%s" alt=""/></figure>' % (b['w'], src) if not for_epub
                       else '<figure class="ill"><img src="%s" alt="Illustrazione"/></figure>' % src)
            first = True
        elif t == 'gloss':
            out.append('<div class="voce"><p class="termine">%s</p><p class="def">%s</p></div>' % (inline_html(b['term']), inline_html(b['def'])))
    return '\n'.join(out)

def section_html(s, for_epub=False):
    k = s['kind']; sid = sec_id(s)
    if k == 'capitolo':
        head = '<h1 class="cap-titolo"><span class="cap-num">Capitolo %d</span><span class="cap-nome">%s</span></h1>' % (s['num'], inline_html(s['title']))
    elif k == 'prologo':
        head = '<h1 class="cap-titolo"><span class="cap-num">Prologo</span><span class="cap-nome">“%s”</span></h1>' % inline_html(s['title'])
    elif k == 'nota':
        head = '<h1 class="nota-titolo">%s</h1>' % inline_html(s['title'])
    else:
        head = '<h1 class="ins-titolo">%s</h1>' % inline_html(s['title'])
    if for_epub:
        head = head.replace('</span><span class="cap-nome">', '</span><span class="sep"> – </span><span class="cap-nome">')
        head = head.replace('<h1 ', '<h1 id="%s" ' % sid, 1)
        return '%s\n%s\n' % (head, blocks_html(s, for_epub))
    return '<section class="sez %s" id="%s">\n%s\n%s\n</section>' % (k, sid, head, blocks_html(s, for_epub))

def toc_entries(sez):
    ent = []
    for s in sez:
        if s['kind'] == 'nota': continue
        if s['kind'] == 'capitolo':
            ent.append((sec_id(s), 'Capitolo %d – %s' % (s['num'], s['title']), 'cap'))
        elif s['kind'] == 'prologo':
            ent.append((sec_id(s), 'Prologo', 'cap'))
        else:
            ent.append((sec_id(s), s['title'], 'ins' if s['kind'] == 'inserto' else 'cap'))
    return ent

PRINT_CSS = open(os.path.join(BASE, 'stampa.css'), encoding='utf-8').read() if os.path.exists(os.path.join(BASE, 'stampa.css')) else ''

def build_print(sez):
    toc = ''.join('<li class="%s"><a href="#%s">%s</a></li>' % (c, i, inline_html(t)) for i, t, c in toc_entries(sez))
    front = f'''
<section class="front occhietto"><p class="occ-tit">{TITOLO}</p></section>
<section class="front vuota"><p>&#160;</p></section>
<section class="front frontespizio">
  <p class="fr-autrice">{AUTRICE}</p>
  <h1 class="fr-titolo">La Radioterapista<br/>Invisibile</h1>
  <p class="fr-sotto">{SOTTOTITOLO}</p>
</section>
<section class="front colophon">
  <p>{TITOLO}<br/>{SOTTOTITOLO}</p>
  <p>© 2026 {AUTRICE}<br/>Tutti i diritti riservati.</p>
  <p>Nuova edizione ampliata, 2026.</p>
  <p class="disc">{DISCLAIMER}</p>
</section>'''
    body = []
    for s in sez:
        body.append(section_html(s))
        if s['kind'] == 'nota':
            body.append('<section class="front indice" id="indice"><h1 class="nota-titolo">Indice</h1><ul class="toc">%s</ul></section>' % toc)
    doc = f'''<!doctype html><html lang="it"><head><meta charset="utf-8"/><title>{TITOLO}</title>
<style>{PRINT_CSS}</style>
<script>window.PagedConfig={{auto:true,after:function(){{window.__pagedDone=true;}}}};</script>
<script src="../build/paged.polyfill.js"></script>
</head><body>{front}
{''.join(body)}
</body></html>'''
    p = os.path.join(OUT, 'stampa.html')
    open(p, 'w', encoding='utf-8').write(doc)
    return p

def build_epub_html(sez):
    parts = []
    for s in sez:
        parts.append(section_html(s, for_epub=True))
    doc = f'''<!doctype html><html lang="it"><head><meta charset="utf-8"/><title>{TITOLO}</title></head><body>
<h1 class="nota-titolo" id="colophon">Colophon</h1><div class="colophon"><p>{TITOLO}<br/>{SOTTOTITOLO}</p><p>© 2026 {AUTRICE}. Tutti i diritti riservati.</p><p>Nuova edizione ampliata, 2026.</p><p class="disc">{DISCLAIMER}</p></div>
{''.join(parts)}</body></html>'''
    p = os.path.join(OUT, 'epub.html')
    open(p, 'w', encoding='utf-8').write(doc)
    return p

# ---------------------------------------------------------------- DOCX
def build_docx(sez, review, completo=True):
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    d = Document()
    sec = d.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    for m in ('left_margin', 'right_margin'): setattr(sec, m, Cm(2.5))
    st = d.styles['Normal']; st.font.name = 'Garamond'; st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Garamond')
    pf = st.paragraph_format; pf.space_after = Pt(6); pf.line_spacing = 1.25
    for hn, sz in (('Heading 1', 18), ('Heading 2', 13)):
        h = d.styles[hn]; h.font.name = 'Garamond'; h.font.size = Pt(sz); h.font.color.rgb = RGBColor(0x22, 0x22, 0x22); h.font.bold = False
        rpr = h.element.get_or_add_rPr(); rf = rpr.find(qn('w:rFonts'))
        if rf is None: rf = OxmlElement('w:rFonts'); rpr.append(rf)
        for a in ('w:ascii', 'w:hAnsi', 'w:asciiTheme', 'w:hAnsiTheme'):
            if rf.get(qn(a)) is not None and 'Theme' in a: del rf.attrib[qn(a)]
        rf.set(qn('w:ascii'), 'Garamond'); rf.set(qn('w:hAnsi'), 'Garamond')
    COL = {'new': 'FFF2C2', 'rev': 'DCEBFA'}
    def shade(p, mark):
        if not (review and mark): return
        pPr = p._p.get_or_add_pPr(); shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), COL[mark]); pPr.append(shd)
    def add_runs(p, text):
        parts = [text]
        for s_ in ITALICI:
            nxt = []
            for part in parts:
                if isinstance(part, tuple): nxt.append(part); continue
                bits = part.split(s_)
                for k, bit in enumerate(bits):
                    if bit: nxt.append(bit)
                    if k < len(bits) - 1: nxt.append((s_,))
            parts = nxt
        for part in parts:
            if isinstance(part, tuple): r = p.add_run(part[0]); r.italic = True
            else: p.add_run(part)
    def para(text, mark=None, style=None, align=None, italic=False, size=None):
        p = d.add_paragraph(style=style)
        add_runs(p, text)
        if italic:
            for r in p.runs: r.italic = True
        if size:
            for r in p.runs: r.font.size = Pt(size)
        if align: p.alignment = align
        shade(p, mark); return p
    # copertina
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; r = p.add_run(TITOLO); r.font.size = Pt(26)
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; r = p.add_run(SOTTOTITOLO); r.italic = True; r.font.size = Pt(14)
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; r = p.add_run(AUTRICE); r.font.size = Pt(13)
    if review:
        d.add_paragraph()
        p = d.add_paragraph(); r = p.add_run('Versione di revisione – come leggere questo file'); r.bold = True
        p = d.add_paragraph('I paragrafi su fondo giallo sono nuovi. ')
        shade(p, 'new')
        p = d.add_paragraph('I paragrafi su fondo azzurro sono frasi del testo originale ritoccate (refusi, coerenza, raccordi). ')
        shade(p, 'rev')
        d.add_paragraph('Tutto il resto è il testo originale, invariato.' + (' I capitoli 20, 23, 26 e 28 sono episodi interamente nuovi.' if completo else ''))
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(DISCLAIMER); r.font.size = Pt(9); r.italic = True
    for s in sez:
        d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        if s['kind'] == 'capitolo':
            p = para('Capitolo %d' % s['num'], align=WD_ALIGN_PARAGRAPH.CENTER, size=11)
            h = d.add_heading(s['title'], level=1); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif s['kind'] == 'prologo':
            para('Prologo', align=WD_ALIGN_PARAGRAPH.CENTER, size=11)
            h = d.add_heading('“%s”' % s['title'], level=1); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            h = d.add_heading(s['title'], level=1); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for b in s['blocks']:
            t = b['t']
            if t == 'p': para(b['text'], b['mark'])
            elif t in ('poesia', 'citazione'):
                stanzas, st_ = [], []
                for l in b['lines'] + ['']:
                    if l.strip(): st_.append(l)
                    elif st_: stanzas.append(st_); st_ = []
                for x in stanzas:
                    p = d.add_paragraph(); p.paragraph_format.left_indent = Cm(1.5)
                    for k, l in enumerate(x):
                        r = p.add_run(l)
                        if t == 'citazione': r.italic = True
                        if k < len(x) - 1: r.add_break()
            elif t == 'lista':
                for k, l in enumerate([l for l in b['lines'] if l.strip()]):
                    para(('%d. ' % (k + 1) if b['numbered'] else '– ') + l).paragraph_format.left_indent = Cm(1)
            elif t == 'riquadro':
                body = ' '.join(l.strip() for l in b['lines'] if l.strip())
                mk = 'rev' if body.startswith('~ ') else None
                p = para(b['title']); p.runs[0].bold = True
                para(body.lstrip('~ ').strip(), mk, size=10.5)
            elif t == 'sezione':
                d.add_heading(b['text'], level=2)
            elif t == 'sottotitolo':
                para(b['text'], italic=True, align=WD_ALIGN_PARAGRAPH.CENTER)
            elif t == 'stacco':
                para('*', align=WD_ALIGN_PARAGRAPH.CENTER)
            elif t == 'img':
                p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.add_run().add_picture(os.path.join(BASE, 'img', b['file']), width=Inches(min(b['w'], 5.0)))
            elif t == 'gloss':
                p = d.add_paragraph(); r = p.add_run(b['term']); r.bold = True
                p.paragraph_format.space_after = Pt(0); shade(p, b['mark'])
                p = para(b['def'], b['mark'])
    name = 'revisione.docx' if review else 'manoscritto.docx'
    d.save(os.path.join(OUT, name))

# ---------------------------------------------------------------- statistiche
def stats(sez):
    W = lambda t: len(re.findall(r"[A-Za-zÀ-ÿ0-9’']+", t))
    rows = []
    tot = {'orig': 0, 'new': 0}
    for s in sez:
        o = n = 0
        for b in s['blocks']:
            txt = ''
            if b['t'] == 'p': txt = b['text']
            elif b['t'] in ('poesia', 'citazione', 'lista', 'riquadro'): txt = ' '.join(b['lines'])
            elif b['t'] in ('sezione', 'sottotitolo'): txt = b['text']
            elif b['t'] == 'gloss': txt = b['term'] + ' ' + b['def']
            if b.get('mark') == 'new': n += W(txt)
            else: o += W(txt)
        rows.append((label(s) or s['kind'], s['title'], o, n))
        tot['orig'] += o; tot['new'] += n
    return rows, tot

if __name__ == '__main__':
    sez = parse()
    build_print(sez)
    build_epub_html(sez)
    build_docx(sez, review=True)
    build_docx(sez, review=False)
    rows, tot = stats(sez)
    with open(os.path.join(OUT, 'conteggio.tsv'), 'w') as f:
        for r in rows: f.write('%s\t%s\t%d\t%d\n' % r)
    for r in rows: print('%-12s %-48s %5d %5d' % (r[0], r[1][:48], r[2], r[3]))
    print('TOTALE originale(+ritoccato): %d  nuovo: %d  complessivo: %d' % (tot['orig'], tot['new'], tot['orig'] + tot['new']))
