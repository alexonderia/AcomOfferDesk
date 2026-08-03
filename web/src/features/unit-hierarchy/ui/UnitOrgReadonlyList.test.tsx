import type { ReactElement } from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { describe, expect, it } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { appTheme } from '@shared/theme/appTheme';
import { UnitOrgReadonlyList } from './UnitOrgReadonlyList';

const renderView = (ui: ReactElement) => render(
  <ThemeProvider theme={appTheme}>
    {ui}
  </ThemeProvider>
);

describe('UnitOrgReadonlyList', () => {
  it('shows the user hierarchy using unit nesting when child members have no parent links', () => {
    renderView(
      <UnitOrgReadonlyList
        units={[
          {
            unit_id: 1,
            name: 'АО',
            id_parent: null,
            is_active: true,
            members: [
              {
                user_id: 'lead',
                full_name: 'Руководитель',
                role_id: ROLE.PROJECT_MANAGER,
                role_name: 'Руководитель проекта',
                status: 'active',
                id_parent_user: null,
              },
            ],
            children: [
              {
                unit_id: 2,
                name: 'Модуль 1',
                id_parent: 1,
                is_active: true,
                members: [
                  {
                    user_id: 'econ',
                    full_name: 'Ведущий',
                    role_id: ROLE.LEAD_ECONOMIST,
                    role_name: 'Ведущий экономист',
                    status: 'active',
                    id_parent_user: null,
                  },
                ],
                children: [
                  {
                    unit_id: 3,
                    name: 'Модуль 1.1',
                    id_parent: 2,
                    is_active: true,
                    members: [
                      {
                        user_id: 'staff',
                        full_name: 'Экономист',
                        role_id: ROLE.ECONOMIST,
                        role_name: 'Экономист',
                        status: 'active',
                        id_parent_user: null,
                      },
                    ],
                    children: [],
                    actions: {
                      canCreateChild: false,
                      canUpdate: false,
                      canDelete: false,
                      canManageMembers: false,
                    },
                  },
                ],
                actions: {
                  canCreateChild: false,
                  canUpdate: false,
                  canDelete: false,
                  canManageMembers: false,
                },
              },
            ],
            actions: {
              canCreateChild: false,
              canUpdate: false,
              canDelete: false,
              canManageMembers: false,
            },
          },
        ]}
      />
    );

    expect(screen.queryByText('Подразделение')).not.toBeInTheDocument();
    expect(screen.queryByText('АО')).not.toBeInTheDocument();
    expect(screen.queryByText('Объединение')).not.toBeInTheDocument();
    expect(screen.queryByText('Модуль 1')).not.toBeInTheDocument();
    expect(screen.getByText('Руководитель')).toBeInTheDocument();
    expect(screen.getByText('Ведущий')).toBeInTheDocument();
    expect(screen.getAllByText('Экономист').length).toBeGreaterThan(0);
  });
});
