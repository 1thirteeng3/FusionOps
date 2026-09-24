import React, { useState } from 'react';
import { Activity, RefreshCw, CheckCircle2, AlertTriangle, ShieldAlert, Cpu, Database, Check, X, ShieldCheck } from 'lucide-react';
import { MLOpsStatus } from '../../types';
import { useAuth } from '../../context/AuthContext';

interface DriftPanelProps {
  driftStatus: MLOpsStatus | null;
  onRetrain: () => Promise<void>;
}

export const DriftPanel: React.FC<DriftPanelProps> = ({
  driftStatus,
  onRetrain,
}) => {
  const { hasPermission, user } = useAuth();
  const canRetrain = hasPermission('retrain');
  
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [retraining, setRetraining] = useState(false);
  const [retrainSuccess, setRetrainSuccess] = useState(false);

  const handleRetrainSubmit = async () => {
    try {
      setIsConfirmModalOpen(false);
      setRetraining(true);
      setRetrainSuccess(false);
      await onRetrain();
      setRetrainSuccess(true);
      setTimeout(() => setRetrainSuccess(false), 4000);
    } catch (e) {
      console.error(e);
    } finally {
      setRetraining(false);
    }
  };

  if (!driftStatus) {
    return (
      <div className="glass-panel" style={{ padding: 'var(--space-6)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
        Carregando observabilidade MLOps...
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'stable':
      case 'healthy':
        return (
          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: 'rgba(22, 163, 74, 0.15)', color: 'var(--color-risk-low)', border: '1px solid rgba(22, 163, 74, 0.3)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle2 size={11} /> Estável
          </span>
        );
      case 'warning':
        return (
          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: 'rgba(202, 138, 4, 0.15)', color: 'var(--color-risk-medium)', border: '1px solid rgba(202, 138, 4, 0.3)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <AlertTriangle size={11} /> Atenção (Drift)
          </span>
        );
      default:
        return (
          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: 'rgba(220, 38, 38, 0.15)', color: 'var(--color-risk-critical)', border: '1px solid rgba(220, 38, 38, 0.3)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <ShieldAlert size={11} /> Drift Crítico
          </span>
        );
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
      {/* Header with Retrain Trigger */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
              MLOps & Monitoramento de Data Drift (Evidently AI / KS-Test)
            </h3>
            {getStatusBadge(driftStatus.drift_status)}
          </div>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
            Modelo ativo: <strong>{driftStatus.model_version}</strong> • Último treino: {driftStatus.last_trained}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {retrainSuccess && (
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-risk-low)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Check size={14} /> Modelo retreinado com sucesso!
            </span>
          )}

          <button
            onClick={() => setIsConfirmModalOpen(true)}
            disabled={retraining || !canRetrain}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: 'var(--radius-md)',
              background: !canRetrain ? 'var(--color-bg-elevated)' : (retraining ? 'var(--color-bg-hover)' : 'var(--color-border-focus)'),
              border: 'none',
              color: !canRetrain ? 'var(--color-text-muted)' : '#fff',
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--font-weight-bold)',
              cursor: !canRetrain || retraining ? 'not-allowed' : 'pointer',
              boxShadow: canRetrain ? 'var(--shadow-glow-blue)' : 'none',
            }}
            title={!canRetrain ? 'Requer perfil de Administrador para retreinar modelos' : 'Disparar retreinamento'}
            aria-label="Retreinar modelo de machine learning"
          >
            <RefreshCw size={14} className={retraining ? 'animate-spin' : ''} />
            {retraining ? 'Retreinando Modelos...' : (canRetrain ? 'Retreinar Modelo' : 'Retreino (Apenas Admin)')}
          </button>
        </div>
      </div>

      {/* Model Performance KPIs */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 'var(--space-3)',
        }}
      >
        <div className="glass-panel" style={{ padding: 'var(--space-3) var(--space-4)' }}>
          <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>ROC-AUC Score</span>
          <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 'bold', color: 'var(--color-risk-low)', marginTop: '2px' }}>
            {driftStatus.roc_auc}
          </div>
          <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>Meta &ge; 0.80</span>
        </div>

        <div className="glass-panel" style={{ padding: 'var(--space-3) var(--space-4)' }}>
          <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Recall (Sensibilidade)</span>
          <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 'bold', color: 'var(--color-risk-low)', marginTop: '2px' }}>
            {driftStatus.recall}
          </div>
          <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>Meta &ge; 0.75</span>
        </div>

        <div className="glass-panel" style={{ padding: 'var(--space-3) var(--space-4)' }}>
          <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Precisão OLA</span>
          <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 'bold', color: 'var(--color-text-primary)', marginTop: '2px' }}>
            {driftStatus.precision}
          </div>
          <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>F1-Score: {driftStatus.f1_score}</span>
        </div>

        <div className="glass-panel" style={{ padding: 'var(--space-3) var(--space-4)' }}>
          <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>WAPE Forecast</span>
          <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 'bold', color: 'var(--color-border-focus)', marginTop: '2px' }}>
            {(driftStatus.wape * 100).toFixed(1)}%
          </div>
          <span style={{ fontSize: '10px', color: 'var(--color-text-secondary)' }}>Meta &le; 15%</span>
        </div>
      </div>

      {/* Feature Drift Statistical Testing Table */}
      <div className="glass-panel" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: 'bold', color: 'var(--color-text-primary)' }}>
          Teste Estatístico Kolmogorov-Smirnov (Data Drift por Feature)
        </h4>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-xs)', textAlign: 'left' }} role="table" aria-label="Tabela de Testes Kolmogorov-Smirnov">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border-default)', color: 'var(--color-text-muted)' }}>
                <th style={{ padding: '8px' }}>Feature</th>
                <th style={{ padding: '8px' }}>Média de Treino</th>
                <th style={{ padding: '8px' }}>Média de Inferência</th>
                <th style={{ padding: '8px' }}>Estatística KS</th>
                <th style={{ padding: '8px' }}>p bruto</th>
                <th style={{ padding: '8px' }}>p ajustado (Holm)</th>
                <th style={{ padding: '8px' }}>Janela (n)</th>
                <th style={{ padding: '8px', textAlign: 'right' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {driftStatus.feature_drifts.map((feat, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                    backgroundColor: feat.drift_detected ? 'rgba(202, 138, 4, 0.06)' : 'transparent',
                  }}
                >
                  <td style={{ padding: '8px', fontWeight: '500', color: 'var(--color-text-primary)', fontFamily: 'var(--font-family-mono)' }}>
                    {feat.feature_name}
                  </td>
                  <td style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>{feat.reference_mean}</td>
                  <td style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>{feat.current_mean}</td>
                  <td style={{ padding: '8px', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-family-mono)' }}>
                    {feat.statistic}
                  </td>
                  <td
                    style={{
                      padding: '8px',
                      fontFamily: 'var(--font-family-mono)',
                      fontWeight: feat.drift_detected ? 'bold' : 'normal',
                      color: feat.drift_detected ? 'var(--color-risk-medium)' : 'var(--color-text-primary)',
                    }}
                  >
                    {feat.p_value}
                  </td>
                  <td style={{ padding: '8px', fontFamily: 'var(--font-family-mono)', color: 'var(--color-text-primary)' }}>
                    {feat.p_adjusted ?? '—'}
                  </td>
                  <td style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>
                    {feat.window_n ?? '—'}
                  </td>
                  <td style={{ padding: '8px', textAlign: 'right' }}>{getStatusBadge(feat.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Retrain Confirmation Modal */}
      {isConfirmModalOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 2200,
            padding: 'var(--space-4)',
          }}
          onClick={() => setIsConfirmModalOpen(false)}
        >
          <div
            className="glass-modal"
            style={{
              width: '100%',
              maxWidth: '460px',
              borderRadius: 'var(--radius-xl)',
              padding: 'var(--space-6)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-4)',
            }}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-labelledby="retrain-modal-title"
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={20} color="var(--color-border-focus)" />
                <h3 id="retrain-modal-title" style={{ fontSize: 'var(--text-base)', fontWeight: 'bold', color: 'var(--color-text-primary)' }}>
                  Confirmar Retreinamento de Modelo
                </h3>
              </div>
              <button
                onClick={() => setIsConfirmModalOpen(false)}
                style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}
                aria-label="Cancelar"
              >
                <X size={18} />
              </button>
            </div>

            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', lineHeight: '1.5' }}>
              Esta ação irá refazer o treinamento do <strong>Random Forest Classifier</strong> e do <strong>TF-IDF Vectorizer</strong> incorporando os chamados e reatribuições mais recentes da base ITSM, reajustando os pesos de explicabilidade SHAP e zerando o drift acumulado.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: 'var(--space-2)' }}>
              <button
                onClick={() => setIsConfirmModalOpen(false)}
                style={{
                  padding: '8px 14px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--color-bg-elevated)',
                  border: '1px solid var(--color-border-default)',
                  color: 'var(--color-text-primary)',
                  fontSize: 'var(--text-xs)',
                  cursor: 'pointer',
                }}
              >
                Cancelar
              </button>
              <button
                onClick={handleRetrainSubmit}
                style={{
                  padding: '8px 16px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--color-border-focus)',
                  border: 'none',
                  color: '#fff',
                  fontSize: 'var(--text-xs)',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                }}
              >
                Confirmar e Retreinar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
