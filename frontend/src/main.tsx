import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import { App } from '@/app/App';
import { QueryProvider } from '@/app/providers/QueryProvider';
import { ThemeProvider } from '@/app/providers/ThemeProvider';
import { WebSocketProvider } from '@/app/providers/WebSocketProvider';
import '@/styles/globals.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <QueryProvider>
        <WebSocketProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </WebSocketProvider>
      </QueryProvider>
    </ThemeProvider>
  </React.StrictMode>,
);

