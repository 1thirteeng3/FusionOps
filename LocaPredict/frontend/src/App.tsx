import React, { useState, useEffect, useCallback } from 'react';
import {
  Incident,
  Forecast,
  Regime,
  Cluster,
  MLOpsStatus,
  MetricsOverview,
  DashboardMode,
  FilterState,
  ToastMessage,
} from './types';
import { apiService } from './services/api';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { OperationsView } from './components/operations/OperationsView';
import { TacticalView } from './components/tactical/TacticalView';
import { EngineeringView } from './components/engineering/EngineeringView';
import { SHAPWaterfallModal } from './components/operations/SHAPWaterfallModal';
import { ReassignModal, EscalateModal, ShortcutsModal, ToastContainer } from './components/common/Modals';

export const App: React.FC = () => {
  // Navigation & Mode
  const [activeMode, setActiveMode] = useState<DashboardMode>('operations');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Global Data State
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [forecastHorizon, setForecastHorizon] = useState<'D+1' | 'D+7'>('D+7');
  const [regime, setRegime] = useState<Regime | null>(null);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [driftStatus, setDriftStatus] = useState<MLOpsStatus | null>(null);
  const [metricsOverview, setMetricsOverview] = useState<MetricsOverview | null>(null);
  // Fallback pré-carga (valores canônicos reais; substituídos por /metadata).
  const [metadata, setMetadata] = useState<{ groups: string[]; products: string[] }>({
    groups: ['Team14', 'Team11', 'Team05', 'Team09', 'Team07 (NOC)', 'Team19 (Infra)'],
    products: ['Hosting Linux', 'Cloud VPS', 'Email Corporativo', 'Criador de Sites', 'Revenda de Hospedagem'],
  });

  // UI Status
  const [loading, setLoading] = useState(false);
  const [apiHealthy, setApiHealthy] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Modals State
  const [selectedIncidentForSHAP, setSelectedIncidentForSHAP] = useState<Incident | null>(null);
  const [reassignModalId, setReassignModalId] = useState<string | null>(null);
  const [escalateModalId, setEscalateModalId] = useState<string | null>(null);
  const [isShortcutsOpen, setIsShortcutsOpen] = useState(false);

  // Global Filter State
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    priority: 'all',
    group: 'all',
    product: 'all',
    status: 'all',
    minRisk: 0,
    maxRisk: 100,
    sortBy: 'risk_desc',
  });

  // Helper for Toasts
  const addToast = (type: ToastMessage['type'], title: string, message: string) => {
    const id = Date.now().toString() + Math.random().toString().substring(2, 5);
    setToasts((prev) => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Load Data from Backend
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [incs, fc, reg, clus, drift, meta] = await Promise.all([
        apiService.getIncidents(filters),
        apiService.getForecast(forecastHorizon),
        apiService.getRegime(),
        apiService.getClusters(),
        apiService.getDriftAndMLOps(),
        apiService.getMetadata().catch(() => null),
      ]);

      setIncidents(incs);
      setForecast(fc);
      setRegime(reg);
      setClusters(clus);
      setDriftStatus(drift);
      if (meta) {
        setMetadata({ groups: meta.groups, products: meta.products });
      }

      setApiHealthy(true);
      setLastUpdated(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    } catch (err) {
      console.error('Error loading API data:', err);
      setApiHealthy(false);
    } finally {
      setLoading(false);
    }
  }, [filters, forecastHorizon]);

  // Initial Load & Interval Polling (every 30s)
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Keyboard Shortcuts Listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if inside an input or textarea
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) {
        return;
      }

      if (e.key === '1') {
        setActiveMode('operations');
        addToast('info', 'Navegação', 'Modo Operações (Triagem & Risco) ativado');
      } else if (e.key === '2') {
        setActiveMode('tactical');
        addToast('info', 'Navegação', 'Modo Gestão Tática (Forecast D+1/D+7) ativado');
      } else if (e.key === '3') {
        setActiveMode('engineering');
        addToast('info', 'Navegação', 'Modo Engenharia & MLOps ativado');
      } else if (e.key === 's' || e.key === 'S') {
        handleSimulateTicket();
      } else if (e.key === '?') {
        setIsShortcutsOpen(true);
      } else if (e.key === 'Escape') {
        setSelectedIncidentForSHAP(null);
        setReassignModalId(null);
        setEscalateModalId(null);
        setIsShortcutsOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Filter Handlers
  const handleFilterChange = (newFilters: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  };

  const handleResetFilters = () => {
    setFilters({
      search: '',
      priority: 'all',
      group: 'all',
      product: 'all',
      status: 'all',
      minRisk: 0,
      maxRisk: 100,
      sortBy: 'risk_desc',
    });
    addToast('info', 'Filtros', 'Filtros restaurados para o padrão.');
  };

  // Actions Handlers
  const handleSimulateTicket = async () => {
    try {
      const newInc = await apiService.simulateIncident();
      addToast('warning', 'Novo Chamado Injetado', `${newInc.id}: ${newInc.title} (Risco: ${newInc.risk_score}%)`);
      loadData();
    } catch (err) {
      addToast('error', 'Erro', 'Falha ao simular novo chamado.');
    }
  };

  const handleSimulateCrisis = async () => {
    try {
      await apiService.overrideRegime('crisis');
      addToast('error', 'Regime de Crise', 'Regime de crise ativado! Fila operacional em alta criticidade.');
      loadData();
    } catch (err) {
      addToast('error', 'Erro', 'Falha ao alterar regime.');
    }
  };

  const handleRegimeOverride = async (newRegime: string) => {
    try {
      await apiService.overrideRegime(newRegime);
      addToast('info', 'Regime Atualizado', `Regime operacional definido como '${newRegime.toUpperCase()}'.`);
      loadData();
    } catch (err) {
      addToast('error', 'Erro', 'Falha ao atualizar regime.');
    }
  };

  const handleOpenDetails = async (id: string) => {
    const inc = incidents.find((i) => i.id === id);
    if (inc) {
      setSelectedIncidentForSHAP(inc);
    } else {
      try {
        const fetched = await apiService.getIncident(id);
        setSelectedIncidentForSHAP(fetched);
      } catch (err) {
        addToast('error', 'Erro', 'Não foi possível carregar os detalhes do incidente.');
      }
    }
  };

  const handleOpenAssign = (id: string) => {
    setReassignModalId(id);
  };

  const handleOpenEscalate = (id: string) => {
    setEscalateModalId(id);
  };

  const handleNotify = async (id: string) => {
    try {
      const res = await apiService.notifyIncident(id);
      addToast('success', 'Alerta Enviado', res.message);
    } catch (err) {
      addToast('error', 'Erro', 'Falha ao enviar notificação.');
    }
  };

  const handleAssignSubmit = async (id: string, newGroup: string, notes?: string) => {
    try {
      const updated = await apiService.assignIncident(id, newGroup, notes);
      addToast('success', 'Reatribuição Concluída', `Chamado ${id} reatribuído com sucesso para ${newGroup}. Risco reduzido para ${updated.risk_score}%.`);
      loadData();
    } catch (err) {
      addToast('error', 'Erro', 'Falha ao reatribuir incidente.');
    }
  };

  const handleEscalateSubmit = async (id: string, priority: string, reason: string) => {
    try {
      await apiService.escalateIncident(id, priority, reason);
      addToast('warning', 'Incidente Escalado', `Chamado ${id} escalado para ${priority} com notificação de emergência enviada.`);
      loadData();
    } catch (err) {
      addToast('error', 'Erro', 'Falha ao escalar incidente.');
    }
  };

  const handleRetrainModel = async () => {
    const res = await apiService.retrainModel();
    addToast('success', 'Modelo Retreinado', `${res.message} Nova versão: ${res.model_version}.`);
    loadData();
  };

  const handleExportCsv = () => {
    window.open(apiService.getExportUrl(), '_blank');
    addToast('info', 'Exportação', 'Download do relatório CSV iniciado.');
  };

  // Find incidents for modals
  const activeReassignIncident = incidents.find((i) => i.id === reassignModalId);
  const activeEscalateIncident = incidents.find((i) => i.id === escalateModalId);

  return (
    <DashboardLayout
      activeMode={activeMode}
      onModeChange={setActiveMode}
      regime={regime}
      onRegimeOverride={handleRegimeOverride}
      onOpenShortcuts={() => setIsShortcutsOpen(true)}
      apiHealthy={apiHealthy}
      filters={filters}
      onFilterChange={handleFilterChange}
      onResetFilters={handleResetFilters}
      onSimulateTicket={handleSimulateTicket}
      onSimulateCrisis={handleSimulateCrisis}
      isSidebarCollapsed={isSidebarCollapsed}
      onToggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      groups={metadata.groups}
      products={metadata.products}
      operatingPoint={metricsOverview?.operating_point_risk ?? 4}
      lastUpdated={lastUpdated}
      driftCount={driftStatus?.feature_drifts.filter((d) => d.drift_detected).length || 0}
      totalTickets={incidents.length}
    >
      {/* Mode 1: Operations View */}
      {activeMode === 'operations' && (
        <OperationsView
          incidents={incidents}
          loading={loading}
          filters={filters}
          onFilterChange={handleFilterChange}
          onRefresh={loadData}
          onSimulateTicket={handleSimulateTicket}
          onSelectIncident={handleOpenDetails}
          onDetails={handleOpenDetails}
          onAssign={handleOpenAssign}
          onEscalate={handleOpenEscalate}
          onNotify={handleNotify}
        />
      )}

      {/* Mode 2: Tactical View */}
      {activeMode === 'tactical' && (
        <TacticalView
          forecast={forecast}
          horizon={forecastHorizon}
          onHorizonChange={setForecastHorizon}
          onExportCsv={handleExportCsv}
        />
      )}

      {/* Mode 3: Engineering View */}
      {activeMode === 'engineering' && (
        <EngineeringView
          clusters={clusters}
          driftStatus={driftStatus}
          onRetrain={handleRetrainModel}
          onDrillDownTicket={handleOpenDetails}
        />
      )}

      {/* SHAP Waterfall Deep Dive Modal */}
      <SHAPWaterfallModal
        incident={selectedIncidentForSHAP}
        onClose={() => setSelectedIncidentForSHAP(null)}
        onReassign={(id) => {
          setSelectedIncidentForSHAP(null);
          handleOpenAssign(id);
        }}
      />

      {/* Reassign Squad Modal */}
      <ReassignModal
        isOpen={!!reassignModalId}
        incidentId={reassignModalId}
        currentGroup={activeReassignIncident?.group || 'Team14'}
        availableGroups={metadata.groups}
        onClose={() => setReassignModalId(null)}
        onSubmit={handleAssignSubmit}
      />

      {/* Escalate Priority Modal */}
      <EscalateModal
        isOpen={!!escalateModalId}
        incidentId={escalateModalId}
        currentPriority={activeEscalateIncident?.priority || 'P2'}
        onClose={() => setEscalateModalId(null)}
        onSubmit={handleEscalateSubmit}
      />

      {/* Keyboard Shortcuts Overlay */}
      <ShortcutsModal
        isOpen={isShortcutsOpen}
        onClose={() => setIsShortcutsOpen(false)}
      />

      {/* Floating Notifications Toaster */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </DashboardLayout>
  );
};
export default App;
