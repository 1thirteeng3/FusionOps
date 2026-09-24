import React, { useState } from 'react';
import { Cluster, MLOpsStatus } from '../../types';
import { ClusterPanel } from './ClusterPanel';
import { DriftPanel } from './DriftPanel';
import { Layers, Activity, Cpu } from 'lucide-react';

interface EngineeringViewProps {
  clusters: Cluster[];
  driftStatus: MLOpsStatus | null;
  onRetrain: () => Promise<void>;
  onDrillDownTicket?: (ticketId: string) => void;
}

export const EngineeringView: React.FC<EngineeringViewProps> = ({
  clusters,
  driftStatus,
  onRetrain,
  onDrillDownTicket,
}) => {
  const [subTab, setSubTab] = useState<'clusters' | 'drift'>('clusters');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)', animation: 'fadeIn 300ms ease-out' }}>
      {/* Sub-tab Navigation */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--color-border-default)', paddingBottom: 'var(--space-2)' }}>
        <button
          onClick={() => setSubTab('clusters')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 16px',
            borderRadius: 'var(--radius-md)',
            background: subTab === 'clusters' ? 'var(--color-bg-elevated)' : 'transparent',
            color: subTab === 'clusters' ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
            border: subTab === 'clusters' ? '1px solid var(--color-border-default)' : 'none',
            fontSize: 'var(--text-sm)',
            fontWeight: 'var(--font-weight-semibold)',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
        >
          <Layers size={16} color={subTab === 'clusters' ? '#60A5FA' : 'var(--color-text-muted)'} />
          Clusters Semânticos & Ruído ({clusters.length})
        </button>

        <button
          onClick={() => setSubTab('drift')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 16px',
            borderRadius: 'var(--radius-md)',
            background: subTab === 'drift' ? 'var(--color-bg-elevated)' : 'transparent',
            color: subTab === 'drift' ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
            border: subTab === 'drift' ? '1px solid var(--color-border-default)' : 'none',
            fontSize: 'var(--text-sm)',
            fontWeight: 'var(--font-weight-semibold)',
            cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
        >
          <Activity size={16} color={subTab === 'drift' ? '#60A5FA' : 'var(--color-text-muted)'} />
          MLOps & Drift Observability
        </button>
      </div>

      {/* Tab Content */}
      {subTab === 'clusters' ? (
        <ClusterPanel clusters={clusters} onDrillDownTicket={onDrillDownTicket} />
      ) : (
        <DriftPanel driftStatus={driftStatus} onRetrain={onRetrain} />
      )}
    </div>
  );
};
