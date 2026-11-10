import { useState } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PreviewZoomControls } from './PreviewZoomControls';

const Controls = () => {
  const [zoom, setZoom] = useState(1);
  return <PreviewZoomControls zoom={zoom} onChange={setZoom} disabled={false} />;
};

describe('preview zoom controls', () => {
  it('supports enlarging, reducing and returning to fit height', () => {
    render(<Controls />);
    fireEvent.click(screen.getByRole('button', { name: 'Увеличить' }));
    expect(screen.getByText('125%')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Уменьшить' }));
    fireEvent.click(screen.getByRole('button', { name: 'Уменьшить' }));
    expect(screen.getByText('75%')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'По высоте окна' }));
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('bounds zoom and disables actions while loading', () => {
    const view = render(<PreviewZoomControls zoom={0.25} onChange={vi.fn()} disabled={false} />);
    expect(screen.getByRole('button', { name: 'Уменьшить' })).toBeDisabled();
    view.rerender(<PreviewZoomControls zoom={4} onChange={vi.fn()} disabled={false} />);
    expect(screen.getByRole('button', { name: 'Увеличить' })).toBeDisabled();
    view.rerender(<PreviewZoomControls zoom={1} onChange={vi.fn()} disabled />);
    expect(screen.getByRole('button', { name: 'Увеличить' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'По высоте окна' })).toBeDisabled();
  });
});
