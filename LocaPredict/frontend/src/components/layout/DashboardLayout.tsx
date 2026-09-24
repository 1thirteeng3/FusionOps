import React from 'react';
import { Regime, DashboardMode } from '../../types';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Footer } from './Footer';

interface DashboardLayoutProps {
  activeMode: DashboardMode;
  onModeChange: (mode: DashboardMode) => void;
  regime: Regime | null;
  onRegimeOverride: (regime: string) => void;
  onOpenShortcuts: () => void;
  apiHealthy: boolean;
  filters: any;
  onFilterChange: (filters: any) => void;
  onResetFilters: () => void;
  onSimulateTicket: () => void;
  onSimulateCrisis: () => void;
  isSidebarCollapsed: boolean;
  onToggleSidebar: () => void;
  groups: string[];
  products: string[];
  operatingPoint?: number;
  lastUpdated: string;
  driftCount: number;
  totalTickets: number;
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  activeMode,
  onModeChange,
  regime,
  onRegimeOverride,
  onOpenShortcuts,
  apiHealthy,
  filters,
  onFilterChange,
  onResetFilters,
  onSimulateTicket,
  onSimulateCrisis,
  isSidebarCollapsed,
  onToggleSidebar,
  groups,
  products,
  operatingPoint = 4,
  lastUpdated,
  driftCount,
  totalTickets,
  children,
}) => {
  const isCrisis = regime?.current === 'crisis';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        backgroundColor: 'var(--color-bg-primary)',
      }}
      role="application"
    >
      {/* Header */}
      <Header
        activeMode={activeMode}
        onModeChange={onModeChange}
        regime={regime}
        onRegimeOverride={onRegimeOverride}
        onOpenShortcuts={onOpenShortcuts}
        apiHealthy={apiHealthy}
      />

      {/* Crisis Warning Banner if in Crisis mode */}
      {isCrisis && (
        <div
          style={{
            backgroundColor: 'var(--color-risk-critical)',
            color: '#fff',
            padding: '6px var(--space-6)',
            fontSize: 'var(--text-xs)',
            fontWeight: 'var(--font-weight-bold)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            animation: 'pulseBorder 2s infinite',
            zIndex: 95,
          }}
        >
          <span>⚠️ ALERTA OPERACIONAL: Regime de Crise Ativo! Alto risco de estouro de OLA em incidentes P1/P2.</span>
          <button
            onClick={() => onRegimeOverride('normal')}
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              border: '1px solid rgba(255, 255, 255, 0.4)',
              color: '#fff',
              padding: '2px 8px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '11px',
            }}
          >
            Normalizar Regime
          </button>
        </div>
      )}

      {/* Middle Workspace: Sidebar + Main Content Area */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <Sidebar
          filters={filters}
          onFilterChange={onFilterChange}
          onResetFilters={onResetFilters}
          onSimulateTicket={onSimulateTicket}
          onSimulateCrisis={onSimulateCrisis}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={onToggleSidebar}
          groups={groups}
          products={products}
          operatingPoint={operatingPoint}
        />

        {/* Main Content Area */}
        <main
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 'var(--space-6)',
            backgroundColor: 'var(--color-bg-primary)',
          }}
          role="main"
          aria-live="polite"
        >
          {children}
        </main>
      </div>

      {/* Footer */}
      <Footer
        lastUpdated={lastUpdated}
        apiHealthy={apiHealthy}
        driftCount={driftCount}
        totalTickets={totalTickets}
      />
    </div>
  );
};
