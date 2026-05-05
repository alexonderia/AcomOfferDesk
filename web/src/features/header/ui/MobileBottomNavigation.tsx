import {
  Box,
  Button,
  Menu,
  MenuItem,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import LogoutRounded from '@mui/icons-material/LogoutRounded';
import type { MouseEvent } from 'react';
import { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ActionButton } from '@shared/components/ActionButton';
import { FeedbackButton } from '@shared/components/FeedbackButton';
import { NormativeFileButton } from '@shared/components/NormativeFileButton';
import { ProfileButton } from '@shared/components/ProfileButton';
import { RoleGuideButton } from '@shared/components/RoleGuideButton';
import {
  MOBILE_BOTTOM_NAV_HEIGHT_PX,
  MOBILE_BOTTOM_NAV_SAFE_AREA,
} from '@shared/lib/responsive';
import type { HeaderConfig, HeaderMobileNavItem } from '../model/types';
import { getHeaderNavigationIcon } from './navigationIcons';

type MobileBottomNavigationProps = {
  config: HeaderConfig;
  onLogout: () => void;
};

const isRouteActive = (pathname: string, targetPath: string) => {
  if (targetPath === '/pm-dashboard') {
    return pathname.startsWith('/pm-dashboard');
  }

  if (targetPath === '/requests') {
    return pathname.startsWith('/requests') || pathname.startsWith('/offers/');
  }

  return pathname === targetPath || pathname.startsWith(`${targetPath}/`);
};

const resolveFallbackItems = (config: HeaderConfig): HeaderMobileNavItem[] => {
  if (config.tabs.length > 0) {
    return config.tabs.map((tab) => ({
      key: tab.key,
      label: tab.label,
      tabValue: tab.value,
    }));
  }

  const sidebarItems = (config.sidebarItems ?? [])
    .filter((item) => Boolean(item.to) && !item.disabled && item.key !== 'logout')
    .map((item) => ({
      key: item.key,
      label: item.label,
      to: item.to,
    }));

  if (sidebarItems.length > 0) {
    return sidebarItems;
  }

  const breadcrumbsItem = (config.breadcrumbs ?? []).find((item) => Boolean(item.to));
  if (breadcrumbsItem?.to) {
    return [{ key: breadcrumbsItem.key, label: breadcrumbsItem.label, to: breadcrumbsItem.to }];
  }

  return [{ key: 'requests', label: 'Заявки', to: '/requests' }];
};

const isNavItemActive = (
  item: HeaderMobileNavItem,
  pathname: string,
  activeTab?: string
): boolean => {
  if (item.tabValue && activeTab === item.tabValue) {
    return true;
  }

  if (item.to && isRouteActive(pathname, item.to)) {
    return true;
  }

  if (item.children && item.children.length > 0) {
    return item.children.some((child) => isNavItemActive(child, pathname, activeTab));
  }

  return false;
};

const hasChildItems = (item: HeaderMobileNavItem) => Boolean(item.children && item.children.length > 0);

export const MobileBottomNavigation = ({ config, onLogout }: MobileBottomNavigationProps) => {
  const location = useLocation();
  const navigate = useNavigate();

  const [submenuAnchorEl, setSubmenuAnchorEl] = useState<HTMLElement | null>(null);
  const [submenuItems, setSubmenuItems] = useState<HeaderMobileNavItem[]>([]);
  const [moreAnchorEl, setMoreAnchorEl] = useState<HTMLElement | null>(null);

  const navigationItems = useMemo(() => {
    const sourceItems = config.mobileNavItems && config.mobileNavItems.length > 0
      ? config.mobileNavItems
      : resolveFallbackItems(config);

    return sourceItems.filter((item) => !item.disabled).slice(0, 4);
  }, [config]);

  const activeKey = useMemo(() => {
    const activeItem = navigationItems.find((item) => isNavItemActive(item, location.pathname, config.activeTab));
    return activeItem?.key ?? false;
  }, [config.activeTab, location.pathname, navigationItems]);

  const moreItem = useMemo(
    () => navigationItems.find((item) => item.key === 'more'),
    [navigationItems]
  );

  const executeNavItem = (item: HeaderMobileNavItem) => {
    if (item.key === 'logout') {
      onLogout();
      return;
    }

    if (item.tabValue) {
      config.onTabChange?.(item.tabValue);
      return;
    }

    if (item.to) {
      navigate(item.to);
    }
  };

  const handleTopLevelItemClick = (item: HeaderMobileNavItem, event: MouseEvent<HTMLElement>) => {
    if (item.key === 'more') {
      setMoreAnchorEl(event.currentTarget);
      return;
    }

    if (hasChildItems(item)) {
      setSubmenuAnchorEl(event.currentTarget);
      setSubmenuItems(item.children ?? []);
      return;
    }

    executeNavItem(item);
  };

  const handleSubmenuSelect = (item: HeaderMobileNavItem) => {
    executeNavItem(item);
    setSubmenuAnchorEl(null);
    setSubmenuItems([]);
  };

  const renderMoreAction = (item: HeaderMobileNavItem) => {
    if (item.key === 'profile') {
      return <ProfileButton sidebar />;
    }

    if (item.key === 'normative') {
      return <NormativeFileButton sidebar />;
    }

    if (item.key === 'guide') {
      return <RoleGuideButton sidebar />;
    }

    if (item.key === 'feedback') {
      return <FeedbackButton sidebar />;
    }

    if (item.key === 'logout') {
      return (
        <ActionButton
          kind="custom"
          showNavigationIcons={false}
          onClick={() => {
            setMoreAnchorEl(null);
            onLogout();
          }}
          sx={{
            width: '100%',
            minHeight: 42,
            minWidth: 0,
            justifyContent: 'flex-start',
            px: 1.75,
            gap: 1.25,
            borderRadius: (theme) => `${theme.acomShape.buttonRadius}px !important`,
            fontSize: 14,
            fontWeight: 500,
            lineHeight: 1.2,
            textTransform: 'none'
          }}
        >
          <Box component="span" sx={{ display: 'inline-flex', lineHeight: 1 }}>
            <LogoutRounded fontSize="small" />
          </Box>
          Выйти
        </ActionButton>
      );
    }

    return (
      <Button
        variant="text"
        onClick={() => {
          setMoreAnchorEl(null);
          executeNavItem(item);
        }}
        sx={{ width: '100%', justifyContent: 'flex-start', border: 'none', px: 1.25 }}
      >
        {item.label}
      </Button>
    );
  };

  return (
    <>
      <Paper
        elevation={0}
        sx={{
          position: 'fixed',
          left: 0,
          right: 0,
          bottom: 0,
          borderTop: '1px solid',
          borderColor: 'divider',
          px: 1,
          pt: 0.5,
          pb: `calc(6px + ${MOBILE_BOTTOM_NAV_SAFE_AREA})`,
          bgcolor: 'background.paper',
          zIndex: (theme) => theme.zIndex.appBar,
        }}
      >
        <Stack direction="row" alignItems="stretch" sx={{ height: MOBILE_BOTTOM_NAV_HEIGHT_PX }}>
          {navigationItems.map((item) => {
            const isActive = activeKey === item.key;

            return (
              <Box
                key={item.key}
                component="button"
                type="button"
                onClick={(event: MouseEvent<HTMLElement>) => handleTopLevelItemClick(item, event)}
                sx={{
                  flex: 1,
                  border: 'none',
                  backgroundColor: 'transparent',
                  px: 0.25,
                  py: 0.2,
                  borderRadius: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 0.35,
                  color: isActive ? 'primary.main' : 'text.secondary',
                }}
              >
                <Box
                  sx={{
                    width: 28,
                    height: 28,
                    display: 'grid',
                    placeItems: 'center',
                    color: isActive ? 'primary.main' : 'text.secondary',
                    transition: 'color 0.2s ease'
                  }}
                >
                  {getHeaderNavigationIcon(item.key)}
                </Box>
                <Typography sx={{ fontSize: 11, lineHeight: 1.1, fontWeight: isActive ? 600 : 500 }}>
                  {item.label}
                </Typography>
              </Box>
            );
          })}
        </Stack>
      </Paper>

      <Menu
        open={Boolean(submenuAnchorEl && submenuItems.length > 0)}
        anchorEl={submenuAnchorEl}
        onClose={() => {
          setSubmenuAnchorEl(null);
          setSubmenuItems([]);
        }}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        transformOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        {submenuItems.map((item) => (
          <MenuItem key={item.key} onClick={() => handleSubmenuSelect(item)}>
            {item.label}
          </MenuItem>
        ))}
      </Menu>

      <Menu
        open={Boolean(moreAnchorEl)}
        anchorEl={moreAnchorEl}
        onClose={() => setMoreAnchorEl(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        transformOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Stack spacing={0.75} sx={{ p: 1, minWidth: 240 }}>
          {config.backAction ? (
            <Button
              variant="text"
              onClick={() => {
                config.backAction?.onClick();
                setMoreAnchorEl(null);
              }}
              sx={{ width: '100%', justifyContent: 'flex-start', border: 'none', px: 1.25 }}
            >
              {config.backAction.label}
            </Button>
          ) : null}
          {config.actions.map((action) => (
            <Button
              key={action.key}
              variant="text"
              onClick={() => {
                action.onClick();
                setMoreAnchorEl(null);
              }}
              sx={{ width: '100%', justifyContent: 'flex-start', border: 'none', px: 1.25 }}
            >
              {action.label}
            </Button>
          ))}
          {(moreItem?.children ?? []).map((item) => (
            <Box key={item.key} sx={{ '& > *': { width: '100%' } }}>
              {renderMoreAction(item)}
            </Box>
          ))}
        </Stack>
      </Menu>
    </>
  );
};
