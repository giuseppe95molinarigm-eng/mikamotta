#!/usr/bin/env python3
"""Crea un Word di revisione con solo alcuni capitoli. Uso: python3 estratto.py 1 3"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build
da, a = int(sys.argv[1]), int(sys.argv[2])
sez = [s for s in build.parse() if s['kind'] == 'capitolo' and da <= s['num'] <= a]
build.build_docx(sez, review=True, completo=False)
src = os.path.join(build.OUT, 'revisione.docx')
dst = os.path.join(os.path.dirname(build.BASE), 'La_Radioterapista_Invisibile_capitoli_%d-%d_revisione.docx' % (da, a))
os.replace(src, dst); print(dst)
