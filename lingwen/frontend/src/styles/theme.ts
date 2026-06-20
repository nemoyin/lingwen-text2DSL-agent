/** Lingwen brand theme — MUI theme overrides for the login-page visual language. */
import { createTheme, alpha } from '@mui/material/styles';

export const BRAND = {
  primary: '#3478F6',
  gradient: 'linear-gradient(90deg, #2065F5 0%, #3478F6 48%, #4A88FF 100%)',
  gradientHover: 'linear-gradient(90deg, #1a56e0 0%, #2b6aef 48%, #3d7bf5 100%)',
  border: '#E5E7EB',
  text: { primary: '#1F2937', secondary: '#374151', muted: '#6B7280' },
  tableHead: '#FAFAFA',
  inputBg: '#fff',
  inputFocus: '#3478F6',
};

const theme = createTheme({
  palette: {
    primary: { main: BRAND.primary },
  },
  shape: { borderRadius: 4 },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          height: 40,
          borderRadius: 4,
          fontWeight: 600,
          textTransform: 'none',
          '&.MuiButton-contained': {
            background: '#3478F6',
            color: '#fff',
            boxShadow: 'none',
            '&:hover': {
              background: '#4A88FF',
              boxShadow: 'none',
            },
            '&.Mui-disabled': {
              background: '#8da5f4',
              color: alpha('#fff', 0.72),
            },
          },
          '&.MuiButton-outlined': {
            borderColor: BRAND.border,
            color: BRAND.text.secondary,
            '&:hover': { borderColor: BRAND.primary, color: BRAND.primary, background: alpha(BRAND.primary, 0.04) },
          },
          '&.MuiButton-text': {
            color: BRAND.primary,
            '&:hover': { background: alpha(BRAND.primary, 0.06) },
          },
          '&.MuiButton-sizeSmall': { height: 32, fontSize: 13 },
          '&.MuiButton-sizeLarge': { height: 52, fontSize: 16 },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            height: 48,
            borderRadius: 8,
            background: BRAND.inputBg,
            fontSize: 14,
            '& fieldset': { borderColor: BRAND.border },
            '&:hover fieldset': { borderColor: '#bfc8d8' },
            '&.Mui-focused fieldset': { borderColor: BRAND.inputFocus, boxShadow: `0 0 0 3px ${alpha(BRAND.inputFocus, 0.1)}` },
          },
          '& .MuiInputLabel-root': { fontSize: 14 },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: { borderRadius: 10 },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          fontSize: 16,
          fontWeight: 700,
          borderBottom: `1px solid ${BRAND.border}`,
          padding: '16px 24px',
        },
      },
    },
    MuiDialogActions: {
      styleOverrides: {
        root: {
          padding: '12px 24px',
          borderTop: `1px solid ${BRAND.border}`,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          '&.MuiChip-outlined': { borderColor: BRAND.border },
        },
        sizeSmall: { height: 24, fontSize: 11 },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            background: BRAND.tableHead,
            fontWeight: 500,
            fontSize: 13,
            color: BRAND.text.primary,
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': { background: '#F8FAFC' },
        },
      },
    },
  },
});

export default theme;
