import React, { useState } from 'react';
import { Network, TrendingUp, TrendingDown, Minus, Bot, AlertTriangle, ArrowRight, X, Layers, Tag } from 'lucide-react';
import { Cluster, Incident } from '../../types';

interface ClusterPanelProps {
  clusters: Cluster[];
  onSelectCluster?: (clusterId: string) => void;
  onDrillDownTicket?: (ticketId: string) => void;
}

export const ClusterPanel: React.FC<ClusterPanelProps> = ({
  clusters,
  onSelectCluster,
  onDrillDownTicket,
}) => {
  const [activeModalCluster, setActiveModalCluster] = useState<Cluster | null>(null);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'growing':
        return <span title="Tendência: Crescendo"><TrendingUp size={14} color="var(--color-risk-critical)" /></span>;
      case 'declining':
        return <span title="Tendência: Declinando"><TrendingDown size={14} color="var(--color-risk-low)" /></span>;
      default:
        return <span title="Tendência: Estável"><Minus size={14} color="var(--color-text-secondary)" /></span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
        <div>
          <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
            Clusters Semânticos & Famílias de Incidentes ({clusters[0]?.algorithm === 'hdbscan' ? 'HDBSCAN validado' : 'baseline léxica'} + contagens medidas)
          </h3>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
            Identificação de padrões ocultos, surtos repetitivos e filtragem de falsos positivos
          </span>
        </div>

        <span style={{ fontSize: 'var(--text-xs)', padding: '4px 10px', borderRadius: 'var(--radius-full)', background: 'var(--color-bg-elevated)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border-default)' }}>
          {clusters.length} Clusters Detectados
        </span>
      </div>

      {/* Cluster Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
          gap: 'var(--space-4)',
        }}
      >
        {clusters.map((cluster) => {
          const isHighFP = cluster.false_positive_rate >= 50;

          return (
            <div
              key={cluster.id}
              className="glass-panel"
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                padding: 'var(--space-4)',
                borderRadius: 'var(--radius-lg)',
                border: isHighFP ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid var(--color-border-default)',
                background: isHighFP ? 'linear-gradient(180deg, rgba(59, 130, 246, 0.08) 0%, rgba(30, 41, 59, 1) 100%)' : 'var(--color-bg-secondary)',
                gap: 'var(--space-3)',
                transition: 'transform var(--transition-fast), border-color var(--transition-fast)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.borderColor = 'var(--color-border-focus)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.borderColor = isHighFP ? 'rgba(59, 130, 246, 0.4)' : 'var(--color-border-default)';
              }}
            >
              {/* Card Header */}
              <div>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: isHighFP ? '#60A5FA' : 'var(--color-risk-high)' }} />
                    <h4 style={{ fontSize: 'var(--text-base)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
                      {cluster.name}
                    </h4>
                  </div>
                  {getTrendIcon(cluster.trend)}
                </div>

                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', lineHeight: '1.4', marginBottom: '8px' }}>
                  {cluster.sample_description}
                </p>
              </div>

              {/* Metrics Badge Row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', background: 'var(--color-bg-primary)', padding: '8px', borderRadius: 'var(--radius-md)' }}>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', display: 'block' }}>Volume</span>
                  <strong style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-primary)' }}>{cluster.incident_count} tickets</strong>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', display: 'block' }}>Taxa Falsos +</span>
                  <strong style={{ fontSize: 'var(--text-sm)', color: isHighFP ? '#60A5FA' : 'var(--color-text-primary)' }}>
                    {cluster.false_positive_rate}%
                  </strong>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', display: 'block' }}>Risco Médio</span>
                  <strong style={{ fontSize: 'var(--text-sm)', color: cluster.avg_risk_score >= 80 ? 'var(--color-risk-critical)' : 'var(--color-risk-medium)' }}>
                    {Math.round(cluster.avg_risk_score)}%
                  </strong>
                </div>
              </div>

              {/* Top Keywords / Features */}
              <div>
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '2px' }}>
                  {cluster.top_features.map((feat, i) => (
                    <span
                      key={i}
                      style={{
                        fontSize: '10px',
                        padding: '2px 6px',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--color-bg-elevated)',
                        color: 'var(--color-text-secondary)',
                        fontFamily: 'var(--font-family-mono)',
                      }}
                    >
                      #{feat}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action Button */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255, 255, 255, 0.05)', paddingTop: '8px' }}>
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  P1: {cluster.p1_count} • P2: {cluster.p2_count} • P3: {cluster.p3_count}
                </span>

                <button
                  onClick={() => setActiveModalCluster(cluster)}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--color-bg-elevated)',
                    border: '1px solid var(--color-border-default)',
                    color: 'var(--color-text-primary)',
                    fontSize: '11px',
                    cursor: 'pointer',
                  }}
                >
                  Inspecionar Tickets
                  <ArrowRight size={12} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Cluster Drill-down Modal */}
      {activeModalCluster && (
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
            zIndex: 2000,
            padding: 'var(--space-4)',
          }}
          onClick={() => setActiveModalCluster(null)}
        >
          <div
            className="glass-modal"
            style={{
              width: '100%',
              maxWidth: '680px',
              maxHeight: '85vh',
              overflowY: 'auto',
              borderRadius: 'var(--radius-xl)',
              padding: 'var(--space-6)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-4)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--color-border-default)', paddingBottom: 'var(--space-3)' }}>
              <div>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-border-focus)', fontWeight: 'bold' }}>
                  {activeModalCluster.id.toUpperCase()}
                </span>
                <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
                  {activeModalCluster.name}
                </h3>
              </div>
              <button
                onClick={() => setActiveModalCluster(null)}
                style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
              <span style={{ fontSize: 'var(--text-xs)', fontWeight: 'bold', color: '#60A5FA', display: 'block', marginBottom: '2px' }}>
                Recomendação de Engenharia / Automação:
              </span>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', lineHeight: '1.4' }}>
                {activeModalCluster.recommended_action}
              </p>
            </div>

            <div>
              <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: 'bold', color: 'var(--color-text-primary)', marginBottom: '8px' }}>
                Incidentes Associados a este Cluster:
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {activeModalCluster.incident_ids.map((ticketId, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      background: 'var(--color-bg-secondary)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--color-border-default)',
                    }}
                  >
                    <span style={{ fontFamily: 'var(--font-family-mono)', fontSize: 'var(--text-xs)', fontWeight: 'bold', color: 'var(--color-text-primary)' }}>
                      {ticketId}
                    </span>
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
                      {ticketId === 'INC8654273' ? 'Problem: Apache Busy Workers (14s - Falso Positivo)' : 'Incidente associado ao cluster'}
                    </span>
                    {onDrillDownTicket && (
                      <button
                        onClick={() => {
                          setActiveModalCluster(null);
                          onDrillDownTicket(ticketId);
                        }}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#60A5FA',
                          fontSize: '11px',
                          cursor: 'pointer',
                          textDecoration: 'underline',
                        }}
                      >
                        Ver Detalhes
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
