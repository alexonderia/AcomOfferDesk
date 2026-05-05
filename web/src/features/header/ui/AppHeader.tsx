import { SuperadminSidebarHeader } from './SuperadminSidebarHeader';
import type { HeaderConfig } from '../model/types';

type AppHeaderProps = {
  config: HeaderConfig;
  onLogout: () => void;
  sidebarCollapsed?: boolean;
  onToggleSidebarCollapse?: () => void;
};

export const AppHeader = ({ config, onLogout, sidebarCollapsed = false, onToggleSidebarCollapse }: AppHeaderProps) => {
  if (config.mode === 'hidden') {
    return null;
  }

  return (
    <SuperadminSidebarHeader
      config={config}
      onLogout={onLogout}
      collapsed={sidebarCollapsed}
      onToggleCollapse={onToggleSidebarCollapse}
    />
  );
};
