import type { Breakpoint } from '@mui/material/styles';

export const MOBILE_VIEWPORT_BREAKPOINT: Breakpoint = 'sm';
export const MOBILE_BOTTOM_NAV_HEIGHT_PX = 64;
export const MOBILE_BOTTOM_NAV_SAFE_AREA = 'env(safe-area-inset-bottom, 0px)';
export const MOBILE_BOTTOM_NAV_OFFSET = `calc(${MOBILE_BOTTOM_NAV_HEIGHT_PX}px + ${MOBILE_BOTTOM_NAV_SAFE_AREA})`;
export const MOBILE_BOTTOM_NAV_CONTENT_PADDING = `calc(${MOBILE_BOTTOM_NAV_HEIGHT_PX + 16}px + ${MOBILE_BOTTOM_NAV_SAFE_AREA})`;
