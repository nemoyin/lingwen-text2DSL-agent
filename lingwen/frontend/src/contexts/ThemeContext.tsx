import { createContext, useContext, useState, useMemo, type ReactNode } from 'react';
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import lingwenTheme from '../styles/theme';

type Language = 'zh' | 'en';

interface ThemeContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (zh: string, en: string) => string;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>('zh');

  const t = (zh: string, en: string) => language === 'zh' ? zh : en;

  const value = useMemo(() => ({ language, setLanguage, t }), [language]);

  return (
    <MuiThemeProvider theme={lingwenTheme}>
      <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
    </MuiThemeProvider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
