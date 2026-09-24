import React, { useState, useEffect } from 'react';
import { ShieldAlert, Zap, HelpCircle, RefreshCw, Radio, Bell, Settings, User, ShieldCheck } from 'lucide-react';
import { Regime, DashboardMode } from '../../types';
import { OperationalRegimeIndicator } from '../common/OperationalRegimeIndicator';
import { useAuth, UserRole } from '../../context/AuthContext';

interface HeaderProps {
  activeMode: DashboardMode;
  onModeChange: (mode: DashboardMode) => void;
  regime: Regime | null;
  onRegimeOverride?: (regime: string) => void;
  onOpenShortcuts: () => void;
  apiHealthy: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeMode,
  onModeChange,
  regime,
  onRegimeOverride,
  onOpenShortcuts,
  apiHealthy,
}) => {
  const [timeStr, setTimeStr] = useState<string>('');
  const { user, switchRole } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const isCrisis = regime?.current === 'crisis';

  return (
    <header
      style={{
        height: '64px',
        backgroundColor: 'var(--color-bg-secondary)',
        borderBottom: isCrisis ? '1px solid var(--color-risk-critical)' : '1px solid var(--color-border-default)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--space-6)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        boxShadow: isCrisis ? '0 2px 12px rgba(220, 38, 38, 0.25)' : 'var(--shadow-sm)',
        transition: 'border-color var(--transition-normal), box-shadow var(--transition-normal)',
      }}
      role="banner"
      aria-label="LocaPredict SLA Guard — Painel de Controle"
    >
      {/* Brand & Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'var(--shadow-glow-blue)',
            }}
          >
            <Zap size={20} color="#fff" />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <h1 style={{ fontSize: 'var(--text-base)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', letterSpacing: '-0.02em', margin: 0 }}>
                LocaPredict
              </h1>
              <span style={{ fontSize: '10px', padding: '1px 5px', borderRadius: '3px', background: 'rgba(59, 130, 246, 0.2)', color: 'var(--color-border-focus)', fontWeight: 'bold' }}>
                SLA Guard v3
              </span>
            </div>
            <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)', display: 'block', letterSpacing: '0.04em' }}>
              FUSIONOPS INTELLIGENCE PLATFORM
            </span>
          </div>
        </div>

        {/* Operational Regime Indicator Badge */}
        <OperationalRegimeIndicator regime={regime} onOverride={onRegimeOverride} />
      </div>

      {/* Center: 3 Modes Navigation Tabs */}
      <nav
        style={{
          display: 'flex',
          background: 'var(--color-bg-primary)',
          padding: '3px',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-border-default)',
        }}
        role="tablist"
        aria-label="Modos do Dashboard"
      >
        <button
          role="tab"
          aria-selected={activeMode === 'operations'}
          onClick={() => onModeChange('operations')}
          style={{
            padding: '6px 16px',
            borderRadius: 'var(--radius-md)',
            border: 'none',
            background: activeMode === 'operations' ? 'var(--color-border-focus)' : 'transparent',
            color: activeMode === 'operations' ? '#fff' : 'var(--color-text-secondary)',
            fontSize: 'var(--text-xs)',
            fontWeight: 'var(--font-weight-semibold)',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
        >
          Operações (Triagem)
        </button>

        <button
          role="tab"
          aria-selected={activeMode === 'tactical'}
          onClick={() => onModeChange('tactical')}
          style={{
            padding: '6px 16px',
            borderRadius: 'var(--radius-md)',
            border: 'none',
            background: activeMode === 'tactical' ? 'var(--color-border-focus)' : 'transparent',
            color: activeMode === 'tactical' ? '#fff' : 'var(--color-text-secondary)',
            fontSize: 'var(--text-xs)',
            fontWeight: 'var(--font-weight-semibold)',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
        >
          Gestão Tática (Forecast)
        </button>

        <button
          role="tab"
          aria-selected={activeMode === 'engineering'}
          onClick={() => onModeChange('engineering')}
          style={{
            padding: '6px 16px',
            borderRadius: 'var(--radius-md)',
            border: 'none',
            background: activeMode === 'engineering' ? 'var(--color-border-focus)' : 'transparent',
            color: activeMode === 'engineering' ? '#fff' : 'var(--color-text-secondary)',
            fontSize: 'var(--text-xs)',
            fontWeight: 'var(--font-weight-semibold)',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
        >
          Engenharia & MLOps
        </button>
      </nav>

      {/* Right Actions: Clock, Status, User Role Switcher, Help */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        {/* User Role Switcher Dropdown */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '5px 10px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-bg-elevated)',
              border: '1px solid var(--color-border-default)',
              color: 'var(--color-text-primary)',
              fontSize: '11px',
              fontWeight: 'var(--font-weight-medium)',
              cursor: 'pointer',
            }}
            title="Trocar perfil de usuário (RBAC Demo)"
          >
            <User size={13} color="var(--color-border-focus)" />
            <span>{user.role === 'admin' ? 'Admin' : user.role === 'operator' ? 'Operador' : 'Viewer'}</span>
          </button>

          {showUserMenu && (
            <div
              className="glass-modal"
              style={{
                position: 'absolute',
                top: 'calc(100% + 6px)',
                right: 0,
                width: '210px',
                padding: 'var(--space-3)',
                borderRadius: 'var(--radius-md)',
                zIndex: 1100,
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
              }}
            >
              <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: '2px' }}>
                Perfil de Acesso (RBAC):
              </span>

              {(['admin', 'operator', 'viewer'] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => {
                    switchRole(r);
                    setShowUserMenu(false);
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '6px 8px',
                    borderRadius: 'var(--radius-sm)',
                    background: user.role === r ? 'var(--color-border-focus)' : 'transparent',
                    color: user.role === r ? '#fff' : 'var(--color-text-primary)',
                    border: 'none',
                    fontSize: 'var(--text-xs)',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <span style={{ textTransform: 'capitalize' }}>
                    {r === 'admin' ? '👑 Administrador' : r === 'operator' ? '⚡ Operador NOC' : '👁️ Visualizador'}
                  </span>
                  {user.role === r && <ShieldCheck size={12} />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Live Telemetry Ping */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
          <div
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: apiHealthy ? 'var(--color-risk-low)' : 'var(--color-risk-critical)',
              boxShadow: apiHealthy ? '0 0 8px rgba(34, 197, 94, 0.6)' : '0 0 8px rgba(220, 38, 38, 0.6)',
            }}
          />
          <span style={{ fontFamily: 'var(--font-family-mono)' }}>{timeStr}</span>
        </div>

        {/* Shortcuts Help Button */}
        <button
          onClick={onOpenShortcuts}
          style={{
            padding: '6px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--color-bg-elevated)',
            border: '1px solid var(--color-border-default)',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
          }}
          title="Atalhos de teclado (?)"
          aria-label="Atalhos de teclado"
        >
          <HelpCircle size={16} />
        </button>
      </div>
    </header>
  );
};
