# Frontend Visualization Components

Complete React components for displaying contract data heatmaps and geographic distribution across Spain.

## 📦 Files Included

1. **TemporalHeatmap.tsx** - GitHub-style heatmap showing contract activity over time
2. **SpainGeographicMap.tsx** - Regional distribution with budgets and risk metrics
3. **VisualizationDashboard.tsx** - Main dashboard combining both visualizations
4. **README.md** - This file

## ⚙️ Installation

### 1. Install Dependencies

```bash
npm install recharts
```

Optional (for advanced features):
```bash
npm install leaflet react-leaflet geojson-bounds
npm install --save-dev @types/geojson
```

### 2. Copy Components

Copy the three `.tsx` files to your React project:

```bash
src/
├── components/
│   ├── TemporalHeatmap.tsx
│   ├── SpainGeographicMap.tsx
│   └── VisualizationDashboard.tsx
```

### 3. Make sure you have Tailwind CSS

The components use Tailwind CSS classes. If you don't have it installed:

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

## 🚀 Quick Start

### Basic Usage

```tsx
// In your app/page
import { VisualizationDashboard } from './components/VisualizationDashboard';

export default function AnalyticsPage() {
  return <VisualizationDashboard />;
}
```

### Individual Components

```tsx
// Just the heatmap
import { TemporalHeatmap } from './components/TemporalHeatmap';

export default function Page() {
  return (
    <TemporalHeatmap
      granularity="daily"
      days={180}
    />
  );
}
```

```tsx
// Just the map
import { SpainGeographicMap } from './components/SpainGeographicMap';

export default function Page() {
  return <SpainGeographicMap />;
}
```

## 🔌 Backend API Requirements

The components expect these endpoints to exist:

### 1. Temporal Heatmap Endpoint

```
GET /api/v1/analytics/temporal_heatmap/?granularity=daily&days=180
```

**Query Parameters:**
- `granularity` (optional): 'daily' or 'weekly' (default: 'daily')
- `days` (optional): Number of days to look back (default: 180)

**Response:**
```json
[
  {
    "date": "2025-08-01",
    "total_contracts": 1,
    "high_risk": 0,
    "medium_risk": 0,
    "low_risk": 1,
    "total_budget": 2500000.0,
    "avg_risk": 21.75
  },
  ...
]
```

### 2. Geographical Distribution Endpoint

```
GET /api/v1/analytics/geographical_distribution/
```

**Response:**
```json
{
  "detailed": [
    {
      "region": "La Rioja",
      "province": "La Rioja",
      "municipality": "Logroño",
      "total_contracts": 6,
      "total_budget": 15000000.0,
      "awarded_amount": 14500000.0,
      "avg_risk_score": 16.79,
      "high_risk_count": 1
    },
    ...
  ],
  "summary_by_region": {
    "La Rioja": {
      "total_budget": 15000000.0,
      "avg_risk_score": 16.79,
      "high_risk_count": 1,
      "total_contracts": 6
    },
    ...
  }
}
```

## 🎨 Customization

### Change Colors

Edit the `getRiskColor()` function in each component:

```tsx
const getRiskColor = (riskScore: number): string => {
  if (riskScore >= 70) return '#YOUR_COLOR';
  // ... modify as needed
};
```

### Modify Layout

All components use Tailwind CSS. Replace classes like:
- `grid-cols-2` → `grid-cols-3` (number of columns)
- `p-6` → `p-4` (padding)
- `rounded-lg` → `rounded-xl` (border radius)

### Change Font Sizes

Replace Tailwind size classes:
- `text-2xl` → `text-3xl` (larger)
- `text-lg` → `text-base` (smaller)

## 📊 Component Props

### TemporalHeatmap

```tsx
interface TemporalHeatmapProps {
  granularity?: 'daily' | 'weekly';  // Default: 'daily'
  days?: number;                      // Default: 180
}
```

### SpainGeographicMap

```tsx
// No props - configures itself from API data
```

### VisualizationDashboard

```tsx
// No props - manages its own state and includes both visualizations
```

## 🐛 Troubleshooting

### "Module not found: Can't resolve 'recharts'"

```bash
npm install recharts
```

### "Tailwind CSS classes not working"

Make sure your `tailwind.config.js` includes:
```js
content: [
  "./src/**/*.{js,ts,jsx,tsx}",
]
```

### API returns 404

Make sure:
1. Backend is running on `localhost:8000`
2. Endpoints are registered in your Django URLs
3. Check: `http://localhost:8000/api/v1/analytics/temporal_heatmap/`

### Data not loading

Check browser console (F12) for:
1. Network tab - is the API returning data?
2. Console tab - any JavaScript errors?
3. Response status should be 200, not 404 or 500

## 🔄 Data Refresh

Components fetch data on mount. To refresh:

```tsx
// In your parent component
import { VisualizationDashboard } from './components/VisualizationDashboard';

export default function Page() {
  const [key, setKey] = useState(0);

  const handleRefresh = () => {
    setKey(prev => prev + 1);
  };

  return (
    <div>
      <button onClick={handleRefresh}>Refresh Data</button>
      <VisualizationDashboard key={key} />
    </div>
  );
}
```

## 📈 Features

### TemporalHeatmap

✅ GitHub-style grid heatmap
✅ Daily/weekly granularity toggle
✅ Risk-based color coding
✅ Hover tooltips with detailed info
✅ Bar chart showing risk distribution
✅ Line chart showing risk trend
✅ Summary statistics

### SpainGeographicMap

✅ Regional summary cards
✅ Click to filter detailed table
✅ Sortable detailed table
✅ Budget visualization
✅ Risk scoring with color codes
✅ High-risk contract tracking
✅ Budget bar for each region

### VisualizationDashboard

✅ Tab-based navigation
✅ Unified control panel for heatmap
✅ Responsive design
✅ Mobile-friendly layout
✅ Easy to extend

## 🎯 Next Steps

### Add Leaflet Map (Optional)

For an actual interactive map of Spain:

1. Install Leaflet:
```bash
npm install leaflet react-leaflet
```

2. Download Spanish regions GeoJSON:
```bash
# From Natural Earth or:
curl -o spain.geojson https://raw.githubusercontent.com/deldersveld/topojson/master/countries/spain/spain-provinces.json
```

3. Add to SpainGeographicMap.tsx:
```tsx
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';

<MapContainer center={[40, -3.7]} zoom={5}>
  <TileLayer
    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
  />
  <GeoJSON
    data={spainGeoJSON}
    style={(feature) => ({
      color: getRiskColor(regionData[feature.properties.name]),
      fillOpacity: 0.7,
    })}
  />
</MapContainer>
```

### Add Real-time Updates

```tsx
useEffect(() => {
  const interval = setInterval(() => {
    fetchData();
  }, 5 * 60 * 1000); // Refresh every 5 minutes

  return () => clearInterval(interval);
}, []);
```

### Add Export Functionality

```tsx
const exportAsCSV = () => {
  const csv = data.map(d => `${d.date},${d.total_contracts},...`).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  // ... download logic
};
```

## 📝 License

Use freely in your project.

## 🆘 Support

For issues:
1. Check the troubleshooting section above
2. Check browser console (F12)
3. Check API endpoint is responding
4. Verify Tailwind CSS is properly configured

---

**Ready to visualize your data!** 🚀
