import { Tabs, Tab } from '@mui/material';
import type { HeaderTab } from '../model/types';

type HeaderNavProps = {
  tabs: HeaderTab[];
  activeTab?: string;
  onTabChange?: (value: string) => void;
};

export const HeaderNav = ({ tabs, activeTab, onTabChange }: HeaderNavProps) => {
  if (!tabs.length || !activeTab || !onTabChange) {
    return null;
  }

  return (
    <Tabs
      value={activeTab}
      onChange={(_, value: string) => onTabChange(value)}
      variant="scrollable"
      scrollButtons="auto"
    >
      {tabs.map((tab) => (
        <Tab key={tab.key} value={tab.value} label={tab.label} />
      ))}
    </Tabs>
  );
};
