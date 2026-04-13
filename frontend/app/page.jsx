/**
 * Preview Entry Point for v0
 * This file allows the v0 preview system to render the React + Vite app
 * The actual application runs through src/main.jsx and Vite
 */

import App from '../src/App'
import '../src/styles/global.css'
import '../src/App.css'

/**
 * Default export for v0 preview
 * Renders the complete OneStopAnalytics application
 */
export default function Page() {
  return <App />
}
