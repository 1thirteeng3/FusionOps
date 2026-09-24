import React from 'react';
import { Activity, ShieldCheck, RefreshCw, Cpu, Layers } from 'lucide-react';

interface FooterProps {
  lastUpdated: string;
  apiHealthy: boolean;
  driftCount: number;
  totalTickets: number;
}

export const Footer: React.FC<FooterProps> = ({
  lastUpdated,
  apiHealthy,
  driftCount,
  totalTickets,
}) => {
  return (
    <footer
      style={{
        height: '48px',
        backgroundColor: 'var(--color-bg-secondary)',
        borderTop: '1px solid var(--color-border-default)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--space-6)',
        fontSize: 'var(--text-xs)',
        color: 'var(--color-text-secondary)',
        zIndex: 90,
      }}
      role="contentinfo"
      aria-label="Status do Sistema"
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: apiHealthy ? 'var(--color-risk-low)' : 'var(--color-risk-critical)',
            }}
          />
          <span>API Core: <strong>{apiHealthy ? 'Saudável (FastAPI)' : 'Degradada'}</strong></span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity size={13} color="#60A5FA" />
          <span>Fila Ativa: <strong>{totalTickets} chamados</strong></span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <ShieldCheck size={13} color={driftCount > 0 ? 'var(--color-risk-medium)' : 'var(--color-risk-low)'} />
          <span>Observabilidade: <strong>{driftCount > 0 ? `${driftCount} Alertas de Drift` : 'Modelos Alinhados'}</strong></span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
        <span>Última atualização: <strong style={{ color: 'var(--color-text-primary)' }}>{lastUpdated}</strong></span>
        <span style={{ fontFamily: 'var(--font-family-mono)', color: 'var(--color-text-muted)' }}>v3.0.0 MVP</span>
      </div>
    </footer>
  );
};
