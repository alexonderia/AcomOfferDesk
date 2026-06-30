import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { BreadcrumbItem } from '@shared/components/BreadcrumbsNav';

type PageBreadcrumbActionsContextValue = {
  actions: ReactNode;
  items: BreadcrumbItem[];
  setActions: (actions: ReactNode) => void;
  setItems: (items: BreadcrumbItem[]) => void;
};

const PageBreadcrumbActionsContext = createContext<PageBreadcrumbActionsContextValue | null>(null);

export const PageBreadcrumbActionsProvider = ({ children }: { children: ReactNode }) => {
  const [actions, setActions] = useState<ReactNode>(null);
  const [items, setItems] = useState<BreadcrumbItem[]>([]);
  const value = useMemo(() => ({ actions, items, setActions, setItems }), [actions, items]);

  return (
    <PageBreadcrumbActionsContext.Provider value={value}>{children}</PageBreadcrumbActionsContext.Provider>
  );
};

export const usePageBreadcrumbActionsState = () => {
  const context = useContext(PageBreadcrumbActionsContext);
  if (!context) {
    throw new Error('usePageBreadcrumbActionsState must be used within PageBreadcrumbActionsProvider');
  }
  return context.actions;
};

export const usePageBreadcrumbItemsState = () => {
  const context = useContext(PageBreadcrumbActionsContext);
  if (!context) {
    throw new Error('usePageBreadcrumbItemsState must be used within PageBreadcrumbActionsProvider');
  }
  return context.items;
};

export const useSetPageBreadcrumbActions = (actions: ReactNode) => {
  const context = useContext(PageBreadcrumbActionsContext);
  if (!context) {
    throw new Error('useSetPageBreadcrumbActions must be used within PageBreadcrumbActionsProvider');
  }

  const { setActions } = context;

  useEffect(() => {
    setActions(actions);
    return () => setActions(null);
  }, [actions, setActions]);
};

export const useSetPageBreadcrumbItems = (items: BreadcrumbItem[]) => {
  const context = useContext(PageBreadcrumbActionsContext);
  if (!context) {
    throw new Error('useSetPageBreadcrumbItems must be used within PageBreadcrumbActionsProvider');
  }

  const { setItems } = context;

  useEffect(() => {
    setItems(items);
    return () => setItems([]);
  }, [items, setItems]);
};
