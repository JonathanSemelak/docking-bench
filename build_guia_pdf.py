# -*- coding: utf-8 -*-
"""Genera GUIA-ACTIVIDADES.pdf: la guia del estudiante como PDF rellenable
(AcroForm). Los nombres de los campos coinciden con los ids de la version HTML,
asi que las dos versiones se corresponden campo a campo.

    pip install reportlab
    python3 build_guia_pdf.py

Necesita Liberation Sans y DejaVu Sans Mono instaladas (paquetes
fonts-liberation y fonts-dejavu-core en Debian/Ubuntu). Si el contenido de
GUIA-ACTIVIDADES.md cambia, hay que reflejarlo aca: no se lee el markdown."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, Flowable, KeepTogether)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUIA-ACTIVIDADES.pdf")
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

INK    = colors.HexColor("#131C26")
MESH   = colors.HexColor("#2B6CAB")
MESHBG = colors.HexColor("#EDF3FA")
MESHED = colors.HexColor("#B9D3EA")
RULE   = colors.HexColor("#D5DFEA")
MUTED  = colors.HexColor("#57697B")
DIM    = colors.HexColor("#8497A9")
POS    = colors.HexColor("#1B7F53")
NEG    = colors.HexColor("#BE3A2E")
AMB    = colors.HexColor("#8A5A12")
AMBBG  = colors.HexColor("#FAF0DC")
PANEL  = colors.HexColor("#FFFFFF")

PW, PH = A4
LM = RM = 18 * mm
TM = 16 * mm
BM = 16 * mm
CW = PW - LM - RM          # ancho util ~ 481 pt

def S(name, **kw):
    kw.setdefault("fontName", "DJ")
    kw.setdefault("fontSize", 9.2)
    kw.setdefault("leading", 13.4)
    kw.setdefault("textColor", INK)
    kw.setdefault("alignment", TA_LEFT)
    return ParagraphStyle(name, **kw)

body    = S("body", spaceAfter=6)
small   = S("small", fontSize=8.2, leading=11.6, textColor=MUTED)
tiny    = S("tiny", fontSize=7.4, leading=10, textColor=MUTED)
cell    = S("cell", fontSize=8.4, leading=11.4, spaceAfter=0)
cellb   = S("cellb", fontSize=8.4, leading=11.4, fontName="DJB", spaceAfter=0)
cellh   = S("cellh", fontSize=7.4, leading=10, fontName="DJB", textColor=DIM, spaceAfter=0)
h1      = S("h1", fontName="DJB", fontSize=23, leading=26, spaceAfter=7)
hpart   = S("hpart", fontName="DJB", fontSize=15.5, leading=19, spaceAfter=2)
hact    = S("hact", fontName="DJB", fontSize=11.4, leading=14.6, spaceAfter=1)
eyebrow = S("eyebrow", fontName="DJB", fontSize=7.4, leading=10, textColor=DIM, spaceAfter=4)
qst     = S("qst", fontSize=9.0, leading=12.8, leftIndent=15, firstLineIndent=-15, spaceAfter=4)
step    = S("step", fontSize=9.0, leading=12.8, leftIndent=13, firstLineIndent=-13, spaceAfter=3)
notest  = S("notest", fontSize=8.6, leading=12.2, spaceAfter=4)

def ui(t):    return '<font face="DJM" size="8.2" color="#2B6CAB">%s</font>' % t
def uia(t):   return '<font face="DJM" size="8.2" color="#8A5A12">%s</font>' % t
def num(t):   return '<font face="DJM">%s</font>' % t
def b(t):     return "<b>%s</b>" % t
def i(t):     return "<i>%s</i>" % t

# --------------------------------------------------------------- campos
class Field(Flowable):
    """Un campo de texto AcroForm dentro del flujo de Platypus."""
    def __init__(self, name, width, height=14.5, multiline=False, tip=""):
        Flowable.__init__(self)
        self.name = name; self.width = width; self.height = height
        self.multiline = multiline; self.tip = tip or name
    def wrap(self, aw, ah):
        return (self.width, self.height)
    def draw(self):
        self.canv.acroForm.textfield(
            name=self.name, tooltip=self.tip, relative=True,
            x=0, y=0, width=self.width, height=self.height,
            borderStyle="underlined", borderWidth=0.8,
            borderColor=MESHED, fillColor=MESHBG, textColor=INK,
            fontName="Helvetica", fontSize=9,
            fieldFlags="multiline" if self.multiline else "",
            forceBorder=True, maxlen=400 if self.multiline else 60,
        )

class Rule(Flowable):
    def __init__(self, w, thickness=2, color=MESH, space=5):
        Flowable.__init__(self); self.w=w; self.t=thickness; self.c=color; self.space=space
    def wrap(self, aw, ah): return (self.w, self.t + self.space)
    def draw(self):
        self.canv.setStrokeColor(self.c); self.canv.setLineWidth(self.t)
        self.canv.line(0, self.space, self.w, self.space)

# --------------------------------------------------------------- helpers
GRID = TableStyle([
    ("GRID",        (0,0), (-1,-1), 0.5, RULE),
    ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#EAF0F7")),
    ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
    ("RIGHTPADDING",(0,0), (-1,-1), 6),
    ("TOPPADDING",  (0,0), (-1,-1), 4),
    ("BOTTOMPADDING",(0,0),(-1,-1), 4),
])

def table(header, rows, widths, style=None):
    data = [[Paragraph(h, cellh) for h in header]] + rows
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(style or GRID)
    return t

def act(code, title, mins=None):
    """Encabezado de actividad: codigo | titulo."""
    badge = Paragraph('<font face="DJMB" size="8.6" color="#2B6CAB">%s</font>' % code, cell)
    t = Table([[badge, Paragraph(title, hact)]],
              colWidths=[26, CW - 26], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),0), ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),1), ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("BACKGROUND",(0,0),(0,0), MESHBG), ("BOX",(0,0),(0,0),0.5,MESHED),
        ("ALIGN",(0,0),(0,0),"CENTER"),
        ("LEFTPADDING",(1,0),(1,0),8),
    ]))
    return t

def qs(items):
    out = []
    for lab, txt in items:
        out.append(Paragraph('<font face="DJMB" size="8.4" color="#2B6CAB">%s)</font>  %s'
                             % (lab, txt), qst))
    return out

def steps(items):
    out = []
    for n, txt in enumerate(items, 1):
        out.append(Paragraph('<font face="DJMB" size="8.4" color="#2B6CAB">%d.</font>  %s'
                             % (n, txt), step))
    return out

def callout(tag, paras, accent=MESH, bg=None):
    inner = [Paragraph('<font face="DJB" size="7.4" color="#%s">%s</font>'
                       % (accent.hexval()[2:], tag), notest)] if tag else []
    inner += [Paragraph(p, notest) for p in paras]
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

# --------------------------------------------------------------- documento
story = []
A = story.append

# ---- portada / encabezado
A(Paragraph("UNIVERSIDAD SIGLO 21 · GUÍA DE ACTIVIDADES", eyebrow))
A(Paragraph("Team teaching «Diseñá tu propio fármaco»",
            S("tt", fontName="DJB", fontSize=12, leading=15, textColor=MESH, spaceAfter=7)))
A(Paragraph("Docking molecular:<br/>lo que el score no dice", h1))
A(Paragraph("Resultados %s de AutoDock Vina 1.2.5 sobre dos blancos terapéuticos. Nada acá está "
            "simulado ni maquillado: los casos que funcionan y los que fracasan son los que dio "
            "el programa." % b("reales"),
            S("lede", fontSize=10, leading=14.5, textColor=MUTED, spaceAfter=10)))

A(table(["Blancos", "Ligandos", "App"],
        [[Paragraph(num("1HSG · 1M17"), cell),
          Paragraph("20 inhibidores + 96 análogos", cell),
          Paragraph('<link href="https://jonathansemelak.github.io/docking-bench/">'
                    '<font color="#2B6CAB">jonathansemelak.github.io/docking-bench</font></link>', cell)]],
        [90, 160, CW - 250]))
A(sp(9))

A(table(["Estudiantes", "Fecha"],
        [[Field("pareja", 250), Field("fecha", CW - 250 - 12 - 4)]],
        [250 + 12, CW - 250 - 12]))
A(sp(9))

A(callout("Cómo se completa este PDF", [
    "Este archivo es un %s: los recuadros celestes se escriben directamente en Acrobat Reader, "
    "en Vista Previa (Mac) o en el propio navegador. %s con otro nombre antes de cerrar, "
    "o lo escrito se pierde." % (b("formulario"), b("Guardar una copia")),
    "La interfaz de la aplicación está %s. Acá los nombres de botones, pestañas y columnas "
    "van en inglés y en tipografía de máquina, tal como se leen en pantalla: %s."
    % (b("en inglés"), ui("Docking setup")),
], accent=AMB, bg=AMBBG))
A(sp(10))

# ---- que se hace
A(Paragraph("QUÉ SE HACE EN ESTA CLASE", eyebrow))
A(Paragraph("El docking molecular (acoplamiento molecular) intenta responder dos preguntas "
            "distintas, y conviene no confundirlas nunca:", body))
A(Paragraph('<font face="DJMB" size="8.4" color="#2B6CAB">1.</font>  %s Es un problema de %s, '
            'y se mide con el %s contra la estructura cristalográfica.'
            % (b("¿Dónde y cómo se une el ligando?"), b("búsqueda"), b("RMSD")), step))
A(Paragraph('<font face="DJMB" size="8.4" color="#2B6CAB">2.</font>  %s Es un problema de %s '
            '(%s), y se mide con el %s, en kcal/mol.'
            % (b("¿Con qué fuerza se une?"), b("puntuación"), i("scoring"), b("score")), step))
A(sp(3))
A(Paragraph("Van a trabajar sobre la %s (PDB 1HSG) y el %s (PDB 1M17)."
            % (b("proteasa de HIV-1"), b("dominio quinasa de EGFR")), body))
A(sp(4))

A(Paragraph("VOCABULARIO MÍNIMO", eyebrow))
A(table(["Término", "Qué es", "Regla práctica"], [
    [Paragraph(b("Pose"), cell), Paragraph("Una orientación y conformación propuesta del ligando en el sitio", cell), Paragraph("La app muestra 9 por ligando", cell)],
    [Paragraph(b("Score"), cell), Paragraph("Energía libre de unión estimada, en kcal/mol", cell), Paragraph("Más negativo = predicho como mejor unión", cell)],
    [Paragraph(b("RMSD"), cell), Paragraph("Desviación cuadrática media respecto de la pose cristalográfica, en Å", cell), Paragraph("Ver la escala de abajo", cell)],
    [Paragraph(b("Caja de búsqueda"), cell), Paragraph("El volumen dentro del cual el programa puede buscar (%s)" % ui("Search box"), cell), Paragraph("Si la respuesta queda afuera, es imposible acertar", cell)],
    [Paragraph(b("LE"), cell), Paragraph("%s: score dividido por número de átomos pesados" % i("Ligand efficiency"), cell), Paragraph("Corrige el premio automático al tamaño", cell)],
], [78, CW - 78 - 150, 150]))
A(sp(7))

leg = Table([[Paragraph('<font face="DJMB" color="#1B7F53">≤ 2 Å</font><br/>'
                        '<font size="8" color="#57697B">Acierto</font>', cell),
              Paragraph('<font face="DJMB" color="#8A5A12">2 – 4 Å</font><br/>'
                        '<font size="8" color="#57697B">Parcial</font>', cell),
              Paragraph('<font face="DJMB" color="#BE3A2E">&gt; 4 Å</font><br/>'
                        '<font size="8" color="#57697B">Fallo</font>', cell)]],
            colWidths=[CW/3.0]*3, hAlign="LEFT")
leg.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,RULE),
                         ("LEFTPADDING",(0,0),(-1,-1),9), ("TOPPADDING",(0,0),(-1,-1),6),
                         ("BOTTOMPADDING",(0,0),(-1,-1),6)]))
A(leg)
A(sp(6))
A(Paragraph("En el visor 3D: %s = pose calculada (%s) · %s = pose cristalográfica (%s). "
            "En la tabla %s, el RMSD se colorea solo con esa misma escala."
            % ('<font color="#4A8FD4">' + b("azul claro") + "</font>", ui("docked pose"),
               '<font color="#1B7F53">' + b("verde") + "</font>", ui("crystal reference"),
               ui("Poses")), small))

# =============================================================== PARTE A
A(sp(14)); A(Rule(CW, 2.5, MESH))
A(Paragraph("Parte A · Pestaña %s" % ui("Pose"), hpart))
A(Paragraph("Siete actividades sobre fármacos ya conocidos", small))
A(sp(6))

A(callout("Orientación rápida", [
    "En la barra superior: el selector de modo %s / %s y, a su derecha, los dos blancos "
    "(%s y %s). En el panel izquierdo, %s (las ocho condiciones de cálculo) y %s "
    "(los diez ligandos). El visor 3D ocupa el centro. El panel derecho, de arriba abajo: "
    "la tabla %s (columnas %s), los datos del ligando y las casillas %s."
    % (ui("Pose"), ui("Design"), ui("HIV-1 protease"), ui("EGFR kinase domain"),
       ui("Docking setup"), ui("Ligand library"), ui("Poses"),
       i("Rank, Score, RMSD, LE"), ui("Display")),
    "%s modo %s, setup %s, y la casilla %s activada."
    % (b("Punto de partida:"), ui("Pose"), uia("Standard, 24 A, exh 8"), ui("Crystal reference pose")),
]))
A(sp(10))

# ---- A1
A(act("A1", "El control que hay que hacer siempre", 5))
A(Paragraph("Blanco %s, ligando %s (aparece etiquetado %s: es el ligando que venía en ese cristal)."
            % (ui("HIV-1 protease"), ui("Indinavir"), i("redocked")), body))
for s_ in steps(["Anotar el score y el RMSD de la pose %s." % num("#1"),
                 "Girar el visor y comparar la pose azul con la verde."]): A(s_)
A(sp(3))
A(table(["", "Score (kcal/mol)", "RMSD (Å)"],
        [[Paragraph(b("Indinavir, pose #1"), cell), Field("a1s", 120), Field("a1r", 120)]],
        [CW - 264, 132, 132]))
A(sp(5))
for q in qs([("a", "¿Este resultado es un acierto o un fallo? ¿Con qué criterio lo deciden?"),
             ("b", "Este cálculo se llama %s: se saca el ligando de su propio cristal y se lo vuelve "
                   "a colocar. ¿Por qué un resultado así %s demuestra que el método vaya a funcionar "
                   "con una molécula nueva?" % (i("redocking"), b("no")))]): A(q)
A(sp(10))

# ---- A2
A(act("A2", "El caso central: el mejor score en el lugar equivocado", 12))
A(Paragraph("Cambiar el blanco a %s y elegir %s (también %s: 1M17 es su propio cristal)."
            % (ui("EGFR kinase domain"), ui("Erlotinib"), i("redocked")), body))
for s_ in steps(["Anotar score y RMSD de la pose %s." % num("#1"),
                 "Recorrer la tabla %s completa, haciendo clic en cada fila y mirando cómo se "
                 "mueve la molécula azul respecto de la verde." % ui("Poses"),
                 "Encontrar %s de las nueve, y anotar su rango y su score."
                 % b("la pose de menor RMSD")]): A(s_)
A(sp(3))
A(table(["", "Rango", "Score", "RMSD"], [
    [Paragraph(b("Pose mejor puntuada"), cell), Paragraph(num("#1"), cell), Field("a2s1", 95), Field("a2r1", 95)],
    [Paragraph(b("Pose más parecida al cristal"), cell), Field("a2k", 95), Field("a2s2", 95), Field("a2r2", 95)],
], [CW - 321, 107, 107, 107]))
A(sp(5))
for q in qs([("a", "¿Cuántas kcal/mol separan a esas dos poses?"),
             ("b", "El programa %s la pose correcta pero la %s por debajo de otras cuatro. "
                   "¿Esto es un fallo de búsqueda o de puntuación? Justificar."
                   % (b("encontró"), b("ranqueó"))),
             ("c", "Si esta molécula fuera desconocida y no existiera el cristal para compararla, "
                   "¿qué pose habrían elegido? ¿Cómo se habrían dado cuenta del error?"),
             ("d", "Leer el aviso rojo %s del panel derecho. En la lista de ligandos, contar cuántos "
                   "llevan la etiqueta roja %s en este blanco."
                   % (ui("Best score, wrong pose"), ui("top pose off")))]): A(q)
A(sp(10))

# ---- A3
A(act("A3", "¿Y si buscamos más?", 5))
A(Paragraph("Sin cambiar de ligando, pasar el selector %s de %s a %s. El parámetro %s multiplica "
            "por cuatro el esfuerzo de búsqueda."
            % (ui("Docking setup"), uia("Standard, 24 A, exh 8"), uia("Standard box, exh 32"),
               i("exhaustiveness")), body))
A(table(["Setup", "Score #1", "RMSD #1"], [
    [Paragraph(b("Standard, 24 A, exh 8"), cell), Field("a3s1", 120), Field("a3r1", 120)],
    [Paragraph(b("Standard box, exh 32"), cell), Field("a3s2", 120), Field("a3r2", 120)],
], [CW - 264, 132, 132]))
A(sp(5))
for q in qs([("a", "¿Mejoró? ¿Por qué el resultado es coherente con la conclusión de A2?"),
             ("b", "Escribir en una frase en qué caso %s esperarían que aumentar %s cambie el "
                   "resultado." % (b("sí"), i("exhaustiveness")))]): A(q)
A(sp(10))

# ---- A4
A(act("A4", "La caja: el error que no se puede recuperar", 8))
A(Paragraph("Activar en %s la casilla %s para ver el volumen de búsqueda. Probar sobre el mismo "
            "ligando los setups %s, %s, %s y %s."
            % (ui("Display"), ui("Search box"), uia("Tight box, 18 A"), uia("Loose box, 34 A"),
               uia("Blind, whole protein"), uia("Mis-centred by 6 A")), body))
for s_ in steps(["Volver al blanco %s, ligando %s, y poner el setup %s (la caja corrida 6 Å "
                 "respecto del sitio)." % (ui("HIV-1 protease"), ui("Indinavir"),
                                           uia("Mis-centred by 6 A")),
                 "Leer el recuadro %s en el panel derecho."
                 % ui("The crystal pose is outside this box")]): A(s_)
A(sp(3))
A(table(["Setup", "Score #1", "RMSD #1", "¿Aviso de pose fuera de la caja?"], [
    [Paragraph(b("Standard, 24 A, exh 8"), cell), Field("a4s1", 72), Field("a4r1", 72), Field("a4w1", 150)],
    [Paragraph(b("Mis-centred by 6 A"), cell),    Field("a4s2", 72), Field("a4r2", 72), Field("a4w2", 150)],
    [Paragraph(b("Blind, whole protein"), cell),  Field("a4s3", 72), Field("a4r3", 72), Field("a4w3", 150)],
], [CW - 84 - 84 - 162, 84, 84, 162]))
A(sp(5))
for q in qs([("a", "En %s el score sigue siendo muy negativo pero el RMSD es enorme. ¿Por qué sería "
                   "un error decir que “falló la función de puntuación”?" % uia("Mis-centred by 6 A")),
             ("b", "¿Qué ventaja y qué costo tiene el docking a ciegas (%s), que no necesita saber "
                   "dónde está el sitio?" % uia("Blind, whole protein")),
             ("c", "¿Por qué una caja demasiado chica puede ser tan mala como una mal centrada?")]): A(q)
A(sp(10))

# ---- A5
A(act("A5", "Cambiar la función de puntuación", 7))
A(Paragraph("Volver a %s / %s y elegir el setup %s. Vinardo usa %s que Vina: lo único que cambia "
            "es cómo se puntúan las poses encontradas."
            % (ui("EGFR kinase domain"), ui("Erlotinib"), uia("Vinardo scoring"),
               b("exactamente la misma búsqueda")), body))
A(table(["Ligando", "Setup", "Score #1", "RMSD #1"], [
    [Paragraph(b("Erlotinib"), cell), Paragraph("Standard", cell), Field("a5s1", 95), Field("a5r1", 95)],
    [Paragraph(b("Erlotinib"), cell), Paragraph("Vinardo", cell),  Field("a5s2", 95), Field("a5r2", 95)],
    [Paragraph(b("Atazanavir") + " " + i("(HIV)"), cell), Paragraph("Standard", cell), Field("a5s3", 95), Field("a5r3", 95)],
    [Paragraph(b("Atazanavir") + " " + i("(HIV)"), cell), Paragraph("Vinardo", cell),  Field("a5s4", 95), Field("a5r4", 95)],
], [CW - 90 - 214, 90, 107, 107]))
A(sp(5))
for q in qs([("a", "¿Qué pasó con el RMSD? ¿Y con el valor absoluto del score?"),
             ("b", "Un compañero compara el score Vina de un ligando con el score Vinardo de otro y "
                   "concluye cuál es mejor. ¿Qué error está cometiendo?"),
             ("c", "Revisar también %s y %s con Vinardo. ¿Mejora %s los ligandos? ¿Qué dice esto "
                   "sobre “elegir la mejor función”?" % (ui("Lapatinib"), ui("Neratinib"), i("todos")))]): A(q)
A(sp(10))

# ---- A6
A(act("A6", "Una molécula de agua", 8))
A(Paragraph("Blanco %s — %s. Todos los setups anteriores se corrieron con el receptor %s, que es "
            "la práctica habitual. El setup %s devuelve al sitio las aguas conservadas que puentean "
            "los %s (Ile50/Ile50') con el ligando."
            % (ui("HIV-1 protease"), b("esta actividad se hace solo acá"), b("sin aguas"),
               uia("Standard + flap water"), i("flaps")), body))
A(table(["Ligando", "RMSD seco", "RMSD con agua", "¿Mejora?"], [
    [Paragraph(b(n), cell), Field("a6d%d" % k, 88), Field("a6w%d" % k, 88), Field("a6m%d" % k, 120)]
    for k, n in enumerate(["Saquinavir", "Ritonavir", "Indinavir", "Tipranavir"], 1)
], [CW - 100 - 100 - 132, 100, 100, 132]))
A(sp(5))
for q in qs([("a", "¿Cuál es la mejora más grande que vieron en toda la Parte A? ¿Vino de un "
                   "parámetro del docking o de la preparación del receptor?"),
             ("b", "%s Es un inhibidor %s que contacta directamente los NH de los %s. Proponer una "
                   "explicación física." % (b("Tipranavir empeora."), b("no peptídico"), i("flaps"))),
             ("c", "¿Por qué EGFR no tiene versión “con agua” en esta app?")]): A(q)
A(sp(10))

# ---- A7
A(act("A7", "¿El score predice la potencia?", 5))
A(Paragraph("Blanco %s, setup %s. El panel derecho muestra, para cada ligando, el dato %s. "
            "Completar y %s."
            % (ui("HIV-1 protease"), uia("Standard, 24 A, exh 8"),
               ui("Experimental Ki / IC50"), b("ordenar las dos columnas por separado")), body))
LIG = ["Lopinavir", "Darunavir", "Ritonavir", "Saquinavir", "Indinavir", "Amprenavir", "Nelfinavir"]
A(table(["Ligando", "Ki / Kd exp.", "Score #1", "Puesto exp.", "Puesto score"], [
    [Paragraph(b(n), cell), Field("a7ki%d" % k, 92), Field("a7sc%d" % k, 78),
     Field("a7pe%d" % k, 70), Field("a7ps%d" % k, 70)]
    for k, n in enumerate(LIG)
], [CW - 104 - 90 - 82 - 82, 104, 90, 82, 82]))
A(sp(5))
for q in qs([("a", "¿Coinciden los dos ordenamientos? Comparar en particular %s (el más potente de "
                   "la tabla) con %s." % (b("Darunavir"), b("Indinavir"))),
             ("b", "Si el score no ordena por potencia, ¿para qué sirve el docking en un proyecto "
                   "real? Escribir dos usos legítimos.")]): A(q)

# =============================================================== PARTE B
A(sp(14)); A(Rule(CW, 2.5, MESH))
A(Paragraph("Parte B · Pestaña %s" % ui("Design"), hpart))
A(Paragraph("De comparar fármacos a construirlos", small))
A(sp(6))
A(Paragraph("Sobre el núcleo %s —el esqueleto que comparten erlotinib y gefitinib— se cuelgan "
            "sustituyentes en dos posiciones. Leer el panel %s: los dos vectores apuntan en "
            "direcciones opuestas." % (b("4-anilinoquinazolina"), ui("Growth vectors")), body))
A(table(["Vector", "Posición", "Apunta a"], [
    [Paragraph(b("R1"), cell), Paragraph("%s de la anilina" % i("meta"), cell),
     Paragraph("el %s, pasando el residuo guardián (%s) %s"
               % (b("bolsillo hidrofóbico posterior"), i("gatekeeper"), b("Thr766")), cell)],
    [Paragraph(b("R2"), cell), Paragraph("6 de la quinazolina", cell),
     Paragraph(b("fuera del sitio, hacia el solvente"), cell)],
], [46, 118, CW - 164]))
A(sp(6))
A(Paragraph("Los 96 análogos están precalculados: los dibujos resaltan %s y %s, de modo que "
            "siempre se ve qué acaba de cambiar."
            % (b("R1 en azul"), b("R2 en ámbar")), body))
A(sp(3))
A(callout("Cómo se opera", [
    "Hacer clic en %s o %s (panel %s) para elegir el vector activo; la galería de abajo, bajo el "
    "rótulo %s, muestra las opciones %s y un clic las aplica. La estructura 2D se actualiza al "
    "instante, junto con el panel %s —donde cada propiedad se compara contra el núcleo desnudo— y "
    "las cuatro insignias de Lipinski (%s), verdes o rojas."
    % (b("R1"), b("R2"), ui("Growth vectors"), ui("Where do you want to go?"), b("de ese vector"),
       ui("Properties"), num("MW≤500, logP≤5, HBD≤5, HBA≤10")),
]))
A(sp(10))

# ---- B1
A(act("B1", "Dibujar un fármaco real", 5))
for s_ in steps(["Partir del núcleo desnudo (R1 = %s, R2 = %s)." % (i("hydrogen"), i("hydrogen")),
                 "Seleccionar el vector %s y elegir %s en la galería." % (b("R1"), i("ethynyl")),
                 "Seleccionar %s y elegir %s." % (b("R2"), i("2-methoxyethoxy"))]): A(s_)
A(sp(3))
for q in qs([("a", "¿Qué nombre aparece debajo de la estructura?"),
             ("b", "Probar ahora R1 = %s con R2 = %s. ¿Qué fármaco se parece a este?"
                   % (i("chloro"), i("3-morpholinopropoxy"))),
             ("c", "Mirar el panel %s: ¿cuánto cambió el peso molecular respecto del núcleo desnudo?"
                   % ui("Properties"))]): A(q)
A(sp(10))

# ---- B2
A(act("B2", "Explorar un vector por vez", 8))
A(Paragraph("Volver R2 a %s y dejar %s variando. Usar los botones de sugerencia (%s, %s, %s) para "
            "reordenar la galería, y leer la línea de comentario que aparece sobre ellos. Probar al "
            "menos: %s, %s, %s, %s, %s, %s."
            % (i("hydrogen"), b("solo R1"), ui("Make it bigger here"), ui("Something greasier"),
               ui("Something more polar"), i("fluoro"), i("methyl"), i("ethynyl"),
               i("cyclopropyl"), i("phenyl"), i("methoxy")), body))
for q in qs([("a", "¿Qué grupo dispara el aviso %s? ¿Contra qué residuo advierte?" % ui("Bulky")),
             ("b", "Poner un grupo polar en R1 (%s, %s): aparece el aviso %s. Explicar con la palabra "
                   "%s por qué es costoso meter un grupo polar en un bolsillo hidrofóbico."
                   % (i("hydroxyl"), i("nitrile"), ui("Mismatch"), b("desolvatación"))),
             ("c", "Repetir lo mismo en %s con %s o %s. ¿Por qué ahí no se dispara ninguna advertencia?"
                   % (b("R2"), i("3-morpholinopropoxy"), i("2-piperazinylethoxy"))),
             ("d", "Activar %s en el panel del visor. Buscar %s y %s. ¿Qué tipo de grupo convendría "
                   "apuntar hacia cada uno?"
                   % (ui("Pocket residues, by H-bond role"), b("Thr766"), b("Lys721")))]): A(q)
A(sp(10))

# ---- B3
A(act("B3", "Docking de análogos propios", 10))
A(Paragraph("Elegir %s análogos: dos que crean buenos y dos que crean malos. Para cada uno, apretar "
            "%s y anotar el resultado. La espera de cuatro segundos no es decorativa: la barra "
            "muestra las tres etapas reales del cálculo. %s Los scores quedan visibles en las "
            "tarjetas de la galería para comparar."
            % (b("cuatro"), ui("Dock this analog"),
               b("Antes de docar cada uno, escribir la predicción.")), body))
A(table(["#", "R1", "R2", "Predicción (mejor / peor que erlotinib)", "Score"], [
    [Paragraph(num(str(k)), cell), Field("b3r1%d" % k, 78), Field("b3r2%d" % k, 96),
     Field("b3pred%d" % k, 150), Field("b3score%d" % k, 70)]
    for k in range(1, 5)
], [22, 90, 108, 162, CW - 22 - 90 - 108 - 162]))
A(sp(5))
A(table(["Referencia", "R1", "R2", "Score"], [
    [Paragraph(b("Erlotinib"), cell), Paragraph("ethynyl", cell), Paragraph("2-methoxyethoxy", cell), Field("b3ref1", 92)],
    [Paragraph(b("Núcleo desnudo"), cell), Paragraph("hydrogen", cell), Paragraph("hydrogen", cell), Field("b3ref2", 92)],
], [CW - 100 - 140 - 104, 100, 140, 104]))
A(sp(5))
A(callout("Subir a la planilla de clase", [
    "Pasar las cuatro filas a la planilla compartida, una fila por análogo, con los nombres "
    "que pusieron en la primera página:",
    '<link href="https://docs.google.com/spreadsheets/d/1Yv7o8EZ0DfMaYWOfijEJVUX4r5ZJUb-0d1eXeOj7Do0/edit">'
    '<font face="DJM" size="8" color="#2B6CAB">docs.google.com/spreadsheets/d/1Yv7o8EZ0Df…</font></link>',
]))
A(sp(5))
for q in qs([("a", "¿Cuántas kcal/mol separan al %s análogo que encontraron del %s?"
                   % (b("mejor"), b("núcleo desnudo"))),
             ("b", "El núcleo desnudo tiene 22 átomos pesados; erlotinib, 29. Comparar sus scores. "
                   "¿Qué tiene de incómodo ese resultado?"),
             ("c", "Los 96 análogos caben en un rango total de %s. Sabiendo que el error típico de "
                   "estas funciones ronda 1–2 kcal/mol, ¿qué se puede afirmar honestamente al ordenar "
                   "esta serie por score?" % b("menos de 2 kcal/mol"))]): A(q)
A(sp(10))

# ---- B4
A(act("B4", "Eficiencia de ligando", 7))
A(Paragraph("El score casi siempre premia a la molécula más grande: más átomos, más contactos. "
            "La %s corrige eso." % b("eficiencia de ligando"), body))
A(callout("", ['<font face="DJMB" size="10">LE = score / número de átomos pesados</font>'
               '<font size="9" color="#57697B">   (kcal/mol por átomo)</font>']))
A(sp(5))
A(Paragraph("Calcular la LE de los análogos de B3 usando el número de átomos pesados que figura en "
            "%s, e incluir estas dos referencias:" % ui("Properties"), body))
A(table(["Análogo", "Score", "Át. pesados", "LE"], [
    [Paragraph(b("methyl + hydroxyl"), cell), Field("b4s1", 92), Paragraph(num("24"), cell), Field("b4l1", 92)],
    [Paragraph(b("phenyl + 3-morpholinopropoxy"), cell), Field("b4s2", 92), Paragraph(num("38"), cell), Field("b4l2", 92)],
    [Paragraph(b("Propio 1"), cell), Field("b4s3", 92), Field("b4h3", 80), Field("b4l3", 92)],
    [Paragraph(b("Propio 2"), cell), Field("b4s4", 92), Field("b4h4", 80), Field("b4l4", 92)],
], [CW - 104 - 92 - 104, 104, 92, 104]))
A(sp(5))
for q in qs([("a", "¿Cuál gana por score y cuál gana por LE? ¿Son el mismo?"),
             ("b", "En una campaña real se parte de fragmentos pequeños con buena LE y se crece desde "
                   "ahí. ¿Qué justifica esa estrategia, a la luz de lo que acaban de calcular?")]): A(q)
A(sp(10))

# ---- B5
A(act("B5", "El costo de crecer", 5))
A(Paragraph("Construir R1 = %s + R2 = %s y mirar el panel %s junto con las insignias de Lipinski."
            % (i("phenyl"), i("3-morpholinopropoxy"), ui("Properties")), body))
for q in qs([("a", "¿Qué aviso aparece y a partir de qué peso molecular? ¿Qué %s regla de Lipinski "
                   "rompe además este análogo?" % b("segunda")),
             ("a bis", "Cambiar R2 a %s (PM %s): el aviso desaparece. ¿Es químicamente distinta esta "
                       "molécula de la anterior? ¿Qué dice esto sobre usar umbrales fijos como "
                       "criterio de decisión?" % (i("2-piperazinylethoxy"), num("499,6"))),
             ("b", "Un análogo con mejor score pero PM &gt; 500 y muchos enlaces rotables, ¿es mejor "
                   "candidato? Nombrar dos propiedades que el score %s mide." % b("no")),
             ("c", "%s Promediando los 96 análogos, el grupo R2 con mejor score es el %s, y el peor "
                   "es justamente el %s que lleva erlotinib. Sin embargo la química medicinal real "
                   "eligió el segundo. Proponer al menos dos razones."
                   % (b("Pregunta final."), b("hidroxilo"), b("2-metoxietoxi")))]): A(q)

# =============================================================== CIERRE
A(sp(14)); A(Rule(CW, 2.5, MESH))
A(Paragraph("Cierre y discusión", hpart))
A(sp(6))
A(Paragraph("Escribir, en no más de tres renglones cada una, las conclusiones de la clase:", body))
A(sp(3))
CONC = [("c1", "Un fallo de %s y un fallo de %s se distinguen porque…" % (b("búsqueda"), b("puntuación"))),
        ("c2", "La decisión que más impactó en los resultados de toda la guía fue…"),
        ("c3", "Frente a un score de %s kcal/mol para una molécula nueva, lo que se puede afirmar "
               "es… y lo que %s se puede afirmar es…" % (num("−9,5"), b("no")))]
for k, (fid, txt) in enumerate(CONC, 1):
    t = Table([[Paragraph('<font face="DJM" size="8" color="#8497A9">%d</font>  %s' % (k, txt), cell)],
               [Field(fid, CW - 20, height=42, multiline=True)]],
              colWidths=[CW], hAlign="LEFT")
    t.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.5,RULE),
                           ("LEFTPADDING",(0,0),(-1,-1),9), ("RIGHTPADDING",(0,0),(-1,-1),9),
                           ("TOPPADDING",(0,0),(-1,-1),6), ("BOTTOMPADDING",(0,0),(-1,-1),7)]))
    A(KeepTogether(t)); A(sp(5))

A(sp(3))
A(callout("Para llevarse", [
    "Todos los resultados de esta guía son salida real de Vina. Nadie eligió los ejemplos para que "
    "fallaran: se docó un conjunto de fármacos aprobados en sus propios blancos, y esto fue lo que salió.",
]))
A(sp(10))
A(Paragraph("NOTAS", eyebrow))
A(Paragraph("• Los residuos de EGFR aparecen con dos numeraciones distintas según el panel: la de la "
            "estructura 1M17 (%s, %s, %s) y la de la proteína madura (%s, %s, %s). Se diferencian en "
            "24 posiciones y designan el mismo residuo."
            % (b("Thr766"), b("Lys721"), b("Met769"), b("Thr790"), b("Lys745"), b("Met793")), small))
A(Paragraph("• La etiqueta verde %s junto a un score indica que es un cálculo real. Si apareciera "
            "una etiqueta ámbar %s, ese número es un marcador de posición y no debe usarse."
            % (ui("vina"), uia("mock")), small))

# --------------------------------------------------------------- build
def deco(canv, doc):
    canv.saveState()
    canv.setFont("DJ", 7.2); canv.setFillColor(DIM)
    canv.drawString(LM, BM - 9, "Diseñá tu propio fármaco · Universidad Siglo 21")
    canv.drawRightString(PW - RM, BM - 9, "%d" % doc.page)
    canv.setStrokeColor(RULE); canv.setLineWidth(0.5)
    canv.line(LM, BM - 3, PW - RM, BM - 3)
    canv.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4,
                      leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                      title="Docking molecular — guía de actividades",
                      author="Docking Bench", subject="Práctico de docking molecular")
frame = Frame(LM, BM, CW, PH - TM - BM, id="main",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=deco)])
doc.build(story)
print("OK ->", OUT, os.path.getsize(OUT), "bytes")
