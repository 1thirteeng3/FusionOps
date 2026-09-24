import React, { useState, useRef, useEffect } from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2, TrendingUp, TrendingDown, Minus, RefreshCw, X } from 'lucide-react';
import { Regime } from '../../types';
import { useAuth } from '../../context/AuthContext';

interface OperationalRegimeProps {
  regime: Regime | null;
  onOverride?: (regime: string) => void;
  size?: 'inline' | 'detailed' | 'alert';
}

export const OperationalRegimeIndicator: React.FC<OperationalRegimeProps> = ({
  regime,
  onOverride,
  size = 'inline',
}) => {
  const [showPopover, setShowPopover] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);
  const { hasPermission } = useAuth();
  const canOverride = hasPermission('override_regime');

  // Close popover when clicking outside
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setShowPopover(false);
      }
    };
    if (showPopover) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [showPopover]);

  if (!regime) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)' }}>
        <RefreshCw className="animate-spin" size={16} />
        <span>Carregando regime...</span>
      </div>
    );
  }

  const regimeConfig = {
    normal: {
      color: 'var(--color-regime-normal)',
      bg: 'rgba(22, 163, 74, 0.15)',
      border: 'rgba(22, 163, 74, 0.35)',
      label: 'NORMAL',
      icon: <CheckCircle2 size={16} color="var(--color-regime-normal)" />,
    },
    stress: {
      color: 'var(--color-regime-stress)',
      bg: 'rgba(202, 138, 4, 0.15)',
      border: 'rgba(202, 138, 4, 0.4)',
      label: 'ESTRESSE',
      icon: <AlertTriangle size={16} color="var(--color-regime-stress)" />,
    },
    saturation: {
      color: 'var(--color-regime-saturation)',
      bg: 'rgba(234, 88, 12, 0.15)',
      border: 'rgba(234, 88, 12, 0.4)',
      label: 'SATURAÇÃO',
      icon: <AlertTriangle size={16} color="var(--color-regime-saturation)" />,
    },
    crisis: {
      color: 'var(--color-regime-crisis)',
      bg: 'rgba(220, 38, 38, 0.2)',
      border: 'rgba(220, 38, 38, 0.5)',
      label: 'CRISE',
      icon: <ShieldAlert size={16} color="var(--color-regime-crisis)" />,
    },
    recovery: {
      color: 'var(--color-regime-recovery)',
      bg: 'rgba(37, 99, 235, 0.15)',
      border: 'rgba(37, 99, 235, 0.4)',
      label: 'RECUPERAÇÃO',
      icon: <TrendingUp size={16} color="var(--color-regime-recovery)" />,
    },
  };

  const currentConfig = regimeConfig[regime.current] || regimeConfig.normal;
  const isCrisis = regime.current === 'crisis';

  const renderTrendIcon = () => {
    if (regime.trend === 'worsening') return <span title="Tendência: Piorando"><TrendingUp size={14} color="var(--color-risk-critical)" /></span>;
    if (regime.trend === 'improving') return <span title="Tendência: Melhorando"><TrendingDown size={14} color="var(--color-risk-low)" /></span>;
    return <span title="Tendência: Estável"><Minus size={14} color="var(--color-text-secondary)" /></span>;
  };

  return (
    <div style={{ position: 'relative' }} ref={popoverRef}>
      <button
        onClick={() => setShowPopover(!showPopover)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 12px',
          borderRadius: 'var(--radius-full)',
          backgroundColor: currentConfig.bg,
          border: `1px solid ${currentConfig.border}`,
          color: currentConfig.color,
          fontSize: 'var(--text-xs)',
          fontWeight: 'var(--font-weight-bold)',
          cursor: 'pointer',
          transition: 'all var(--transition-fast)',
          animation: isCrisis ? 'pulseRisk 2s infinite ease-in-out' : 'none',
          boxShadow: isCrisis ? 'var(--shadow-glow-crisis)' : 'none',
        }}
        aria-expanded={showPopover}
        aria-haspopup="dialog"
        aria-label={`Regime Operacional: ${currentConfig.label}. Confiança: ${Math.round(regime.confidence * 100)}%`}
      >
        {currentConfig.icon}
        <span style={{ letterSpacing: '0.04em' }}>{currentConfig.label}</span>
        <span style={{ color: 'var(--color-text-secondary)', fontWeight: 'var(--font-weight-normal)' }}>
          {Math.round(regime.confidence * 100)}%
        </span>
        {renderTrendIcon()}
      </button>

      {/* Detailed Regime Popover */}
      {showPopover && (
        <div
          className="glass-modal"
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            right: 0,
            width: '340px',
            padding: 'var(--space-4)',
            borderRadius: 'var(--radius-lg)',
            zIndex: 1000,
            animation: 'scaleIn 200ms ease-out',
          }}
          role="dialog"
          aria-label="Detalhes do Regime Operacional"
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {currentConfig.icon}
              <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
                Regime Operacional: {currentConfig.label}
              </h4>
            </div>
            <button
              onClick={() => setShowPopover(false)}
              style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}
              aria-label="Fechar popover"
            >
              <X size={16} />
            </button>
          </div>

          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-3)', lineHeight: '1.4' }}>
            {regime.description || 'Detecção de telemetria operacional em tempo real baseada em fila, prioridade e OLA.'}
          </p>

          <div style={{ background: 'var(--color-bg-primary)', padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-3)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', marginBottom: '4px' }}>
              <span style={{ color: 'var(--color-text-muted)' }}>Confiança do Modelo:</span>
              <span style={{ color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-semibold)' }}>{Math.round(regime.confidence * 100)}%</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', marginBottom: '4px' }}>
              <span style={{ color: 'var(--color-text-muted)' }}>Última Transição:</span>
              <span style={{ color: 'var(--color-text-primary)' }}>há {regime.changed_at}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)' }}>
              <span style={{ color: 'var(--color-text-muted)' }}>Tendência Operacional:</span>
              <span style={{ color: currentConfig.color, fontWeight: 'var(--font-weight-medium)', textTransform: 'capitalize' }}>
                {regime.trend === 'worsening' ? 'Piorando (Demanda Alta)' : (regime.trend === 'improving' ? 'Melhorando (Fila Baixando)' : 'Estável')}
              </span>
            </div>
          </div>

          {regime.active_triggers && regime.active_triggers.length > 0 && (
            <div style={{ marginBottom: 'var(--space-3)' }}>
              <span style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-secondary)' }}>
                Gatilhos Ativos:
              </span>
              <ul style={{ listStyle: 'disc', paddingLeft: '16px', marginTop: '4px', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
                {regime.active_triggers.map((t, idx) => (
                  <li key={idx} style={{ marginBottom: '2px' }}>{t}</li>
                ))}
              </ul>
            </div>
          )}

          {onOverride && canOverride && (
            <div style={{ borderTop: '1px solid var(--color-border-default)', paddingTop: 'var(--space-3)' }}>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', display: 'block', marginBottom: '6px' }}>
                Simular Regime Operacional:
              </span>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {(['normal', 'stress', 'crisis', 'recovery', 'auto'] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => {
                      onOverride(mode);
                      setShowPopover(false);
                    }}
                    style={{
                      fontSize: '11px',
                      padding: '3px 8px',
                      borderRadius: 'var(--radius-sm)',
                      background: mode === regime.current ? 'var(--color-border-focus)' : 'var(--color-bg-elevated)',
                      color: 'var(--color-text-primary)',
                      border: 'none',
                      cursor: 'pointer',
                      textTransform: 'uppercase',
                    }}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
