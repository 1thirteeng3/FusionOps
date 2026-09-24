import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../services/api';

export type UserRole = 'admin' | 'operator' | 'viewer';

export interface UserProfile {
  username: string;
  role: UserRole;
  name: string;
}

interface AuthContextType {
  user: UserProfile;
  token: string | null;
  switchRole: (role: UserRole) => Promise<void>;
  hasPermission: (action: 'retrain' | 'assign' | 'escalate' | 'export' | 'override_regime') => boolean;
  logout: () => void;
}

const defaultUser: UserProfile = {
  username: 'demo-admin',
  role: 'admin',
  name: 'Administrador AIOps (LocaPredict)',
};

const AuthContext = createContext<AuthContextType>({
  user: defaultUser,
  token: null,
  switchRole: async () => {},
  hasPermission: () => true,
  logout: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile>(() => {
    const saved = localStorage.getItem('locapredict_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return defaultUser;
      }
    }
    return defaultUser;
  });

  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('locapredict_token') || null;
  });

  // Switch role via demo-token endpoint (DEV-ONLY convenience; the backend
  // returns 404 for it in production, and server-side RBAC always enforces).
  const switchRole = async (newRole: UserRole) => {
    try {
      const res = await apiService.getDemoToken(newRole);
      setToken(res.access_token);
      setUser(res.user as UserProfile);
      localStorage.setItem('locapredict_token', res.access_token);
      localStorage.setItem('locapredict_user', JSON.stringify(res.user));
    } catch (e) {
      console.error('Failed to switch demo role:', e);
      // Fail closed: clear any stale token so no authenticated action proceeds.
      setToken(null);
      localStorage.removeItem('locapredict_token');
      // Fallback local state
      const fallbackUser: UserProfile = {
        username: `demo-${newRole}`,
        role: newRole,
        name: newRole === 'admin' ? 'Administrador AIOps' : (newRole === 'operator' ? 'Operador NOC / ITSM' : 'Visualizador / Auditor'),
      };
      setUser(fallbackUser);
      localStorage.setItem('locapredict_user', JSON.stringify(fallbackUser));
    }
  };

  const hasPermission = (action: 'retrain' | 'assign' | 'escalate' | 'export' | 'override_regime'): boolean => {
    if (user.role === 'admin') return true;
    if (user.role === 'operator') {
      return action !== 'retrain';
    }
    if (user.role === 'viewer') {
      return false; // read-only
    }
    return false;
  };

  const logout = () => {
    localStorage.removeItem('locapredict_token');
    localStorage.removeItem('locapredict_user');
    setUser({ username: 'guest', role: 'viewer', name: 'Visitante' });
    setToken(null);
  };

  useEffect(() => {
    // Acquire initial demo token if none exists
    if (!token) {
      switchRole(user.role);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, switchRole, hasPermission, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
