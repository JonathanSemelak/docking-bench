# -*- coding: utf-8 -*-
"""Genera GUIA-ACTIVIDADES-CLAVE.pdf: la clave docente.

    pip install reportlab
    python3 build_clave_pdf.py

Mismo sistema visual que build_guia_pdf.py, sin campos de formulario. Los
valores son los de GUIA-ACTIVIDADES-CLAVE.md, que salen de data.json y
analogs.json; si se regeneran los datos hay que revisar los dos archivos."""

import os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, Flowable, KeepTogether)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "GUIA-ACTIVIDADES-CLAVE.pdf")
LS = "/usr/share/fonts/truetype/liberation"
DV = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DJ",   LS + "/LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("DJB",  LS + "/LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DJI",  LS + "/LiberationSans-Italic.ttf"))
pdfmetrics.registerFont(TTFont("DJBI", LS + "/LiberationSans-BoldItalic.ttf"))
pdfmetrics.registerFont(TTFont("DJM",  DV + "/DejaVuSansMono.ttf"))
pdfmetrics.registerFont(TTFont("DJMB", DV + "/DejaVuSansMono-Bold.ttf"))
pdfmetrics.registerFontFamily("DJ", normal="DJ", bold="DJB", italic="DJI", boldItalic="DJBI")
pdfmetrics.registerFontFamily("DJM", normal="DJM", bold="DJMB", italic="DJM", boldItalic="DJMB")

INK   = colors.HexColor("#131C26"); MESH  = colors.HexColor("#2B6CAB")
MESHBG= colors.HexColor("#EDF3FA"); MESHED= colors.HexColor("#B9D3EA")
RULE  = colors.HexColor("#D5DFEA"); MUTED = colors.HexColor("#57697B")
DIM   = colors.HexColor("#8497A9"); POS   = colors.HexColor("#1B7F53")
NEG   = colors.HexColor("#BE3A2E"); NEGBG = colors.HexColor("#FBE9E7")
AMB   = colors.HexColor("#8A5A12"); AMBBG = colors.HexColor("#FAF0DC")

PW, PH = A4
LM = RM = 18 * mm; TM = 16 * mm; BM = 16 * mm
CW = PW - LM - RM

def S(name, **kw):
    kw.setdefault("fontName", "DJ"); kw.setdefault("fontSize", 9.2)
    kw.setdefault("leading", 13.2);  kw.setdefault("textColor", INK)
    kw.setdefault("alignment", TA_LEFT)
    return ParagraphStyle(name, **kw)

body  = S("body", spaceAfter=6)
small = S("small", fontSize=8.2, leading=11.6, textColor=MUTED)
cell  = S("cell", fontSize=8.4, leading=11.4, spaceAfter=0)
celln = S("celln", fontSize=8.4, leading=11.4, fontName="DJM", spaceAfter=0, alignment=TA_RIGHT)
cellh = S("cellh", fontSize=7.4, leading=10, fontName="DJB", textColor=DIM, spaceAfter=0)
h1    = S("h1", fontName="DJB", fontSize=23, leading=26, spaceAfter=7)
hpart = S("hpart", fontName="DJB", fontSize=15.5, leading=19, spaceAfter=2)
hact  = S("hact", fontName="DJB", fontSize=11.4, leading=14.6, spaceAfter=1)
eyeb  = S("eyeb", fontName="DJB", fontSize=7.4, leading=10, textColor=DIM, spaceAfter=4)
ansst = S("ans", fontSize=8.8, leading=12.4, leftIndent=16, firstLineIndent=-16, spaceAfter=5)
notest= S("notest", fontSize=8.6, leading=12.2, spaceAfter=4)

# ------------------------------------------------------- markdown -> markup
def md(t):
    """Convierte el subconjunto de markdown que usa la clave."""
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"`([^`]+)`", r'<font face="DJM" size="8">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", t)
    return t

def ui(t):  return '<font face="DJM" size="8.2" color="#2B6CAB">%s</font>' % t
def n(t):   return '<font face="DJM">%s</font>' % t

class Rule(Flowable):
    def __init__(self, w, thickness=2.5, color=MESH, space=5):
        Flowable.__init__(self); self.w=w; self.t=thickness; self.c=color; self.space=space
    def wrap(self, aw, ah): return (self.w, self.t + self.space)
    def draw(self):
        self.canv.setStrokeColor(self.c); self.canv.setLineWidth(self.t)
        self.canv.line(0, self.space, self.w, self.space)

GRID = TableStyle([
    ("GRID",(0,0),(-1,-1),0.5,RULE),
    ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#EAF0F7")),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("LEFTPADDING",(0,0),(-1,-1),6), ("RIGHTPADDING",(0,0),(-1,-1),6),
    ("TOPPADDING",(0,0),(-1,-1),3.5), ("BOTTOMPADDING",(0,0),(-1,-1),3.5),
])

def table(header, rows, widths):
    data = [[Paragraph(h, cellh) for h in header]]
    for r in rows:
        data.append([c if not isinstance(c, str) else Paragraph(md(c), cell) for c in r])
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(GRID)
    return t

def N(v, color=None, bold=False):
    """Celda numerica, monoespaciada y alineada a la derecha."""
    f = "DJMB" if bold else "DJM"
    c = ' color="%s"' % color if color else ""
    return Paragraph('<font face="%s"%s>%s</font>' % (f, c, v), celln)

def act(code, title):
    badge = Paragraph('<font face="DJMB" size="8.6" color="#2B6CAB">%s</font>' % code, cell)
    t = Table([[badge, Paragraph(title, hact)]], colWidths=[26, CW-26], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),0), ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),1), ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("BACKGROUND",(0,0),(0,0), MESHBG), ("BOX",(0,0),(0,0),0.5,MESHED),
        ("ALIGN",(0,0),(0,0),"CENTER"), ("LEFTPADDING",(1,0),(1,0),8),
    ]))
    return t

def ans(items):
    return [Paragraph('<font face="DJMB" size="8.4" color="#2B6CAB">%s)</font>  %s'
                      % (lab, md(txt)), ansst) for lab, txt in items]

def callout(tag, paras, accent=MESH, bg=None):
    inner = []
    if tag:
        inner.append(Paragraph('<font face="DJB" size="7.4" color="#%s">%s</font>'
                               % (accent.hexval()[2:], tag), notest))
    inner += [Paragraph(md(p), notest) for p in paras]
    t = Table([[inner]], colWidths=[CW], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), bg or colors.HexColor("#F7FAFD")),
        ("LINEBEFORE",(0,0),(0,-1), 2.2, accent),
        ("BOX",(0,0),(-1,-1),0.5,RULE),
        ("LEFTPADDING",(0,0),(-1,-1),9), ("RIGHTPADDING",(0,0),(-1,-1),9),
        ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
    ]))
    return t

def sp(h=6): return Spacer(1, h)

story = []; A = story.append

# =========================================================== encabezado
A(Paragraph("UNIVERSIDAD SIGLO 21 · CLAVE DOCENTE", eyeb))
A(Paragraph("Team teaching «Diseñá tu propio fármaco»",
            S("tt", fontName="DJB", fontSize=12, leading=15, textColor=MESH, spaceAfter=7)))
A(Paragraph("Clave docente", h1))
A(callout("No repartir a los estudiantes", [
    "Complemento de la guía de actividades. Todos los valores salen de `data.json` y "
    "`analogs.json`, y son salida directa de AutoDock Vina 1.2.5: si se regeneran los datos, "
    "hay que revisar esta clave.",
], accent=NEG, bg=NEGBG))
A(sp(8))
A(callout("Cronograma sugerido", [
    "**90 min:** Parte A 45 · Parte B 35 · cierre 10.",
    "Si hay solo **60 min**, recortar A4 y B5 y dar A7 como tarea. El núcleo irreductible "
    "es **A2 + A6 + B3**.",
]))
A(sp(12))

# =========================================================== PARTE A
A(Rule(CW))
A(Paragraph("Parte A — Pestaña %s" % ui("Pose"), hpart))
A(sp(8))

# ---- A1
A(act("A1", "Indinavir, control"))
A(table(["", "Score", "RMSD"], [
    ["**Indinavir, pose #1**", N("−11,62", bold=True), N("0,60 Å", POS.hexval(), True)],
], [CW-220, 110, 110]))
A(sp(5))
for p in ans([
    ("a", "Acierto. Criterio: RMSD ≤ 2 Å, el umbral convencional en la literatura."),
    ("b", "Es *redocking*: el receptor ya está moldeado alrededor de **esa** molécula (cadenas "
          "laterales, aperturas de flaps, todo el ajuste inducido ya ocurrió). Es un control de "
          "que la cañería funciona, no una prueba de capacidad predictiva. En esta app **solo "
          "indinavir y erlotinib** son nativos de su receptor; los otros 18 son *cross-docking*, "
          "que es el caso realista."),
]): A(p)
A(sp(9))

# ---- A2
A(act("A2", "Erlotinib — el caso central"))
A(table(["", "Rango", "Score", "RMSD"], [
    ["Mejor puntuada", N("#1"), N("−7,21"), N("7,90 Å", NEG.hexval(), True)],
    ["Más parecida al cristal", N("#5", MESH.hexval(), True), N("−6,93"), N("1,43 Å", POS.hexval(), True)],
], [CW-270, 80, 90, 100]))
A(sp(5))
for p in ans([
    ("a", "**0,28 kcal/mol** — muy por debajo del error de la función (≈1–2 kcal/mol)."),
    ("b", "Fallo de **puntuación**. La búsqueda encontró la pose correcta y la puso en la lista; "
          "lo que falló fue el orden. El dato que lo cierra: se repite con *exhaustiveness* 8, 32 "
          "y 64 y con tres semillas distintas, así que no es fluctuación del muestreo."),
    ("c", "Se habría elegido la #1, que está mal. **Sin el cristal no hay forma de saberlo**: ese "
          "es el punto incómodo de toda la clase. Salidas parciales: consenso entre funciones de "
          "puntuación, coherencia con la SAR conocida, inspección de contactos esperados (acá, el "
          "puente con la bisagra Met769)."),
    ("d", "En EGFR, con el setup estándar, llevan **“top pose off”** **siete de diez**: erlotinib, "
          "gefitinib, lapatinib, osimertinib, AEE788, afatinib y TAK-285. Los tres restantes no es "
          "que acierten: neratinib y el pirrolotriazina W2R tienen la pose cristalográfica **fuera "
          "de la caja** (la app no los juzga, y muestra el aviso correspondiente), y dacomitinib "
          "**no tiene referencia cristalográfica** en el conjunto. Vale hacer notar que afatinib "
          "entra en la lista por 2,74 Å, apenas pasado el umbral: no es el mismo tipo de fallo que "
          "los 11 Å de osimertinib."),
]): A(p)
A(sp(9))

# ---- A3
A(act("A3", "Exhaustiveness"))
A(table(["Setup", "Score", "RMSD"], [
    ["exh 8",  N("−7,21"), N("7,90 Å")],
    ["exh 32", N("−7,21"), N("7,90 Å")],
], [CW-220, 110, 110]))
A(sp(5))
for p in ans([
    ("a", "Idéntico. Coherente con A2: si la búsqueda ya encontraba la pose correcta, buscar "
          "cuatro veces más no puede arreglar un problema de puntuación."),
    ("b", "Sirve cuando el fallo **sí** es de búsqueda: ligandos muy flexibles (muchos enlaces "
          "rotables), cajas grandes, docking a ciegas. Regla útil: subir *exhaustiveness* si "
          "repeticiones con distinta semilla dan poses distintas; si convergen a la misma pose "
          "equivocada, el problema es el score."),
]): A(p)
A(sp(9))

# ---- A4
A(act("A4", "La caja"))
A(Paragraph("Indinavir, HIV-1 proteasa:", body))
A(table(["Setup", "Score", "RMSD", "Aviso"], [
    ["“Standard, 24 A, exh 8”",  N("−11,62"), N("0,60 Å", POS.hexval()),  N("no")],
    ["“Mis-centred by 6 A”",     N("−10,66"), N("10,67 Å", NEG.hexval()), N("sí", NEG.hexval(), True)],
    ["“Blind, whole protein”",   N("−11,55"), N("0,62 Å", POS.hexval()),  N("no")],
], [CW-260, 90, 90, 80]))
A(sp(5))
for p in ans([
    ("a", "Porque el aviso **“The crystal pose is outside this box”** dice que la respuesta "
          "correcta estaba **fuera del espacio de búsqueda**: era inalcanzable, y la función de "
          "puntuación nunca llegó a evaluarla. Es un fallo de **preparación**, y confundirlo con "
          "un fallo de scoring es el error clásico. En ese setup **10 ligandos** quedan con la "
          "pose cristalográfica fuera de caja."),
    ("b", "No exige conocer el sitio (útil para blancos nuevos o sitios alostéricos), pero el "
          "volumen enorme diluye el muestreo y agrega mínimos falsos: la mediana de RMSD sube a "
          "**8,94 Å**, la peor del conjunto junto con la caja descentrada. Indinavir igual "
          "acierta, lo cual muestra que un buen caso no valida el método."),
    ("c", "Una caja chica recorta el espacio accesible y puede excluir parte de la pose correcta "
          "o impedir la orientación adecuada: con “Tight box, 18 A” hay **6 ligandos** con la "
          "referencia fuera de caja. Curiosamente su mediana de RMSD (5,75 Å) es la mejor de las "
          "cajas secas, porque restringir ayuda a los que sí entran — buen disparador de "
          "discusión sobre métricas agregadas."),
]): A(p)
A(sp(4))
A(Paragraph(md("**Medianas de RMSD top-1** (para proyectar, si se quiere cerrar la parte):"), body))
A(table(["Setup", "Mediana", "Referencia fuera de caja"], [
    ["Tight box, 18 A",        N("5,75"), N("6")],
    ["Standard, 24 A, exh 8",  N("7,01"), N("2")],
    ["Standard box, exh 32",   N("7,90"), N("2")],
    ["Loose box, 34 A",        N("7,87"), N("0")],
    ["Mis-centred by 6 A",     N("8,69"), N("10")],
    ["Vinardo scoring",        N("4,98"), N("2")],
    ["Blind, whole protein",   N("8,94"), N("0")],
    ["**Standard + flap water** (solo HIV)", N("3,70", POS.hexval(), True), N("0")],
], [CW-200, 90, 110]))
A(sp(9))

# ---- A5
A(act("A5", "Vinardo"))
A(table(["Ligando", "Setup", "Score", "RMSD"], [
    ["Erlotinib",  "Vina estándar", N("−7,21"),  N("7,90 Å")],
    ["Erlotinib",  "Vinardo",       N("−5,32"),  N("3,08 Å", POS.hexval(), True)],
    ["Atazanavir", "Vina estándar", N("−10,15"), N("11,56 Å")],
    ["Atazanavir", "Vinardo",       N("−7,58"),  N("1,30 Å", POS.hexval(), True)],
], [CW-110-90-100, 110, 90, 100]))
A(sp(5))
for p in ans([
    ("a", "El RMSD mejora mucho; los scores se vuelven **sistemáticamente menos negativos**. "
          "Vinardo está calibrado en otra escala."),
    ("b", "Los scores de funciones distintas **no son comparables**: no son energías medidas sino "
          "números en escalas propias. Solo se comparan valores de la misma función, con el mismo "
          "receptor y la misma caja. (Estrictamente, tampoco son comparables entre blancos "
          "distintos.)"),
    ("c", "No mejora todos: lapatinib pasa de 6,60 a 8,45 Å, neratinib de 7,01 a 9,34 Å, el "
          "pirrolotriazina W2R de 7,12 a 10,25 Å. Mejora la **mediana** (7,01 → 4,98 Å), no cada "
          "caso. No existe “la mejor función”; existe la que anda mejor en un sistema dado, y "
          "saber cuál es requiere justamente los datos experimentales que en un proyecto real "
          "todavía no se tienen."),
]): A(p)
A(sp(9))

# ---- A6
A(act("A6", "El agua de los flaps"))
A(table(["Ligando", "Seco", "Con agua", ""], [
    ["Saquinavir",    N("10,21 Å"), N("2,43 Å", POS.hexval(), True),  "mejora drástica"],
    ["Ritonavir",     N("11,76 Å"), N("3,34 Å", POS.hexval(), True),  "mejora drástica"],
    ["Darunavir",     N("4,78 Å"),  N("3,74 Å"),                      "mejora"],
    ["Amprenavir",    N("4,50 Å"),  N("3,67 Å"),                      "mejora"],
    ["DMP323",        N("6,14 Å"),  N("4,36 Å"),                      "mejora"],
    ["Indinavir",     N("0,60 Å"),  N("0,61 Å"),                      "sin cambio (ya acertaba)"],
    ["**Tipranavir**", N("2,31 Å", None, True), N("10,77 Å", NEG.hexval(), True), "**empeora**"],
], [CW-90-90-150, 90, 90, 150]))
A(sp(5))
for p in ans([
    ("a", "La mejora más grande de toda la guía viene de **devolver tres moléculas de agua al "
          "receptor**, no de ningún parámetro de docking: la mediana de RMSD en HIV-1 proteasa "
          "pasa de **5,46 Å a 3,70 Å**. Es el mensaje central de la clase — la preparación del "
          "receptor pesa más que el ajuste fino de parámetros."),
    ("b", "HOH 308 hace de puente: acepta de ambos NH de Ile50/Ile50' y dona al carbonilo del "
          "ligando. Los inhibidores **peptidomiméticos** se unen *a través* de esa agua, y sin "
          "ella pierden dos puentes de hidrógeno y se acomodan mal. **Tipranavir es no peptídico "
          "y desplaza esa agua**, contactando los NH directamente: al reponerla, el sitio le "
          "queda bloqueado. Una decisión de preparación puede ser correcta para un ligando e "
          "incorrecta para otro del mismo sitio. *Matiz honesto:* DMP323 (urea cíclica) también "
          "desplaza esa agua y sin embargo mejora un poco — no es una dicotomía limpia, y decirlo "
          "es parte de la lección sobre datos reales."),
    ("c", "Porque el criterio automático (`pipeline/prep_wet.py`: aguas a menos de 3,6 Å del "
          "ligando nativo y con ≥2 contactos polares a proteína) **no selecciona ninguna en "
          "1M17**. La app omite el setup en vez de docar contra un receptor distinto y no avisar."),
]): A(p)
A(sp(9))

# ---- A7
A(act("A7", "Score vs. potencia"))
A(table(["Ligando", "Experimental", "ΔG exp. (kcal/mol, 37 °C)", "Score Vina"], [
    ["Lopinavir",  N("Ki 1,3 pM"),   N("−16,86"), N("−10,83")],
    ["Darunavir",  N("Kd 4,5 pM"),   N("−16,09"), N("−8,41", NEG.hexval(), True)],
    ["Tipranavir", N("Ki 8 pM"),     N("−15,74"), N("−10,10")],
    ["Ritonavir",  N("Ki 15 pM"),    N("−15,35"), N("−9,52")],
    ["Saquinavir", N("Ki 0,12 nM"),  N("−14,07"), N("−10,54")],
    ["Atazanavir", N("Ki 0,19 nM"),  N("−13,79"), N("−10,15")],
    ["Indinavir",  N("Ki 0,56 nM"),  N("−13,12"), N("−11,62", MESH.hexval(), True)],
    ["Amprenavir", N("Ki 0,6 nM"),   N("−13,08"), N("−7,97")],
    ["Nelfinavir", N("Ki 2 nM"),     N("−12,34"), N("−10,29")],
], [CW-110-150-90, 110, 150, 90]))
A(sp(5))
A(callout("", ['<font face="DJMB" size="10">Spearman ρ = −0,02 (n = 9)</font>'
               '<font size="9" color="#57697B">   correlación nula</font>'], accent=NEG))
A(sp(5))
for p in ans([
    ("a", "No coinciden en absoluto. **Darunavir**, el más potente (4,5 pM, ≈3000 veces más que "
          "indinavir), obtiene el **peor score menos uno**; **indinavir**, de los más flojos de la "
          "lista, obtiene **el mejor**. El rango experimental cubre ~4,5 kcal/mol y el de los "
          "scores 3,7: no es que la señal sea chica, es que está desordenada."),
    ("b", "Usos legítimos: (i) **enriquecimiento** en cribado virtual — ordenar 10<super>6</super> "
          "compuestos para que el 1 % que se compra tenga más activos que al azar, sin creerse el "
          "orden interno; (ii) **generar hipótesis estructurales** sobre el modo de unión, para "
          "después testearlas con mutagénesis o SAR; (iii) filtrar lo groseramente imposible "
          "(choques estéricos, moléculas que no entran). Lo que **no** es: un predictor de "
          "afinidad ni un sustituto de medirla."),
]): A(p)

# =========================================================== PARTE B
A(sp(12)); A(Rule(CW))
A(Paragraph("Parte B — Pestaña %s" % ui("Design"), hpart))
A(sp(8))

# ---- B1
A(act("B1", "Landmarks"))
for p in ans([
    ("a", "ethynyl + 2-methoxyethoxy = **erlotinib** (Tarceva), exacto. Score **−7,25**. "
          "*Control de calidad del dataset:* la misma molécula, docada por el camino "
          "independiente de la Parte A, da −7,21. **0,04 kcal/mol de diferencia.**"),
    ("b", "chloro + 3-morpholinopropoxy = **similar a gefitinib** (Iressa); score **−7,54**. La "
          "app lo etiqueta *Gefitinib-like*, no gefitinib, y con razón: al gefitinib real le falta "
          "acá el **4-fluoro** de la anilina (es 3-Cl-4-F) y en la posición 7 lleva un **metoxi**, "
          "no el 2-metoxietoxi fijo de este andamio. El morfolinopropoxi en la posición 6 sí es el "
          "mismo."),
    ("c", "Núcleo desnudo PM 295,3 → erlotinib PM 393,4: **+98 Da**."),
]): A(p)
A(sp(3))
A(callout("Ojo con el “núcleo desnudo”", [
    "No es una 4-anilinoquinazolina pelada: el andamio lleva **fijo un 2-metoxietoxi en la "
    "posición 7** (por eso PM 295,3 y no 221). Es la parte que erlotinib y gefitinib comparten y "
    "que la app no deja variar. Si alguien pregunta por qué el dibujo de `hydrogen + hydrogen` ya "
    "tiene una cadena colgando, la respuesta es esa.",
    "Consecuencia útil: al construir erlotinib, la molécula termina con **dos** 2-metoxietoxi, el "
    "fijo en 7 y el que se eligió en R2 — que es exactamente la estructura del fármaco.",
], accent=AMB, bg=AMBBG))
A(sp(9))

# ---- B2
A(act("B2", "Vectores"))
for p in ans([
    ("a", "**“Bulky”** salta cuando R1 agrega ≥6 átomos pesados: *phenyl*. Advierte sobre "
          "**Thr766**, el *gatekeeper* que limita el acceso al bolsillo posterior. (Es el mismo "
          "residuo que muta a Met en la resistencia T790M — vale mencionarlo.)"),
    ("b", "**“Mismatch”** salta con TPSA ≥20 en R1. Un grupo polar en solución está rodeado de "
          "aguas que lo solvatan; para entrar a un bolsillo hidrofóbico hay que **arrancarle esa "
          "capa de hidratación**, y el bolsillo no ofrece nada que compense esa pérdida — no hay "
          "dadores ni aceptores con quién reemplazarla. El balance neto es desfavorable aunque la "
          "molécula “entre”."),
    ("c", "Porque R2 apunta al **solvente**: el grupo queda hidratado, no hay que desolvatarlo, y "
          "la afinidad es poco sensible a lo que se cuelgue ahí. Es donde se paga solubilidad "
          "barata. La app tiene una advertencia (**“Wasted”**) para cuando se cuelga ahí algo "
          "grande y grasoso —gasta logP sin comprar afinidad—, pero **ninguno de los ocho R2 de "
          "este conjunto la dispara**: todos se unen por oxígeno y ninguno agrega lipofilia "
          "suficiente. Si algún grupo aumenta la lipofilia en R2, es el morfolinopropoxi, y apenas "
          "(+0,10 de logP)."),
    ("d", "Con **“Pocket residues, by H-bond role”**: rojo = acepta (Asp, Glu) → hay que ofrecerle "
          "un **N-H u O-H**; azul = dona (Arg, **Lys721**, Trp) → ofrecerle un **N u O**; violeta "
          "= ambos (Ser, **Thr766**, Tyr…); dorado = hidrofóbico → algo graso. Respuesta esperada: "
          "contra Lys721, un aceptor; contra Thr766, puede ser cualquiera de los dos, pero es "
          "angosto, así que primero conviene ser chico."),
]): A(p)
A(sp(3))
A(callout("Dato para cerrar B2", [
    "La combinación que dispara el mensaje verde **“Sensible”** —chico y graso atrás, polaridad "
    "hacia el solvente— incluye exactamente a erlotinib (ethynyl + 2-metoxietoxi). La regla "
    "heurística y el fármaco real coinciden, lo cual no es casualidad: la regla se escribió "
    "mirando la SAR de esta familia.",
], accent=POS))
A(sp(9))

# ---- B3
A(act("B3", "Docking de análogos"))
A(table(["Referencia", "Score"], [
    ["Erlotinib (ethynyl + 2-methoxyethoxy)",   N("−7,25", None, True)],
    ["Núcleo desnudo (hydrogen + hydrogen)",    N("−7,30", None, True)],
    ["Mejor de los 96 (phenyl + carboxamida)",  N("−8,48", POS.hexval(), True)],
    ["Peor de los 96 (methoxy + 2-methoxyethoxy)", N("−6,64", NEG.hexval(), True)],
], [CW-120, 120]))
A(sp(5))
for p in ans([
    ("a", "Del núcleo desnudo (−7,30) al mejor (−8,48): **1,18 kcal/mol** ganadas agregando "
          "**9 átomos pesados** (22 → 31) y 119 Da. Poco retorno para tanto tamaño, y esa es la "
          "idea."),
    ("b", "**El núcleo desnudo puntúa mejor que erlotinib** (−7,30 vs. −7,25), con siete átomos "
          "pesados menos. Si la serie se ordenara por score, el punto de partida le ganaría al "
          "fármaco aprobado. La diferencia (0,05 kcal/mol) es ruido: el resultado correcto de leer "
          "esa tabla es **“son indistinguibles”**."),
    ("c", "Los 96 caben en **1,84 kcal/mol** (−6,64 a −8,48), menos que el error típico de la "
          "función. Honestamente: se pueden separar **extremos** (los mejores diez de los peores "
          "diez, con reservas) y **no** se puede afirmar que el análogo #1 sea mejor que el #12. "
          "Comparaciones de 0,1–0,3 kcal/mol entre análogos vecinos no significan nada."),
]): A(p)
A(sp(4))
A(Paragraph(md("**Promedios por sustituyente** (por si sale la pregunta de cuál vector “manda”):"),
            body))
R1M = [("phenyl","−8,07"),("trifluorometilo","−7,80"),("hydroxyl","−7,69"),("ethynyl","−7,68"),
       ("nitrilo","−7,65"),("fluoro","−7,64"),("methyl","−7,62"),("ciclopropilo","−7,61"),
       ("chloro","−7,52"),("hydrogen","−7,40"),("bromo","−7,38"),("methoxy","−7,18")]
R2M = [("hydroxyl","−7,98"),("carboxamida","−7,92"),("2-piperazinyletoxi","−7,90"),
       ("hydrogen","−7,73"),("3-morfolinopropoxi","−7,62"),("methoxy","−7,31"),
       ("2-dimetilaminoetoxi","−7,25"),("**2-metoxietoxi**","−7,11")]
rows = []
for k in range(12):
    a1, v1 = R1M[k]
    if k < len(R2M):
        a2, v2 = R2M[k]
        bold = a2.startswith("**")
        rows.append([a1, N(v1), a2, N(v2, AMB.hexval() if bold else None, bold)])
    else:
        rows.append([a1, N(v1), "", ""])
A(table(["R1 (mejor→peor)", "⟨score⟩", "R2 (mejor→peor)", "⟨score⟩"], rows,
        [CW/2-70, 70, CW/2-70, 70]))
A(sp(4))
A(Paragraph(md("Obsérvese que el “mejor” R1 es el más grande (phenyl) y el “mejor” R2 es el más "
               "chico con oxígeno (hydroxyl): el score está siguiendo **tamaño y contactos**, no "
               "química fina."), body))
A(sp(9))

# ---- B4
A(act("B4", "Eficiencia de ligando"))
A(table(["Análogo", "Score", "Át. pesados", "LE"], [
    ["methyl + hydroxyl",            N("−8,15"), N("24"), N("−0,340", POS.hexval(), True)],
    ["phenyl + 3-morpholinopropoxy", N("−8,18"), N("38"), N("−0,215", NEG.hexval(), True)],
    ["Núcleo desnudo",               N("−7,30"), N("22"), N("−0,332")],
    ["Erlotinib",                    N("−7,25"), N("29"), N("−0,250")],
], [CW-90-100-100, 90, 100, 100]))
A(sp(5))
for p in ans([
    ("a", "Por **score** ganan casi empatados (0,03 kcal/mol: indistinguibles). Por **LE**, "
          "*methyl + hydroxyl* gana por lejos: **−0,340 vs. −0,215**, con 14 átomos menos. Los dos "
          "criterios eligen moléculas distintas."),
    ("b", "Cada átomo agregado casi siempre baja algo el score (más superficie de contacto), así "
          "que el score **premia el tamaño casi automáticamente** y una serie ordenada por score "
          "tiende a ordenarse por peso molecular. Partiendo de fragmentos con LE alta queda "
          "**presupuesto de tamaño** para crecer después hacia potencia manteniendo el compuesto "
          "en rango oral. Crecer desde un punto de partida de LE baja lleva a moléculas grandes, "
          "insolubles y con mala farmacocinética. Umbral habitual de referencia: LE ≥ 0,3."),
]): A(p)
A(sp(9))

# ---- B5
A(act("B5", "El costo de crecer"))
for p in ans([
    ("a", "El aviso **“Heavy”** aparece con **PM > 500**. *phenyl + 3-morfolinopropoxi* pesa "
          "**514,6** y además tiene **logP 5,17**, así que rompe **dos** reglas de Lipinski "
          "(PM ≤ 500 y logP ≤ 5), con 12 enlaces rotables. Solo **4 de los 96** análogos superan "
          "500: Br+PZE (502,4), CF3+MPO (506,5), Ph+MPO (514,6) y Br+MPO (517,4). Regla de "
          "Lipinski completa: PM ≤ 500, logP ≤ 5, dadores de H ≤ 5, aceptores ≤ 10."),
    ("a bis", "*phenyl + 2-piperazinyletoxi* pesa **499,6** y no dispara nada, pese a ser "
              "prácticamente la misma molécula (un CH2 y un O de diferencia). Las reglas de "
              "Lipinski son **descripciones estadísticas** de fármacos orales comerciales, no "
              "leyes: 499 y 515 no describen compuestos con destinos distintos. Se usan como "
              "semáforo de atención, no como criterio de descarte —y muchos fármacos aprobados, "
              "incluidos varios inhibidores de la Parte A, las violan."),
    ("b", "No necesariamente. El score no mide **solubilidad acuosa**, **permeabilidad**, "
          "**estabilidad metabólica**, **selectividad** frente a otras quinasas, **toxicidad**, "
          "ni el **costo entrópico** de los enlaces rotables. Tampoco mide biodisponibilidad "
          "oral, que es lo que decide si el compuesto llega a ser comprimido. Dos bastan para la "
          "respuesta."),
    ("c", "El 2-metoxietoxi de erlotinib puntúa **peor** en promedio que el hidroxilo "
          "(−7,11 vs. −7,98) y aun así es el que está en el fármaco. Razones esperadas: "
          "**(1)** sale al solvente, donde la afinidad importa poco y se optimiza otra cosa: los "
          "dos éteres mejoran **solubilidad** y perfil farmacocinético; **(2)** un **hidroxilo "
          "fenólico es un pasivo metabólico** — se glucuronida y sulfata rápido (fase II), "
          "acortando la vida media, y el éter lo evita; **(3)** un OH agrega un **dador** de "
          "puente de hidrógeno que hay que desolvatar y que puede penalizar la permeabilidad de "
          "membrana; **(4)** esa posición es el **punto de enganche sintético** para linkers y "
          "profármacos; **(5)** el score **no ve nada de esto**: optimiza una sola dimensión de "
          "las muchas que definen un fármaco."),
]): A(p)

# =========================================================== CIERRE
A(sp(12)); A(Rule(CW))
A(Paragraph("Cierre — respuestas esperadas", hpart))
A(sp(8))
for k, txt in enumerate([
    "**Búsqueda vs. puntuación:** si la pose correcta **aparece** entre las nueve pero mal "
    "ranqueada → falló la puntuación (erlotinib, A2). Si **no aparece en ninguna** → falló la "
    "búsqueda o la caja, y hay que revisar el aviso de pose fuera de caja antes de culpar al "
    "score (A4).",
    "**La decisión de mayor impacto:** la preparación del receptor — tres aguas (A6) valen más "
    "que cuadruplicar la búsqueda (A3) o elegir función (A5).",
    "**Frente a −9,5 kcal/mol:** se puede afirmar que la molécula **entra** en el sitio sin "
    "choques y que hay al menos un modo de unión geométricamente plausible. **No** se puede "
    "afirmar que se una con más fuerza que otra de −8,5 (A7: ρ ≈ 0), ni que la pose mostrada sea "
    "la real (A2), ni convertir ese número a una constante de disociación.",
], 1):
    A(Paragraph('<font face="DJMB" size="8.4" color="#2B6CAB">%d.</font>  %s' % (k, md(txt)), ansst))

A(sp(10))
A(Paragraph("Puntos de fricción previsibles", hpart))
A(sp(6))
A(callout("Atención — dos fallas de la app que van a aparecer en clase", [
    "**No hacer clic en “Dacomitinib”.** Es el único ligando sin pose cristalográfica de "
    "referencia, y hoy la app **se rompe** al seleccionarlo: `renderPoses()` hace "
    "`p.rmsdToRef.toFixed(2)` sobre un `null` y lanza una excepción, con lo cual la tabla "
    "**“Poses”** queda vacía y el visor sigue mostrando el ligando anterior. Conceptualmente el "
    "caso es bueno —ausencia de referencia no es resultado negativo— pero hasta que se corrija "
    "conviene saltearlo.",
    "**El setup “Standard + flap water” en EGFR no existe, pero el botón sí.** 1M17 no tiene "
    "aguas puente que califiquen, así que no se corrió esa condición; al apretar ese botón "
    "estando en EGFR, la app **cae silenciosamente** a los resultados de **“Tight box, 18 A”** "
    "sin avisar. La actividad A6 se hace **solo en HIV-1 proteasa**.",
], accent=NEG, bg=NEGBG))
A(sp(7))
for txt in [
    "**“Entonces el docking no sirve.”** Reencuadrar: sirve para **enriquecer** y para **generar "
    "hipótesis**, no para predecir afinidad. El indinavir a 0,60 Å muestra que la física está "
    "bien puesta; lo que no está resuelto es la puntuación. Es una herramienta de triaje, no un "
    "oráculo.",
    "**Comparar scores entre blancos o entre funciones.** Sale sistemáticamente. Cortarlo en A5 "
    "y no dejarlo pasar en B3.",
    "**Caveat que conviene decir en voz alta:** salvo el setup “+ flap water”, todos los "
    "receptores están **sin aguas**, que es lo habitual y es un handicap real.",
    "**Si los scores aparecen con etiqueta ámbar “mock”** en la pestaña Design, la app no cargó "
    "`analogs.json` (típicamente por abrir el archivo sin servidor). Los 96 tienen score real de "
    "Vina. Solución: servir la carpeta (`python3 -m http.server 8000`) o usar el "
    "`docking-bench-standalone.html`, que no necesita servidor.",
    "**Plan B sin internet:** copiar `docking-bench-standalone.html` en un pendrive. Es "
    "autocontenido y anda sin red.",
]:
    A(Paragraph('<font color="#2B6CAB">•</font>  ' + md(txt),
                S("bul", fontSize=8.8, leading=12.4, leftIndent=13, firstLineIndent=-13, spaceAfter=5)))

def deco(canv, doc):
    canv.saveState()
    canv.setFont("DJ", 7.2); canv.setFillColor(DIM)
    canv.drawString(LM, BM - 9, "Clave docente · Diseñá tu propio fármaco · Universidad Siglo 21")
    canv.drawRightString(PW - RM, BM - 9, "%d" % doc.page)
    canv.setStrokeColor(RULE); canv.setLineWidth(0.5)
    canv.line(LM, BM - 3, PW - RM, BM - 3)
    canv.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4,
                      leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                      title="Clave docente — Diseñá tu propio fármaco",
                      author="Universidad Siglo 21", subject="Clave docente")
frame = Frame(LM, BM, CW, PH - TM - BM, id="main",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=deco)])
doc.build(story)
print("OK ->", OUT, os.path.getsize(OUT), "bytes")
