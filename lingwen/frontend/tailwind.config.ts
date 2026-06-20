import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
  // Use #root as the important selector to avoid conflicts with MUI
  important: '#root',
};

export default config;
