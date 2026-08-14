import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { setAuthRuntime } from '@shared/api/client';
import {
  getWebSession,
  issueCsrfToken,
  logoutIamBrowserSession,
  logoutWebSession,
  refreshWebSession,
  type AuthSessionResponse,
} from '@shared/api/auth/loginWebUser';

type AuthStatus = 'unauthenticated' | 'authenticating' | 'authenticated' | 'unavailable';
type RefreshReason = 'bootstrap' | 'http_401' | 'ws_4401';

export type AuthSession = {
  userId: string;
  login: string;
  roleId: number;
  role: string;
  status: string;
  authProvider: string;
  businessAccess: boolean;
  onboardingState: string | null;
  permissions: string[];
};

type AuthContextValue = {
  status: AuthStatus;
  session: AuthSession | null;
  isAuthenticated: boolean;
  beginLogin: (nextPath?: string, options?: { forcePrompt?: boolean }) => void;
  refresh: (reason: RefreshReason) => Promise<boolean>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const mapSession = (response: AuthSessionResponse): AuthSession => ({
  userId: response.data.user_id,
  login: response.data.login,
  roleId: response.data.role_id,
  role: response.data.role,
  status: response.data.status,
  authProvider: response.data.auth_provider ?? 'iam',
  businessAccess: response.data.business_access ?? false,
  onboardingState: response.data.onboarding_state ?? null,
  permissions: response.data.permissions ?? [],
});

const isUnavailableError = (error: unknown): boolean => {
  const message = error instanceof Error ? error.message.toLowerCase() : '';
  return message.includes('недоступ') || message.includes('сеть') || message.includes('соединен');
};

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [status, setStatus] = useState<AuthStatus>('authenticating');
  const [session, setSession] = useState<AuthSession | null>(null);

  const refresh = useCallback(async (_reason: RefreshReason): Promise<boolean> => {
    try {
      await issueCsrfToken();
      const restored = mapSession(await refreshWebSession());
      setSession(restored);
      setStatus('authenticated');
      return true;
    } catch (error) {
      setSession(null);
      setStatus(isUnavailableError(error) ? 'unavailable' : 'unauthenticated');
      return false;
    }
  }, []);

  const beginLogin = useCallback((nextPath = '/', _options?: { forcePrompt?: boolean }) => {
    const safeNext = nextPath.startsWith('/') && !nextPath.startsWith('//') ? nextPath : '/';
    window.location.assign(`/api/v1/auth/login?next=${encodeURIComponent(safeNext)}`);
  }, []);

  const logout = useCallback(() => {
    void (async () => {
      try {
        await issueCsrfToken();
        await logoutWebSession();
      } finally {
        try {
          await logoutIamBrowserSession();
        } catch {
          // Local BFF cookies are already cleared; the next login will not reuse a stale app session.
        }
        setSession(null);
        setStatus('unauthenticated');
        window.location.assign('/login');
      }
    })();
  }, []);

  useEffect(() => {
    let cancelled = false;
    const bootstrap = async () => {
      setStatus('authenticating');
      try {
        await issueCsrfToken();
        const restored = mapSession(await getWebSession());
        if (!cancelled) {
          setSession(restored);
          setStatus('authenticated');
        }
      } catch {
        if (!cancelled) {
          await refresh('bootstrap');
        }
      }
    };
    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  useEffect(() => {
    setAuthRuntime({
      refresh,
      canAttemptSilentRefresh: () => status === 'authenticated',
      forceLogout: logout,
    });
    return () => setAuthRuntime(null);
  }, [logout, refresh, status]);

  const value = useMemo<AuthContextValue>(() => ({
    status,
    session,
    isAuthenticated: status === 'authenticated' && session !== null,
    beginLogin,
    refresh,
    logout,
  }), [beginLogin, logout, refresh, session, status]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
