import React from 'react';
import ReactDOM from 'react-dom/client';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { App } from '@app/App';
import { appTheme } from '@shared/theme/appTheme';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@app/providers/AuthProvider';
import { ChatRealtimeProvider } from '@app/providers/ChatRealtimeProvider';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <BrowserRouter>
        <AuthProvider>
          <ChatRealtimeProvider>
            <App />
          </ChatRealtimeProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>
);
