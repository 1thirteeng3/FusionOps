import React from 'react';
import { Search, Filter, RotateCcw, Plus, AlertTriangle, ShieldCheck, Activity, ChevronLeft, ChevronRight } from 'lucide-react';
import { FilterState, DashboardMode } from '../../types';

interface SidebarProps {
  filters: FilterState;
  onFilterChange: (filters: Partial<FilterState>) => void;
  onResetFilters: () => void;
  onSimulateTicket: () => void;
  onSimulateCrisis: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  groups: string[];
  products: string[];
  operatingPoint?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  filters,
  onFilterChange,
  onResetFilters,
  onSimulateTicket,
  onSimulateCrisis,
  isCollapsed,
  onToggleCollapse,
  groups,
  products,
  operatingPoint = 4,
}) => {
  if (isCollapsed) {
    return (
      <aside
        style={{
          width: '56px',
          backgroundColor: 'var(--color-bg-secondary)',
          borderRight: '1px solid var(--color-border-default)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: 'var(--space-4) 0',
          gap: 'var(--space-4)',
          transition: 'width 300ms ease',
        }}
      >
        <button
          onClick={onToggleCollapse}
          style={{
            background: 'var(--color-bg-elevated)',
            border: '1px solid var(--color-border-default)',
            color: 'var(--color-text-secondary)',
            borderRadius: 'var(--radius-md)',
            padding: '6px',
            cursor: 'pointer',
          }}
          title="Expandir Barra Lateral"
        >
          <ChevronRight size={18} />
        </button>

        <button
          onClick={onSimulateTicket}
          style={{
            background: 'var(--color-border-focus)',
            border: 'none',
            color: '#fff',
            borderRadius: 'var(--radius-md)',
            padding: '8px',
            cursor: 'pointer',
          }}
          title="Simular Chamado"
        >
          <Plus size={16} />
        </button>
      </aside>
    );
  }

  return (
    <aside
      style={{
        width: '320px',
        backgroundColor: 'var(--color-bg-secondary)',
        borderRight: '1px solid var(--color-border-default)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: 'var(--space-4)',
        gap: 'var(--space-4)',
        overflowY: 'auto',
        transition: 'width 300ms ease',
      }}
      role="navigation"
      aria-label="Filtros Globais e Ações"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        {/* Header with collapse button */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border-default)', paddingBottom: 'var(--space-2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Filter size={16} color="#60A5FA" />
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
              Filtros Operacionais
            </h3>
          </div>

          <button
            onClick={onToggleCollapse}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              padding: '2px',
            }}
            title="Recolher Barra Lateral"
          >
            <ChevronLeft size={18} />
          </button>
        </div>

        {/* Search Input */}
        <div>
          <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '4px' }}>
            Buscar Incidente / IC / Erro:
          </label>
          <div style={{ position: 'relative' }}>
            <Search size={14} color="var(--color-text-muted)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input
              type="text"
              placeholder="Ex: INC8654273, Apache, web9..."
              value={filters.search}
              onChange={(e) => onFilterChange({ search: e.target.value })}
              style={{
                width: '100%',
                padding: '8px 10px 8px 32px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-bg-primary)',
                border: '1px solid var(--color-border-default)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--text-xs)',
              }}
            />
          </div>
        </div>

        {/* Priority Filter */}
        <div>
          <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '4px' }}>
            Prioridade:
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '4px' }}>
            {(['all', 'P1', 'P2', 'P3', 'P4'] as const).map((prio) => (
              <button
                key={prio}
                onClick={() => onFilterChange({ priority: prio })}
                style={{
                  padding: '5px 0',
                  borderRadius: 'var(--radius-sm)',
                  border: filters.priority === prio ? '1px solid var(--color-border-focus)' : '1px solid var(--color-border-default)',
                  background: filters.priority === prio ? 'var(--color-border-focus)' : 'var(--color-bg-primary)',
                  color: filters.priority === prio ? '#fff' : 'var(--color-text-secondary)',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                {prio === 'all' ? 'Todos' : prio}
              </button>
            ))}
          </div>
        </div>

        {/* Squad / Group Filter */}
        <div>
          <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '4px' }}>
            Squad Designada:
          </label>
          <select
            value={filters.group}
            onChange={(e) => onFilterChange({ group: e.target.value })}
            style={{
              width: '100%',
              padding: '7px 10px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-bg-primary)',
              border: '1px solid var(--color-border-default)',
              color: 'var(--color-text-primary)',
              fontSize: 'var(--text-xs)',
            }}
          >
            <option value="all">Todas as Squads ({groups.length})</option>
            {groups.map((grp) => (
              <option key={grp} value={grp}>{grp}</option>
            ))}
          </select>
        </div>

        {/* Product Filter */}
        <div>
          <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '4px' }}>
            Produto Locaweb:
          </label>
          <select
            value={filters.product}
            onChange={(e) => onFilterChange({ product: e.target.value })}
            style={{
              width: '100%',
              padding: '7px 10px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-bg-primary)',
              border: '1px solid var(--color-border-default)',
              color: 'var(--color-text-primary)',
              fontSize: 'var(--text-xs)',
            }}
          >
            <option value="all">Todos os Produtos ({products.length})</option>
            {products.map((prod) => (
              <option key={prod} value={prod}>{prod}</option>
            ))}
          </select>
        </div>

        {/* Risk Score Range Slider (filter fix): calibrated scale runs ~1-20,
            so granularity is 0-50 step 5; highlight at the validated point. */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
            <span>Risco OLA Mínimo:</span>
            <strong style={{ color: filters.minRisk >= operatingPoint ? 'var(--color-risk-critical)' : 'var(--color-text-primary)' }}>
              {filters.minRisk}% (ponto ≥{operatingPoint}%)
            </strong>
          </div>
          <input
            type="range"
            min="0"
            max="50"
            step="5"
            value={Math.min(filters.minRisk, 50)}
            onChange={(e) => onFilterChange({ minRisk: parseInt(e.target.value, 10) })}
            style={{ width: '100%', accentColor: 'var(--color-border-focus)', cursor: 'pointer' }}
          />
        </div>

        {/* Reset Filters Button */}
        <button
          onClick={onResetFilters}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            padding: '6px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--color-bg-elevated)',
            border: '1px solid var(--color-border-default)',
            color: 'var(--color-text-secondary)',
            fontSize: 'var(--text-xs)',
            cursor: 'pointer',
          }}
        >
          <RotateCcw size={13} />
          Limpar Filtros
        </button>

        {/* Quick Simulation Trigger Section */}
        <div style={{ borderTop: '1px solid var(--color-border-default)', paddingTop: 'var(--space-3)' }}>
          <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: '8px' }}>
            Ações Rápidas de Simulação:
          </span>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <button
              onClick={onSimulateTicket}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                padding: '7px 12px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(59, 130, 246, 0.15)',
                border: '1px solid rgba(59, 130, 246, 0.4)',
                color: '#60A5FA',
                fontSize: 'var(--text-xs)',
                fontWeight: 'bold',
                cursor: 'pointer',
              }}
            >
              <Plus size={14} />
              Injetar Novo Chamado
            </button>

            <button
              onClick={onSimulateCrisis}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                padding: '7px 12px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(220, 38, 38, 0.15)',
                border: '1px solid rgba(220, 38, 38, 0.4)',
                color: 'var(--color-risk-critical)',
                fontSize: 'var(--text-xs)',
                fontWeight: 'bold',
                cursor: 'pointer',
              }}
            >
              <AlertTriangle size={14} />
              Simular Regime de Crise
            </button>
          </div>
        </div>
      </div>

      {/* Live System Stats Box */}
      <div
        style={{
          background: 'var(--color-bg-primary)',
          padding: 'var(--space-3)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border-default)',
          fontSize: '11px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
          <Activity size={13} color="#4ADE80" />
          <strong style={{ color: 'var(--color-text-primary)' }}>Inferência ML Online</strong>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-text-muted)', marginBottom: '2px' }}>
          <span>Latência SHAP:</span>
          <span style={{ color: '#4ADE80', fontWeight: 'bold' }}>&lt; 38 ms</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-text-muted)' }}>
          <span>ROC-AUC (CV):</span>
          <span style={{ color: 'var(--color-text-primary)', fontWeight: 'bold' }}>0.85 (CV 5-fold)</span>
        </div>
      </div>
    </aside>
  );
};
