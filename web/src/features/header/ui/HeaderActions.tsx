import { Box, Button, Stack } from '@mui/material';
import { FeedbackButton } from '@shared/components/FeedbackButton';
import { ProfileButton } from '@shared/components/ProfileButton';
import { RoleGuideButton } from '@shared/components/RoleGuideButton';
import type { HeaderAction } from '../model/types';

type HeaderActionsProps = {
  actions: HeaderAction[];
  showFeedback: boolean;
  showRoleGuide: boolean;
  showProfile: boolean;
  showLogout: boolean;
  onLogout: () => void;
  sidebar?: boolean;
};

export const HeaderActions = ({
  actions,
  showFeedback,
  showRoleGuide,
  showProfile,
  showLogout,
  onLogout,
  sidebar = false
}: HeaderActionsProps) => {
  const commonActions = (
    <>
      {showFeedback ? <FeedbackButton /> : null}
      {showRoleGuide ? <RoleGuideButton /> : null}
      {showProfile ? <ProfileButton /> : null}
      {showLogout ? (
        <Button variant="outlined" onClick={onLogout}>
          Выйти
        </Button>
      ) : null}
    </>
  );

  if (sidebar) {
    return (
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1fr) auto',
          gap: 1.2,
          alignItems: 'center',
          '& > .sa-feedback button': { width: '100%', height: 44 },
          '& > .sa-logout': { gridColumn: '1 / -1', height: 44 }
        }}
      >
        {showFeedback ? (
          <Box className="sa-feedback">
            <FeedbackButton />
          </Box>
        ) : null}
        {showRoleGuide ? <RoleGuideButton /> : null}
        {showLogout ? (
          <Button className="sa-logout" variant="outlined" onClick={onLogout}>
            Выйти
          </Button>
        ) : null}
      </Box>
    );
  }

  return (
    <Stack direction="row" spacing={1.5} alignItems="center">
      {actions.map((action) => (
        <Button
          key={action.key}
          variant={action.variant}
          sx={action.variant === 'outlined'
            ? { px: 3, borderRadius: 999, textTransform: 'none', whiteSpace: 'nowrap' }
            : { px: 3, boxShadow: 'none', '&:hover': { boxShadow: 'none' } }}
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      ))}
      {commonActions}
    </Stack>
  );
};
