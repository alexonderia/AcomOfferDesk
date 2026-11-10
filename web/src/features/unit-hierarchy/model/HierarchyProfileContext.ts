import { createContext, useContext } from 'react';
import type { UnitMember } from '@shared/api/units';

export const HierarchyProfileContext = createContext<((member: UnitMember) => void) | null>(null);
export const useHierarchyProfile = () => useContext(HierarchyProfileContext);
