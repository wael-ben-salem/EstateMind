import { CssBaseline, ThemeProvider as MuiThemeProvider, createTheme } from '@mui/material';
import { ReactNode, useMemo } from 'react';

export function ThemeProvider({ children }: { children: ReactNode }) {
  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: 'light',
          primary: { main: '#3b82f6' },
          success: { main: '#10b981' },
          warning: { main: '#f59e0b' },
          error: { main: '#ef4444' },
          background: { default: '#f8fafc', paper: '#ffffff' },
          text: { primary: '#0f172a' }
        },
        shape: { borderRadius: 12 },
        typography: {
          fontFamily: [
            'Inter',
            'ui-sans-serif',
            'system-ui',
            '-apple-system',
            'Segoe UI',
            'Roboto',
            'Helvetica',
            'Arial',
            'sans-serif'
          ].join(',')
        },
        components: {
          MuiCard: {
            styleOverrides: {
              root: { border: '1px solid rgba(15,23,42,0.08)' }
            }
          }
        }
      }),
    [],
  );

  return (
    <MuiThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </MuiThemeProvider>
  );
}

