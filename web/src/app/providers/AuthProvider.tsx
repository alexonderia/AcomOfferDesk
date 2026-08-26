import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { setAuthRuntime, type AuthRefreshResult } from '@shared/api/client';
import {
  clearIamBrowserSession,
  getWebSession,
  issueCsrfToken,
  logoutWebSession,
  refreshWebSession,
  type AuthSessionResponse,
} from '@shared/api/auth/loginWebUser';

type AuthStatus = 'unauthenticated' | 'authenticating' | 'authenticated' | 'unavailable';
type RefreshReason = 'bootstrap' | 'http_401' | 'ws_4401';
const PERMISSION_REFRESH_INTERVAL_MS = 60_000;

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
  refresh: (reason: RefreshReason) => Promise<AuthRefreshResult>;
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

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [status, setStatus] = useState<AuthStatus>('authenticating');
  const [session, setSession] = useState<AuthSession | null>(null);
  const refreshPromiseRef = useRef<Promise<AuthRefreshResult> | null>(null);
  const logoutPromiseRef = useRef<Promise<void> | null>(null);

  const refresh = useCallback((_reason: RefreshReason): Promise<AuthRefreshResult> => {
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    const task = (async (): Promise<AuthRefreshResult> => {
      try {
        await issueCsrfToken();
        const result = await refreshWebSession();
        if (result.kind === 'success') {
          setSession(mapSession(result.session));
          setStatus('authenticated');
          return { kind: 'success' };
        }
        if (result.kind === 'terminal') {
          setSession(null);
          setStatus('unauthenticated');
          return result;
        }
        setStatus('unavailable');
        return result;
      } catch {
        setStatus('unavailable');
        return { kind: 'unavailable' };
      }
    })();

    refreshPromiseRef.current = task;
    void task.finally(() => {
      if (refreshPromiseRef.current === task) {
        refreshPromiseRef.current = null;
      }
    });
    return task;
  }, []);

  const beginLogin = useCallback((nextPath = '/', _options?: { forcePrompt?: boolean }) => {
    const safeNext = nextPath.startsWith('/') && !nextPath.startsWith('//') ? nextPath : '/';
    window.location.assign(`/api/v1/auth/login?next=${encodeURIComponent(safeNext)}`);
  }, []);

  const logout = useCallback(() => {
    if (logoutPromiseRef.current) {
      return;
    }
    setSession(null);
    setStatus('unauthenticated');
    const task = (async () => {
      try {
        await issueCsrfToken();
        await logoutWebSession();
      } finally {
        try {
          await clearIamBrowserSession();
        } catch {
          // The primary BFF logout has already run; always continue to login.
        }
        window.location.assign('/login');
      }
    })();
    logoutPromiseRef.current = task;
    void task.finally(() => {
      if (logoutPromiseRef.current === task) {
        logoutPromiseRef.current = null;
      }
    });
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
    if (status !== 'authenticated') {
      return undefined;
    }
    const intervalId = window.setInterval(() => {
      void refresh('bootstrap');
    }, PERMISSION_REFRESH_INTERVAL_MS);
    return () => window.clearInterval(intervalId);
  }, [refresh, status]);

  useEffect(() => {
    setAuthRuntime({
      refresh,
      canAttemptSilentRefresh: () => status === 'authenticated' && !logoutPromiseRef.current,
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
