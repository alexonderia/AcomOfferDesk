import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

type PageBreadcrumbActionsContextValue = {
  actions: ReactNode;
  setActions: (actions: ReactNode) => void;
};

const PageBreadcrumbActionsContext = createContext<PageBreadcrumbActionsContextValue | null>(null);

export const PageBreadcrumbActionsProvider = ({ children }: { children: ReactNode }) => {
  const [actions, setActions] = useState<ReactNode>(null);
  const value = useMemo(() => ({ actions, setActions }), [actions]);

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
