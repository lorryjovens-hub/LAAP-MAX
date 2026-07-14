/**
 * Overlay 页面入口脚本。
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import OverlayApp from './overlay'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <OverlayApp />
  </React.StrictMode>,
)
