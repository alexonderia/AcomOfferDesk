import type { ReactNode } from 'react';

export type HeaderMode = 'hidden' | 'topbar' | 'sidebar';

export type HeaderTab = {
  key: string;
  label: string;
  value: string;
};

export type HeaderAction = {
  key: string;
  label: string;
  variant: 'contained' | 'outlined';
  onClick: () => void;
};

export type HeaderBackAction = {
  label: string;
  onClick: () => void;
};

export type HeaderSidebarItem = {
  key: string;
  label: string;
  icon?: ReactNode;
  to?: string;
  disabled?: boolean;
  isBottomItem?: boolean;
};

export type HeaderMobileNavItem = {
  key: string;
  label: string;
  to?: string;
  tabValue?: string;
  disabled?: boolean;
  children?: HeaderMobileNavItem[];
};

export type HeaderConfig = {
  mode: HeaderMode;
  title?: string;
  tabs: HeaderTab[];
  activeTab?: string;
  onTabChange?: (value: string) => void;
  actions: HeaderAction[];
  backAction?: HeaderBackAction;
  breadcrumbs?: { key: string; label: string; to?: string }[];
  sidebarItems?: HeaderSidebarItem[];
  mobileNavItems?: HeaderMobileNavItem[];
  showFeedback: boolean;
  showRoleGuide: boolean;
  showProfile: boolean;
  showLogout: boolean;
};
