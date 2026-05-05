import { Box, Link, Stack, Typography } from '@mui/material';
import { useEffect, useRef, useState } from 'react';
import bitrixLogo from '@shared/assets/bitrix24-logo.png';
import maxLogo from '@shared/assets/max-logo-2025.png';
import { useIsMobileViewport } from '@shared/lib/responsive';

const BITRIX_LINK = 'https://team.alabuga.ru/company/structure.php?set_filter_structure=Y&structure_UF_DEPARTMENT=8304&filter=Y&set_filter=Y';
const MAX_CONTACT_LINK = 'https://max.ru/u/f9LHodD0cOIA4s2RhH3dW5NoCLRn88NF67UYfQe_rOnnM6Y1a7VW_vOUt5I';

const iconLinkSx = {
  width: 34,
  height: 34,
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: 2.5,
  border: '1px solid',
  borderColor: 'divider',
  backgroundColor: 'rgba(255, 255, 255, 0.86)',
  transition: 'transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease, background-color 0.2s ease',
  '&:hover': {
    borderColor: 'primary.main',
    backgroundColor: '#fff',
    transform: 'translateY(-1px) scale(1.02)',
    boxShadow: '0 8px 16px rgba(15, 35, 75, 0.16)'
  }
};

const compactIconLinkSx = {
  ...iconLinkSx,
  width: 30,
  height: 30
};

const iconImageSx = {
  display: 'block',
  width: 24,
  height: 24,
  objectFit: 'cover' as const,
  borderRadius: 2
};

const compactIconImageSx = {
  ...iconImageSx,
  width: 20,
  height: 20,
  borderRadius: 99
};

const CREATED_BY_LABEL = 'Created by "Цифровизация проектных задач"';
const SUPPORT_LABEL = 'По вопросам системы писать сюда';
const BITRIX_ARIA_LABEL = 'Перейти в Битрикс';
const MAX_ARIA_LABEL = 'Открыть MAX';

type AppFooterProps = {
  compact?: boolean;
};

export const AppFooter = ({ compact = false }: AppFooterProps) => {
  const isMobileViewport = useIsMobileViewport();
  const layoutRef = useRef<HTMLDivElement | null>(null);
  const requiredRowWidthRef = useRef(0);
  const [shouldUseMobileLayout, setShouldUseMobileLayout] = useState(false);
  const shouldUseCompactLayout = isMobileViewport || shouldUseMobileLayout;

  useEffect(() => {
    if (compact) {
      return;
    }

    const element = layoutRef.current;
    if (!element) {
      return;
    }

    const RECOVER_LAYOUT_GAP_PX = 28;

    const updateLayout = () => {
      setShouldUseMobileLayout((prev) => {
        if (!prev) {
          const hasOverflow = element.scrollWidth > element.clientWidth + 1;
          if (hasOverflow) {
            requiredRowWidthRef.current = Math.max(requiredRowWidthRef.current, element.scrollWidth);
            return true;
          }
          return false;
        }

        const requiredRowWidth = requiredRowWidthRef.current;
        if (requiredRowWidth <= 0) {
          return prev;
        }

        const hasEnoughFreeSpace = element.clientWidth >= requiredRowWidth + RECOVER_LAYOUT_GAP_PX;
        return hasEnoughFreeSpace ? false : prev;
      });
    };

    updateLayout();

    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(() => {
        updateLayout();
      });
      observer.observe(element);
      return () => observer.disconnect();
    }

    window.addEventListener('resize', updateLayout);
    return () => window.removeEventListener('resize', updateLayout);
  }, [compact]);

  if (compact) {
    return (
      <Box
        component="footer"
        sx={{
          width: '100%',
          px: 0.5,
          pt: 0.25,
          pb: 0.75,
          pr: { lg: 'var(--offer-workspace-chat-offset, 0px)' },
          transition: 'padding-right 0.2s ease'
        }}
      >
        <Box
          sx={{
            maxWidth: '100%',
            mx: 'auto',
          px: 1.2,
          py: 0.7,
          borderRadius: { xs: 1.5, sm: 2 },
            border: '1px solid',
            borderColor: 'divider',
            backgroundColor: 'rgba(255, 255, 255, 0.88)'
          }}
        >
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'minmax(0, 1fr) auto',
              gridTemplateRows: 'auto auto',
              columnGap: 1,
              rowGap: 0.6,
              alignItems: 'center'
            }}
          >
            <Typography
              variant="h6"
              sx={{
                gridColumn: 1,
                gridRow: 1,
                fontWeight: 650,
                fontSize: { xs: 18, sm: 17 },
                lineHeight: 1.1
              }}
            >
              AcomOfferDesk
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ gridColumn: 1, gridRow: 2, fontWeight: 500, fontSize: 12.5 }}
            >
              {CREATED_BY_LABEL}
            </Typography>
            <Stack
              direction="row"
              spacing={0.75}
              sx={{
                gridColumn: 2,
                gridRow: '1 / span 2',
                alignSelf: 'stretch',
                alignItems: 'center',
                justifyContent: 'flex-end'
              }}
            >
              <Link href={BITRIX_LINK} target="_blank" rel="noreferrer" aria-label={BITRIX_ARIA_LABEL} sx={compactIconLinkSx}>
                <Box component="img" src={bitrixLogo} alt="Bitrix24" sx={compactIconImageSx} />
              </Link>
              <Link href={MAX_CONTACT_LINK} target="_blank" rel="noreferrer" aria-label={MAX_ARIA_LABEL} sx={compactIconLinkSx}>
                <Box component="img" src={maxLogo} alt="MAX" sx={compactIconImageSx} />
              </Link>
            </Stack>
          </Box>
        </Box>
      </Box>
    );
  }

  return (
    <Box
      component="footer"
      sx={{
        width: '100%',
        pr: { lg: 'var(--offer-workspace-chat-offset, 0px)' },
        px: { xs: 0.5, md: 1.2 },
        pt: { xs: 0.4, md: 0.6 },
        pb: { xs: 0.9, md: 1.1 },
        transition: 'padding-right 0.2s ease'
      }}
    >
      <Box
        sx={{
          maxWidth: '100%',
          mx: 'auto',
          px: { xs: 1.1, md: 1.45 },
          py: { xs: 0.7, md: 0.8 },
          borderRadius: { xs: 2, md: 2.5 },
          backgroundColor: '#ffffff',
          boxShadow: '0 4px 14px rgba(15, 35, 75, 0.04)',
          position: 'relative',
          zIndex: 0,
        }}
      >
        {shouldUseCompactLayout ? (
          <Stack ref={layoutRef} spacing={0.8}>
            <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={1}>
              <Typography variant="h6" sx={{ fontWeight: 650, fontSize: { xs: 20, md: 18 }, lineHeight: 1.1 }}>
                AcomOfferDesk
              </Typography>
              <Stack direction="row" spacing={0.8}>
                <Link href={BITRIX_LINK} target="_blank" rel="noreferrer" aria-label={BITRIX_ARIA_LABEL} sx={compactIconLinkSx}>
                  <Box component="img" src={bitrixLogo} alt="Bitrix24" sx={compactIconImageSx} />
                </Link>
                <Link href={MAX_CONTACT_LINK} target="_blank" rel="noreferrer" aria-label={MAX_ARIA_LABEL} sx={compactIconLinkSx}>
                  <Box component="img" src={maxLogo} alt="MAX" sx={compactIconImageSx} />
                </Link>
              </Stack>
            </Stack>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, fontSize: 12.5 }}>
              {CREATED_BY_LABEL}
            </Typography>
          </Stack>
        ) : (
          <Stack
            ref={layoutRef}
            direction="row"
            alignItems="center"
            justifyContent="space-between"
            spacing={1.2}
            sx={{ width: '100%' }}
          >
            <Box sx={{ flex: 1, display: 'flex', justifyContent: 'flex-start' }}>
              <Stack direction="row" alignItems="center" spacing={1.1} useFlexGap flexWrap="nowrap" justifyContent="flex-start">
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    fontWeight: 500,
                    fontSize: 12.5,
                    textAlign: 'left',
                    whiteSpace: 'nowrap'
                  }}
                >
                  {CREATED_BY_LABEL}
                </Typography>
                <Link href={BITRIX_LINK} target="_blank" rel="noreferrer" aria-label={BITRIX_ARIA_LABEL} sx={iconLinkSx}>
                  <Box component="img" src={bitrixLogo} alt="Bitrix24" sx={iconImageSx} />
                </Link>
              </Stack>
            </Box>

            <Typography
              variant="body2"
              color="text.primary"
              sx={{
                fontWeight: 550,
                fontSize: { xs: 16, md: 14 },
                letterSpacing: 0.1,
                textTransform: 'none',
                textAlign: 'center'
              }}
            >
              AcomOfferDesk
            </Typography>

            <Box sx={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
              <Stack direction="row" alignItems="center" spacing={1.1} useFlexGap flexWrap="nowrap" justifyContent="flex-end">
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    fontWeight: 500,
                    fontSize: 12.5,
                    textAlign: 'right',
                    whiteSpace: 'nowrap'
                  }}
                >
                  {SUPPORT_LABEL}
                </Typography>
                <Link href={MAX_CONTACT_LINK} target="_blank" rel="noreferrer" aria-label={MAX_ARIA_LABEL} sx={iconLinkSx}>
                  <Box component="img" src={maxLogo} alt="MAX" sx={iconImageSx} />
                </Link>
              </Stack>
            </Box>
          </Stack>
        )}
      </Box>
    </Box>
  );
};
