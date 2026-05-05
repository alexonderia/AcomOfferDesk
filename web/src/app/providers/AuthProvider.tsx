import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import type { AuthSessionResponse } from '@shared/api/auth/loginWebUser';
import { logoutWebSession, refreshWebSession } from '@shared/api/auth/loginWebUser';
import { setAuthRuntime, setAuthToken } from '@shared/api/client';

type AuthStatus = 'bootstrapping' | 'authenticated' | 'anonymous' | 'refreshing';
type RefreshReason = 'bootstrap' | 'http_401' | 'ws_4401';

const roleById: Record<number, string> = {
  1: 'superadmin',
  2: 'admin',
  3: 'contractor',
  4: 'project_manager',
  5: 'lead_economist',
  6: 'economist',
  7: 'operator'
};

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

const IDLE_WINDOW_MS = 30 * 60 * 1000;

const mapSession = (response: AuthSessionResponse): AuthSession => ({
  token: response.data.access_token,
  tokenType: response.data.token_type,
  tokenExpiresAt: response.data.access_token_expires_at,
  userId: response.data.user_id,
  login: response.data.login,
  roleId: response.data.role_id,
  role: roleById[response.data.role_id] ?? `role_${response.data.role_id}`,
  status: response.data.status,
  authProvider: response.data.auth_provider ?? 'keycloak',
  businessAccess: Boolean(response.data.business_access),
  onboardingState: response.data.onboarding_state ?? null,
  permissions: response.data.permissions ?? []
});

const buildLoginUrl = (nextPath: string, forcePrompt: boolean) => {
  const query = new URLSearchParams({ next_path: nextPath });
  if (forcePrompt) {
    query.set('force_prompt', '1');
  }
  return `/api/v1/auth/oidc/login?${query.toString()}`;
};

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [status, setStatus] = useState<AuthStatus>('bootstrapping');
  const [session, setSession] = useState<AuthSession | null>(null);
  const refreshPromiseRef = useRef<Promise<boolean> | null>(null);
  const bootstrapStartedRef = useRef(false);
  const loginRedirectStartedRef = useRef(false);
  const lastActivityAtRef = useRef<number>(Date.now());
  const sessionRef = useRef<AuthSession | null>(null);
  const statusRef = useRef<AuthStatus>('bootstrapping');

  const applySession = useCallback((nextSession: AuthSession | null, nextStatus: AuthStatus) => {
    sessionRef.current = nextSession;
    statusRef.current = nextStatus;
    setSession(nextSession);
    setStatus(nextStatus);
    setAuthToken(nextSession?.token ?? null);
  }, []);

  const trackActivity = useCallback(() => {
    lastActivityAtRef.current = Date.now();
  }, []);

  const canAttemptSilentRefresh = useCallback((reason: RefreshReason) => {
    if (reason === 'bootstrap') {
      return true;
    }
    if (refreshPromiseRef.current) {
      return true;
    }
    if (statusRef.current !== 'authenticated') {
      return false;
    }
    return Date.now() - lastActivityAtRef.current < IDLE_WINDOW_MS;
  }, []);

  const performLogout = useCallback(async (params?: { revokeRemote?: boolean; redirectToLogin?: boolean }) => {
    const revokeRemote = params?.revokeRemote ?? true;
    const redirectToLogin = params?.redirectToLogin ?? true;

    applySession(null, 'anonymous');

    if (revokeRemote) {
      try {
        await logoutWebSession();
      } catch {
        // Local logout already happened.
      }
    }

    if (redirectToLogin && location.pathname !== '/login' && location.pathname !== '/auth/login') {
      navigate('/login?logged_out=1', { replace: true });
    }
  }, [applySession, location.pathname, navigate]);

  const refresh = useCallback(async (reason: RefreshReason): Promise<boolean> => {
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    if (!canAttemptSilentRefresh(reason)) {
      return false;
    }

    refreshPromiseRef.current = (async () => {
      const previousStatus = statusRef.current;
      if (reason !== 'bootstrap' && previousStatus === 'authenticated') {
        statusRef.current = 'refreshing';
        setStatus('refreshing');
      }
      try {
        const response = await refreshWebSession();
        const nextSession = mapSession(response);
        trackActivity();
        applySession(nextSession, 'authenticated');
        return true;
      } catch {
        applySession(null, 'anonymous');
        return false;
      } finally {
        refreshPromiseRef.current = null;
        if (sessionRef.current && statusRef.current === 'refreshing') {
          setStatus('authenticated');
          statusRef.current = 'authenticated';
        } else if (!sessionRef.current && statusRef.current === 'refreshing') {
          setStatus('anonymous');
          statusRef.current = 'anonymous';
        }
      }
    })();

    return refreshPromiseRef.current;
  }, [applySession, canAttemptSilentRefresh, trackActivity]);

  const beginLogin = useCallback((nextPath?: string, options?: { forcePrompt?: boolean }) => {
    if (loginRedirectStartedRef.current) {
      return;
    }
    loginRedirectStartedRef.current = true;
    const target = nextPath ?? location.pathname ?? '/';
    window.location.assign(buildLoginUrl(target, Boolean(options?.forcePrompt)));
  }, [location.pathname]);

  const logout = useCallback(() => {
    void performLogout({ revokeRemote: true, redirectToLogin: true });
  }, [performLogout]);

  useEffect(() => {
    const handler = () => trackActivity();
    const events: Array<keyof WindowEventMap> = ['mousedown', 'mousemove', 'keydown', 'pointerdown', 'touchstart', 'focus'];
    events.forEach((eventName) => window.addEventListener(eventName, handler, { passive: true }));
    return () => {
      events.forEach((eventName) => window.removeEventListener(eventName, handler));
    };
  }, [trackActivity]);

  useEffect(() => {
    trackActivity();
  }, [location.key, trackActivity]);

  useEffect(() => {
    setAuthRuntime({
      refresh,
      canAttemptSilentRefresh,
      forceLogout: () => {
        void performLogout({ revokeRemote: false, redirectToLogin: true });
      }
    });
    return () => {
      setAuthRuntime(null);
    };
  }, [canAttemptSilentRefresh, performLogout, refresh]);

  useEffect(() => {
    if (bootstrapStartedRef.current) {
      return;
    }
    bootstrapStartedRef.current = true;
    void refresh('bootstrap').then((restored: boolean) => {
      if (!restored) {
        applySession(null, 'anonymous');
      }
    });
  }, [applySession, refresh]);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      session,
      isAuthenticated: (status === 'authenticated' || status === 'refreshing') && Boolean(session?.token),
      beginLogin,
      refresh,
      logout
    }),
    [beginLogin, logout, refresh, session, status]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
