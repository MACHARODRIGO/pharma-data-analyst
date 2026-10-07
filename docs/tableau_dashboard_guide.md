# Instructivo — Dashboard de Tableau "Pastela Pharmaceuticals — Pharmacovigilance Risk Monitor"

Este instructivo está en español; **todo lo que se ve en el dashboard (títulos, campos, tooltips, rótulos y textos) va en inglés**. Los textos en inglés para copiar y pegar están en bloques de código.

Todas las cifras de este documento salen de la ejecución de `exemplar_data_analysis_portfolio_pharma.ipynb`. Si se regeneran los datos, hay que re-ejecutar el notebook antes de construir el dashboard.

---

## 0. Qué vas a construir

Son tres dashboards con navegación entre ellos:

| Dashboard | Para quién | Pregunta que responde |
|---|---|---|
| **Treatment Risk Overview** | Equipo de Helena (monitoreo) | Sobre toda la cartera, ¿qué tratamientos activos conviene revisar primero y qué drogas concentran el riesgo? |
| **Drug Deep Dive** | Farmacovigilancia y revisión de señales | Para **una** droga elegida, ¿cómo se compara con el resto de la red y dónde se concentran sus eventos? |
| **Site Monitoring (RBQM)** | Helena, Marcus y auditoría | ¿Qué sitios tienen datos poco confiables o desvíos de proceso? |

El flujo de uso es: el Overview muestra **qué droga mirar**, el Deep Dive la analiza **de a una** y el Site Monitoring responde **si se puede confiar en los datos** de cada sitio. Aclaración: es monitoreo de seguridad post-comercialización, no un ensayo clínico; no hay grupo control, y lo único que se compara es cada droga contra el resto de la red.

---

## 1. Fuentes de datos

Todos los archivos están en `processed/`:

| Archivo | Nivel | Uso |
|---|---|---|
| `tableau_pharma_risk_data.hyper` (o `.csv`) | 1 fila por tratamiento (31,583) | Dashboard 1 y los filtros |
| `tableau_site_risk.csv` | 1 fila por sitio × KRI (50) | Site Risk Score y grilla de KRIs |
| `tableau_kri_by_hospital.csv` | 1 fila por sitio (10) | Funnel O/E por sitio |
| `tableau_qtl_quarterly.csv` | 1 fila por trimestre | Gráfico QTL del programa |

**Pasos:**
1. *Connect → More… → Hyper* (o *Text file*) → `tableau_pharma_risk_data.hyper`. Renombrá la fuente como `Treatments`.
2. Agregá las otras tres con *Data → New Data Source*. Renombralas `Site Risk`, `Site O/E` y `Programme QTL`.
3. Revisá l os tipos de dato en `Treatments`:
   - `start_date`, `end_date`, `event_date` y `report_date` como **Date**.
   - `patient_id`, `doctor_id`, `medication_id` y `treatment_id` como **Dimension** (clic derecho → *Convert to Dimension*). Son IDs, no números para sumar.
   - `adverse_event_flag` y `required_hospitalization` quedan como **Measure** (0/1), para poder sumarlos.
4. Para que el filtro de hospital funcione entre fuentes, usá *Data → Edit Blend Relationships*, elegí `Treatments` como primaria y vinculá `hospital` con `hospital` en `Site Risk` y `Site O/E`.
5. `Programme QTL` **no se vincula** con ninguna otra fuente, y es a propósito: el QTL es un límite de todo el programa (los 10 sitios juntos, por trimestre), así que no tiene columna `hospital` y no debe filtrarse por sitio ni por droga. Sus límites están pre-calculados para el total; si se filtrara, los límites dejarían de corresponder a los datos. Si querés ver O/E y límites que se recalculen con filtros, usá la hoja opcional 3.11 (`O/E Funnel - Live`).

> Tableau muestra los nombres "embellecidos" (por ejemplo, `patient_id` aparece como *Patient Id*). En las fórmulas de abajo uso el nombre original entre corchetes; si Tableau lo muestra distinto, usá el nombre que aparezca en el panel.

---

## 2. Campos calculados (fuente `Treatments`)

*Analysis → Create Calculated Field*. Los nombres van en inglés porque se ven en el dashboard.

| Nombre (EN) | Fórmula |
|---|---|
| `Total Patients` | `COUNTD([patient_id])` |
| `Total Prescribers` | `COUNTD([doctor_id])` |
| `Total Medications` | `COUNTD([medication_id])` |
| `Total Treatments` | `COUNTD([treatment_id])` |
| `Adverse Events` | `SUM([adverse_event_flag])` |
| `AE Rate` | `SUM([adverse_event_flag]) / COUNTD([treatment_id])` → formato % con 1 decimal |
| `Hospitalisations` | `SUM([required_hospitalization])` |
| `Active High-Risk Treatments` | `COUNTD(IF [status] = "Active" AND [risk_level] = "High" THEN [treatment_id] END)` |
| `Expected Events` | `SUM([risk_score])` |
| `O/E Ratio` | `[Adverse Events] / [Expected Events]` |
| `Reports Within 15 Days` | `SUM(IF [report_lag_days] <= 15 THEN 1 ELSE 0 END) / SUM([adverse_event_flag])` → formato % |
| `Risk Level Order` | `CASE [risk_level] WHEN "High" THEN 1 WHEN "Medium" THEN 2 ELSE 3 END` |
| `Risk Level Label` | `CASE [risk_level] WHEN "High" THEN "▲ High" WHEN "Medium" THEN "● Medium" ELSE "▽ Low" END` |
| `Model Agreement` | `IF ABS([risk_score] - [predicted_risk_tree]) > 0.10 THEN "Models disagree - review" ELSE "Models agree" END` |
| `Age Group` | `IF [age_at_start] < 40 THEN "< 40" ELSEIF [age_at_start] < 65 THEN "40-64" ELSE "65+" END` |
| `Network AE Rate` | `{ FIXED : SUM([adverse_event_flag]) / COUNTD([treatment_id]) }` → formato % con 1 decimal. El `FIXED` hace que **no cambie** cuando se filtra por droga: es el valor de referencia de toda la red (7.5%) |
| `AE Rate vs Network (pts)` | `([AE Rate] - [Network AE Rate]) * 100` → formato `+0.0;-0.0` |
| `Secondary Lower` | `1 - 1.96 / SQRT([Expected Events])` |
| `Secondary Upper` | `1 + 1.96 / SQRT([Expected Events])` |
| `Action Lower` | `1 - 3.09 / SQRT([Expected Events])` |
| `Action Upper` | `1 + 3.09 / SQRT([Expected Events])` |

Notas:
- El símbolo en `Risk Level Label` (▲ ● ▽) da una segunda señal además del color, por la discapacidad visual de Helena.
- Los cuatro campos de límites usan la aproximación normal a Poisson (95% → 1.96; 99.8% → 3.09). Así los límites **se recalculan con cada filtro**. El notebook usa Poisson exacto y la diferencia es mínima con más de 100 eventos esperados.
- `Risk Level Order` sirve para ordenar: arrastralo a *Sort → Field* en cualquier hoja que use `risk_level`.

---

## 3. Hojas (worksheets)

Primero se arman todas las hojas (una pestaña por gráfico) y **después** se arrastran al dashboard (sección 5). Los títulos "Hojas del Dashboard 1, 2 y 3" de abajo indican a qué dashboard va cada hoja; todavía no se arma ningún dashboard en esta sección.

Cada hoja lleva el título en inglés indicado. Para todas las hojas:
- **Format → Font** en Tableau Book ≥ 12 pt, con los títulos en 15 pt.
- **Color → Edit Colors → Color Blind** (paleta incorporada). No usar rojo/verde como única diferencia.

### Hojas del Dashboard 1 — Treatment Risk Overview

**Hoja 3.1 `KPI Banner`**: una sola hoja con *Measure Names / Measure Values*.
- Medidas: `Total Patients`, `Total Prescribers`, `Total Medications`, `Total Treatments`, `Adverse Events`, `AE Rate` y `Active High-Risk Treatments`. (`Hospitalisations` queda solo para tooltips y el Deep Dive.)
- Armado: arrastrá `Measure Names` a *Columns* y `Measure Values` a *Text*. En el panel *Measure Values* dejá solo esas 7 medidas, en ese orden (arrastrándolas para reordenar).
- **`AE Rate` en porcentaje:** en el panel *Measure Values*, clic derecho en `AGG(AE Rate)` → *Format… → Default → Numbers → Percentage*, con 1 decimal. Si no, un 0.075 se muestra como "0".
- Texto grande (Tableau muestra el nombre de la medida **arriba** del número; es lo normal y se lee bien):
  1. *Worksheet → Show Title*: desactivalo (saca el "Sheet 1").
  2. *Format → Font*: en *Worksheet* poné 28 pt y negrita (los números); en *Header* poné 12 pt (los nombres).
  3. *Format → Alignment*: *Default → Horizontal: Center* para centrar los números bajo cada nombre.
  4. En la barra superior, cambiá la vista de *Standard* a *Entire View*, para que la banda ocupe todo el ancho.
- Valores esperados sin filtros: 17,060 · 200 · 40 · 31,583 · 2,381 · 7.5% · 696.

**Hoja 3.2 `Adverse Event Rate by Medication Class`**
- Gráfico: **barras horizontales ordenadas**. Hay 40 categorías: mostrá solo las 15 con mayor tasa con un filtro *Top → By field → Top 15 by `AE Rate`* en `who_atc_category` (el resto se ve filtrando).
- Filas: `who_atc_category`. Columnas: `AE Rate`. Orden descendente.
- Etiquetas: `AE Rate` y `Total Treatments` en cada barra (ej. `22.0% (n=277)`), porque con pocos tratamientos la tasa es menos precisa.
- Valores esperados sin filtros: Anthracycline 22.0% (n=277) · Platinum 21.6% (328) · Antimetabolite/DMARD 20.7% (445) · Calcineurin inhibitor (L04AD02) 20.2% (322) · Factor Xa 20.1% (637). Los 9 primeros están entre 18% y 22%; del décimo en adelante bajan a ≤ 12%. Promedio de la red: 7.5%.
- *Analytics → Reference Line → Entire Table*, con **Value: `Network AE Rate`** (Average) y la etiqueta `Network average (7.5%)`. Se ve como línea punteada. **No uses `Average` sobre `AE Rate`**: con el filtro Top 15 promediaría solo las barras visibles (~16%) en lugar del 7.5% de la red.
- Tooltip: `<who_atc_category>: <AE Rate> adverse event rate across <Total Treatments> treatments`.

**Hoja 3.3 `Risk Level vs Observed Events`**: es la hoja que demuestra que el score es confiable.
- Columnas: `Risk Level Label`, ordenado por `Risk Level Order`.
- Filas: `Total Treatments` como barra y `AE Rate` como línea con marcadores, en eje dual (*Dual Axis*, sin sincronizar).
- Etiquetas en ambos.
- Sin filtros se espera: Low 4.6%, Medium 11.4% y High 21.0% de tasa observada. Cada nivel casi duplica al anterior.

**Hoja 3.4 `Active Treatments by Specialty and Risk`** *(opcional: no va en el Dashboard 1; ver sección 5)*
- Filtro de la hoja: `status` = Active.
- Filas: `doctor_specialty`. Columnas: `Risk Level Label`. Marca: *Square*.
- Color: `Total Treatments` (secuencial, un solo tono). Etiqueta: `Total Treatments`, de modo que el número se lea sin depender del color.

**Hoja 3.5 `Severity Profile`**
- Filtro de la hoja: `adverse_event_flag` = 1.
- Gráfico: **barras apiladas al 100%**, una barra por nivel de riesgo.
- Filtro: arrastrá `Adverse Event Flag` a *Filters* y dejá solo el valor 1 (si no, aparece "None" en la leyenda).
- Filas: `Risk Level Label` (ordenado por `Risk Level Order`). Columnas: `Adverse Events`.
- Color: `severity`. Orden: clic derecho en `severity` → *Sort → Manual* → Mild, Moderate, Severe, Fatal (si no, se apila en orden alfabético). Colores: *Edit Colors* con un solo tono azul de claro (Mild) a oscuro (Fatal); **no uses la paleta por defecto** (tiene rojo y verde).
- **Porcentaje por barra:** clic en el triángulo (Δ) de `Adverse Events` → *Quick Table Calculation → Percent of Total* y después *Compute Using → Specific Dimensions*, tildando **solo `severity`**. Con *Table (Across)* Tableau calcula el % sobre el total de todos los eventos y las barras no llegan al 100%.
- Etiqueta: clic derecho en la pastilla `Adverse Events` de *Marks → Label* → *Quick Table Calculation → Percent of Total*, con el mismo *Compute Using → severity*; formato *Percentage* con 1 decimal.
- Detalle (tooltip): `reaction_type` y `Adverse Events` (cantidad, sin cálculo).
- Comprobación: cada barra tiene que terminar en 100%.
- Valores esperados (% de eventos por gravedad):

| Nivel | Mild | Moderate | Severe | Fatal | Eventos |
|---|---|---|---|---|---|
| High | 27.8% | 36.3% | 24.3% | 11.6% | 658 |
| Medium | 36.2% | 38.3% | 18.7% | 6.7% | 699 |
| Low | 43.2% | 36.3% | 15.0% | 5.5% | 1,024 |

- Lectura: en riesgo alto, el 36% de los eventos son severos o fatales, contra el 20% en riesgo bajo. El score no solo anticipa *cuántos* eventos hay, sino también que sean más graves.

**Hoja 3.6 `Monitoring Workload`** *(opcional: no va en el Dashboard 1; ver sección 5)*: convierte el score en una decisión: cuántos tratamientos activos hay que atender y con qué intensidad.
- Filtro de la hoja: `status` = Active.
- Filas: `Risk Level Label` (ordenado por `Risk Level Order`). Columnas: `Total Treatments`. Barras horizontales.
- Etiqueta: `Total Treatments` y `monitoring_action` (arrastrá `monitoring_action` a *Label*; como cada nivel tiene una sola acción, no se duplican filas).
- Opcional: `Expected Events` en el tooltip (eventos que se esperan entre esos tratamientos).
- Valores esperados (tratamientos activos): High 696 → Proactive patient outreach · Medium 1,349 → Enhanced case review · Low 4,854 → Routine surveillance. Total 6,899.
- Lectura: el equipo no puede mirar los 6,899 tratamientos activos, pero sí los 696 de riesgo alto; esta hoja muestra el tamaño de ese trabajo.
- La lista nominal de tratamientos **no va en el Dashboard 1**: por droga está en el Deep Dive (hoja 3.18).

### Hojas del Dashboard 2 — Site Monitoring (RBQM)

**Hoja 3.7 `Site Risk Score`** (fuente `Site Risk`)
- Filas: `hospital`. Columnas: `AVG(site_risk_score)`. Orden descendente.
- Etiqueta: `site_risk_level` y `site_action`.
- **Líneas de umbral**, que son el pedido central:
  1. *Analytics → Reference Line → Entire Table → Value: Constant 20*.
     - Etiqueta: *Custom* → `Secondary limit (20)`.
     - Línea: **punteada**, negra, 1.5 pt.
  2. Otra *Reference Line → Constant 50*.
     - Etiqueta: `Action limit (50)`.
     - Línea: **sólida**, negra, 2 pt.
  3. En *Fill Above/Below* no pongas color. El estilo de la línea (punteada o sólida) más la etiqueta de texto alcanzan para diferenciarlas sin color.
- Tooltip: `triggered_by`.
- Resultado esperado:
  - Summit Health System y Northgate University Hospital: 60 (**High**).
  - Harborview Clinical Center: 20 (**Medium**).
  - Lakeview Regional Hospital: 10 (Low).
  - El resto: 0.

**Hoja 3.8 `KRI Status Grid`** (fuente `Site Risk`)
- Filas: `hospital`. Columnas: `kri`. Marca: *Shape*.
- Shape: `status`, con círculo vacío = Within limits, triángulo = Secondary limit breached y cruz/X = Action limit breached.
- Color: `status`, con escala de grises de claro a oscuro.
- Etiqueta: `status`, abreviado con un alias: OK / SECONDARY / ACTION.
- Tooltip: `value`, `z_score`, `secondary_limit`, `action_limit` y `limit_basis`.

**Hoja 3.9 `Adverse Event O/E by Site`** (fuente `Site O/E`)
- Filas: `hospital`. Columnas: `AVG(oe_ratio)`. Marca: *Circle*, tamaño grande.
- **Bandas por sitio**:
  1. *Analytics → Reference Band → Per Cell*.
     - Desde `MIN(secondary_lower)` hasta `MAX(secondary_upper)`.
     - Relleno gris muy claro, etiqueta `Secondary limit (95%)`.
  2. *Reference Line → Per Cell → MIN(qtl_lower)*: línea sólida, etiqueta `Action limit`. Repetir con `MAX(qtl_upper)`.
  3. *Reference Line → Entire Table → Constant 1*, gris fino, etiqueta `Expected (O/E = 1)`.
- Resultado esperado: Summit (0.71) y Northgate (0.68) quedan **fuera** de la línea de acción, del lado de sub-reporte.

**Hoja 3.10 `Programme QTL - Quarterly O/E`** (fuente `Programme QTL`)
- Columnas: `quarter` (dimensión, orden alfabético = cronológico). Filas: `AVG(oe_ratio)`. Marca: *Line* con marcadores.
- Cuatro *Reference Lines → Entire Table*:

| Valor | Estilo | Etiqueta |
|---|---|---|
| `AVG(secondary_lower)` = 0.80 | punteada | `Secondary limit (0.80)` |
| `AVG(secondary_upper)` = 1.21 | punteada | `Secondary limit (1.21)` |
| `AVG(qtl_lower)` = 0.70 | sólida | `QTL (0.70)` |
| `AVG(qtl_upper)` = 1.34 | sólida | `QTL (1.34)` |

- *Annotate → Point* sobre 2026Q3 con el texto: `Below secondary limit: data-entry backlog at 2 sites`.

**Hoja 3.11 (opcional) `O/E Funnel - Live`** (fuente `Treatments`, se recalcula con filtros)
- Detalle: `hospital`. Columnas: `Expected Events`. Filas: `O/E Ratio`. Marca: círculo.
- Agregá `Secondary Lower`, `Secondary Upper`, `Action Lower` y `Action Upper` como *Reference Lines → Per Cell*.
- Sirve, por ejemplo, para filtrar por categoría ATC y ver si el sub-reporte de un sitio se concentra en ciertas drogas.

### Hojas del Dashboard 3 — Drug Deep Dive (fuente `Treatments`)

Todas estas hojas se filtran por **una sola droga**, con el filtro *Drug (single)* de la sección 4. Para armarlas más rápido, duplicá la hoja equivalente del Dashboard 1 (clic derecho en la pestaña → *Duplicate*) y renombrala. Todos los gráficos muestran el `n` (tratamientos o eventos), porque con una sola droga las muestras son chicas: una droga tiene en promedio 859 tratamientos y 54 eventos (mínimo 277 y 21).

**Hoja 3.12 `Drug KPI Banner`**
- Misma construcción que la hoja 3.1, con estas medidas: `Total Treatments`, `Total Patients`, `Adverse Events`, `Hospitalisations`, `AE Rate`, `Network AE Rate`, `AE Rate vs Network (pts)` y `O/E Ratio`. Formato de porcentaje en las tasas y 2 decimales en `O/E Ratio`.
- Ejemplo para verificar (Doxorubicin): 277 tratamientos · 277 pacientes · 61 eventos · 17 hospitalizaciones · 22.0% · 7.5% (red) · +14.5 pts · O/E 1.02.
- Un O/E cercano a 1.0 es esperable: el modelo está calibrado sobre toda la red, así que una droga no se aparta mucho de lo que predice su perfil de pacientes.

**Hoja 3.13 `Drug - Risk Level vs Observed Events`**: duplicado de la hoja 3.3. Con una sola droga las barras muestran cuántos de sus tratamientos caen en cada nivel y qué tasa observada tiene cada uno. Si un nivel tiene menos de 10 eventos, la tasa es poco precisa: lo indica el `n` en la etiqueta.

**Hoja 3.14 `Drug - Severity Profile`**: duplicado de la hoja 3.5, con la cantidad de eventos (no solo el %) en la etiqueta. Ejemplo (Doxorubicin, 61 eventos): Mild 21 · Moderate 21 · Severe 11 · Fatal 8.

**Hoja 3.15 `Drug - Event Rate by Specialty`**
- Filas: `doctor_specialty`. Columnas: `AE Rate`. Orden descendente. Etiqueta: `AE Rate` y `Total Treatments` (ej. `39.3% (n=28)`).
- Filtro de la hoja sobre la medida: `Total Treatments` ≥ 30 (clic derecho en la pastilla → *Filter → At least 30*), para esconder especialidades con muy pocos casos.
- *Analytics → Reference Line → Entire Table → Average de `Network AE Rate`*, con la etiqueta `Network average` y línea punteada.
- Lectura: **cuidado con sobreinterpretar**. Por droga y especialidad hay una mediana de 63 tratamientos y 5 eventos; en Doxorubicin, las tasas por especialidad varían de 11% a 39% con n entre 24 y 36, lo que es ruido y no un hallazgo. Esta hoja sirve para detectar concentraciones grandes, no diferencias pequeñas. Agregá como subtítulo: `Small samples: differences between specialties are not statistically reliable`.

**Hoja 3.16 `Drug - Event Rate by Site`**: igual que la 3.15 con `hospital` en filas. Mismo filtro `Total Treatments` ≥ 30 y misma advertencia en el subtítulo.

**Hoja 3.17 `Drug - Most Frequent Reactions`**
- Filtro de la hoja: `adverse_event_flag` = 1.
- Filas: `reaction_type`. Columnas: `Adverse Events`. Orden descendente. Etiqueta con la cantidad y el % del total.
- Ejemplo (Doxorubicin): Neutropenia 34 · Nausea and vomiting 27.

**Hoja 3.18 `Drug - Review Queue`**: tabla de los tratamientos activos de riesgo alto de la droga elegida (por droga son decenas de filas, no cientos).
- Filtros de la hoja: `status` = Active y `risk_level` = High.
- Columnas: `treatment_id`, `brand_name`, `hospital`, `doctor_specialty`, `Age Group`, `dose_ratio` (2 decimales), `polypharmacy_count`, `risk_score` (formato %), `monitoring_action` y `Model Agreement`. Orden: `risk_score` descendente.
- Si la droga no tiene tratamientos activos en riesgo alto, la tabla queda vacía; mostrá en el título `No high-risk active treatments for this drug` mediante una anotación.

---

## 4. Filtros

Hay **dos grupos de filtros independientes**. Es importante no mezclarlos: si los filtros del Dashboard 1 se aplicaran también a las hojas del Deep Dive, éstas quedarían filtradas sin que el usuario lo sepa.

### 4.1 Filtros del Dashboard 1 (hojas 3.1, 3.2, 3.3 y 3.5)

Son solo **4 filtros**. Para cada uno: clic derecho → *Apply to Worksheets → Selected Worksheets…* y marcá **solo las hojas 3.1, 3.2, 3.3 y 3.5** (no las del Deep Dive):

| Filtro | Campo | Tipo de control | Valor por defecto |
|---|---|---|---|
| Medication class | `who_atc_category` | Multiple values (dropdown) con búsqueda | All |
| Prescriber specialty | `doctor_specialty` | Multiple values (dropdown) | All |
| Site | `hospital` | Multiple values (dropdown) | All |
| Risk level | `Risk Level Label` | Multiple values (dropdown) | All |

Lo que se sacó y por qué:
- **Drug y Brand:** en este dataset cada droga tiene su propia categoría ATC (40 drogas, 40 categorías) y una sola marca, así que *Medication class* ya filtra por droga. En datos reales una categoría agrupa varias drogas y convendría sumar *Drug*.
- **Treatment status = Active:** con ese filtro por defecto, los KPIs dejarían de dar 31,583 tratamientos y 2,381 eventos. El estado "Active" solo se usa dentro de `Active High-Risk Treatments` y de las hojas 3.4, 3.6 y 3.18.
- **Severity, Sex, Age group y Treatment start:** son útiles para el análisis de una droga, así que quedan solo en el Deep Dive (sección 4.2). En el Overview saturan.

### 4.2 Filtros del Dashboard 3 — Drug Deep Dive (hojas 3.12 a 3.18)

Son filtros **propios** del Deep Dive. Para cada uno: clic derecho → *Apply to Worksheets → Selected Worksheets…* y marcá **solo las hojas 3.12 a 3.18**.

| Filtro | Campo | Tipo de control | Valor por defecto |
|---|---|---|---|
| **Drug (single)** | `active_ingredient` | **Single value (dropdown)**, sin la opción "All" (*Customize → Show "All" Value*: desactivado) | Una droga cualquiera, por ejemplo Doxorubicin |
| Treatment status | `status` | Multiple values (list) | All |
| Treatment start | `start_date` | Range of dates | Todo el rango |

Como el selector no admite "All", el Deep Dive nunca se muestra mezclando drogas. Se pueden sumar *Severity*, *Sex* y *Age group* con la misma configuración (*Selected Worksheets* → hojas 3.12 a 3.18) para comparar subgrupos de una droga, teniendo presente que cada filtro adicional reduce el n.

### 4.3 Interacciones entre hojas

- El filtro **Site** (del Dashboard 1) tiene que aplicar también al Dashboard 2: *Apply to Worksheets → Selected Worksheets* y marcar las hojas 3.7 a 3.9, que funcionan gracias a la relación de blending del paso 1.4. La hoja 3.10 (QTL del programa) queda siempre sin filtrar (ver paso 1.5). Agregale como subtítulo: `Programme-wide indicator: not affected by filters`.
- **Dashboard actions**: *Dashboard → Actions → Add Action → Filter*.
  - `Select on Category`: origen `Adverse Event Rate by Medication Class`, destino las hojas 3.1, 3.3 y 3.5, acción *Select*. Un clic en una categoría filtra el resto.
  - `Select on Site`: origen `Site Risk Score`, destino `KRI Status Grid`.
  - **`Go to Drug Deep Dive`** (puente entre dashboards): *Add Action → Filter*, origen el Dashboard 1 → hoja `Adverse Event Rate by Medication Class`, destino el Dashboard 3 → hojas 3.12 a 3.18, acción *Select*, campos de destino `who_atc_category` → `active_ingredient` (ver nota abajo). Así, un clic en una barra del Overview abre el análisis de esa droga.
  - Activá *Clearing the selection will: Show all values* en las dos primeras; en la del Deep Dive elegí *Leave the filter*, para que la droga elegida no se borre.

  > Como cada droga tiene su propia categoría, el clic en una barra por `who_atc_category` selecciona exactamente una droga. Si tu versión de Tableau no deja asociar campos con nombre distinto, usá el filtro *Drug (single)* directamente o creá el campo calculado `Drug Key = [active_ingredient]` y usalo como origen de la acción.

---

## 5. Armado de los dashboards

- **Tamaño:** *Automatic* para publicar en web, o *Fixed 1400 × 1000*.
- **Título** (objeto *Text*, 22 pt, negrita):
  ```
  Pastela Pharmaceuticals — Pharmacovigilance Risk Monitor
  ```
- **Subtítulo** (12 pt, gris oscuro, no gris claro, por contraste):
  ```
  Synthetic portfolio dataset · 20,000 registered patients · 10 sites · Data snapshot: 17 Aug 2026
  ```
- **Layout del Dashboard 1 — Treatment Risk Overview.** Un solo propósito: responder tres preguntas, una por gráfico, sin repetir ninguna:

  | Pregunta | Hoja |
  |---|---|
  | ¿Dónde se concentra el riesgo? | 3.2 Adverse Event Rate by Medication Class |
  | ¿El score funciona? | 3.3 Risk Level vs Observed Events |
  | ¿Los eventos de riesgo alto son más graves? | 3.5 Severity Profile |

  Más la banda de KPIs (3.1), 4 filtros y el recuadro "What does the risk score mean?". **Las hojas 3.4 y 3.6 no se colocan** (la 3.6 ya está resumida en el KPI `Active High-Risk Treatments`; la 3.4 se cubre en el Deep Dive). No hace falta borrarlas.

  ```
  +-------------------------------------------------------------+
  | Título (22 pt)               [Go to Deep Dive] [Site Monitoring]
  | Subtítulo (12 pt)                                           |
  +-------------------------------------------------------------+
  | Filtros: [Medication class] [Specialty] [Site] [Risk level] |
  +-------------------------------------------------------------+
  | 3.1 KPI Banner (7 números, ~110 px de alto)                 |
  +------------------------------+------------------------------+
  | 3.2 AE rate by class         | 3.3 Risk level vs observed   |
  | (barras, top 15)             | events                       |
  +------------------------------+------------------------------+
  | 3.5 Severity profile         | Recuadro: What does the risk |
  | (barras apiladas al 100%)    | score mean? (texto)          |
  +------------------------------+------------------------------+
  ```

  **Cómo armarlo en Tableau, paso a paso:**
  1. *Dashboard → New Dashboard*. Abajo a la izquierda, *Size → Fixed size → 1400 × 1000*. Nombralo `Treatment Risk Overview`.
  2. En el panel izquierdo, pestaña *Layout*: vas a trabajar con **contenedores** (horizontales y verticales), no con objetos sueltos, porque así los bloques se ordenan solos.
  3. Arrastrá un contenedor **Vertical** al lienzo; todo lo demás va adentro. Cada fila del esquema es un contenedor **Horizontal** dentro del vertical.
  4. **Fila del título:** un objeto *Text* (título y subtítulo, ver arriba) y a la derecha dos objetos *Navigation*.
  5. **Fila de filtros:** primero colocá las hojas (pasos 6 a 8). Después, en la tarjeta de la hoja 3.2, menú ▾ → *Filters* y tildá los 4 filtros: aparecen como tarjetas. Arrastralas a un contenedor horizontal bajo el título y en el menú de cada una elegí *Multiple Values (Dropdown)*. Como los filtros ya se aplican a las 4 hojas (sección 4.1), no hace falta repetir las tarjetas.
  6. **KPI Banner:** arrastrá la hoja 3.1 bajo los filtros. En el menú de la tarjeta, *Fit → Entire View*. Fijá la altura en ~110 px.
  7. **Dos gráficos:** un contenedor horizontal con 3.2 (izquierda, ~55% del ancho) y 3.3 (derecha, ~45%).
  8. **Dos elementos abajo:** otro contenedor horizontal con 3.5 (izquierda) y un objeto *Text* con el recuadro de la sección 7 (derecha).
  9. **Títulos:** en cada hoja ya desactivaste *Show Title*; en el dashboard activalo por tarjeta (menú ▾ → *Title*) con el texto que dice qué mirar, no solo el nombre del gráfico.
  10. **Aire:** *Layout → Padding* de 6–8 px y borde gris claro entre bloques. Si algo se ve apretado, **sacá elementos, no los achiques**.
  11. **Prueba:** elegí una categoría en el filtro. Tienen que cambiar los KPIs y las tres hojas, no el título.

- **Layout del Dashboard 2:**
  - Fila 1: título.
  - Fila 2: Site Risk Score (izquierda) y KRI Status Grid (derecha).
  - Fila 3: O/E by Site (izquierda) y Programme QTL (derecha).
- **Layout del Dashboard 3 — Drug Deep Dive** (título `Pastela Pharmaceuticals — Drug Deep Dive`):
  - Fila 1: título, filtro *Drug (single)* bien visible a la izquierda y subtítulo `Compared with the whole network · Monitoring data, not a controlled trial`.
  - Fila 2: Drug KPI Banner a todo el ancho.
  - Fila 3: Risk Level vs Observed Events (izquierda) y Severity Profile (derecha).
  - Fila 4: Event Rate by Specialty (izquierda) y Event Rate by Site (derecha).
  - Fila 5: Most Frequent Reactions (izquierda) y Review Queue (derecha).
- **Navegación:** objeto *Navigation* (botón) en cada dashboard:
  - Dashboard 1: `Go to Drug Deep Dive →` y `Go to Site Monitoring →`.
  - Dashboard 3: `← Back to Treatment Risk Overview` y `Go to Site Monitoring →`.
  - Dashboard 2: `← Back to Treatment Risk Overview`.

---

## 6. Accesibilidad (requisito de Helena)

Lista de chequeo antes de publicar:

- [ ] Ninguna información depende solo del color: los niveles llevan símbolo (▲ ● ▽) y texto, y las líneas de umbral se distinguen por estilo (punteada o sólida) y etiqueta.
- [ ] Paleta *Color Blind* o escala de grises; sin combinaciones rojo/verde.
- [ ] Contraste: texto negro o gris oscuro (#333 o más oscuro) sobre fondo blanco.
- [ ] Fuentes ≥ 12 pt, títulos ≥ 15 pt y BANs ≥ 28 pt.
- [ ] Todos los gráficos tienen etiquetas con el número, no solo el tamaño de barra.
- [ ] Tooltips con frases completas.
- [ ] Cada gráfico muestra sus números en etiquetas, así que se puede leer sin depender de la forma ni del color.
- [ ] Cada gráfico tiene un título que dice qué mirar, no solo qué es.

---

## 7. Recuadro "What does the risk score mean?" (requisito de Marcus / auditoría)

Va como objeto *Text* en el Dashboard 1, con borde gris:

```
What does the risk score mean?
The risk score is the estimated probability that a treatment will be followed by a
reported adverse event, based on patient age, dose relative to the usual dose for that
medication, number of treatments, medication class, route, frequency and sex.
It is a PRIORITISATION tool for the monitoring team: it decides which treatments to
review first. It is NOT a diagnosis and NOT a prescribing recommendation.
Risk levels are pre-specified and tied to actions:
  ▲ High (top 10%)   → Proactive patient outreach
  ● Medium (next 20%) → Enhanced case review
  ▽ Low               → Routine surveillance
The score is calibrated: across all treatments, the number of events it predicts
matches the number observed (observed/expected = 1.00).
```

En el Dashboard 3 (Deep Dive):

```
How to read this page
Everything on this page refers to ONE drug, compared with the whole network.
This is post-marketing safety monitoring, not a controlled clinical trial: there is
no untreated control group, so differences are descriptive, not causal.
Each drug has a few hundred treatments and tens of events. Rates based on small
numbers (see n on each bar) can move a lot by chance: use them to spot large
concentrations, not small differences.
```

En el Dashboard 2:

```
How to read site monitoring
Each site is checked on 5 Key Risk Indicators. Dashed line = secondary limit (early
warning: review and watch). Solid line = action limit (documented investigation).
Site Risk Score = KRI points / maximum × 100.
Low < 20: routine central monitoring · Medium 20–49: targeted remote review ·
High ≥ 50: for-cause audit.
```

---

## 8. Hallazgos para mostrar

Estos son los insights que el dashboard debe hacer evidentes. **No los pegues en el dashboard** (lo saturan): usalos en el blog, en el resumen ejecutivo o en la descripción de Tableau Public.

```
Key findings
1. 2,381 adverse events across 31,583 treatments (7.5%) in 17,060 patients treated
   by 200 prescribers at 10 sites, with 40 medications.
2. Risk is concentrated: antineoplastics (anthracyclines 22.0%, platinum 21.6%),
   immunosuppressants and anticoagulants show the highest event rates.
3. The risk score works as a triage tool: observed event rates are 4.6% (Low),
   11.4% (Medium) and 21.0% (High). High-risk treatments have 8x the
   hospitalisation rate of Low-risk ones (5.6% vs 0.7%).
4. 696 of 6,899 active treatments are currently High risk and flagged for proactive
   patient outreach.
5. Two sites (Summit Health System, Northgate University Hospital) breach the
   action limit: ~3 in 4 reports arrive after 15 days and they report only
   ~70% of the events expected for their patients — a data-entry backlog,
   not safer patients. Recommended: for-cause audit.
6. Harborview Clinical Center: 89.5% female patients vs ~46% at the median site.
   Data capture is normal (O/E 1.02); the patient mix needs explanation.
7. Programme QTL: the latest quarter fell below the secondary limit (O/E 0.78),
   an early warning explained by the backlog at the two delayed sites.
```

---

## 9. Publicar en Tableau Public y llevarlo al blog

1. *File → Save to Tableau Public As…* con el nombre `Pastela Pharmacovigilance Risk Monitor`. Tableau Public guarda una extracción de los datos; el `.hyper` funciona directo.
2. En el perfil de Tableau Public: *Settings* → dejar visible y activar *Allow Access* para que se pueda descargar.
3. Copiá la URL pública, que tiene la forma `https://public.tableau.com/app/profile/<usuario>/viz/<nombre>/<dashboard>`, y pasámela. Reemplaza el placeholder `TABLEAU_PUBLIC_URL` en los 4 idiomas del post.
4. **Captura para el blog:**
   - Dashboard 1 sin filtros, a ~1600 px de ancho.
   - Guardala como `public/images/blog/farmacovigilancia/tableau-dashboard.png` en el proyecto del portfolio. El post ya apunta a esa ruta.
   - Opcional: capturas del Dashboard 3 (con una droga elegida, por ejemplo Doxorubicin) como `tableau-drug-deep-dive.png` y del Dashboard 2 como `tableau-site-monitoring.png`.
5. Rebuild del sitio (`npm run build`) y deploy de `dist/` a InfinityFree.
