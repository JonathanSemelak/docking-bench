# Clave docente — Guía de actividades

**Universidad Siglo 21** · Team teaching **«Diseñá tu propio fármaco»**

Complemento de [`GUIA-ACTIVIDADES.md`](GUIA-ACTIVIDADES.md). **No repartir a los
estudiantes.** Todos los valores salen de `data.json` y `analogs.json`, y son
salida directa de AutoDock Vina 1.2.5.

**Cronograma sugerido (90 min):** Parte A 45 min · Parte B 35 min · cierre 10 min.
Si hay solo 60 min, recortar A4 y B5 y dar A7 como tarea: el núcleo irreductible
es **A2 + A6 + B3**.

---

## Parte A — Pestaña "Pose"

### A1 · Indinavir, control

| | Score | RMSD |
|---|---|---|
| Indinavir, pose #1 | **−11,62** | **0,60 Å** |

- **a)** Acierto. Criterio: RMSD ≤ 2 Å, el umbral convencional en la literatura.
- **b)** Es *redocking*: el receptor ya está moldeado alrededor de **esa** molécula
  (cadenas laterales, aperturas de flaps, todo el ajuste inducido ya ocurrió).
  Es un control de que la cañería funciona, no una prueba de capacidad
  predictiva. En esta app **solo indinavir y erlotinib** son nativos de su
  receptor; los otros 18 son *cross-docking*, que es el caso realista.

### A2 · Erlotinib — el caso central

| | Rango | Score | RMSD |
|---|---|---|---|
| Mejor puntuada | #1 | −7,21 | **7,90 Å** |
| Más parecida al cristal | **#5** | −6,93 | **1,43 Å** |

- **a)** **0,28 kcal/mol** — muy por debajo del error de la función (≈1–2 kcal/mol).
- **b)** Fallo de **puntuación**. La búsqueda encontró la pose correcta y la puso
  en la lista; lo que falló fue el orden. El dato que lo cierra: se repite con
  *exhaustiveness* 8, 32 y 64 y con tres semillas distintas, así que no es
  fluctuación del muestreo.
- **c)** Se habría elegido la #1, que está mal. **Sin el cristal no hay forma de
  saberlo**: ese es el punto incómodo de toda la clase. Salidas parciales:
  consenso entre funciones de puntuación, coherencia con la SAR conocida,
  inspección de contactos esperados (acá, el puente con la bisagra Met769).
- **d)** En EGFR, con el setup estándar, llevan **"top pose off"** **siete de diez**:
  erlotinib, gefitinib, lapatinib, osimertinib, AEE788, afatinib y TAK-285.
  Los tres restantes no es que acierten: neratinib y el pirrolotriazina W2R
  tienen la pose cristalográfica **fuera de la caja** (la app no los juzga, y
  muestra el aviso correspondiente), y dacomitinib **no tiene referencia
  cristalográfica** en el conjunto. Vale hacer notar que afatinib entra en la
  lista por 2,74 Å, apenas pasado el umbral: no es el mismo tipo de fallo que
  los 11 Å de osimertinib.

### A3 · Exhaustiveness

| Setup | Score | RMSD |
|---|---|---|
| exh 8 | −7,21 | 7,90 Å |
| exh 32 | −7,21 | 7,90 Å |

- **a)** Idéntico. Coherente con A2: si la búsqueda ya encontraba la pose correcta,
  buscar cuatro veces más no puede arreglar un problema de puntuación.
- **b)** Sirve cuando el fallo **sí** es de búsqueda: ligandos muy flexibles
  (muchos enlaces rotables), cajas grandes, docking a ciegas. Regla útil:
  subir *exhaustiveness* si repeticiones con distinta semilla dan poses
  distintas; si convergen a la misma pose equivocada, el problema es el score.

### A4 · La caja

Indinavir, HIV-1 proteasa:

| Setup | Score | RMSD | Aviso |
|---|---|---|---|
| "Standard, 24 A, exh 8" | −11,62 | 0,60 Å | no |
| "Mis-centred by 6 A" | −10,66 | 10,67 Å | **sí** |
| "Blind, whole protein" | −11,55 | 0,62 Å | no |

- **a)** Porque el aviso **"The crystal pose is outside this box"** dice que la
  respuesta correcta estaba **fuera del espacio de búsqueda**: era inalcanzable.
  La función de puntuación nunca llegó a evaluarla. Es un fallo de
  **preparación**, y confundirlo con un fallo de scoring es el error clásico.
  En ese setup **10 ligandos** quedan con la pose cristalográfica fuera de caja.
- **b)** No exige conocer el sitio (útil para blancos nuevos o sitios alostéricos),
  pero el volumen enorme diluye el muestreo y agrega mínimos falsos: la mediana
  de RMSD sube a **8,94 Å**, la peor del conjunto junto con la caja descentrada.
  Indinavir igual acierta, lo cual muestra que un buen caso no valida el método.
- **c)** Una caja chica recorta el espacio accesible y puede excluir parte de la
  pose correcta o impedir la orientación adecuada: con "Tight box, 18 A" hay
  **6 ligandos** con la referencia fuera de caja. Curiosamente su mediana de
  RMSD (5,75 Å) es la mejor de las cajas secas, porque restringir ayuda a los
  que sí entran — buen disparador de discusión sobre métricas agregadas.

**Medianas de RMSD top-1 (para proyectar, si se quiere cerrar la parte):**

| Setup | Mediana | Referencia fuera de caja |
|---|---|---|
| Tight box, 18 A | 5,75 | 6 |
| Standard, 24 A, exh 8 | 7,01 | 2 |
| Standard box, exh 32 | 7,90 | 2 |
| Loose box, 34 A | 7,87 | 0 |
| Mis-centred by 6 A | 8,69 | 10 |
| Vinardo scoring | 4,98 | 2 |
| Blind, whole protein | 8,94 | 0 |
| **Standard + flap water** (solo HIV) | **3,70** | 0 |

### A5 · Vinardo

| Ligando | Setup | Score | RMSD |
|---|---|---|---|
| Erlotinib | Vina estándar | −7,21 | 7,90 Å |
| Erlotinib | Vinardo | −5,32 | **3,08 Å** |
| Atazanavir | Vina estándar | −10,15 | 11,56 Å |
| Atazanavir | Vinardo | −7,58 | **1,30 Å** |

- **a)** El RMSD mejora mucho; los scores se vuelven **sistemáticamente menos
  negativos**. Vinardo está calibrado en otra escala.
- **b)** Los scores de funciones distintas **no son comparables**: no son energías
  medidas sino números en escalas propias. Solo se comparan valores de la misma
  función, con el mismo receptor y la misma caja. (Estrictamente, tampoco son
  comparables entre blancos distintos.)
- **c)** No mejora todos: lapatinib pasa de 6,60 a 8,45 Å, neratinib de 7,01 a
  9,34 Å, el pirrolotriazina W2R de 7,12 a 10,25 Å. Mejora la **mediana**
  (7,01 → 4,98 Å), no cada caso. No existe "la mejor función"; existe la que
  anda mejor en un sistema dado, y saber cuál es requiere justamente los datos
  experimentales que en un proyecto real todavía no se tienen.

### A6 · El agua de los flaps

| Ligando | Seco | Con agua | |
|---|---|---|---|
| Saquinavir | 10,21 Å | **2,43 Å** | mejora drástica |
| Ritonavir | 11,76 Å | **3,34 Å** | mejora drástica |
| Darunavir | 4,78 Å | 3,74 Å | mejora |
| Amprenavir | 4,50 Å | 3,67 Å | mejora |
| DMP323 | 6,14 Å | 4,36 Å | mejora |
| Indinavir | 0,60 Å | 0,61 Å | sin cambio (ya acertaba) |
| **Tipranavir** | **2,31 Å** | **10,77 Å** | **empeora** |

- **a)** La mejora más grande de toda la guía viene de **devolver tres moléculas
  de agua al receptor**, no de ningún parámetro de docking: la mediana de RMSD
  en HIV-1 proteasa pasa de **5,46 Å a 3,70 Å**. Es el mensaje central de la
  clase — la preparación del receptor pesa más que el ajuste fino de parámetros.
- **b)** HOH 308 hace de puente: acepta de ambos NH de Ile50/Ile50' y dona al
  carbonilo del ligando. Los inhibidores **peptidomiméticos** se unen *a través*
  de esa agua, y sin ella pierden dos puentes de hidrógeno y se acomodan mal.
  **Tipranavir es no peptídico y desplaza esa agua**, contactando los NH
  directamente: al reponerla, el sitio le queda bloqueado. Una decisión de
  preparación puede ser correcta para un ligando e incorrecta para otro del
  mismo sitio. *Matiz honesto:* DMP323 (urea cíclica) también desplaza esa agua
  y sin embargo mejora un poco — no es una dicotomía limpia, y decirlo es parte
  de la lección sobre datos reales.
- **c)** Porque el criterio automático (`pipeline/prep_wet.py`: aguas a menos de
  3,6 Å del ligando nativo y con ≥2 contactos polares a proteína) **no selecciona
  ninguna en 1M17**. La app omite el setup en vez de docar contra un receptor
  distinto y no avisar.

### A7 · Score vs. potencia

| Ligando | Experimental | ΔG exp. (kcal/mol, 37 °C) | Score Vina |
|---|---|---|---|
| Lopinavir | Ki 1,3 pM | −16,86 | −10,83 |
| Darunavir | Kd 4,5 pM | −16,09 | **−8,41** |
| Tipranavir | Ki 8 pM | −15,74 | −10,10 |
| Ritonavir | Ki 15 pM | −15,35 | −9,52 |
| Saquinavir | Ki 0,12 nM | −14,07 | −10,54 |
| Atazanavir | Ki 0,19 nM | −13,79 | −10,15 |
| Indinavir | Ki 0,56 nM | −13,12 | **−11,62** |
| Amprenavir | Ki 0,6 nM | −13,08 | −7,97 |
| Nelfinavir | Ki 2 nM | −12,34 | −10,29 |

**Spearman ρ = −0,02 (n = 9): correlación nula.**

- **a)** No coinciden en absoluto. **Darunavir**, el más potente (4,5 pM, ≈3000
  veces más que indinavir), obtiene el **peor score menos uno**; **indinavir**,
  de los más flojos de la lista, obtiene **el mejor**. El rango experimental
  cubre ~4,5 kcal/mol y el de los scores 3,7: no es que la señal sea chica, es
  que está desordenada.
- **b)** Usos legítimos: (i) **enriquecimiento** en cribado virtual — ordenar 10⁶
  compuestos para que el 1 % que se compra tenga más activos que al azar, sin
  creerse el orden interno; (ii) **generar hipótesis estructurales** sobre el
  modo de unión, para después testearlas con mutagénesis o SAR; (iii) filtrar
  lo groseramente imposible (choques estéricos, moléculas que no entran).
  Lo que **no** es: un predictor de afinidad ni un sustituto de medirla.

---

## Parte B — Pestaña "Design"

### B1 · Landmarks

- **a)** ethynyl + 2-methoxyethoxy = **erlotinib** (Tarceva), exacto. Score **−7,25**.
  *Control de calidad del dataset:* la misma molécula, docada por el camino
  independiente de la Parte A, da −7,21. **0,04 kcal/mol de diferencia.**
- **b)** chloro + 3-morpholinopropoxy = **similar a gefitinib** (Iressa); score
  **−7,54**. La app lo etiqueta *Gefitinib-like*, no gefitinib, y con razón: al
  gefitinib real le falta acá el **4-fluoro** de la anilina (es 3-Cl-4-F) y en la
  posición 7 lleva un **metoxi**, no el 2-metoxietoxi fijo de este andamio. El
  morfolinopropoxi en la posición 6 sí es el mismo.
- **c)** Núcleo desnudo PM 295,3 → erlotinib PM 393,4: **+98 Da**.

> **Ojo con el "núcleo desnudo".** No es una 4-anilinoquinazolina pelada: el
> andamio lleva **fijo un 2-metoxietoxi en la posición 7** (por eso PM 295,3 y no
> 221). Es la parte que erlotinib y gefitinib comparten y que la app no deja
> variar. Si alguien pregunta por qué el dibujo de `hydrogen + hydrogen` ya tiene
> una cadena colgando, la respuesta es esa. Consecuencia útil: al construir
> erlotinib, la molécula termina con **dos** 2-metoxietoxi, el fijo en 7 y el que
> se eligió en R2 — que es exactamente la estructura del fármaco.

### B2 · Vectores

- **a)** **"Bulky"** salta cuando R1 agrega ≥6 átomos pesados: *phenyl*. Advierte
  sobre **Thr766**, el *gatekeeper* que limita el acceso al bolsillo posterior.
  (Es el mismo residuo que muta a Met en la resistencia T790M — vale mencionarlo.)
- **b)** **"Mismatch"** salta con TPSA ≥20 en R1. Un grupo polar en solución está
  rodeado de aguas que lo solvatan; para entrar a un bolsillo hidrofóbico hay que
  **arrancarle esa capa de hidratación**, y el bolsillo no ofrece nada que
  compense esa pérdida — no hay dadores ni aceptores con quién reemplazarla.
  El balance neto es desfavorable aunque la molécula "entre".
- **c)** Porque R2 apunta al **solvente**: el grupo queda hidratado, no hay que
  desolvatarlo, y la afinidad es poco sensible a lo que se cuelgue ahí. Es donde
  se paga solubilidad barata. La app tiene una advertencia (**"Wasted"**) para
  cuando se cuelga ahí algo grande y grasoso —gasta logP sin comprar afinidad—,
  pero **ninguno de los ocho R2 de este conjunto la dispara**: todos se unen por
  oxígeno y ninguno agrega lipofilia suficiente. Si algún grupo aumenta la
  lipofilia en R2, es el morfolinopropoxi, y apenas (+0,10 de logP).
- **d)** Con **"Pocket residues, by H-bond role"**: rojo = acepta (Asp, Glu) → hay
  que ofrecerle un **N-H u O-H**; azul = dona (Arg, **Lys721**, Trp) → ofrecerle
  un **N u O**; violeta = ambos (Ser, **Thr766**, Tyr…); dorado = hidrofóbico →
  algo graso. Respuesta esperada: contra Lys721, un aceptor; contra Thr766, puede
  ser cualquiera de los dos, pero es angosto, así que primero conviene ser chico.

**Dato para cerrar B2:** la combinación que dispara el mensaje verde
**"Sensible"** —chico y graso atrás, polaridad hacia el solvente— incluye
exactamente a erlotinib (ethynyl + 2-metoxietoxi). La regla heurística y el
fármaco real coinciden, lo cual no es casualidad: la regla se escribió mirando
la SAR de esta familia.

### B3 · Docking de análogos

| Referencia | Score |
|---|---|
| Erlotinib (ethynyl + 2-methoxyethoxy) | **−7,25** |
| Núcleo desnudo (hydrogen + hydrogen) | **−7,30** |
| Mejor de los 96 (phenyl + carboxamida) | **−8,48** |
| Peor de los 96 (methoxy + 2-methoxyethoxy) | **−6,64** |

- **a)** Del núcleo desnudo (−7,30) al mejor (−8,48): **1,18 kcal/mol** ganadas
  agregando **9 átomos pesados** (22 → 31) y 119 Da. Poco retorno para tanto
  tamaño, y esa es la idea.
- **b)** **El núcleo desnudo puntúa mejor que erlotinib** (−7,30 vs. −7,25), con
  siete átomos pesados menos. Si la serie se ordenara por score, el punto de
  partida le ganaría al fármaco aprobado. La diferencia (0,05 kcal/mol) es ruido:
  el resultado correcto de leer esa tabla es **"son indistinguibles"**.
- **c)** Los 96 caben en **1,84 kcal/mol** (−6,64 a −8,48), menos que el error
  típico de la función. Honestamente: se pueden separar **extremos**
  (los mejores diez de los peores diez, con reservas) y **no** se puede afirmar
  que el análogo #1 sea mejor que el #12. Comparaciones de 0,1–0,3 kcal/mol
  entre análogos vecinos no significan nada.

**Promedios por sustituyente** (por si sale la pregunta de cuál vector "manda"):

| R1 (mejor→peor) | ⟨score⟩ | | R2 (mejor→peor) | ⟨score⟩ |
|---|---|---|---|---|
| phenyl | −8,07 | | hydroxyl | −7,98 |
| trifluorometilo | −7,80 | | carboxamida | −7,92 |
| hydroxyl | −7,69 | | 2-piperazinyletoxi | −7,90 |
| ethynyl | −7,68 | | hydrogen | −7,73 |
| nitrilo | −7,65 | | 3-morfolinopropoxi | −7,62 |
| fluoro | −7,64 | | methoxy | −7,31 |
| methyl | −7,62 | | 2-dimetilaminoetoxi | −7,25 |
| ciclopropilo | −7,61 | | **2-metoxietoxi** | **−7,11** |
| chloro | −7,52 | | | |
| hydrogen | −7,40 | | | |
| bromo | −7,38 | | | |
| methoxy | −7,18 | | | |

Obsérvese que el "mejor" R1 es el más grande (phenyl) y el "mejor" R2 es el más
chico con oxígeno (hydroxyl): el score está siguiendo tamaño y contactos, no
química fina.

### B4 · Eficiencia de ligando

| Análogo | Score | Át. pesados | LE |
|---|---|---|---|
| methyl + hydroxyl | −8,15 | 24 | **−0,340** |
| phenyl + 3-morpholinopropoxy | −8,18 | 38 | **−0,215** |
| Núcleo desnudo | −7,30 | 22 | −0,332 |
| Erlotinib | −7,25 | 29 | −0,250 |

- **a)** Por **score** ganan casi empatados (0,03 kcal/mol: indistinguibles). Por
  **LE**, *methyl + hydroxyl* gana por lejos: **−0,340 vs. −0,215**, con 14
  átomos menos. Los dos criterios eligen moléculas distintas.
- **b)** Cada átomo agregado casi siempre baja algo el score (más superficie de
  contacto), así que el score **premia el tamaño casi automáticamente** y una
  serie ordenada por score tiende a ordenarse por peso molecular. Partiendo de
  fragmentos con LE alta queda **presupuesto de tamaño** para crecer después
  hacia potencia manteniendo el compuesto en rango oral. Crecer desde un punto
  de partida de LE baja lleva a moléculas grandes, insolubles y con mala
  farmacocinética. Umbral habitual de referencia: LE ≥ 0,3.

### B5 · El costo de crecer

- **a)** El aviso **"Heavy"** aparece con **PM > 500**. *phenyl +
  3-morfolinopropoxi* pesa **514,6** y además tiene **logP 5,17**, así que rompe
  **dos** reglas de Lipinski (PM ≤ 500 y logP ≤ 5), con 12 enlaces rotables.
  Solo **4 de los 96** análogos superan 500: Br+PZE (502,4), CF₃+MPO (506,5),
  Ph+MPO (514,6) y Br+MPO (517,4). Regla de Lipinski completa: PM ≤ 500,
  logP ≤ 5, dadores de H ≤ 5, aceptores ≤ 10.
- **a bis)** *phenyl + 2-piperazinyletoxi* pesa **499,6** y no dispara nada, pese
  a ser prácticamente la misma molécula (un CH₂ y un O de diferencia). Las reglas
  de Lipinski son **descripciones estadísticas** de fármacos orales comerciales,
  no leyes: 499 y 515 no describen compuestos con destinos distintos. Se usan
  como semáforo de atención, no como criterio de descarte —y muchos fármacos
  aprobados, incluidos varios inhibidores de la Parte A, las violan.
- **b)** No necesariamente. El score no mide **solubilidad acuosa**, **permeabilidad**,
  **estabilidad metabólica**, **selectividad** frente a otras quinasas,
  **toxicidad**, ni el **costo entrópico** de los enlaces rotables. Tampoco mide
  biodisponibilidad oral, que es lo que decide si el compuesto llega a ser
  comprimido. Dos bastan para la respuesta.
- **c)** El 2-metoxietoxi de erlotinib puntúa **peor** en promedio que el hidroxilo
  (−7,11 vs. −7,98) y aun así es el que está en el fármaco. Razones esperadas:
  1. **Sale al solvente**: ahí la afinidad importa poco y se optimiza otra cosa.
     Los dos éteres mejoran **solubilidad** y perfil farmacocinético.
  2. Un **hidroxilo fenólico es un pasivo metabólico**: se glucuronida y sulfata
     rápido (fase II), acortando la vida media. El éter lo evita.
  3. Un OH agrega un **dador** de puente de hidrógeno que hay que desolvatar y
     que puede penalizar la permeabilidad de membrana.
  4. Esa posición es el **punto de enganche sintético** para linkers y profármacos.
  5. El score **no ve nada de esto**: optimiza una sola dimensión de las muchas
     que definen un fármaco.

---

## Cierre — respuestas esperadas

1. **Búsqueda vs. puntuación:** si la pose correcta **aparece** entre las nueve
   pero mal ranqueada → falló la puntuación (erlotinib, A2). Si **no aparece en
   ninguna** → falló la búsqueda o la caja, y hay que revisar el aviso de pose
   fuera de caja antes de culpar al score (A4).
2. **La decisión de mayor impacto:** la preparación del receptor — tres aguas
   (A6) valen más que cuadruplicar la búsqueda (A3) o elegir función (A5).
3. **Frente a −9,5 kcal/mol:** se puede afirmar que la molécula **entra** en el
   sitio sin choques y que hay al menos un modo de unión geométricamente
   plausible. **No** se puede afirmar que se una con más fuerza que otra de −8,5
   (A7: ρ ≈ 0), ni que la pose mostrada sea la real (A2), ni convertir ese número
   a una constante de disociación.

---

## Puntos de fricción previsibles

- **"Entonces el docking no sirve."** Reencuadrar: sirve para **enriquecer** y
  para **generar hipótesis**, no para predecir afinidad. El indinavir a 0,60 Å
  muestra que la física está bien puesta; lo que no está resuelto es la
  puntuación. Es una herramienta de triaje, no un oráculo.
- **Comparar scores entre blancos o entre funciones.** Sale sistemáticamente.
  Cortarlo en A5 y no dejarlo pasar en B3.
- **⚠ No hacer clic en "Dacomitinib" durante la clase.** Es el único ligando sin
  pose cristalográfica de referencia, y hoy la app **se rompe** al seleccionarlo:
  `renderPoses()` hace `p.rmsdToRef.toFixed(2)` sobre un `null` y lanza una
  excepción, con lo cual la tabla **"Poses"** queda vacía y el visor sigue
  mostrando el ligando anterior. Conceptualmente el caso es bueno —ausencia de
  referencia no es resultado negativo— pero hasta que se corrija conviene
  saltearlo. (Arreglo: mostrar "—" cuando `rmsdToRef` es `null`.)
- **⚠ El setup "Standard + flap water" en EGFR no existe, pero el botón sí.**
  1M17 no tiene aguas puente que califiquen, así que no se corrió esa condición;
  al apretar ese botón estando en EGFR, la app **cae silenciosamente** a los
  resultados de **"Tight box, 18 A"** sin avisar. La actividad A6 se hace
  **solo en HIV-1 proteasa**; si alguien lo prueba en EGFR, los números que ve
  no son de esa condición.
- **Caveat que conviene decir en voz alta:** salvo el setup "+ flap water", todos
  los receptores están **sin aguas**, que es lo habitual y es un handicap real.
- **Si los scores aparecen con etiqueta ámbar "mock"** en la pestaña Design, la
  app no cargó `analogs.json` (típicamente por abrir el archivo sin servidor).
  Los 96 tienen score real de Vina; el marcador ámbar no debería aparecer nunca.
  Solución: servir la carpeta (`python3 -m http.server 8000`) o usar el
  `docking-bench-standalone.html`, que no necesita servidor.
- **Plan B sin internet:** copiar `docking-bench-standalone.html` en un pendrive.
  Es autocontenido y anda sin red.
