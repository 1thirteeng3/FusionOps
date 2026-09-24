import React, { useState, useMemo } from 'react';
import { ShieldAlert, AlertTriangle, Clock, Bot, Search, Filter, ArrowUpDown, RefreshCw, Plus } from 'lucide-react';
import { Incident, FilterState } from '../../types';
import { IncidentCard } from './IncidentCard';

interface OperationsViewProps {
  incidents: Incident[];
  loading: boolean;
  filters: FilterState;
  onFilterChange: (filters: Partial<FilterState>) => void;
  onRefresh: () => void;
  onSimulateTicket: () => void;
  onSelectIncident: (id: string) => void;
  onDetails: (id: string) => void;
  onAssign: (id: string) => void;
  onEscalate: (id: string) => void;
  onNotify: (id: string) => void;
}

export const OperationsView: React.FC<OperationsViewProps> = ({
  incidents,
  loading,
  filters,
  onFilterChange,
  onRefresh,
  onSimulateTicket,
  onSelectIncident,
  onDetails,
  onAssign,
  onEscalate,
  onNotify,
}) => {
  const [activeChip, setActiveChip] = useState<'all' | 'critical' | 'fp' | 'p1p2'>('all');

  // Validated operating point (filter fix): "flagged" means risk at/above the
  // recall-constrained threshold tau carried by each incident — the legacy
  // >=80 rule never fired under calibrated probabilities.
  const opPoint = Math.max(1, Math.round(
    (incidents.find((i) => i.threshold_tau != null)?.threshold_tau ?? 0.04) * 100));

  // Filtered incidents based on active quick chip
  const displayedIncidents = useMemo(() => {
    if (activeChip === 'critical') {
      return incidents.filter((i) => i.risk_score >= opPoint);
    }
    if (activeChip === 'fp') {
      return incidents.filter((i) => i.is_automated_fp);
    }
    if (activeChip === 'p1p2') {
      return incidents.filter((i) => i.priority === 'P1' || i.priority === 'P2');
    }
    return incidents;
  }, [incidents, activeChip, opPoint]);

  // Operational KPI calculations
  const totalCount = incidents.length;
  const criticalCount = incidents.filter((i) => i.risk_score >= opPoint).length;
  const imminentCount = incidents.filter((i) => i.sla_remaining_minutes > 0 && i.sla_remaining_minutes <= 45).length;
  const fpCount = incidents.filter((i) => i.is_automated_fp).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)', animation: 'fadeIn 300ms ease-out' }}>
      {/* 4 Hero KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 'var(--space-4)',
        }}
      >
        {/* KPI 1: Active Tickets */}
        <div className="glass-panel" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Incidentes em Fila de Triagem
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: 'var(--text-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
              {totalCount}
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>chamados ativos</span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Ponto operacional τ≥{opPoint}% (recall≥80% validado)</span>
        </div>

        {/* KPI 2: Flagged Risk >= operating point */}
        <div
          className="glass-panel"
          style={{
            padding: 'var(--space-4)',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
            border: criticalCount > 0 ? '1px solid rgba(220, 38, 38, 0.4)' : '1px solid var(--color-border-default)',
            background: criticalCount > 0 ? 'linear-gradient(180deg, rgba(220, 38, 38, 0.12) 0%, rgba(30, 41, 59, 1) 100%)' : 'var(--color-bg-secondary)',
          }}
        >
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-risk-critical)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 'bold' }}>
            Risco Sinalizado OLA (&ge; {opPoint}% — ponto operacional)
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: 'var(--text-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-risk-critical)' }}>
              {criticalCount}
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-risk-critical)', display: 'flex', alignItems: 'center' }}>
              Intervenção imediata
            </span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Risco calibrado (p calibrada × 100) • P1: base com n=1, sem generalização</span>
        </div>

        {/* KPI 3: Imminent SLA Breaches */}
        <div className="glass-panel" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-risk-medium)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 'bold' }}>
            SLA Iminente (&le; 45min)
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: 'var(--text-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-risk-medium)' }}>
              {imminentCount}
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-risk-medium)' }}>em contagem regressiva</span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Priorizados no topo da fila</span>
        </div>

        {/* KPI 4: Automated False Positives */}
        <div className="glass-panel" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: '#60A5FA', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 'bold' }}>
            Falsos Positivos NLP (Ruído)
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: 'var(--text-3xl)', fontWeight: 'var(--font-weight-bold)', color: '#60A5FA' }}>
              {fpCount}
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: '#60A5FA' }}>detectados automaticamente</span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Ex: Apache Busy Workers (14s)</span>
        </div>
      </div>

      {/* Filter and Action Bar */}
      <div
        className="glass-panel"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          padding: 'var(--space-3) var(--space-4)',
          gap: 'var(--space-3)',
        }}
      >
        {/* Quick Filter Chips */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setActiveChip('all')}
            style={{
              padding: '5px 12px',
              borderRadius: 'var(--radius-full)',
              border: activeChip === 'all' ? '1px solid var(--color-border-focus)' : '1px solid var(--color-border-default)',
              backgroundColor: activeChip === 'all' ? 'rgba(59, 130, 246, 0.2)' : 'var(--color-bg-primary)',
              color: activeChip === 'all' ? '#60A5FA' : 'var(--color-text-secondary)',
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--font-weight-medium)',
              cursor: 'pointer',
            }}
          >
            Todos ({totalCount})
          </button>

          <button
            onClick={() => setActiveChip('critical')}
            style={{
              padding: '5px 12px',
              borderRadius: 'var(--radius-full)',
              border: activeChip === 'critical' ? '1px solid var(--color-risk-critical)' : '1px solid var(--color-border-default)',
              backgroundColor: activeChip === 'critical' ? 'rgba(220, 38, 38, 0.2)' : 'var(--color-bg-primary)',
              color: activeChip === 'critical' ? 'var(--color-risk-critical)' : 'var(--color-text-secondary)',
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--font-weight-medium)',
              cursor: 'pointer',
            }}
          >
            Sinalizados &ge;{opPoint}% ({criticalCount})
          </button>

          <button
            onClick={() => setActiveChip('p1p2')}
            style={{
              padding: '5px 12px',
              borderRadius: 'var(--radius-full)',
              border: activeChip === 'p1p2' ? '1px solid var(--color-risk-high)' : '1px solid var(--color-border-default)',
              backgroundColor: activeChip === 'p1p2' ? 'rgba(234, 88, 12, 0.2)' : 'var(--color-bg-primary)',
              color: activeChip === 'p1p2' ? 'var(--color-risk-high)' : 'var(--color-text-secondary)',
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--font-weight-medium)',
              cursor: 'pointer',
            }}
          >
            Prioridade P1 / P2
          </button>

          <button
            onClick={() => setActiveChip('fp')}
            style={{
              padding: '5px 12px',
              borderRadius: 'var(--radius-full)',
              border: activeChip === 'fp' ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid var(--color-border-default)',
              backgroundColor: activeChip === 'fp' ? 'rgba(59, 130, 246, 0.2)' : 'var(--color-bg-primary)',
              color: activeChip === 'fp' ? '#60A5FA' : 'var(--color-text-secondary)',
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--font-weight-medium)',
              cursor: 'pointer',
            }}
          >
            Falso Positivo NLP ({fpCount})
          </button>
        </div>

        {/* Sort & Live Action */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <select
            value={filters.sortBy}
            onChange={(e) => onFilterChange({ sortBy: e.target.value as any })}
            style={{
              padding: '6px 10px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-bg-primary)',
              border: '1px solid var(--color-border-default)',
              color: 'var(--color-text-primary)',
              fontSize: 'var(--text-xs)',
            }}
          >
            <option value="risk_desc">Maior Risco OLA (Decrescente)</option>
            <option value="risk_asc">Menor Risco OLA (Crescente)</option>
            <option value="sla_asc">Menor Tempo Restante de SLA</option>
            <option value="created_desc">Mais Recentes</option>
          </select>

          <button
            onClick={onSimulateTicket}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '6px 12px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-border-focus)',
              border: 'none',
              color: '#fff',
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--font-weight-semibold)',
              cursor: 'pointer',
            }}
            title="Simula chegada de novo chamado de alta criticidade no stream"
          >
            <Plus size={13} />
            Simular Chamado
          </button>

          <button
            onClick={onRefresh}
            style={{
              padding: '6px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-bg-elevated)',
              border: '1px solid var(--color-border-default)',
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
            }}
            title="Atualizar lista de chamados"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Incident Cards Feed */}
      {displayedIncidents.length === 0 ? (
        <div
          className="glass-panel"
          style={{
            padding: 'var(--space-12)',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 'var(--space-3)',
          }}
        >
          <Bot size={36} color="var(--color-text-muted)" />
          <h4 style={{ fontSize: 'var(--text-base)', color: 'var(--color-text-primary)' }}>
            Nenhum incidente encontrado para os filtros aplicados
          </h4>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
            Tente ajustar os filtros na barra lateral ou selecionar outro chip de triagem.
          </span>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {displayedIncidents.map((incident) => (
            <IncidentCard
              key={incident.id}
              incident={incident}
              onSelect={onSelectIncident}
              onDetails={onDetails}
              onAssign={onAssign}
              onEscalate={onEscalate}
              onNotify={onNotify}
            />
          ))}
        </div>
      )}
    </div>
  );
};
