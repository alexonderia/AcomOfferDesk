import type { ReactNode } from 'react';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { alpha, useTheme } from '@mui/material/styles';
import { ActionButton } from '@shared/components/ActionButton';

type SidebarMenuButtonProps = {
  label: string;
  icon: ReactNode;
  collapsed: boolean;
  active?: boolean;
  onClick?: () => void;
  disabled?: boolean;
};

export const SidebarMenuButton = ({
  label,
  icon,
  collapsed,
  active = false,
  onClick,
  disabled = false,
}: SidebarMenuButtonProps) => {
  const theme = useTheme();

  return (
    <Tooltip title={label} placement="right" enterDelay={150} disableHoverListener={!collapsed}>
      <Stack component="span" sx={{ display: 'block', width: '100%' }}>
        <ActionButton
          kind="custom"
          selected={active}
          showNavigationIcons={false}
          onClick={onClick}
          disabled={disabled}
          sx={{
            width: '100%',
            minHeight: 42,
            minWidth: 0,
            borderRadius: `${theme.acomShape.buttonRadius}px !important`,
            justifyContent: collapsed ? 'center' : 'flex-start',
            px: collapsed ? 0 : 1.75,
            gap: collapsed ? 0 : 1.25,
            transition: 'background-color 0.28s ease, border-color 0.28s ease, color 0.28s ease, padding 0.32s ease, gap 0.32s ease',
            '&:focus-visible': {
              outline: `2px solid ${alpha(theme.palette.primary.main, 0.28)}`,
              outlineOffset: 1,
            },
          }}
        >
          <Stack component="span" sx={{ display: 'inline-flex', lineHeight: 1 }}>
            {icon}
          </Stack>
          <Typography
            sx={{
              maxWidth: collapsed ? 0 : 160,
              opacity: collapsed ? 0 : 1,
              transform: collapsed ? 'translateX(-4px)' : 'translateX(0)',
              overflow: 'hidden',
              textOverflow: 'clip',
              whiteSpace: 'nowrap',
              fontSize: 14,
              fontWeight: active ? 600 : 500,
              lineHeight: 1.2,
              transition: 'max-width 0.34s ease, opacity 0.24s ease, transform 0.34s ease',
            }}
          >
            {label}
          </Typography>
        </ActionButton>
      </Stack>
    </Tooltip>
  );
};
