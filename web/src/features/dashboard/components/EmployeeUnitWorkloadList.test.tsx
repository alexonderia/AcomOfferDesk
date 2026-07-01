import type { ReactElement } from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { describe, expect, it, vi } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { appTheme } from '@shared/theme/appTheme';
import { EmployeeUnitWorkloadList } from './EmployeeUnitWorkloadList';

vi.mock('./EmployeeNodeCard', () => ({
  EmployeeNodeCard: function MockEmployeeNodeCard(
    {
      level,
      node,
    }: {
      level: number;
      node: { user_id: string };
    },
  ) {
    return <div>{`employee:${node.user_id}:level:${level}`}</div>;
  },
}));

const renderView = (ui: ReactElement) => render(
  <ThemeProvider theme={appTheme}>
    {ui}
  </ThemeProvider>
);

describe('EmployeeUnitWorkloadList', () => {
  it('renders one user tree following unit nesting when employee parent links are missing', () => {
    renderView(
      <EmployeeUnitWorkloadList
        activeUnavailabilityByUser={{}}
        employeeTree={[
          {
            user_id: 'lead',
            full_name: 'Lead',
            role_id: ROLE.PROJECT_MANAGER,
            role_name: 'Руководитель проекта',
            parent_user_id: null,
            in_progress_total: 1,
            statuses: [],
            children: [
              {
                user_id: 'econ',
                full_name: 'Senior',
                role_id: ROLE.LEAD_ECONOMIST,
                role_name: 'Ведущий экономист',
                parent_user_id: null,
                in_progress_total: 1,
                statuses: [],
                children: [
                  {
                    user_id: 'staff',
                    full_name: 'Staff',
                    role_id: ROLE.ECONOMIST,
                    role_name: 'Экономист',
                    parent_user_id: null,
                    in_progress_total: 1,
                    statuses: [],
                    children: [],
                  },
                ],
              },
            ],
          },
        ]}
        expanded={{ lead: true, econ: true }}
        onToggle={() => undefined}
        statusColors={{}}
        units={[
          {
            unit_id: 1,
            name: 'АО',
            id_parent: null,
            is_active: true,
            members: [
              {
                user_id: 'lead',
                full_name: 'Lead',
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
                    full_name: 'Senior',
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
                        full_name: 'Staff',
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
        upcomingUnavailabilityByUser={{}}
      />
    );

    expect(screen.queryByText('Подразделение')).not.toBeInTheDocument();
    expect(screen.queryByText('АО')).not.toBeInTheDocument();
    expect(screen.queryByText('Объединение')).not.toBeInTheDocument();
    expect(screen.queryByText('Модуль 1')).not.toBeInTheDocument();
    expect(screen.getByText('employee:lead:level:0')).toBeInTheDocument();
    expect(screen.getByText('employee:econ:level:1')).toBeInTheDocument();
    expect(screen.getByText('employee:staff:level:2')).toBeInTheDocument();
  });

  it('does not treat staff from other departments as orphans when the visible unit list is filtered', () => {
    renderView(
      <EmployeeUnitWorkloadList
        activeUnavailabilityByUser={{}}
        allUnits={[
          {
            unit_id: 1,
            name: 'АО 1',
            id_parent: null,
            is_active: true,
            members: [
              {
                user_id: 'lead-a',
                full_name: 'Lead A',
                role_id: ROLE.PROJECT_MANAGER,
                role_name: 'Руководитель проекта',
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
          {
            unit_id: 2,
            name: 'АО 2',
            id_parent: null,
            is_active: true,
            members: [
              {
                user_id: 'lead-b',
                full_name: 'Lead B',
                role_id: ROLE.PROJECT_MANAGER,
                role_name: 'Руководитель проекта',
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
        ]}
        employeeTree={[
          {
            user_id: 'lead-a',
            full_name: 'Lead A',
            role_id: ROLE.PROJECT_MANAGER,
            role_name: 'Руководитель проекта',
            parent_user_id: null,
            in_progress_total: 1,
            statuses: [],
            children: [],
          },
          {
            user_id: 'lead-b',
            full_name: 'Lead B',
            role_id: ROLE.PROJECT_MANAGER,
            role_name: 'Руководитель проекта',
            parent_user_id: null,
            in_progress_total: 1,
            statuses: [],
            children: [],
          },
        ]}
        expanded={{}}
        onToggle={() => undefined}
        showOrphans={false}
        statusColors={{}}
        units={[
          {
            unit_id: 1,
            name: 'АО 1',
            id_parent: null,
            is_active: true,
            members: [
              {
                user_id: 'lead-a',
                full_name: 'Lead A',
                role_id: ROLE.PROJECT_MANAGER,
                role_name: 'Руководитель проекта',
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
        ]}
        upcomingUnavailabilityByUser={{}}
      />
    );

    expect(screen.getByText('employee:lead-a:level:0')).toBeInTheDocument();
    expect(screen.queryByText('employee:lead-b:level:0')).not.toBeInTheDocument();
  });

  it('does not duplicate a department member when the same user exists in a child unit', () => {
    renderView(
      <EmployeeUnitWorkloadList
        activeUnavailabilityByUser={{}}
        employeeTree={[
          {
            user_id: 'lead',
            full_name: 'Lead',
            role_id: ROLE.PROJECT_MANAGER,
            role_name: 'Руководитель проекта',
            parent_user_id: null,
            in_progress_total: 1,
            statuses: [],
            children: [
              {
                user_id: 'shared',
                full_name: 'Shared',
                role_id: ROLE.LEAD_ECONOMIST,
                role_name: 'Ведущий экономист',
                parent_user_id: null,
                in_progress_total: 1,
                statuses: [],
                children: [],
              },
            ],
          },
        ]}
        expanded={{ lead: true }}
        onToggle={() => undefined}
        statusColors={{}}
        units={[
          {
            unit_id: 1,
            name: 'АО',
            id_parent: null,
            is_active: true,
            members: [
              {
                user_id: 'lead',
                full_name: 'Lead',
                role_id: ROLE.PROJECT_MANAGER,
                role_name: 'Руководитель проекта',
                status: 'active',
                id_parent_user: null,
              },
              {
                user_id: 'shared',
                full_name: 'Shared',
                role_id: ROLE.LEAD_ECONOMIST,
                role_name: 'Ведущий экономист',
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
                    user_id: 'shared',
                    full_name: 'Shared',
                    role_id: ROLE.LEAD_ECONOMIST,
                    role_name: 'Ведущий экономист',
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
        ]}
        upcomingUnavailabilityByUser={{}}
      />
    );

    expect(screen.getByText('employee:lead:level:0')).toBeInTheDocument();
    expect(screen.getAllByText('employee:shared:level:1')).toHaveLength(1);
  });
});
