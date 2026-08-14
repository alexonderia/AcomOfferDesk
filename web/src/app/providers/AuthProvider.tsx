import { createContext, useCallback, useContext, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { setAuthRuntime, setAuthToken } from '@shared/api/client';

type AuthStatus = 'unavailable';
type RefreshReason = 'bootstrap' | 'http_401' | 'ws_4401';

export type AuthSession = {
  token: string;
  tokenType: string;
  tokenExpiresAt: number;
  userId: string;
  login: string;
  roleId: number;
  role: string;
  status: string;
  authProvider: string;
  businessAccess: boolean;
  onboardingState: string | null;
  permissions: string[];
  appRoles: string[];
  delegationRoles: string[];
};

type AuthContextValue = {
  status: AuthStatus;
  session: AuthSession | null;
  isAuthenticated: false;
  beginLogin: (nextPath?: string, options?: { forcePrompt?: boolean }) => void;
  refresh: (reason: RefreshReason) => Promise<boolean>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const navigate = useNavigate();

  const refresh = useCallback(async (_reason: RefreshReason): Promise<boolean> => false, []);
  const beginLogin = useCallback((_nextPath?: string, _options?: { forcePrompt?: boolean }) => {
    navigate('/login', { replace: true });
  }, [navigate]);
  const logout = useCallback(() => {
    navigate('/login', { replace: true });
  }, [navigate]);

  useEffect(() => {
    setAuthToken(null);
    setAuthRuntime({
      refresh,
      canAttemptSilentRefresh: () => false,
      forceLogout: logout
    });
    return () => setAuthRuntime(null);
  }, [logout, refresh]);

  const value = useMemo<AuthContextValue>(() => ({
    status: 'unavailable',
    session: null,
    isAuthenticated: false,
    beginLogin,
    refresh,
    logout
  }), [beginLogin, logout, refresh]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
