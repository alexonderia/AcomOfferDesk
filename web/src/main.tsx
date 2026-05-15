import React from 'react';
import ReactDOM from 'react-dom/client';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { App } from '@app/App';
import { appTheme } from '@shared/theme/appTheme';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@app/providers/AuthProvider';
import { ChatRealtimeProvider } from '@app/providers/ChatRealtimeProvider';
import { SnackbarProvider } from 'notistack';
import { NOTIFICATION_PUSH_MAX_SNACK } from '@features/notifications/model/constants';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <BrowserRouter>
        <AuthProvider>
          <ChatRealtimeProvider>
            <SnackbarProvider
              maxSnack={NOTIFICATION_PUSH_MAX_SNACK}
              autoHideDuration={10000}
              preventDuplicate
              dense
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            >
              <App />
            </SnackbarProvider>
          </ChatRealtimeProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>
);
