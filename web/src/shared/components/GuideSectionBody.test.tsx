import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { GuideSectionBody } from './GuideSectionBody';
import type { GuideBlock } from '@shared/content/roleGuideTypes';

describe('Guide illustrations', () => {
  it('keeps instructions readable when an image fails and resets the error for another chapter image', () => {
    const blocks = (src: string): GuideBlock[] => [
      { type: 'paragraph', text: 'Откройте собственное КП.' },
      { type: 'image', src, alt: 'Учебный пример', caption: 'Данные для обучения.' },
    ];
    const view = render(<GuideSectionBody blocks={blocks('/missing.png')} />);
    fireEvent.error(screen.getByRole('img'));
    expect(screen.getByText(/Иллюстрация недоступна/)).toBeInTheDocument();
    expect(screen.getByText('Откройте собственное КП.')).toBeInTheDocument();
    view.rerender(<GuideSectionBody blocks={blocks('/next.png')} />);
    expect(screen.getByRole('img')).toHaveAttribute('src', '/next.png');
    expect(screen.getByRole('link')).toHaveAttribute('rel', 'noopener noreferrer');
  });
});
