import React, { useState } from 'react';
import { X, UserCheck, AlertTriangle, HelpCircle, Check, Info } from 'lucide-react';
import { ToastMessage } from '../../types';

// Reassign Modal
interface ReassignModalProps {
  isOpen: boolean;
  incidentId: string | null;
  currentGroup: string;
  availableGroups: string[];
  onClose: () => void;
  onSubmit: (id: string, newGroup: string, notes?: string) => Promise<void>;
}

export const ReassignModal: React.FC<ReassignModalProps> = ({
  isOpen,
  incidentId,
  currentGroup,
  availableGroups,
  onClose,
  onSubmit,
}) => {
  const [selectedGroup, setSelectedGroup] = useState(currentGroup);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  // RBAC/audit error surfacing (T038, Gate 6): 401/403 from the backend are
  // shown inline instead of failing silently in the console.
  const [actionError, setActionError] = useState<string | null>(null);

  if (!isOpen || !incidentId) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setActionError(null);
      await onSubmit(incidentId, selectedGroup, notes);
      onClose();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Falha na operação.';
      setActionError(`Negado pela governança (${err?.response?.status ?? 'erro'}): ${msg}`);
      console.error(err);
    } finally {
      setSubmitting(false);
    }
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
        zIndex: 2100,
        padding: 'var(--space-4)',
      }}
      onClick={onClose}
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
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <UserCheck size={18} color="var(--color-border-focus)" />
            <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 'bold', color: 'var(--color-text-primary)' }}>
              Reatribuir Incidente {incidentId}
            </h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div>
            <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>
              Selecionar Nova Squad Responsável:
            </label>
            <select
              value={selectedGroup}
              onChange={(e) => setSelectedGroup(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-bg-primary)',
                border: '1px solid var(--color-border-default)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--text-sm)',
              }}
            >
              {availableGroups.map((grp) => (
                <option key={grp} value={grp}>{grp}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>
              Justificativa / Instruções de Transição:
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: Reatribuição preventiva devido a sobrecarga da squad atual..."
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-bg-primary)',
                border: '1px solid var(--color-border-default)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--text-sm)',
                resize: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: 'var(--space-2)' }}>
            <button
              type="button"
              onClick={onClose}
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
              type="submit"
              disabled={submitting}
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
              {submitting ? 'Salvando...' : 'Confirmar Reatribuição'}
            </button>
          </div>
          {actionError && (
            <div role="alert" style={{ marginTop: '8px', fontSize: 'var(--text-xs)', color: 'var(--color-risk-critical)' }}>
              {actionError}
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

// Escalate Modal
interface EscalateModalProps {
  isOpen: boolean;
  incidentId: string | null;
  currentPriority: string;
  onClose: () => void;
  onSubmit: (id: string, newPriority: string, reason: string) => Promise<void>;
}

export const EscalateModal: React.FC<EscalateModalProps> = ({
  isOpen,
  incidentId,
  currentPriority,
  onClose,
  onSubmit,
}) => {
  const [priority, setPriority] = useState('P1');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  if (!isOpen || !incidentId) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setActionError(null);
      await onSubmit(incidentId, priority, reason);
      onClose();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Falha na operação.';
      setActionError(`Negado pela governança (${err?.response?.status ?? 'erro'}): ${msg}`);
      console.error(err);
    } finally {
      setSubmitting(false);
    }
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
        zIndex: 2100,
        padding: 'var(--space-4)',
      }}
      onClick={onClose}
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
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} color="var(--color-risk-critical)" />
            <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 'bold', color: 'var(--color-text-primary)' }}>
              Escalar Incidente {incidentId}
            </h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div>
            <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>
              Nova Criticidade / Prioridade:
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-bg-primary)',
                border: '1px solid var(--color-border-default)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--text-sm)',
              }}
            >
              <option value="P1">P1 — Crítica (Impacto Amplo em Clientes)</option>
              <option value="P2">P2 — Alta (Degradação Severa)</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>
              Motivo do Escalonamento:
            </label>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
              placeholder="Descreva o impacto de negócio e motivo do acionamento de emergência..."
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-bg-primary)',
                border: '1px solid var(--color-border-default)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--text-sm)',
                resize: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: 'var(--space-2)' }}>
            <button
              type="button"
              onClick={onClose}
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
              type="submit"
              disabled={submitting}
              style={{
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--color-risk-critical)',
                border: 'none',
                color: '#fff',
                fontSize: 'var(--text-xs)',
                fontWeight: 'bold',
                cursor: 'pointer',
              }}
            >
              {submitting ? 'Escalando...' : 'Confirmar Escalação'}
            </button>
          </div>
          {actionError && (
            <div role="alert" style={{ marginTop: '8px', fontSize: 'var(--text-xs)', color: 'var(--color-risk-critical)' }}>
              {actionError}
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

// Shortcuts Modal
interface ShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ShortcutsModal: React.FC<ShortcutsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const shortcuts = [
    { key: '1', desc: 'Alternar para Modo Operações (Triagem & Risco)' },
    { key: '2', desc: 'Alternar para Modo Gestão Tática (Forecast D+1/D+7)' },
    { key: '3', desc: 'Alternar para Modo Engenharia (Clusters & MLOps)' },
    { key: 'S', desc: 'Simular chegada de novo chamado em tempo real' },
    { key: '?', desc: 'Abrir este painel de atalhos' },
    { key: 'Esc', desc: 'Fechar qualquer modal aberto' },
  ];

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
        zIndex: 2200,
        padding: 'var(--space-4)',
      }}
      onClick={onClose}
    >
      <div
        className="glass-modal"
        style={{
          width: '100%',
          maxWidth: '480px',
          borderRadius: 'var(--radius-xl)',
          padding: 'var(--space-6)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-4)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <HelpCircle size={18} color="#60A5FA" />
            <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 'bold', color: 'var(--color-text-primary)' }}>
              Atalhos de Teclado
            </h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {shortcuts.map((s, idx) => (
            <div
              key={idx}
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
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>{s.desc}</span>
              <kbd
                style={{
                  fontFamily: 'var(--font-family-mono)',
                  fontSize: '11px',
                  fontWeight: 'bold',
                  padding: '3px 8px',
                  borderRadius: '4px',
                  background: 'var(--color-bg-elevated)',
                  color: '#60A5FA',
                  border: '1px solid var(--color-border-default)',
                }}
              >
                {s.key}
              </kbd>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Toast Notifications Container
export const ToastContainer: React.FC<{ toasts: ToastMessage[]; onDismiss: (id: string) => void }> = ({
  toasts,
  onDismiss,
}) => {
  return (
    <div
      style={{
        position: 'fixed',
        bottom: '60px',
        right: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        zIndex: 3000,
        maxWidth: '380px',
      }}
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="glass-modal"
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
            padding: '12px 16px',
            borderRadius: 'var(--radius-lg)',
            borderLeft: `4px solid ${
              toast.type === 'success'
                ? 'var(--color-risk-low)'
                : toast.type === 'error'
                ? 'var(--color-risk-critical)'
                : toast.type === 'warning'
                ? 'var(--color-risk-medium)'
                : 'var(--color-border-focus)'
            }`,
            animation: 'slideInRight 300ms ease-out',
            boxShadow: 'var(--shadow-lg)',
          }}
        >
          <div style={{ flex: 1 }}>
            <strong style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-primary)', display: 'block', marginBottom: '2px' }}>
              {toast.title}
            </strong>
            <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)', lineHeight: '1.3' }}>
              {toast.message}
            </span>
          </div>

          <button
            onClick={() => onDismiss(toast.id)}
            style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
};
