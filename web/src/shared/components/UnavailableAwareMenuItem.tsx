import { MenuItem, Tooltip } from '@mui/material';
import type { MenuItemProps } from '@mui/material';
import type { MouseEvent, KeyboardEvent } from 'react';
import type { UnavailabilityPeriodInfo } from '@shared/lib/unavailability';
import { getUnavailabilityTooltip } from '@shared/lib/unavailability';

type UnavailableAwareMenuItemProps = Omit<MenuItemProps, 'children'> & {
  value: string;
  label: string;
  unavailablePeriod?: UnavailabilityPeriodInfo | null;
};

export const UnavailableAwareMenuItem = ({
  value,
  label,
  unavailablePeriod = null,
  ...menuItemProps
}: UnavailableAwareMenuItemProps) => {
  const isDisabled = unavailablePeriod !== null;
  const tooltipText = isDisabled ? getUnavailabilityTooltip(unavailablePeriod) : undefined;

  const blockSelection = (event: MouseEvent<HTMLElement> | KeyboardEvent<HTMLElement>) => {
    event.preventDefault();
    event.stopPropagation();
  };

  if (!isDisabled) {
    return (
      <MenuItem value={value} {...menuItemProps}>
        {label}
      </MenuItem>
    );
  }

  return (
    <MenuItem
      {...menuItemProps}
      value={value}
      aria-disabled
      disableRipple
      onClick={blockSelection}
      onMouseDown={blockSelection}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          blockSelection(event);
        }
      }}
      sx={{
        opacity: 0.55,
        color: 'text.disabled',
        cursor: 'not-allowed'
      }}
    >
      <Tooltip title={tooltipText ?? ''} arrow>
        <span style={{ display: 'block', width: '100%' }}>
          {label}
        </span>
      </Tooltip>
    </MenuItem>
  );
};
