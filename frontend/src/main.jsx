import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Plus Jakarta Sans, bundled with the app (works offline, no request to Google Fonts)
import '@fontsource-variable/plus-jakarta-sans'
import './App.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)