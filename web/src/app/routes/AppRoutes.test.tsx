import { render, screen } from '@testing-library/react';
import { MemoryRouter, Outlet, useLocation } from 'react-router-dom';
import type { Location } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AppRoutes } from './AppRoutes';

vi.mock('@app/layouts/AppLayout', () => ({ AppLayout: () => <Outlet /> }));
vi.mock('@app/routes/ProtectedRoute', () => ({ ProtectedRoute: () => <Outlet /> }));
vi.mock('@app/routes/RoleRoute', () => ({ RoleRoute: ({ children }: { children: React.ReactNode }) => children }));
vi.mock('@pages/admin-hierarchy/AdminHierarchyPage', () => ({ AdminHierarchyPage: () => <div>Иерархия</div> }));
vi.mock('@pages/requests/RequestsPage', () => ({ RequestsPage: () => <div>Заявки</div> }));
vi.mock('@pages/requests/CreateRequestPage', () => ({ CreateRequestPage: () => <div>Создание заявки</div> }));

const background: Location = { pathname: '/admin/hierarchy', search: '', hash: '', state: null, key: 'hierarchy' };
const TestRoutes = () => {
  const location = useLocation();
  return <AppRoutes defaultPath="/requests" hasSession location={location} backgroundLocation={background} />;
};

describe('route content and modal background', () => {
  it('renders the selected section despite a stale modal background', async () => {
    render(<MemoryRouter initialEntries={['/requests']}><TestRoutes /></MemoryRouter>);
    expect(await screen.findByText('Заявки')).toBeInTheDocument();
    expect(screen.queryByText('Иерархия')).not.toBeInTheDocument();
  });

  it('keeps the background visible for the request creation dialog', async () => {
    render(<MemoryRouter initialEntries={['/requests/create']}><TestRoutes /></MemoryRouter>);
    expect(await screen.findByText('Иерархия')).toBeInTheDocument();
    expect(await screen.findByText('Создание заявки')).toBeInTheDocument();
  });
});
