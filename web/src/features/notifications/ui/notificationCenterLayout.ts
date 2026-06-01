export type NotificationCenterSize = {
  width: number;
  height: number;
};

/** Screen position of the panel bottom-left corner (fixed while resizing). */
export type NotificationCenterAnchor = {
  left: number;
  bottom: number;
};

/** Distance from the viewport bottom edge for the panel's fixed corner. */
export const NOTIFICATION_CENTER_VIEWPORT_BOTTOM_INSET = 16;

export const captureNotificationCenterAnchor = (anchorEl: HTMLElement): NotificationCenterAnchor => {
  const rect = anchorEl.getBoundingClientRect();
  return {
    left: rect.left,
    bottom: NOTIFICATION_CENTER_VIEWPORT_BOTTOM_INSET,
  };
};

export const NOTIFICATION_CENTER_SIZE_STORAGE_KEY = 'acom.notificationCenter.size';

export const NOTIFICATION_CENTER_DEFAULT_SIZE: NotificationCenterSize = {
  width: 420,
  height: 520,
};

export const NOTIFICATION_CENTER_PANEL_BORDER_RADIUS_PX = 8;
export const NOTIFICATION_CENTER_CARD_BORDER_RADIUS_PX = 6;

export const NOTIFICATION_CENTER_MIN_SIZE: NotificationCenterSize = {
  width: 320,
  height: 360,
};

export const NOTIFICATION_CENTER_MAX_SIZE: NotificationCenterSize = {
  width: 720,
  height: 900,
};

const clampDimension = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

export const getMaxNotificationCenterHeight = () =>
  typeof window === 'undefined' ? 900 : Math.min(window.innerHeight * 0.9, 900);

export const clampNotificationCenterSize = (size: NotificationCenterSize): NotificationCenterSize => ({
  width: clampDimension(size.width, NOTIFICATION_CENTER_MIN_SIZE.width, NOTIFICATION_CENTER_MAX_SIZE.width),
  height: clampDimension(
    size.height,
    NOTIFICATION_CENTER_MIN_SIZE.height,
    getMaxNotificationCenterHeight()
  ),
});

export const loadNotificationCenterSize = (): NotificationCenterSize => {
  if (typeof window === 'undefined') {
    return NOTIFICATION_CENTER_DEFAULT_SIZE;
  }

  try {
    const raw = window.localStorage.getItem(NOTIFICATION_CENTER_SIZE_STORAGE_KEY);
    if (!raw) {
      return NOTIFICATION_CENTER_DEFAULT_SIZE;
    }
    const parsed = JSON.parse(raw) as Partial<NotificationCenterSize>;
    if (typeof parsed.width !== 'number' || typeof parsed.height !== 'number') {
      return NOTIFICATION_CENTER_DEFAULT_SIZE;
    }
    return clampNotificationCenterSize({ width: parsed.width, height: parsed.height });
  } catch {
    return NOTIFICATION_CENTER_DEFAULT_SIZE;
  }
};

export const saveNotificationCenterSize = (size: NotificationCenterSize) => {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.localStorage.setItem(
      NOTIFICATION_CENTER_SIZE_STORAGE_KEY,
      JSON.stringify(clampNotificationCenterSize(size))
    );
  } catch {
    // Ignore quota / private mode errors.
  }
};
