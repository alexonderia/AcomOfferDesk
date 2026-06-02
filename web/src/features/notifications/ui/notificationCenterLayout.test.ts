import { describe, expect, it } from 'vitest';
import {
  NOTIFICATION_CENTER_DEFAULT_SIZE,
  NOTIFICATION_CENTER_MIN_SIZE,
  NOTIFICATION_CENTER_VIEWPORT_BOTTOM_INSET,
  captureNotificationCenterAnchor,
  clampNotificationCenterSize,
  loadNotificationCenterSize,
} from './notificationCenterLayout';

describe('notificationCenterLayout', () => {
  it('clamps size to allowed bounds', () => {
    expect(
      clampNotificationCenterSize({
        width: 100,
        height: 100,
      })
    ).toEqual(NOTIFICATION_CENTER_MIN_SIZE);

    expect(
      clampNotificationCenterSize({
        width: 5000,
        height: 5000,
      }).width
    ).toBe(720);
  });

  it('clamps size to the current viewport when the viewport is narrow', () => {
    const originalInnerWidth = window.innerWidth;
    const originalInnerHeight = window.innerHeight;
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 360 });
    Object.defineProperty(window, 'innerHeight', { configurable: true, value: 500 });

    try {
      expect(
        clampNotificationCenterSize({
          width: 1000,
          height: 1000,
        })
      ).toEqual({
        width: 328,
        height: 468,
      });
    } finally {
      Object.defineProperty(window, 'innerWidth', { configurable: true, value: originalInnerWidth });
      Object.defineProperty(window, 'innerHeight', { configurable: true, value: originalInnerHeight });
    }
  });

  it('returns default size when storage is empty', () => {
    expect(loadNotificationCenterSize()).toEqual(NOTIFICATION_CENTER_DEFAULT_SIZE);
  });

  it('anchors panel to viewport bottom-left near the sidebar control', () => {
    const anchorEl = document.createElement('button');
    anchorEl.getBoundingClientRect = () =>
      ({
        left: 12,
        bottom: 640,
        top: 600,
        right: 220,
        width: 208,
        height: 40,
      }) as DOMRect;

    expect(captureNotificationCenterAnchor(anchorEl)).toEqual({
      left: 12,
      bottom: NOTIFICATION_CENTER_VIEWPORT_BOTTOM_INSET,
    });
  });
});
