import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AuthPageShell } from '@shared/components/AuthPageShell';

describe('AuthPageShell', () => {
  it('renders the branded footer with Bitrix and MAX links', () => {
    render(
      <AuthPageShell title="Подтверждение email">
        <p>Проверьте почту</p>
      </AuthPageShell>,
    );

    expect(screen.getByRole('heading', { name: 'Подтверждение email' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Перейти в Битрикс' })).toHaveAttribute(
      'href',
      'https://team.alabuga.ru/company/structure.php?set_filter_structure=Y&structure_UF_DEPARTMENT=8304&filter=Y&set_filter=Y',
    );
    expect(screen.getByRole('link', { name: 'Открыть MAX' })).toHaveAttribute(
      'href',
      'https://max.ru/u/f9LHodD0cOIA4s2RhH3dW5NoCLRn88NF67UYfQe_rOnnM6Y1a7VW_vOUt5I',
    );
    expect(screen.getByText(/Created by/)).toBeInTheDocument();
    expect(screen.queryByText('Безопасный вход')).not.toBeInTheDocument();
  });
});
