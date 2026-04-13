<!-- Comprehensive OneStopAnalytics Documentation -->
# OneStopAnalytics

A modern, responsive analytics platform built with **React 18 + Vite + Pure CSS**. Create custom dashboards, visualize data intuitively, and make data-driven decisions faster. Powered by Arithwise.

## Features

✅ **Responsive Design** - Mobile-first approach with fluid layouts across all devices
✅ **Custom Color Theme** - Professional purple theme (#78176b) with light backgrounds
✅ **Pure CSS** - No frameworks, optimized custom CSS with detailed comments
✅ **React Router** - Full SPA navigation with protected routes
✅ **User Authentication** - Login/signup with form validation
✅ **Interactive Dashboard** - Metrics widgets and real-time data updates
✅ **Canvas Charts** - Lightweight line, bar, and pie charts
✅ **Visualization Builder** - Create custom charts with data management
✅ **Data Persistence** - localStorage for offline capability
✅ **Advanced Analytics** - Helper utilities for complex data analysis

## Project Structure

```
onestopanalytics/
├── src/
│   ├── components/
│   │   ├── Header.jsx              # Navigation component
│   │   ├── Header.css
│   │   ├── Chart.jsx               # Line/bar/pie chart renderer
│   │   ├── Chart.css
│   │   ├── VisualizationBuilder.jsx # Chart creation interface
│   │   └── VisualizationBuilder.css
│   ├── pages/
│   │   ├── LandingPage.jsx         # Hero and features
│   │   ├── LandingPage.css
│   │   ├── AuthPage.jsx            # Login/signup
│   │   ├── AuthPage.css
│   │   ├── Dashboard.jsx           # Main user dashboard
│   │   └── Dashboard.css
│   ├── utils/
│   │   ├── dataManager.js          # Data persistence & utilities
│   │   └── analyticsHelpers.js     # Advanced analytics functions
│   ├── styles/
│   │   └── global.css              # Global theme and utilities
│   ├── App.jsx                     # Main app with routing
│   ├── App.css
│   └── main.jsx                    # React entry point
├── index.html                      # HTML template
├── vite.config.js                  # Vite configuration
├── package.json                    # Dependencies
└── README.md                       # This file
```

## Getting Started

### Prerequisites
- Node.js 16+ installed

### Installation

1. **Clone or download the project**
```bash
cd onestopanalytics
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```

The app will automatically open at `http://localhost:5173` with hot reload enabled.

### Build for Production

```bash
npm run build
```

Output files will be in the `dist/` directory.

## Color Theme

The application uses a carefully selected color palette for professional analytics:

- **Primary Color**: `#78176b` (Purple) - Buttons, links, highlights
- **Light Background**: `#faf3ff` (Lavender) - Main background
- **Alternative Light**: `#fffafe` (Off-white) - Contrast sections
- **Hover/Active**: `#590a4f` (Dark Purple) - Interactive states
- **Text Dark**: `#333333` - Primary text
- **Text Light**: `#666666` - Secondary text
- **Neutral**: `#f5f5f5`, `#ffffff` - Backgrounds, cards

## Demo Credentials

Try the following credentials on the Auth page:

```
Email: demo@example.com
Password: demo123
```

These will take you to the dashboard with sample analytics data.

## Key Components

### Header Component
- Logo linking to homepage
- Navigation links
- User greeting and logout button
- Sticky positioning for easy access

### Landing Page
- Hero section with value proposition
- 6 feature cards highlighting capabilities
- Benefits section with statistics
- Call-to-action sections

### Authentication Page
- Toggle between login and signup modes
- Form validation with error messages
- Demo credentials display
- Benefits sidebar

### Dashboard
- Key metrics widgets with trends
- Visualization builder for custom charts
- Chart management (add/remove)
- Empty states and tips

### Chart Component
- Canvas-based rendering (lightweight)
- Supported types: Line, Bar, Pie
- Automatic scaling and labels
- Responsive design

### Visualization Builder
- Form for creating charts
- Data point management
- Multiple chart type selection
- Validation and error handling

## Utilities

### Data Manager (`/src/utils/dataManager.js`)

Core data management functions:

```javascript
// Save/load widgets and charts
saveWidgets(widgets)
loadWidgets()
saveCharts(charts)
loadCharts()

// Calculations
calculateSum(data)
calculateAverage(data)
calculateMax(data)
calculateMin(data)
calculatePercentageChange(oldValue, newValue)

// Formatting
formatCurrency(value, currency)
formatNumber(value)

// Export
exportChartDataAsJSON(chart)
exportChartDataAsCSV(chart)
downloadFile(content, filename, mimeType)

// Data validation
validateChartData(chart)
mergeWithDefaults(userData, defaults)

// Sample data
generateSampleData()
```

### Analytics Helpers (`/src/utils/analyticsHelpers.js`)

Advanced analytics functions:

```javascript
// Growth metrics
calculateGrowthRate(current, previous)
getTrendIndicator(growthRate)

// Data filtering & grouping
filterByDateRange(data, start, end)
groupByTimePeriod(data, period)
calculateMovingAverage(data, windowSize)

// Statistical analysis
calculatePerformanceMetrics(data)
detectAnomalies(data, threshold)
calculatePercentileRank(data, value)

// Cohort & Funnel analysis
calculateCohortRetention(cohorts)
calculateFunnelConversions(stages)

// Data segmentation & comparison
segmentByCategory(data)
compareDatasets(dataset1, dataset2)
```

## State Management

The application uses React hooks for state management:

- **App.jsx**: Authentication state (isAuthenticated, userName)
- **Dashboard.jsx**: Widgets and charts with localStorage persistence
- **AuthPage.jsx**: Form data and validation errors
- **VisualizationBuilder.jsx**: Chart creation form state

## Data Persistence

All dashboard data is automatically saved to localStorage:

```javascript
// Storage keys
osa_widgets      // Saved metrics widgets
osa_charts       // Saved visualization charts
osa_user_data    // User profile data
osa_dashboard_settings // Dashboard preferences
```

Data persists across browser sessions and works offline.

## Styling Guidelines

### CSS Architecture
- Global styles in `/src/styles/global.css`
- Component-scoped styles in corresponding .css files
- BEM-inspired naming convention
- Flexbox for layouts, CSS Grid for complex layouts
- Mobile-first responsive design

### CSS Classes

**Layout Utilities**
```css
.flex, .flex-col, .flex-center, .flex-between
.gap-2, .gap-4, .gap-6, .gap-8
.mt-*, .mb-*, .p-*
```

**Components**
```css
.btn, .btn-primary, .btn-secondary, .btn-text
.card, .section, .container
.form-input, .form-label, .error-message
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- **Lightweight Charts**: Canvas-based rendering (no Chart.js)
- **Code Splitting**: Automatic with Vite
- **Fast Refresh**: Hot module reloading for development
- **Optimized Images**: Logo served from CDN
- **Minified CSS**: Inlined for critical path

## Accessibility

- Semantic HTML structure
- ARIA labels for interactive elements
- Keyboard navigation support
- Sufficient color contrast (WCAG AA)
- Form validation feedback

## Development Workflow

1. **Start dev server**: `npm run dev`
2. **Make changes**: Files auto-reload via HMR
3. **Test features**: Use demo credentials to test full flow
4. **Build for production**: `npm run build`
5. **Preview build**: `npm run preview`

## Troubleshooting

### Charts not displaying
- Ensure data array has at least 2 points
- Check browser console for errors
- Verify chart type is valid (line, bar, pie)

### Data not persisting
- Check browser's localStorage is enabled
- Clear localStorage if corrupted: `localStorage.clear()`
- Reload page to reinitialize

### Authentication issues
- Ensure localStorage has 'isAuthenticated' set to true
- Try demo credentials: demo@example.com / demo123
- Clear localStorage and create new account

## Future Enhancements

- Backend API integration for real data
- User accounts and database storage
- Advanced filtering and search
- Real-time data streaming
- Export to PDF/Excel
- Team collaboration features
- Data source integrations
- Custom theme builder

## Code Quality

- **Detailed Comments**: Every function documented
- **Error Handling**: Try-catch blocks for data operations
- **Validation**: Input validation for forms and data
- **Performance**: Optimized re-renders with useEffect
- **Responsive**: Mobile-first design approach

## License

Created for OneStopAnalytics - Powered by Arithwise

## Support

For issues or questions, refer to the code comments or check the browser console for detailed error messages.

---

Built with ❤️ using React, Vite, and Pure CSS
