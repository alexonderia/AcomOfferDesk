import { Avatar } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import {
  getPersonInitials,
  getPersonDisplayName,
  type HierarchyPersonTone,
  type HierarchyPersonVisual,
  resolveUserPhotoUrl,
} from './hierarchyPersonUtils';
import { getHierarchyAvatarSx } from './hierarchyThemeStyles';

type HierarchyPersonAvatarProps = {
  highlight?: boolean;
  person: HierarchyPersonVisual;
  size?: number;
  tone?: HierarchyPersonTone;
};

export const HierarchyPersonAvatar = ({
  highlight = false,
  person,
  size = 36,
  tone = 'default',
}: HierarchyPersonAvatarProps) => {
  const theme = useTheme();
  const photoUrl = resolveUserPhotoUrl(person);
  const displayName = getPersonDisplayName(person.fullName, person.userId);
  const avatarSx = getHierarchyAvatarSx(theme, highlight, tone);

  return (
    <Avatar
      src={photoUrl ?? undefined}
      alt={displayName}
      sx={{
        ...avatarSx,
        width: size,
        height: size,
        fontSize: size <= 30 ? 11 : 13,
      }}
    >
      {getPersonInitials(person.fullName, person.userId)}
    </Avatar>
  );
};
