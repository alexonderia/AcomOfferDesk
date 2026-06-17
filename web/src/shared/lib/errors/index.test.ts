import { describe, expect, it } from 'vitest';

import { formatSettledTaskErrors, joinUserFacingErrors } from './index';

describe('formatSettledTaskErrors', () => {
  it('collects all rejected task messages with labels', () => {
    const results: PromiseSettledResult<unknown>[] = [
      { status: 'rejected', reason: new Error('Файл пустой.') },
      { status: 'fulfilled', value: null },
      { status: 'rejected', reason: new Error('PDF-файл поврежден или не читается.') },
    ];

    expect(
      formatSettledTaskErrors(
        results,
        ['02_empty_file.pdf', '12_valid_pdf_should_pass.pdf', '03_broken_pdf.pdf'],
        'Не удалось загрузить файл',
      ),
    ).toEqual([
      '02_empty_file.pdf: Файл пустой.',
      '03_broken_pdf.pdf: PDF-файл поврежден или не читается.',
    ]);
  });

  it('joins collected errors into a multiline message', () => {
    const joined = joinUserFacingErrors([
      '02_empty_file.pdf: Файл пустой.',
      '03_broken_pdf.pdf: PDF-файл поврежден или не читается.',
    ]);

    expect(joined).toBe(
      '02_empty_file.pdf: Файл пустой.\n03_broken_pdf.pdf: PDF-файл поврежден или не читается.',
    );
  });
});
