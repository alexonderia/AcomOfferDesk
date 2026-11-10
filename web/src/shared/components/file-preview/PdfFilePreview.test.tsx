import { Blob as NodeBlob } from 'node:buffer';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PdfFilePreview } from './PdfFilePreview';

const mocks = vi.hoisted(() => ({ load: vi.fn(), getPage: vi.fn(), render: vi.fn(), cancel: vi.fn(), destroy: vi.fn() }));
vi.mock('pdfjs-dist', () => ({ GlobalWorkerOptions: {}, getDocument: mocks.load }));
const blob = new NodeBlob(['test pdf']) as Blob;

describe('PDF fit height and zoom', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(HTMLElement.prototype, 'clientWidth', 'get').mockReturnValue(800);
    vi.spyOn(HTMLElement.prototype, 'clientHeight', 'get').mockReturnValue(600);
    mocks.render.mockImplementation(() => ({ promise: Promise.resolve(), cancel: mocks.cancel }));
    mocks.destroy.mockResolvedValue(undefined);
    mocks.getPage.mockImplementation(async (number) => ({
      getViewport: ({ scale }: { scale: number }) => ({ width: (number === 1 ? 600 : 1000) * scale, height: (number === 1 ? 800 : 500) * scale }),
      render: mocks.render,
    }));
    mocks.load.mockReturnValue({ promise: Promise.resolve({ numPages: 2, getPage: mocks.getPage }), destroy: mocks.destroy });
  });
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it('fits portrait and landscape pages within the available height and width', async () => {
    render(<PdfFilePreview blob={blob} zoom={1} />);
    await waitFor(() => expect(screen.getByRole('img', { name: 'Страница PDF 1' })).toHaveStyle({ height: '584px', width: '438px' }));
    fireEvent.click(screen.getByRole('button', { name: 'Следующая страница' }));
    await waitFor(() => expect(screen.getByRole('img', { name: 'Страница PDF 2' })).toHaveStyle({ width: '784px', height: '392px' }));
  });

  it('enlarges a page and restores fitting without parsing the PDF again', async () => {
    const view = render(<PdfFilePreview blob={blob} zoom={1} />);
    await waitFor(() => expect(screen.getByRole('img', { name: 'Страница PDF 1' })).toHaveStyle({ height: '584px' }));
    view.rerender(<PdfFilePreview blob={blob} zoom={2} />);
    await waitFor(() => expect(screen.getByRole('img', { name: 'Страница PDF 1' })).toHaveStyle({ height: '1168px' }));
    view.rerender(<PdfFilePreview blob={blob} zoom={1} />);
    await waitFor(() => expect(screen.getByRole('img', { name: 'Страница PDF 1' })).toHaveStyle({ height: '584px' }));
    expect(mocks.load).toHaveBeenCalledOnce();
  });

  it('destroys the PDF document when the viewer closes', async () => {
    const view = render(<PdfFilePreview blob={blob} zoom={1} />);
    await screen.findByText('Страница 1 из 2');
    view.unmount();
    expect(mocks.destroy).toHaveBeenCalledOnce();
  });
});
