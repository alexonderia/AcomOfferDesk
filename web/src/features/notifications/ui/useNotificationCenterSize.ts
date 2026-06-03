import { useCallback, useEffect, useRef, useState, type MouseEvent, type PointerEvent } from 'react';
import {
  clampNotificationCenterSize,
  loadNotificationCenterSize,
  NOTIFICATION_CENTER_DEFAULT_SIZE,
  saveNotificationCenterSize,
  type NotificationCenterSize,
} from './notificationCenterLayout';

export const useNotificationCenterSize = () => {
  const [size, setSize] = useState<NotificationCenterSize>(loadNotificationCenterSize);
  const resizeSessionRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    startWidth: number;
    startHeight: number;
  } | null>(null);

  useEffect(() => {
    const handleWindowResize = () => {
      setSize((current) => clampNotificationCenterSize(current));
    };

    window.addEventListener('resize', handleWindowResize);
    return () => window.removeEventListener('resize', handleWindowResize);
  }, []);

  const handleResizePointerDown = useCallback((event: PointerEvent<HTMLElement>) => {
    event.preventDefault();
    event.stopPropagation();

    resizeSessionRef.current = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      startWidth: size.width,
      startHeight: size.height,
    };

    event.currentTarget.setPointerCapture(event.pointerId);
  }, [size.height, size.width]);

  const handleResizePointerMove = useCallback((event: PointerEvent<HTMLElement>) => {
    const session = resizeSessionRef.current;
    if (!session || session.pointerId !== event.pointerId) {
      return;
    }

    const deltaX = event.clientX - session.startX;
    const deltaY = event.clientY - session.startY;

    setSize(
      clampNotificationCenterSize({
        width: session.startWidth + deltaX,
        height: session.startHeight - deltaY,
      })
    );
  }, []);

  const resetToDefaultSize = useCallback(() => {
    const next = clampNotificationCenterSize(NOTIFICATION_CENTER_DEFAULT_SIZE);
    setSize(next);
    saveNotificationCenterSize(next);
  }, []);

  const handleResizeDoubleClick = useCallback(
    (event: MouseEvent<HTMLElement>) => {
      event.preventDefault();
      event.stopPropagation();
      resetToDefaultSize();
    },
    [resetToDefaultSize]
  );

  const finishResize = useCallback((event: PointerEvent<HTMLElement>) => {
    const session = resizeSessionRef.current;
    if (!session || session.pointerId !== event.pointerId) {
      return;
    }

    resizeSessionRef.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }

    setSize((current) => {
      const next = clampNotificationCenterSize(current);
      saveNotificationCenterSize(next);
      return next;
    });
  }, []);

  return {
    size,
    resizeHandleProps: {
      onPointerDown: handleResizePointerDown,
      onPointerMove: handleResizePointerMove,
      onPointerUp: finishResize,
      onPointerCancel: finishResize,
      onDoubleClick: handleResizeDoubleClick,
    },
  };
};
