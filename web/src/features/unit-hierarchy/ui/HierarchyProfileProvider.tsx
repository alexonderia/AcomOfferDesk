import { useCallback, useState, type ReactNode } from 'react';
import { useAuth } from '@app/providers/AuthProvider';
import { EmployeeCardDialog } from '@features/admin/components/EmployeeCardDialog';
import { hasPermission } from '@shared/auth/permissions';
import type { UnitMember } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';
import { HierarchyProfileContext } from '../model/HierarchyProfileContext';
import { useHierarchyEmployeeCard } from '../model/useHierarchyEmployeeCard';

const HierarchyEmployeeCard = ({ member, onClose }: { member: UnitMember; onClose: () => void }) => {
  const { profile, error, hierarchy, unitsTree, hierarchyError, isLoadingHierarchy, retry } = useHierarchyEmployeeCard(member.user_id);
  return <EmployeeCardDialog open onClose={onClose} user={profile} error={error} onRetry={retry}
    hierarchy={hierarchy} unitsTree={unitsTree} hierarchyError={hierarchyError} isLoadingHierarchy={isLoadingHierarchy} />;
};

export const HierarchyProfileProvider = ({ children }: { children: ReactNode }) => {
  const { session } = useAuth();
  const [member, setMember] = useState<UnitMember | null>(null);
  const openCard = useCallback((selected: UnitMember) => {
    if (selected.role_id !== ROLE.CONTRACTOR) setMember(selected);
  }, []);
  const canOpenCard = hasPermission(session, 'users.read');
  return (
    <HierarchyProfileContext.Provider value={canOpenCard ? openCard : null}>
      {children}
      {canOpenCard && member ? <HierarchyEmployeeCard key={member.user_id} member={member} onClose={() => setMember(null)} /> : null}
    </HierarchyProfileContext.Provider>
  );
};
