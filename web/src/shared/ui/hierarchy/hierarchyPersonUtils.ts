export const hierarchyStatusColorByCode: Record<string, string> = {
  active: '#16a34a',
  inactive: '#9ca3af',
  review: '#d97706',
  blacklist: '#dc2626',
};

export const hierarchyStatusLabelByCode: Record<string, string> = {
  active: 'Активен',
  inactive: 'Неактивен',
  review: 'На проверке',
  blacklist: 'Заблокирован',
};

export const isPlaceholderPersonName = (value: string | null | undefined) => {
  const normalized = (value ?? '').trim().toLowerCase();
  return normalized.includes('вакан') || normalized.includes('не указано');
};

export const getPersonDisplayName = (fullName: string | null | undefined, userId: string) => {
  const name = fullName?.trim();
  if (!name) {
    return userId;
  }
  if (isPlaceholderPersonName(name)) {
    return 'Вакансия';
  }
  return name;
};

export const getPersonInitials = (fullName: string | null | undefined, userId: string) => {
  const name = fullName?.trim();
  if (name && !isPlaceholderPersonName(name)) {
    const parts = name.split(/\s+/).filter(Boolean);
    const initials = `${parts[0]?.[0] ?? ''}${parts.length > 1 ? parts[1]?.[0] ?? '' : ''}`;
    if (initials) {
      return initials.toUpperCase();
    }
  }
  return (userId || '?').slice(0, 2).toUpperCase();
};

export const getMemberAccentColor = (roleName: string) => {
  const normalizedRole = roleName.trim().toLowerCase();
  if (normalizedRole.includes('админ')) {
    return '#1d4ed8';
  }
  if (normalizedRole.includes('ведущ')) {
    return '#0f766e';
  }
  if (normalizedRole.includes('руковод') || normalizedRole.includes('глав')) {
    return '#7c3aed';
  }
  if (normalizedRole.includes('контраг')) {
    return '#b45309';
  }
  return '#475569';
};

export type HierarchyPersonVisual = {
  userId: string;
  fullName: string | null;
  roleName: string;
  status?: string;
  photoUrl?: string | null;
};

export type HierarchyPersonTone = 'default' | 'manager' | 'self' | 'subordinate';

export const resolveUserPhotoUrl = (person: Pick<HierarchyPersonVisual, 'userId' | 'photoUrl'>) =>
  person.photoUrl?.trim() || null;
