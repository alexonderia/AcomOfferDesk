import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { UnitNode } from '@shared/api/units';
import type { UserHierarchy } from '@shared/api/users/getUserHierarchy';
import { appTheme } from '@shared/theme/appTheme';
import { UserHierarchyTree } from './UserHierarchyTree';

const baseHierarchy: UserHierarchy = {
  user: {
    userId: 'lead-1',
    fullName: 'Краснов Игорь Алексеевич',
    roleId: 4,
    roleName: 'Руководитель проекта',
    status: 'active',
  },
  units: [
    {
      unitId: 1,
      name: 'УЭ',
      parentUnitId: null,
    },
  ],
  managers: [],
  subordinates: [
    {
      userId: 'vacancy-1',
      fullName: 'Вакансия',
      roleId: 6,
      roleName: 'Экономист',
      status: 'active',
      sourceUnitId: 1,
      sourceUnitName: 'УЭ',
    },
  ],
  legacyHierarchy: {
    legacyManager: null,
    legacySubordinates: [],
    isBusinessSource: false,
    note: '',
  },
};

const unitsTree: UnitNode[] = [
  {
    unit_id: 1,
    name: 'УЭ',
    id_parent: null,
    is_active: true,
    members: [
      {
        user_id: 'lead-1',
        full_name: 'Краснов Игорь Алексеевич',
        role_id: 4,
        role_name: 'Руководитель проекта',
        status: 'active',
        id_parent_user: null,
      },
    ],
    children: [
      {
        unit_id: 2,
        name: 'Модуль 1.1',
        id_parent: 1,
        is_active: true,
        members: [
          {
            user_id: 'vacancy-1',
            full_name: 'Вакансия',
            role_id: 6,
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
];

describe('UserHierarchyTree', () => {
  it('does not render the self badge text in the user card', () => {
    render(
      <ThemeProvider theme={appTheme}>
        <UserHierarchyTree hierarchy={baseHierarchy} unitsTree={unitsTree} />
      </ThemeProvider>,
    );

    expect(screen.getByText('Вакансия')).toBeInTheDocument();
    expect(screen.queryByText(/^Вы$/)).not.toBeInTheDocument();
  });

  it('shows the relation tooltip on hover for subordinates', async () => {
    const hierarchy: UserHierarchy = {
      ...baseHierarchy,
      user: {
        userId: 'lead-1',
        fullName: 'Краснов Игорь Алексеевич',
        roleId: 4,
        roleName: 'Руководитель проекта',
        status: 'active',
      },
      subordinates: [
        {
          userId: 'vacancy-1',
          fullName: 'Вакансия',
          roleId: 6,
          roleName: 'Экономист',
          status: 'active',
          sourceUnitId: 2,
          sourceUnitName: 'Модуль 1.1.1',
        },
      ],
    };

    const hierarchyUnits: UnitNode[] = [
      {
        unit_id: 1,
        name: 'УЭ',
        id_parent: null,
        is_active: true,
        members: [],
        children: [
          {
            unit_id: 2,
            name: 'Модуль 1.1',
            id_parent: 1,
            is_active: true,
            members: [
              {
                user_id: 'lead-1',
                full_name: 'Краснов Игорь Алексеевич',
                role_id: 4,
                role_name: 'Руководитель проекта',
                status: 'active',
                id_parent_user: null,
              },
            ],
            children: [
              {
                unit_id: 3,
                name: 'Модуль 1.1.1',
                id_parent: 2,
                is_active: true,
                members: [
                  {
                    user_id: 'vacancy-1',
                    full_name: 'Вакансия',
                    role_id: 6,
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
    ];

    render(
      <ThemeProvider theme={appTheme}>
        <UserHierarchyTree hierarchy={hierarchy} unitsTree={hierarchyUnits} />
      </ThemeProvider>,
    );

    fireEvent.mouseOver(screen.getByText('Вакансия'));

    expect(await screen.findByText('Подчинённый выбранного сотрудника')).toBeInTheDocument();
  });

  it('shows relation tooltips for manager and selected employee', async () => {
    const hierarchy: UserHierarchy = {
      user: {
        userId: 'pp',
        fullName: 'ппп ппп рр',
        roleId: 6,
        roleName: 'Экономист',
        status: 'active',
      },
      units: [],
      managers: [],
      subordinates: [],
      legacyHierarchy: {
        legacyManager: null,
        legacySubordinates: [],
        isBusinessSource: false,
        note: '',
      },
    };

    const hierarchyUnits: UnitNode[] = [
      {
        unit_id: 1,
        name: 'УЭ',
        id_parent: null,
        is_active: true,
        members: [],
        children: [
          {
            unit_id: 2,
            name: 'Модуль 1',
            id_parent: 1,
            is_active: true,
            members: [
              {
                user_id: 'lead-1',
                full_name: 'Краснов Игорь Алексеевич',
                role_id: 4,
                role_name: 'Руководитель проекта',
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
                    user_id: 'pp',
                    full_name: 'ппп ппп рр',
                    role_id: 6,
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
    ];

    render(
      <ThemeProvider theme={appTheme}>
        <UserHierarchyTree hierarchy={hierarchy} unitsTree={hierarchyUnits} />
      </ThemeProvider>,
    );

    fireEvent.mouseOver(screen.getByText('Краснов Игорь Алексеевич'));
    expect(await screen.findByText('Руководитель выбранного сотрудника')).toBeInTheDocument();

    fireEvent.mouseOver(screen.getByText('ппп ппп рр'));
    expect(await screen.findByText('Выбранный сотрудник')).toBeInTheDocument();
  });
});
