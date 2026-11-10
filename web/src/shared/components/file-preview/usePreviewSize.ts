import { useEffect, useState, type RefObject } from 'react';

export const usePreviewSize = (ref: RefObject<HTMLElement>) => {
  const [size, setSize] = useState({ width: 1, height: 1 });
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const measure = () => {
      // Scrollbars must not change the fit baseline while zooming in and out.
      const bounds = element.getBoundingClientRect();
      const width = Math.max(1, (bounds.width || element.clientWidth) - 16);
      const height = Math.max(1, (bounds.height || element.clientHeight) - 16);
      setSize((current) => current.width === width && current.height === height ? current : { width, height });
    };
    measure();
    const observer = typeof ResizeObserver === 'undefined' ? undefined : new ResizeObserver(measure);
    observer?.observe(element);
    window.addEventListener('resize', measure);
    return () => { observer?.disconnect(); window.removeEventListener('resize', measure); };
  }, [ref]);
  return size;
};
