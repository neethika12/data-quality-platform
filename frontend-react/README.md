# Data Quality Platform - React Frontend

Professional React frontend for the Data Quality & Drift Detection Platform.

## Features

- 🎨 Modern, responsive UI with Tailwind CSS
- 📊 Interactive dashboards and visualizations
- 🔔 Real-time alerts and notifications
- 📈 Trend analysis and metrics tracking
- 📄 Report generation and export
- ⚙️ Configuration management
- 🌙 Dark mode support
- 🚀 Fast performance with Vite

## Architecture

- **Vite**: Ultra-fast build tool and dev server
- **React 18**: Modern component-based UI
- **React Router**: Client-side navigation
- **Tailwind CSS**: Utility-first styling
- **Lucide React**: Beautiful SVG icons
- **Axios**: API communication

## Setup

### Prerequisites

- Node.js 18+
- Backend running on `http://localhost:8000`

### Installation

```bash
cd frontend-react
npm install
```

### Development

```bash
npm run dev
```

Visit `http://localhost:3000` in your browser.

### Build

```bash
npm run build
```

Output is in the `dist/` directory.

## Project Structure

```
frontend-react/
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── Layout.jsx       # Main layout with sidebar
│   │   ├── Card.jsx         # Card container
│   │   ├── Button.jsx       # Button component
│   │   ├── MetricCard.jsx   # KPI card
│   │   ├── Alert.jsx        # Alert component
│   │   ├── Loading.jsx      # Loading spinner
│   │   └── ErrorDisplay.jsx # Error message
│   ├── pages/               # Page components
│   │   ├── Dashboard.jsx    # Main dashboard
│   │   ├── DataExplorer.jsx # Dataset management
│   │   ├── DriftAnalysis.jsx
│   │   ├── QualityMetrics.jsx
│   │   ├── Alerts.jsx
│   │   ├── MetricsTrends.jsx
│   │   ├── Comparison.jsx
│   │   ├── Reports.jsx
│   │   └── Configuration.jsx
│   ├── utils/
│   │   └── api.js           # API client
│   ├── App.jsx              # Root component with routing
│   ├── main.jsx             # Entry point
│   └── index.css            # Global styles
├── index.html
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── package.json
```

## API Integration

The frontend communicates with the backend via REST API:

- `GET /api/datasets` - List datasets
- `POST /api/datasets/upload` - Upload dataset
- `POST /api/analysis/{id}` - Run quality analysis
- `GET /api/datasets/{id}/latest-result` - Get latest results
- `GET /api/alerts/dataset/{id}` - Get alerts
- `POST /api/reports/generate` - Generate report
- More in `src/utils/api.js`

## Pages

### Dashboard
Real-time overview of data quality with:
- KPI cards (rows, columns, quality score)
- Quality gauge visualization
- Alert summary
- Key metrics breakdown

### Data Explorer
Upload and manage datasets:
- File upload (CSV, Parquet, Excel)
- Dataset listing
- Delete datasets

### Drift Analysis
Detect distribution changes:
- Drift detection results
- Test types and p-values
- Statistical summary

### Quality Metrics
Detailed quality measurements:
- Completeness
- Validity
- Accuracy
- Uniqueness

### Alerts
Monitor and manage alerts:
- Critical alerts
- Warnings
- Info messages
- Acknowledge alerts

### Metrics Trends
Track metrics over time:
- Quality score trends
- Historical comparison
- Detailed metrics table

### Comparison
Compare datasets:
- Select baseline and current
- Quality score differences
- Detailed comparison

### Reports
Generate and export reports:
- Text format
- JSON format
- Download capability

### Configuration
System settings:
- Quality thresholds
- Email alerts
- SMTP configuration

## Styling

Uses Tailwind CSS with custom colors:
- Primary: `#667eea` (Purple)
- Secondary: `#764ba2` (Dark Purple)
- Success: `#52c41a` (Green)
- Danger: `#ff6b6b` (Red)
- Warning: `#ffa94d` (Orange)

## Browser Support

- Chrome/Edge: Latest
- Firefox: Latest
- Safari: Latest

## Performance

- Code splitting via Vite
- Lazy loading of routes
- Optimized builds with tree-shaking
- CSS purging with Tailwind

## Troubleshooting

**Frontend won't connect to backend:**
- Ensure backend is running on port 8000
- Check CORS settings in backend
- Verify API_BASE_URL in `src/utils/api.js`

**Port 3000 already in use:**
```bash
lsof -i :3000
kill -9 <PID>
```

**Module not found errors:**
```bash
rm -rf node_modules package-lock.json
npm install
```

## Future Enhancements

- WebSocket for real-time updates
- Data preview/exploration
- Custom dashboard widgets
- Advanced filtering and search
- Export to PDF/Excel
- User authentication
