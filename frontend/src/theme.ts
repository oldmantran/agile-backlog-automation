import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: true,
};

const theme = extendTheme({
  config,
  colors: {
    brand: {
      50: '#E6F2FF',
      100: '#B3DBFF',
      200: '#80C4FF',
      300: '#4DADFF',
      400: '#1A96FF',
      500: '#0066CC', // Primary blue
      600: '#0052A3',
      700: '#003D7A',
      800: '#002951',
      900: '#001429',
    },
    success: {
      50: '#E6F7ED',
      500: '#00AA44', // Secondary green
    },
    accent: {
      50: '#FFF4E6',
      500: '#FF6B35', // Accent orange
    },
  },
  fonts: {
    heading: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    body: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: 'semibold',
        borderRadius: 'lg',
      },
      variants: {
        solid: {
          _hover: {
            transform: 'translateY(-2px)',
            boxShadow: 'lg',
          },
          transition: 'all 0.2s ease',
        }
      }
    },
  },
});

export default theme;
