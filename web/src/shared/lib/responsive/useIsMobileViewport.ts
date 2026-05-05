import { useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { MOBILE_VIEWPORT_BREAKPOINT } from './constants';

export const useIsMobileViewport = () => {
  const theme = useTheme();

  return useMediaQuery(theme.breakpoints.down(MOBILE_VIEWPORT_BREAKPOINT));
};
