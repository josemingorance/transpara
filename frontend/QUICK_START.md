# 🚀 Quick Start - Contracts Access System

## En 30 segundos

Ahora puedes **clickear en las visualizaciones del dashboard** para ver contratos en detalle:

1. **Heatmap**: Click en celda → Ve contratos de ese día
2. **Mapa**: Click en botón o fila → Ve contratos de esa región
3. **Tabla**: Click en ubicación → Ve contratos específicos

## 🎯 Las 3 Formas de Acceder

### 1️⃣ Por Fecha (Temporal Heatmap)

```
/analytics
   ↓ (Tab "📊 Temporal Heatmap")
   ↓ (Click en cualquier celda)
/contracts/filtered?date=2025-11-26
   ↓ (Click en contrato)
/contracts/{id}
```

### 2️⃣ Por Región (Geographic Map - Button)

```
/analytics
   ↓ (Tab "🗺️ Spain Geographic Map")
   ↓ (Click botón "📋 View Contracts →")
/contracts/filtered?region=Cataluña
   ↓ (Click en contrato)
/contracts/{id}
```

### 3️⃣ Por Municipio (Geographic Map - Table)

```
/analytics
   ↓ (Tab "🗺️ Spain Geographic Map")
   ↓ (Click en fila de tabla)
/contracts/filtered?region=Cataluña&municipality=Barcelona
   ↓ (Click en contrato)
/contracts/{id}
```

## 📁 Archivos Nuevos

| Archivo | Propósito |
|---------|-----------|
| `components/ContractsViewer.tsx` | Muestra contratos filtrados en cards |
| `app/contracts/filtered/page.tsx` | Página con contratos filtrados |
| `CONTRACTS_ACCESS_GUIDE.md` | Guía completa (lee si necesitas detalles) |
| `CONTRACTS_FEATURES_SUMMARY.md` | Resumen técnico |

## 🎨 Lo que Verás

### Cuando haces click en el heatmap:

```
Contracts from 2025-11-26
2 contract(s) found

[Contrato 1]
  📋 ID-001 | Obra de construcción
  🏢 Ayuntamiento de Madrid
  💰 €500,000
  ⚠️  Risk: 45 (Medium)
  📅 Published: Nov 26, 2025
  ✅ Status: Published
  View Details →

[Contrato 2]
  ...
```

### Cuando haces click en una región:

```
Contracts in Cataluña
15 contract(s) found

[Tarjeta 1] [Tarjeta 2] [Tarjeta 3]
[Tarjeta 4] [Tarjeta 5] [Tarjeta 6]
...

Showing 15 of 15 contracts
```

## 🔗 URLs Importantes

```
http://localhost:3000/analytics
   └─ Dashboard principal (donde empiezas)

http://localhost:3000/contracts/filtered?date=2025-11-26
   └─ Contratos filtrados por fecha

http://localhost:3000/contracts/filtered?region=Cataluña
   └─ Contratos filtrados por región

http://localhost:3000/contracts/filtered?region=Cataluña&municipality=Barcelona
   └─ Contratos filtrados por región + municipio

http://localhost:3000/contracts/123
   └─ Detalle completo de un contrato
```

## ⚡ Tips Rápidos

✨ **Hover en el heatmap** para ver tooltip con detalles
✨ **Region name** en tarjeta → filtra tabla debajo
✨ **Click botón azul** en tarjeta → ve todos los contratos
✨ **Click fila tabla** → va directo a municipio filtrado
✨ **Back button** → vuelve al analytics dashboard

## 🧪 Prueba Ahora

1. Abre: `http://localhost:3000/analytics`
2. Haz hover en una celda del heatmap
3. Click en la celda
4. ¡Ves los contratos de ese día!
5. Click en un contrato
6. ¡Ves todos los detalles!

## 📚 Necesitas Más Info?

- **Guía completa**: Lee `CONTRACTS_ACCESS_GUIDE.md`
- **Detalles técnicos**: Lee `CONTRACTS_FEATURES_SUMMARY.md`
- **Código**: Revisa `components/ContractsViewer.tsx`

## 🎯 Resumen

| Acción | Resultado |
|--------|-----------|
| Click celda heatmap | Contratos por fecha |
| Click botón región | Contratos por región |
| Click fila tabla | Contratos por municipio |
| Click contrato | Detalle completo |

---

**¡Eso es todo!** Ahora puedes explorar contratos desde las visualizaciones.

Abre `/analytics` y empieza a clickear. ✨
