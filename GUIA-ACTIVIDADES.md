# Docking molecular: guía de actividades

**Universidad Siglo 21** · Team teaching **«Diseñá tu propio fármaco»**

**App:** https://jonathansemelak.github.io/docking-bench/

> La interfaz de la aplicación está en inglés. En esta guía los nombres de
> botones, pestañas y columnas aparecen **entre comillas y en inglés**, tal como
> se leen en pantalla.

---

## Qué se hace en esta clase

El docking molecular (acoplamiento molecular) intenta responder dos preguntas
distintas, y conviene no confundirlas nunca:

1. **¿Dónde y cómo se une el ligando?** → es un problema de **búsqueda**.
   Se mide con el **RMSD** contra la estructura cristalográfica.
2. **¿Con qué fuerza se une?** → es un problema de **puntuación** (*scoring*).
   Se mide con el **score**, en kcal/mol.

Durante la clase van a usar resultados **reales** de AutoDock Vina 1.2.5 sobre
dos blancos terapéuticos: la **proteasa de HIV-1** (PDB 1HSG) y el **dominio
quinasa de EGFR** (PDB 1M17). Nada está simulado ni maquillado: los casos que
funcionan y los que fracasan son los que dio el programa.

**Al terminar deberían poder:**

- interpretar un score y un RMSD, y explicar por qué no miden lo mismo;
- distinguir un fallo de **búsqueda** de un fallo de **puntuación**;
- justificar por qué la **preparación del receptor** puede pesar más que
  cualquier parámetro del docking;
- proponer análogos de un fármaco sobre vectores químicos definidos y discutir
  hasta dónde el score los puede ordenar.

---

## Vocabulario mínimo

| Término | Qué es | Regla práctica |
|---|---|---|
| **Pose** | Una orientación y conformación propuesta del ligando en el sitio | La app muestra 9 por ligando |
| **Score** | Energía libre de unión estimada, en kcal/mol | Más negativo = predicho como mejor unión |
| **RMSD** | Desviación cuadrática media respecto de la pose cristalográfica, en Å | **≤ 2 Å = acierto** · 2–4 Å = parcial · **> 4 Å = fallo** |
| **Caja de búsqueda** (*search box*) | El volumen dentro del cual el programa puede buscar | Si la respuesta queda afuera, es imposible acertar |
| **LE** (*ligand efficiency*) | Score dividido por número de átomos pesados | Corrige el premio automático al tamaño |

En el visor 3D: **azul claro = pose calculada (*docked pose*)**,
**verde = pose cristalográfica (*crystal reference*)**. En la tabla de poses, el
RMSD se colorea solo: verde ≤ 2 Å, ámbar ≤ 4 Å, rojo > 4 Å.

---

# PARTE A — Pestaña "Pose"

**Orientación rápida.** En la barra superior están, en este orden: el selector de
modo **"Pose" / "Design"** y, a su derecha, los dos blancos
(**"HIV-1 protease"** y **"EGFR kinase domain"**). En el panel izquierdo van
**"Docking setup"** (las ocho condiciones de cálculo) y **"Ligand library"**
(los diez ligandos). El visor 3D ocupa el centro, y debajo la escala
**"Best score per ligand"** ubica al ligando elegido entre los diez. El panel
derecho, de arriba abajo: la tabla **"Poses"** (columnas *Rank, Score, RMSD, LE*),
los datos del ligando y las casillas **"Display"**.

Antes de empezar: modo **"Pose"**, setup **"Standard, 24 A, exh 8"**, y la casilla
**"Crystal reference pose"** activada.

## A1. El control que hay que hacer siempre

Blanco **"HIV-1 protease"**, ligando **"Indinavir"** (aparece etiquetado
*redocked*: es el ligando que venía en ese cristal).

1. Anotar el score y el RMSD de la pose **#1**.
2. Girar el visor y comparar la pose azul con la verde.

| | Score (kcal/mol) | RMSD (Å) |
|---|---|---|
| Indinavir, pose #1 | | |

**Preguntas:**

- a) ¿Este resultado es un acierto o un fallo? ¿Con qué criterio lo deciden?
- b) Este cálculo se llama *redocking*: se saca el ligando de su propio cristal y
  se lo vuelve a colocar. ¿Por qué un resultado así **no** demuestra que el
  método vaya a funcionar con una molécula nueva?

## A2. El caso central: el mejor score en el lugar equivocado

Cambiar el blanco a **"EGFR kinase domain"** y elegir **"Erlotinib"** (también
*redocked*: 1M17 es su propio cristal).

1. Anotar score y RMSD de la pose **#1**.
2. Recorrer la tabla **"Poses"** completa, haciendo clic en cada fila y mirando
   cómo se mueve la molécula azul respecto de la verde.
3. Encontrar **la pose de menor RMSD** de las nueve y anotar su rango y su score.

| | Rango | Score | RMSD |
|---|---|---|---|
| Pose mejor puntuada | #1 | | |
| Pose más parecida al cristal | | | |

**Preguntas:**

- a) ¿Cuántas kcal/mol separan a esas dos poses?
- b) El programa **encontró** la pose correcta pero la **ranqueó** por debajo de
  otras cuatro. ¿Esto es un fallo de búsqueda o de puntuación? Justificar.
- c) Si esta molécula fuera desconocida y no existiera el cristal para
  compararla, ¿qué pose habrían elegido? ¿Cómo se habrían dado cuenta del error?
- d) Leer el aviso rojo **"Best score, wrong pose"** del panel derecho. En la
  lista de ligandos, contar cuántos llevan la etiqueta roja **"top pose off"**
  en este blanco.

## A3. ¿Y si buscamos más?

Sin cambiar de ligando, pasar el selector **"Docking setup"** de
**"Standard, 24 A, exh 8"** a **"Standard box, exh 32"**. El parámetro
*exhaustiveness* multiplica por cuatro el esfuerzo de búsqueda.

| Setup | Score #1 | RMSD #1 |
|---|---|---|
| "Standard, 24 A, exh 8" | | |
| "Standard box, exh 32" | | |

**Preguntas:**

- a) ¿Mejoró? ¿Por qué el resultado es coherente con la conclusión de A2?
- b) Escribir en una frase en qué caso **sí** esperarían que aumentar
  *exhaustiveness* cambie el resultado.

## A4. La caja: el error que no se puede recuperar

Activar en **"Display"** la casilla **"Search box"** para ver el volumen de
búsqueda. Probar sobre el mismo ligando los setups **"Tight box, 18 A"**,
**"Loose box, 34 A"**, **"Blind, whole protein"** y **"Mis-centred by 6 A"**.

1. Volver al blanco **"HIV-1 protease"**, ligando **"Indinavir"**, y poner el
   setup **"Mis-centred by 6 A"** (la caja corrida 6 Å respecto del sitio).
2. Leer el recuadro **"The crystal pose is outside this box"** en el panel
   derecho.

| Setup | Score #1 | RMSD #1 | ¿Aviso de pose fuera de la caja? |
|---|---|---|---|
| "Standard, 24 A, exh 8" | | | |
| "Mis-centred by 6 A" | | | |
| "Blind, whole protein" | | | |

**Preguntas:**

- a) En **"Mis-centred by 6 A"** el score sigue siendo muy negativo pero el RMSD
  es enorme. ¿Por qué sería un error decir que "falló la función de puntuación"?
- b) ¿Qué ventaja y qué costo tiene el docking a ciegas
  (**"Blind, whole protein"**), que no necesita saber dónde está el sitio?
- c) ¿Por qué una caja demasiado chica puede ser tan mala como una mal centrada?

## A5. Cambiar la función de puntuación

Volver a **"EGFR kinase domain"** / **"Erlotinib"** y elegir el setup
**"Vinardo scoring"**. Vinardo usa **exactamente la misma búsqueda** que Vina:
lo único que cambia es cómo se puntúan las poses encontradas.

| Ligando | Setup | Score #1 | RMSD #1 |
|---|---|---|---|
| Erlotinib | "Standard, 24 A, exh 8" | | |
| Erlotinib | "Vinardo scoring" | | |
| Atazanavir (HIV) | "Standard, 24 A, exh 8" | | |
| Atazanavir (HIV) | "Vinardo scoring" | | |

**Preguntas:**

- a) ¿Qué pasó con el RMSD? ¿Y con el valor absoluto del score?
- b) Un compañero compara el score Vina de un ligando con el score Vinardo de
  otro y concluye cuál es mejor. ¿Qué error está cometiendo?
- c) Revisar también **"Lapatinib"** y **"Neratinib"** con Vinardo. ¿Mejora
  *todos* los ligandos? ¿Qué dice esto sobre "elegir la mejor función"?

## A6. Una molécula de agua

Blanco **"HIV-1 protease"**. Todos los setups anteriores se corrieron con el
receptor **sin aguas**, que es la práctica habitual. El setup
**"Standard + flap water"** devuelve al sitio las aguas conservadas que
puentean los *flaps* (Ile50/Ile50') con el ligando.

Comparar **"Standard, 24 A, exh 8"** contra **"Standard + flap water"**:

| Ligando | RMSD seco | RMSD con agua | ¿Mejora? |
|---|---|---|---|
| Saquinavir | | | |
| Ritonavir | | | |
| Indinavir | | | |
| **Tipranavir** | | | |

**Preguntas:**

- a) ¿Cuál es la mejora más grande que vieron en toda la Parte A? ¿Vino de un
  parámetro del docking o de la preparación del receptor?
- b) **Tipranavir empeora**. Es un inhibidor **no peptídico** que contacta
  directamente los NH de los *flaps*. Proponer una explicación física.
- c) ¿Por qué EGFR no tiene versión "con agua" en esta app?

## A7. ¿El score predice la potencia?

Blanco **"HIV-1 protease"**, setup **"Standard, 24 A, exh 8"**. El panel derecho
muestra, para cada ligando, el dato experimental **"Experimental Ki / IC₅₀"**.

Completar y **ordenar las dos columnas por separado**:

| Ligando | Ki / Kd experimental | Score #1 | Puesto experimental | Puesto por score |
|---|---|---|---|---|
| Lopinavir | | | | |
| Darunavir | | | | |
| Ritonavir | | | | |
| Saquinavir | | | | |
| Indinavir | | | | |
| Amprenavir | | | | |
| Nelfinavir | | | | |

**Preguntas:**

- a) ¿Coinciden los dos ordenamientos? Comparar en particular **Darunavir**
  (el más potente de la tabla) con **Indinavir**.
- b) Si el score no ordena por potencia, ¿para qué sirve el docking en un
  proyecto real? Escribir dos usos legítimos.

---

# PARTE B — Pestaña "Design"

Pasar a la pestaña **"Design"**. La app deja de comparar fármacos conocidos y
pasa a construirlos: sobre el núcleo **4-anilinoquinazolina** —el esqueleto que
comparten erlotinib y gefitinib— se cuelgan sustituyentes en dos posiciones.

Leer el panel **"Growth vectors"**. Los dos vectores apuntan en direcciones
opuestas:

- **R1**, posición *meta* de la anilina → entra al **bolsillo hidrofóbico
  posterior**, pasando el residuo guardián (*gatekeeper*) **Thr766**.
- **R2**, posición 6 de la quinazolina → **sale del sitio hacia el solvente**.

Los 96 análogos están precalculados: los dibujos resaltan **R1 en azul** y
**R2 en ámbar**, de modo que siempre se ve qué acaba de cambiar.

**Cómo se opera.** Hacer clic en **R1** o en **R2** (panel **"Growth vectors"**)
para elegir el vector activo; la galería de abajo, bajo el rótulo
**"Where do you want to go?"**, muestra las opciones **de ese vector** y un clic
las aplica. La estructura 2D se actualiza al instante, junto con el panel
**"Properties"** —donde cada propiedad se compara contra el núcleo desnudo— y
las cuatro insignias de Lipinski (**MW≤500, logP≤5, HBD≤5, HBA≤10**), verdes o
rojas. El visor 3D del bolsillo queda arriba a la izquierda y tiene un botón
**"Expand"** para verlo a pantalla completa.

## B1. Dibujar un fármaco real

1. Partir del núcleo desnudo (R1 = *hydrogen*, R2 = *hydrogen*).
2. Seleccionar el vector **R1** y elegir **ethynyl** en la galería.
3. Seleccionar **R2** y elegir **2-methoxyethoxy**.

**Preguntas:**

- a) ¿Qué nombre aparece debajo de la estructura?
- b) Probar ahora R1 = **chloro** con R2 = **3-morpholinopropoxy**. ¿Qué fármaco
  se parece a este?
- c) Mirar el panel **"Properties"**: ¿cuánto cambió el peso molecular respecto
  del núcleo desnudo?

## B2. Explorar un vector por vez

Volver R2 a *hydrogen* y dejar **solo R1** variando. Usar los botones de sugerencia
(**"Make it bigger here"**, **"Something greasier"**, **"Something more polar"**)
para reordenar la galería, y leer la línea de comentario que aparece sobre ellos.

Probar al menos: *fluoro*, *methyl*, *ethynyl*, *cyclopropyl*, *phenyl*, *methoxy*.

**Preguntas:**

- a) ¿Qué grupo dispara el aviso **"Bulky"**? ¿Contra qué residuo advierte?
- b) Poner un grupo polar en R1 (*hydroxyl*, *nitrile*): aparece el aviso
  **"Mismatch"**. Explicar con la palabra **desolvatación** por qué es costoso
  meter un grupo polar en un bolsillo hidrofóbico.
- c) Repetir lo mismo en **R2** con *3-morpholinopropoxy* o
  *2-piperazinylethoxy*. ¿Por qué ahí no se dispara ninguna advertencia?
- d) Activar **"Pocket residues, by H-bond role"** en el panel del visor. Buscar
  **Thr766** y **Lys721**. ¿Qué tipo de grupo convendría apuntar hacia cada uno?

## B3. Docking de análogos propios

Elegir **cuatro** análogos: dos que crean buenos y dos que crean malos.
Para cada uno, apretar **"Dock this analog"** y anotar el resultado. La espera
de cuatro segundos no es decorativa: la barra muestra las tres etapas reales del
cálculo.

**Antes de docar cada uno, escribir la predicción.** Los scores quedan visibles
en las tarjetas de la galería para comparar.

| # | R1 | R2 | Predicción (mejor/peor que erlotinib) | Score obtenido |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |

Referencias obligatorias para comparar:

| Referencia | R1 | R2 | Score |
|---|---|---|---|
| Erlotinib | ethynyl | 2-methoxyethoxy | |
| Núcleo desnudo | hydrogen | hydrogen | |

**Preguntas:**

- a) ¿Cuántas kcal/mol separan al **mejor** análogo que encontraron del
  **núcleo desnudo**?
- b) El núcleo desnudo tiene 22 átomos pesados; erlotinib, 29. Comparar sus
  scores. ¿Qué tiene de incómodo ese resultado?
- c) Los 96 análogos caben en un rango total de **menos de 2 kcal/mol**. Sabiendo
  que el error típico de estas funciones ronda 1–2 kcal/mol, ¿qué se puede
  afirmar honestamente al ordenar esta serie por score?

## B4. Eficiencia de ligando

El score casi siempre premia a la molécula más grande: más átomos, más contactos.
La **eficiencia de ligando** corrige eso:

> **LE = score / número de átomos pesados**  (kcal/mol por átomo)

Calcular la LE de los análogos de B3 usando el número de átomos pesados que
figura en **"Properties"**, e incluir estas dos referencias:

| Análogo | Score | Átomos pesados | LE |
|---|---|---|---|
| methyl + hydroxyl | | 24 | |
| phenyl + 3-morpholinopropoxy | | 38 | |
| (propio 1) | | | |
| (propio 2) | | | |

**Preguntas:**

- a) ¿Cuál gana por score y cuál gana por LE? ¿Son el mismo?
- b) En una campaña real se parte de fragmentos pequeños con buena LE y se crece
  desde ahí. ¿Qué justifica esa estrategia, a la luz de lo que acaban de calcular?

## B5. El costo de crecer

Construir R1 = *phenyl* + R2 = *3-morpholinopropoxy* y mirar el panel
**"Properties"** junto con el indicador de reglas de Lipinski.

**Preguntas:**

- a) ¿Qué aviso aparece y a partir de qué peso molecular? ¿Qué **segunda** regla
  de Lipinski rompe además este análogo?
- a bis) Cambiar R2 a *2-piperazinylethoxy* (PM 499,6): el aviso desaparece.
  ¿Es químicamente distinta esta molécula de la anterior? ¿Qué dice esto sobre
  usar umbrales fijos como criterio de decisión?
- b) Un análogo con mejor score pero PM > 500 y muchos enlaces rotables, ¿es
  mejor candidato? Nombrar dos propiedades que el score **no** mide.
- c) **Pregunta final.** Promediando los 96 análogos, el grupo R2 con mejor score
  es el **hidroxilo**, y el peor es justamente el **2-metoxietoxi** que lleva
  erlotinib. Sin embargo la química medicinal real eligió el segundo.
  Proponer al menos dos razones.

---

## Cierre y discusión

Escribir, en no más de tres renglones cada una, las conclusiones de la clase:

1. Un fallo de **búsqueda** y un fallo de **puntuación** se distinguen porque…
2. La decisión que más impactó en los resultados de toda la guía fue…
3. Frente a un score de −9,5 kcal/mol para una molécula nueva, lo que se puede
   afirmar es… y lo que **no** se puede afirmar es…

**Para llevarse:** todos los resultados de esta guía son salida real de Vina.
Nadie eligió los ejemplos para que fallaran: se docó un conjunto de fármacos
aprobados en sus propios blancos y esto fue lo que salió.

---

### Notas

- Los residuos de EGFR aparecen con dos numeraciones distintas según el panel:
  la de la estructura 1M17 (**Thr766**, **Lys721**, **Met769**) y la de la
  proteína madura (**Thr790**, **Lys745**, **Met793**). Se diferencian en 24
  posiciones y designan el mismo residuo.
- La etiqueta verde **vina** junto a un score indica que es un cálculo real.
  Si apareciera una etiqueta ámbar **mock**, ese número es un marcador de
  posición y no debe usarse.
