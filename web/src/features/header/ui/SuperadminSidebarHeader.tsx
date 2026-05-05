import AddOutlined from '@mui/icons-material/AddOutlined';
import ArrowBackOutlined from '@mui/icons-material/ArrowBackOutlined';
import KeyboardArrowLeftRounded from '@mui/icons-material/KeyboardArrowLeftRounded';
import KeyboardArrowRightRounded from '@mui/icons-material/KeyboardArrowRightRounded';
import LogoutOutlined from '@mui/icons-material/LogoutOutlined';
import { Box, IconButton, Menu, MenuItem, Stack, Tooltip, Typography } from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { ActionButton } from '@shared/components/ActionButton';
import { useAuth } from '@app/providers/AuthProvider';
import { FeedbackButton } from '@shared/components/FeedbackButton';
import { NormativeFileButton } from '@shared/components/NormativeFileButton';
import { ProfileButton } from '@shared/components/ProfileButton';
import { RoleGuideButton } from '@shared/components/RoleGuideButton';
import { ROLE } from '@shared/constants/roles';
import { SidebarMenuButton } from '@shared/components/SidebarMenuButton';
import type { HeaderConfig } from '../model/types';
import { getHeaderNavigationIcon } from './navigationIcons';

const navLinkStyles = { textDecoration: 'none', display: 'block', width: '100%' } as const;

type SuperadminSidebarHeaderProps = {
  config: HeaderConfig;
  onLogout: () => void;
  collapsed: boolean;
  onToggleCollapse?: () => void;
};

export const SuperadminSidebarHeader = ({
  config,
  onLogout,
  collapsed,
  onToggleCollapse,
}: SuperadminSidebarHeaderProps) => {
  const theme = useTheme();
  const { session } = useAuth();
  const [isCompactHeight, setIsCompactHeight] = useState<boolean>(
    typeof window !== 'undefined' ? window.innerHeight <= 760 : false
  );
  const [isEdgeHovered, setIsEdgeHovered] = useState(false);
  const [isToggleHovered, setIsToggleHovered] = useState(false);
  const [isToggleVisible, setIsToggleVisible] = useState(false);
  const [isDashboardMenuHovered, setIsDashboardMenuHovered] = useState(false);
  const [dashboardMenuAnchorEl, setDashboardMenuAnchorEl] = useState<HTMLElement | null>(null);

  useEffect(() => {
    const handleResize = () => setIsCompactHeight(window.innerHeight <= 760);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    const shouldShow = Boolean(onToggleCollapse) && (isEdgeHovered || isToggleHovered);
    if (shouldShow) {
      setIsToggleVisible(true);
      return;
    }

    const hideTimeout = window.setTimeout(() => {
      setIsToggleVisible(false);
    }, 160);

    return () => {
      window.clearTimeout(hideTimeout);
    };
  }, [isEdgeHovered, isToggleHovered, onToggleCollapse]);

  const topItems = (config.sidebarItems ?? []).filter((item) => !item.isBottomItem && item.key !== 'logout');
  const isSuperadmin = session?.roleId === ROLE.SUPERADMIN;
  const hasSavingsTab = config.tabs.some((tabItem) => tabItem.key === 'savings');
  const hasPlanTab = config.tabs.some((tabItem) => tabItem.key === 'plan');
  const hasDashboardProcessTab = hasSavingsTab;
  const isDashboardPopupOpen = collapsed && (hasSavingsTab || hasPlanTab) && Boolean(dashboardMenuAnchorEl);

  return (
    <Stack
      component="aside"
      justifyContent="space-between"
      sx={{
        width: '100%',
        position: 'sticky',
        top: 0,
        minHeight: '100vh',
        height: '100vh',
        bgcolor: 'background.paper',
        borderRight: '1px solid',
        borderColor: 'divider',
        px: collapsed ? 1 : 1.5,
        py: 1.5,
        overflow: 'hidden',
        transition: 'padding 0.24s ease'
      }}
    >
      <Stack sx={{ height: '100%' }}>
        <Stack direction="row" alignItems="center" justifyContent={collapsed ? 'center' : 'space-between'} sx={{ minHeight: 44, mb: 1.8 }}>
          <Typography sx={{ fontSize: 22, fontWeight: 700, lineHeight: 1.1 }}>
            {collapsed ? 'A' : 'AcomOfferDesk'}
          </Typography>
        </Stack>

        <Stack spacing={1.25} sx={{ overflowY: { lg: 'auto' }, pr: { lg: 0.5 } }}>
          {config.title && !collapsed ? (
            <Typography variant="body2" color="text.secondary" sx={{ px: 0.4, pb: 0.25, fontWeight: 600 }}>
              {config.title}
            </Typography>
          ) : null}

          {topItems.map((item) => {
            const icon = item.icon ?? getHeaderNavigationIcon(item.key);
            if (!item.to) {
              return (
                <SidebarMenuButton
                  key={item.key}
                  label={item.label}
                  icon={icon}
                  collapsed={collapsed}
                  disabled={item.disabled}
                />
              );
            }

            return (
              <NavLink key={item.key} to={item.to} style={navLinkStyles}>
                {({ isActive }) => (
                  <SidebarMenuButton
                    label={item.label}
                    icon={icon}
                    collapsed={collapsed}
                    active={isActive}
                    disabled={item.disabled}
                  />
                )}
              </NavLink>
            );
          })}

          {config.tabs.map((tab) => {
            if (tab.key === 'savings') {
              return null;
            }
            if (tab.key === 'plan' && config.tabs.some((tabItem) => tabItem.key === 'dashboard')) {
              return null;
            }

            if (tab.key === 'dashboard') {
              const isDashboardRelatedActive =
                config.activeTab === 'dashboard' || config.activeTab === 'savings' || config.activeTab === 'plan';
              const shouldShowDashboardChildren =
                !collapsed && (hasSavingsTab || hasPlanTab) && (isDashboardMenuHovered || isDashboardRelatedActive);

              return (
                <Stack
                  key={tab.key}
                  spacing={0.5}
                  onMouseEnter={() => {
                    if (!collapsed) {
                      setIsDashboardMenuHovered(true);
                    }
                  }}
                  onMouseLeave={() => {
                    if (!collapsed) {
                      setIsDashboardMenuHovered(false);
                    }
                  }}
                >
                  <Box
                    onClick={(event) => {
                      if (collapsed && (hasSavingsTab || hasPlanTab)) {
                        setDashboardMenuAnchorEl((currentAnchorEl) =>
                          currentAnchorEl ? null : (event.currentTarget as HTMLElement)
                        );
                        return;
                      }

                      config.onTabChange?.('dashboard');
                    }}
                  >
                    <SidebarMenuButton
                      label={tab.label}
                      icon={getHeaderNavigationIcon(tab.key)}
                      collapsed={collapsed}
                      active={collapsed ? isDashboardRelatedActive : false}
                    />
                  </Box>
                  {shouldShowDashboardChildren ? (
                    <Stack spacing={0.35} sx={{ pl: 1.25 }}>
                      {hasDashboardProcessTab ? (
                        <SidebarMenuButton
                          label="Процесс работы"
                          icon={getHeaderNavigationIcon('dashboard-process')}
                          collapsed={false}
                          active={config.activeTab === 'dashboard'}
                          onClick={() => config.onTabChange?.('dashboard')}
                        />
                      ) : null}
                      {hasSavingsTab ? (
                        <SidebarMenuButton
                          label="Экономия"
                          icon={getHeaderNavigationIcon('savings')}
                          collapsed={false}
                          active={config.activeTab === 'savings'}
                          onClick={() => config.onTabChange?.('savings')}
                        />
                      ) : null}
                      {hasPlanTab ? (
                        <SidebarMenuButton
                          label="План"
                          icon={getHeaderNavigationIcon('plan')}
                          collapsed={false}
                          active={config.activeTab === 'plan'}
                          onClick={() => config.onTabChange?.('plan')}
                        />
                      ) : null}
                    </Stack>
                  ) : null}
                </Stack>
              );
            }

            return (
              <SidebarMenuButton
                key={tab.key}
                label={tab.label}
                icon={getHeaderNavigationIcon(tab.key)}
                collapsed={collapsed}
                active={config.activeTab === tab.value}
                onClick={() => config.onTabChange?.(tab.value)}
              />
            );
          })}

          {config.backAction ? (
            <SidebarMenuButton
              label={config.backAction.label}
              icon={<ArrowBackOutlined fontSize="small" />}
              collapsed={collapsed}
              onClick={config.backAction.onClick}
            />
          ) : null}

          {config.actions.map((action) => (
            <SidebarMenuButton
              key={action.key}
              label={action.label}
              icon={<AddOutlined fontSize="small" />}
              collapsed={collapsed}
              onClick={action.onClick}
            />
          ))}

          {isSuperadmin ? null : <NormativeFileButton iconOnly={collapsed} sidebar />}
        </Stack>

        <Menu
          open={isDashboardPopupOpen}
          anchorEl={dashboardMenuAnchorEl}
          onClose={() => {
            setDashboardMenuAnchorEl(null);
          }}
          anchorOrigin={{ vertical: 'center', horizontal: 'right' }}
          transformOrigin={{ vertical: 'center', horizontal: 'left' }}
        >
          {hasDashboardProcessTab ? (
            <MenuItem
              onClick={() => {
                config.onTabChange?.('dashboard');
                setDashboardMenuAnchorEl(null);
              }}
            >
              Процесс работы
            </MenuItem>
          ) : null}
          {hasSavingsTab ? (
            <MenuItem
              onClick={() => {
                config.onTabChange?.('savings');
                setDashboardMenuAnchorEl(null);
              }}
            >
              Экономия
            </MenuItem>
          ) : null}
          {hasPlanTab ? (
            <MenuItem
              onClick={() => {
                config.onTabChange?.('plan');
                setDashboardMenuAnchorEl(null);
              }}
            >
              План
            </MenuItem>
          ) : null}
        </Menu>

        <Stack
          spacing={1.25}
          sx={{
            mt: isCompactHeight ? 2 : 'auto',
            pt: isCompactHeight ? 2 : 0,
            borderTop: isCompactHeight ? '1px solid' : 'none',
            borderColor: 'divider'
          }}
        >
          {config.showRoleGuide ? <RoleGuideButton iconOnly={collapsed} sidebar /> : null}
          {config.showFeedback ? <FeedbackButton iconOnly={collapsed} sidebar /> : null}

          {config.showProfile ? (
            collapsed ? (
              <>
                <ProfileButton iconOnly sidebar />
                <SidebarMenuButton
                  label="Выйти"
                  icon={<LogoutOutlined fontSize="small" />}
                  collapsed
                  onClick={onLogout}
                />
              </>
            ) : (
              <Stack direction="row" spacing={1}>
                <Stack sx={{ flex: 1, minWidth: 0 }}>
                  <ProfileButton sidebar />
                </Stack>
                <Tooltip title="Выйти" placement="right" enterDelay={150}>
                  <Box component="span" sx={{ display: 'inline-flex' }}>
                    <ActionButton
                      kind="custom"
                      showNavigationIcons={false}
                      onClick={onLogout}
                      aria-label="Выйти"
                      sx={{
                        minWidth: 56,
                        width: 56,
                        minHeight: 42,
                        borderRadius: `${theme.acomShape.buttonRadius}px !important`,
                      }}
                    >
                      <LogoutOutlined fontSize="small" />
                    </ActionButton>
                  </Box>
                </Tooltip>
              </Stack>
            )
          ) : config.showLogout ? (
            <SidebarMenuButton
              label="Выйти"
              icon={<LogoutOutlined fontSize="small" />}
              collapsed={collapsed}
              onClick={onLogout}
            />
          ) : null}
        </Stack>

        {onToggleCollapse ? (
          <>
            <Stack
              component="div"
              onMouseEnter={() => setIsEdgeHovered(true)}
              onMouseLeave={() => setIsEdgeHovered(false)}
              sx={{ position: 'absolute', top: 0, right: 0, width: 28, height: '100%', zIndex: 3 }}
            />

            <IconButton
              onClick={onToggleCollapse}
              size="small"
              onMouseEnter={() => setIsToggleHovered(true)}
              onMouseLeave={() => setIsToggleHovered(false)}
              sx={(theme) => ({
                position: 'absolute',
                top: '50%',
                right: 8,
                transform: isToggleVisible ? 'translate(0, -50%)' : 'translate(8px, -50%)',
                opacity: isToggleVisible ? 1 : 0,
                pointerEvents: isToggleVisible ? 'auto' : 'none',
                zIndex: 4,
                borderRadius: `${theme.acomShape.controlRadius}px`,
                border: '1px solid',
                borderColor: 'divider',
                color: 'text.secondary',
                bgcolor: 'background.paper',
                transition: 'opacity 180ms ease, transform 180ms ease, border-color 180ms ease, color 180ms ease',
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: alpha(theme.palette.primary.main, 0.04),
                  color: 'primary.main'
                }
              })}
            >
              {collapsed ? <KeyboardArrowRightRounded fontSize="small" /> : <KeyboardArrowLeftRounded fontSize="small" />}
            </IconButton>
          </>
        ) : null}
      </Stack>
    </Stack>
  );
};


