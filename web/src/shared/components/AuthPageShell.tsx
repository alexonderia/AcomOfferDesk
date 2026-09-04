import { Box, Paper, Stack, Typography } from '@mui/material';
import type { ReactNode } from 'react';

import { AppFooter } from '@shared/components/AppFooter';

const AUTH_PRIMARY = '#2f6fd6';
const AUTH_PRIMARY_DARK = '#245bb5';
const AUTH_TEXT = '#1f2a44';
const AUTH_BORDER = '#d3dbe7';
const AUTH_FONT = 'Inter, "Segoe UI", sans-serif';
const NARROW_AUTH_QUERY = '(max-width: 640px)';

type AuthPageShellProps = {
  title?: string;
  subtitle?: ReactNode;
  children: ReactNode;
  maxWidth?: number;
};

export const AuthPageShell = ({
  title,
  subtitle,
  children,
  maxWidth = 460,
}: AuthPageShellProps) => (
  <Box
    sx={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      color: AUTH_TEXT,
      fontFamily: AUTH_FONT,
      fontSize: '16px',
      background: [
        'radial-gradient(circle at top right, rgba(47, 111, 214, 0.08), transparent 30%)',
        'radial-gradient(circle at bottom left, rgba(47, 111, 214, 0.06), transparent 34%)',
        '#edf3ff',
      ].join(', '),
      '& .MuiTypography-root, & .MuiButton-root, & .MuiInputBase-input, & .MuiInputLabel-root, & label': {
        fontFamily: AUTH_FONT,
      },
      '& .MuiOutlinedInput-root': {
        minHeight: 56,
        borderRadius: '36px',
        backgroundColor: '#ffffff',
        '& .MuiOutlinedInput-input': {
          fontSize: '16px',
          lineHeight: 1.25,
        },
        '& .MuiOutlinedInput-notchedOutline': {
          borderColor: AUTH_BORDER,
        },
        '&:hover .MuiOutlinedInput-notchedOutline': {
          borderColor: '#bcc7da',
        },
        '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
          borderColor: '#aeb9cc',
          borderWidth: 1,
        },
      },
      '& .MuiInputLabel-root, & label': {
        fontSize: '14px',
        fontWeight: 600,
        lineHeight: 1.25,
        color: AUTH_TEXT,
      },
      '& .MuiButton-contained': {
        minHeight: 48,
        borderRadius: '36px',
        backgroundColor: AUTH_PRIMARY,
        fontSize: '16px',
        fontWeight: 600,
        lineHeight: 1.2,
        '&:hover': {
          backgroundColor: AUTH_PRIMARY_DARK,
        },
      },
      '& .MuiButton-text': {
        minHeight: 0,
        py: 0,
        borderRadius: 0,
        alignSelf: 'center',
        width: 'auto',
        color: AUTH_PRIMARY,
        fontSize: '14px',
        fontWeight: 500,
        lineHeight: 1.25,
        '&:hover': {
          backgroundColor: 'transparent',
          color: AUTH_PRIMARY_DARK,
          textDecoration: 'underline',
        },
      },
      '& .MuiIconButton-root': {
        width: 40,
        height: 40,
        backgroundColor: '#f5f8ff',
        color: '#4a5875',
        '&:hover': {
          backgroundColor: '#ebf2ff',
          color: AUTH_TEXT,
        },
      },
    }}
  >
    <Box
      component="main"
      sx={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: '24px',
        [NARROW_AUTH_QUERY]: {
          alignItems: 'flex-start',
          p: '16px',
        },
      }}
    >
      <Paper
        elevation={0}
        sx={{
          width: `min(${maxWidth}px, 94vw)`,
          minHeight: 390,
          borderRadius: '20px',
          border: `1px solid ${AUTH_BORDER}`,
          boxShadow: '0 12px 28px rgba(15, 35, 75, 0.08)',
          p: '32px',
          [NARROW_AUTH_QUERY]: {
            width: '100%',
            minHeight: 0,
            borderRadius: '18px',
            p: '24px 20px 20px',
          },
        }}
      >
        <Stack spacing={2.25} sx={{ width: '100%' }}>
          {title || subtitle ? (
            <Stack spacing={1} sx={{ textAlign: 'center', mb: 0.5 }}>
              {title ? (
                <Typography
                  component="h1"
                  variant="inherit"
                  sx={{
                    m: 0,
                    color: AUTH_TEXT,
                    fontFamily: AUTH_FONT,
                    fontSize: '20px',
                    fontWeight: 700,
                    lineHeight: 1.25,
                  }}
                >
                  {title}
                </Typography>
              ) : null}
              {subtitle ? (
                <Typography
                  component="p"
                  variant="inherit"
                  sx={{
                    m: 0,
                    color: '#4a5875',
                    fontFamily: AUTH_FONT,
                    fontSize: '14px',
                    fontWeight: 400,
                    lineHeight: 1.55,
                  }}
                >
                  {subtitle}
                </Typography>
              ) : null}
            </Stack>
          ) : null}
          {children}
        </Stack>
      </Paper>
    </Box>
    <AppFooter />
  </Box>
);
