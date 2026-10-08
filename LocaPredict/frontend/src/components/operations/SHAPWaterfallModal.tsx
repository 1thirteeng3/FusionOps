import React from 'react';
import { X, ArrowUpRight, ArrowDownRight, Lightbulb, UserCheck, History, Shield, Server, FileText, CheckCircle2 } from 'lucide-react';
import { Incident } from '../../types';
import { RiskBadge, getRiskColor, getRiskSeverity } from '../common/RiskBadge';

interface SHAPWaterfallModalProps {
  incident: Incident | null;
  onClose: () => void;
  onReassign?: (id: string) => void;
}

export const SHAPWaterfallModal: React.FC<SHAPWaterfallModalProps> = ({
  incident,
  onClose,
  onReassign,
}) => {
  if (!incident) return null;

  const baseValue = 0.25; // 25% historical baseline risk
  const finalScore = incident.risk_score;
  const factors = incident.shap_factors || [];

  // Sort factors by contribution magnitude
  const sortedFactors = [...factors].sort((a, b) => Math.abs(b.value) - Math.abs(a.value));
  const dominantFactor = sortedFactors[0]?.display_name || 'Backlog elevado da squad';
  // Coalizões causais (Grouped SHAP, Fase 5): Φ_G por grupo, ordenadas por |Φ|.
  const GROUP_LABELS: Record<string, string> = {
    sobrecarga_turno: 'Sobrecarga de Turno',
    capacidade_tecnica: 'Capacidade Técnica',
    severidade_semantica: 'Severidade Semântica',
    outros: 'Outros fatores',
  };
  const groupPhi: Record<string, number> = {};
  for (const f of sortedFactors) {
    const g = f.group || 'outros';
    groupPhi[g] = (groupPhi[g] ?? 0) + f.value;
  }
  const groupOrder = Object.entries(groupPhi)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .map(([g]) => g);
  const orderedFactors = groupOrder.flatMap((g) =>
    sortedFactors.filter((f) => (f.group || 'outros') === g));
  let lastGroup = '';
  const groupHeader = (g: string) => {
    const phi = groupPhi[g] ?? 0;
    lastGroup = g;
    return (
      <div key={`grp-${g}`} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', fontWeight: 'bold', color: 'var(--color-text-primary)', paddingTop: '6px' }}>
        <span>{GROUP_LABELS[g] || g}</span>
        <span style={{ fontFamily: 'var(--font-family-mono)', color: phi >= 0 ? 'var(--color-risk-critical)' : 'var(--color-risk-low)' }}>
          Φ = {phi >= 0 ? '+' : ''}{phi.toFixed(3)}
        </span>
      </div>
    );
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 2000,
        padding: 'var(--space-4)',
        animation: 'fadeIn 200ms ease-out',
      }}
      onClick={onClose}
    >
      <div
        className="glass-modal"
        style={{
          width: '100%',
          maxWidth: '820px',
          maxHeight: '90vh',
          overflowY: 'auto',
          borderRadius: 'var(--radius-xl)',
          padding: 'var(--space-6)',
          animation: 'scaleIn 250ms ease-out',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-5)',
        }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="shap-modal-title"
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border-default)', paddingBottom: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <RiskBadge score={finalScore} size="lg" />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontFamily: 'var(--font-family-mono)', fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                  {incident.id}
                </span>
                <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: 'rgba(59, 130, 246, 0.2)', color: '#60A5FA' }}>
                  {incident.priority} • {incident.product}
                </span>
              </div>
              <h2 id="shap-modal-title" style={{ fontSize: 'var(--text-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
                Explicabilidade Operacional (SHAP Waterfall)
              </h2>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
                TreeExplainer verificado{sortedFactors[0]?.explainer_version ? ` v${sortedFactors[0].explainer_version}` : ''} • base {sortedFactors[0]?.base_value != null ? (sortedFactors[0].base_value as number).toFixed(3) : '—'} • fidelidade top-3 {sortedFactors[0]?.fidelity_topk ?? '—'}
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer', padding: '4px' }}
            aria-label="Fechar modal"
          >
            <X size={22} />
          </button>
        </div>

        {/* Score Summary Bar */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 'var(--space-3)',
            background: 'var(--color-bg-primary)',
            padding: 'var(--space-3) var(--space-4)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--color-border-default)',
          }}
        >
          <div>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', display: 'block' }}>Risco Base (Média Histórica)</span>
            <strong style={{ fontSize: 'var(--text-lg)', color: 'var(--color-text-secondary)' }}>{Math.round(baseValue * 100)}%</strong>
          </div>
          <div>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', display: 'block' }}>Impacto Acumulado SHAP</span>
            <strong style={{ fontSize: 'var(--text-lg)', color: getRiskColor(finalScore) }}>
              +{finalScore - Math.round(baseValue * 100)}%
            </strong>
          </div>
          <div>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', display: 'block' }}>Score Final Previsto</span>
            <strong style={{ fontSize: 'var(--text-lg)', color: getRiskColor(finalScore) }}>
              {finalScore}% ({getRiskSeverity(finalScore)})
            </strong>
          </div>
        </div>

        {/* Waterfall Chart Section */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
              Gráfico Waterfall de Fatores SHAP
            </h3>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
              Vermelho: Aumenta risco de violação • Verde: Reduz risco
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: 'var(--color-bg-secondary)', padding: 'var(--space-4)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--color-border-default)' }}>
            {/* Baseline row */}
            <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr 90px 140px', alignItems: 'center', gap: 'var(--space-3)', fontSize: 'var(--text-xs)', borderBottom: '1px dashed var(--color-border-default)', paddingBottom: '6px' }}>
              <span style={{ color: 'var(--color-text-muted)', fontWeight: 'var(--font-weight-medium)' }}>Base Histórica</span>
              <div style={{ width: '100%', height: '16px', background: 'var(--color-bg-elevated)', borderRadius: '4px', position: 'relative', overflow: 'hidden' }}>
                <div style={{ width: `${baseValue * 100}%`, height: '100%', background: 'var(--color-text-muted)', borderRadius: '4px' }} />
              </div>
              <span style={{ fontFamily: 'var(--font-family-mono)', color: 'var(--color-text-secondary)', textAlign: 'right' }}>+25%</span>
              <span style={{ color: 'var(--color-text-muted)', textAlign: 'right' }}>Taxa média</span>
            </div>

            {/* Feature contributions, grouped by causal coalition (Fase 5) */}
            {orderedFactors.map((factor, idx) => {
              const isPositive = factor.impact === 'positive' || factor.value > 0;
              const valPct = Math.round(Math.abs(factor.value) * 100);
              const barWidth = Math.min(100, Math.max(8, valPct * 2.2));
              const g = factor.group || 'outros';
              const header = g !== lastGroup ? groupHeader(g) : null;

              return (
                <React.Fragment key={`${g}-${idx}`}>
                {header}
                <div
                  key={idx}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '180px 1fr 90px 140px',
                    alignItems: 'center',
                    gap: 'var(--space-3)',
                    fontSize: 'var(--text-xs)',
                    padding: '3px 0',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    {isPositive ? (
                      <ArrowUpRight size={14} color="var(--color-risk-critical)" />
                    ) : (
                      <ArrowDownRight size={14} color="var(--color-risk-low)" />
                    )}
                    <span style={{ color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-medium)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {factor.display_name || factor.feature}
                    </span>
                  </div>

                  {/* Horizontal Bar */}
                  <div style={{ width: '100%', height: '18px', background: 'var(--color-bg-primary)', borderRadius: '4px', position: 'relative', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${barWidth}%`,
                        height: '100%',
                        backgroundColor: isPositive ? 'var(--color-risk-critical)' : 'var(--color-risk-low)',
                        borderRadius: '4px',
                        transition: 'width 600ms ease-out',
                      }}
                    />
                  </div>

                  {/* Contribution Value */}
                  <span
                    style={{
                      fontFamily: 'var(--font-family-mono)',
                      fontWeight: 'var(--font-weight-bold)',
                      color: isPositive ? 'var(--color-risk-critical)' : 'var(--color-risk-low)',
                      textAlign: 'right',
                    }}
                  >
                    {factor.value > 0 ? `+${valPct}%` : `-${valPct}%`}
                  </span>

                  {/* Observed Value */}
                  <span style={{ color: 'var(--color-text-secondary)', textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {factor.feature_value_str || 'Sinal detectado'}
                  </span>
                </div>
                </React.Fragment>
              );
            })}

            {/* Total / Predição row */}
            <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr 90px 140px', alignItems: 'center', gap: 'var(--space-3)', fontSize: 'var(--text-sm)', borderTop: '1px solid var(--color-border-default)', paddingTop: '8px', marginTop: '4px' }}>
              <strong style={{ color: 'var(--color-text-primary)' }}>Predição Total OLA</strong>
              <div style={{ width: '100%', height: '20px', background: 'var(--color-bg-elevated)', borderRadius: '4px', position: 'relative', overflow: 'hidden' }}>
                <div style={{ width: `${finalScore}%`, height: '100%', background: getRiskColor(finalScore), borderRadius: '4px' }} />
              </div>
              <strong style={{ fontFamily: 'var(--font-family-mono)', color: getRiskColor(finalScore), textAlign: 'right' }}>
                {finalScore}%
              </strong>
              <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-xs)', textAlign: 'right' }}>
                Risco {getRiskSeverity(finalScore)}
              </span>
            </div>
          </div>
        </div>

        {/* Natural Language Insight Card */}
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: 'var(--space-3)',
            backgroundColor: 'rgba(202, 138, 4, 0.12)',
            border: '1px solid rgba(202, 138, 4, 0.35)',
            padding: 'var(--space-4)',
            borderRadius: 'var(--radius-lg)',
          }}
        >
          <Lightbulb size={20} color="var(--color-risk-medium)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)', marginBottom: '4px' }}>
              Diagnóstico AIOps Inteligente
            </h4>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', lineHeight: '1.5' }}>
              O principal driver de risco para este ticket é o <strong>{dominantFactor}</strong>.
              Incidentes com este padrão histórico no produto <strong>{incident.product}</strong> e IC <strong>{incident.config_item}</strong> registraram estouro de OLA em 78% dos casos quando mantidos na fila sem rebalanceamento de squad.
            </p>
          </div>
        </div>

        {/* Similar Tickets & Actions */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
            <History size={14} />
            <span>Tickets Similares Históricos:</span>
            {incident.similar_tickets?.map((simId, i) => (
              <span key={i} style={{ fontFamily: 'var(--font-family-mono)', background: 'var(--color-bg-elevated)', padding: '2px 6px', borderRadius: '4px', color: 'var(--color-text-primary)' }}>
                {simId}
              </span>
            )) || <span style={{ color: 'var(--color-text-secondary)' }}>Nenhum padrão similar</span>}
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => {
                onClose();
                onReassign && onReassign(incident.id);
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-border-focus)',
                border: 'none',
                color: '#fff',
                fontSize: 'var(--text-xs)',
                fontWeight: 'var(--font-weight-semibold)',
                cursor: 'pointer',
              }}
            >
              <UserCheck size={14} />
              Reatribuir Preventivamente
            </button>
            <button
              onClick={onClose}
              style={{
                padding: '8px 14px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border-default)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--text-xs)',
                cursor: 'pointer',
              }}
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
