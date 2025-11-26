# Contracts Access Guide

Una guía completa sobre cómo acceder y ver los contratos detallados desde diferentes vistas del dashboard.

## 📊 Vista General

El sistema tiene múltiples formas de acceder y explorar contratos en detalle:

```
Visualization Dashboard
├── 📊 Temporal Heatmap
│   └── Click on any cell → View contracts from that date
├── 🗺️ Geographic Map
│   ├── Click region card → View Contracts button → Filtered list
│   └── Click table row → View contracts for that location
└── 📋 All Contracts
    └── Browse all contracts with advanced filters
```

## 🔄 Flujos de Acceso

### 1. Desde el Heatmap Temporal (Temporal Heatmap)

**¿Qué es?** Grid tipo GitHub mostrando actividad diaria de contratos.

**Cómo acceder:**
1. Navega a `/analytics`
2. Permanece en la pestaña "📊 Temporal Heatmap"
3. **Hover** sobre cualquier celda para ver detalles
4. **Click** en la celda para ver todos los contratos de ese día

**Ejemplo:**
```
URL generada: /contracts/filtered?date=2025-11-26
```

**Información que ves:**
- Fecha de publicación del contrato
- Número de contratos publicados ese día
- Riesgo promedio (color-coded)
- Presupuesto total

### 2. Desde el Mapa Geográfico (Spain Geographic Map)

#### Opción A: Clickear en la tarjeta de región

**Pasos:**
1. Ve a `/analytics` → Tab "🗺️ Spain Geographic Map"
2. Busca la región (ej: "Cataluña", "Madrid")
3. Lee los datos de la tarjeta:
   - Presupuesto total
   - Número de contratos
   - Riesgo promedio
4. Haz click en el botón azul "📋 View Contracts →"

**Resultado:**
```
URL generada: /contracts/filtered?region=Cataluña
Ves: Todos los contratos de esa región
```

#### Opción B: Click en la etiqueta de región para filtrar tabla

**Pasos:**
1. En la tarjeta de región, haz click en el nombre
2. La tabla abajo se filtra mostrando solo esa región
3. Mira las provincias y municipios

**Resultado:**
La tabla abajo se filtra para mostrar solo esa región.

#### Opción C: Click en una fila de la tabla

**Pasos:**
1. Desplázate a "📊 Detailed Locations" table
2. Haz click en cualquier fila (ej: "Sevilla" en "Andalusía")
3. Automáticamente navega a contracts filtrados

**Resultado:**
```
URL generada: /contracts/filtered?region=Andalusía&municipality=Sevilla
Ves: Contratos específicos de esa ciudad
```

### 3. Vista de Contratos Filtrados

**URL:** `/contracts/filtered`

**Parámetros soportados:**
- `?date=2025-11-26` - Contratos por fecha
- `?region=Cataluña` - Contratos por región
- `?municipality=Barcelona` - Contratos por municipio
- Combinables: `?region=Madrid&municipality=Madrid`

**Características:**
- Vista en tarjetas (cards) mostrando:
  - Título del contrato
  - ID externo
  - Tipo de contrato
  - Autoridad contratante
  - Presupuesto
  - Riesgo (badge)
  - Fecha de publicación
  - Estado
- Link "View Details →" en cada tarjeta
- Botones de navegación atrás/adelante

### 4. Vista de Contratos General

**URL:** `/contracts`

**Características:**
- Lista completa de todos los contratos
- Filtros avanzados:
  - 🔍 Search (ID, título)
  - 🌍 Region
  - 📋 Contract Type (Works, Services, Supplies, etc.)
  - ⚠️ High Risk Only
  - 🚨 Overpriced Only
- Tabla con columnas:
  - ID → Click para ver detalles
  - Título
  - Tipo
  - Autoridad
  - Presupuesto
  - Riesgo
  - Estado
  - Fecha

### 5. Vista de Detalle de Contrato

**URL:** `/contracts/{id}`

**Información completa:**
- Título y ID externo
- **Risk Analysis:**
  - Overall Risk Score
  - Corruption Risk
  - Delay Risk
  - Financial Risk
- **Contract Details:**
  - Budget
  - Awarded Amount (si aplica)
  - Procedure Type
  - Source Platform
- **Timeline:**
  - Publication Date
  - Deadline
  - Award Date (si aplica)
- **Flags:**
  - Overpriced ⚠️
  - Has Amendments
  - Has Delays
  - High Risk
- **Parties:**
  - Contracting Authority (región, provincia, municipio)
  - Awarded To (provider con risk score)
- **Description** (si aplica)
- **Amendments** (listado completo si existen)
- **External Link** (a fuente original)

## 🎯 Casos de Uso Comunes

### Caso 1: "Quiero saber qué contratos se publicaron hoy"

1. Ve a `/analytics`
2. En el heatmap, mira la celda del día actual
3. Click en esa celda
4. Ves todos los contratos publicados hoy

### Caso 2: "Quiero ver contratos de riesgo alto en Andalucía"

1. Ve a `/analytics` → Tab Geographic Map
2. Busca "Andalusía"
3. Lee el "⚠️ Avg Risk" (si es > 50, es riesgo alto)
4. Click botón "📋 View Contracts →"
5. Ves los contratos de Andalucía
6. En la lista general, puedes filtrar por "High Risk Only"

### Caso 3: "Quiero explorar contratos de un municipio específico"

1. Ve a `/analytics` → Tab Geographic Map
2. Desplázate a la tabla "📊 Detailed Locations"
3. Encuentra el municipio (ej: "Barcelona")
4. Click en la fila
5. Ves todos los contratos de Barcelona

### Caso 4: "Quiero comparar presupuestos entre regiones"

1. Ve a `/analytics` → Tab Geographic Map
2. Lee las tarjetas de región ordenadas por presupuesto (Mayor a menor)
3. Compara visualmente con las barras de progreso
4. Haz click en una región para ver sus contratos

## 🔗 Rutas Disponibles

| Ruta | Descripción | Parámetros |
|------|-------------|-----------|
| `/analytics` | Dashboard principal | - |
| `/contracts` | Todos los contratos | query filters |
| `/contracts/filtered` | Contratos filtrados desde viz. | date, region, municipality |
| `/contracts/{id}` | Detalle de un contrato | - |
| `/providers` | Lista de proveedores | - |
| `/providers/{id}` | Detalle de un proveedor | - |

## 💡 Tips & Tricks

### Tip 1: Usar browser back button
Una vez que accedes a contratos filtrados desde el heatmap, puedes usar el botón atrás del navegador para volver al dashboard.

### Tip 2: Abrir en nueva pestaña
Click derecho en una celda del heatmap → "Open in new tab" para comparar múltiples fechas.

### Tip 3: URLs directas
Puedes compartir URLs directas:
- Contratos de Barcelona: `https://tuapp.com/contracts/filtered?region=Cataluña&municipality=Barcelona`
- Contratos del 26 nov: `https://tuapp.com/contracts/filtered?date=2025-11-26`

### Tip 4: Combinar filtros
En `/contracts`, puedes:
- Buscar por ID/título Y
- Filtrar por región Y
- Filtrar por tipo Y
- Solo high risk

## 🎨 Indicadores Visuales

### Colores de Riesgo (usado en todo el sistema)

| Color | Rango | Significado |
|-------|-------|-------------|
| 🟢 Verde | 0-20 | Minimal risk |
| 🟡 Amarillo | 20-40 | Low risk |
| 🟠 Naranja | 40-60 | Medium risk |
| 🔴 Rojo | 60+ | High/Critical risk |

### Badges de Estado

| Badge | Significado |
|-------|------------|
| 📋 Published | Contrato publicado, aceptando ofertas |
| ⏳ In Progress | Contrato en ejecución |
| ✅ Completed | Contrato completado |
| ⚠️ Cancelled | Contrato cancelado |

## 📱 Responsive Design

Todas las vistas están optimizadas para:
- 📱 Mobile (< 640px)
- 💻 Tablet (640px - 1024px)
- 🖥️ Desktop (> 1024px)

En mobile:
- Heatmap: scroll horizontal para ver más días
- Geographic Map: cards en una columna
- Tabla: scroll horizontal para ver todas las columnas

## 🔄 Flujo Recomendado para Análisis

```mermaid
1. Dashboard (/analytics)
   ↓
2. Explorar Heatmap (¿Qué días tienen mucha actividad?)
   ↓
3. Click en día interesante → Ver contratos de ese día
   ↓
4. Volver al Dashboard
   ↓
5. Explorar Geographic Map (¿Qué regiones tienen presupuesto alto?)
   ↓
6. Click en región → Ver contratos de esa región
   ↓
7. Clickear una fila específica → Ver municipio en detalle
   ↓
8. Click en un contrato → Ver detalles completos
   ↓
9. Review del proveedor (si asignado)
```

## ❓ FAQ

**P: ¿Cómo accedo a un contrato específico?**
R: Navega a `/contracts`, usa search para encontrar por ID o título, haz click en el ID.

**P: ¿Puedo filtrar por múltiples regiones?**
R: Actualmente la página filtrada soporta una región. Para ver múltiples, navega a `/contracts` y usa los filtros generales.

**P: ¿Qué significa "High Risk" en el heatmap?**
R: Color rojo significa que el riesgo promedio de los contratos ese día está por encima de 60/100.

**P: ¿Cómo veo contratos de hace 6 meses?**
R: En el heatmap, cambia el selector "Time Period" a "Last 6 months" para ver hasta 180 días atrás.

**P: ¿Puedo exportar la lista de contratos?**
R: Actualmente no, pero puedes copiar URLs filtradas y compartirlas. Contacta al admin para export features.

---

**Última actualización:** 2025-11-26
