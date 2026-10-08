import React, { memo } from 'react';
import { Clock, Users, Server, Shield, ArrowUpRight, ArrowDownRight, Bot, Bell, UserCheck, Zap } from 'lucide-react';
import { Incident } from '../../types';
import { RiskBadge } from '../common/RiskBadge';
import { useAuth } from '../../context/AuthContext';

interface IncidentCardProps {
  incident: Incident;
  isSelected?: boolean;
  onSelect?: (id: string) => void;
  onDetails?: (id: string) => void;
  onAssign?: (id: string) => void;
  onEscalate?: (id: string) => void;
  onNotify?: (id: string) => void;
}

export const IncidentCard: React.FC<IncidentCardProps> = memo(({
  incident,
  isSelected = false,
  onSelect,
  onDetails,
  onAssign,
  onEscalate,
  onNotify,
}) => {
  const { hasPermission } = useAuth();
  const canAssign = hasPermission('assign');
  const canEscalate = hasPermission('escalate');

  const isCritical = incident.risk_category
    ? incident.risk_category === 'CRITICAL'
    : incident.threshold_tau != null
      ? (incident.p_calibrated ?? incident.risk_score / 100) >= incident.threshold_tau
      : incident.risk_score >= 80;
  const isSlaWarning = incident.sla_remaining_minutes > 0 && incident.sla_remaining_minutes <= 45;
  const isSlaBreached = incident.sla_remaining_minutes <= 0;

  const getPriorityBadgeStyle = (prio: string) => {
    switch (prio) {
      case 'P1': return { bg: 'rgba(239, 68, 68, 0.2)', text: 'var(--color-risk-critical)', border: 'rgba(239, 68, 68, 0.4)' };
      case 'P2': return { bg: 'rgba(249, 115, 22, 0.2)', text: 'var(--color-risk-high)', border: 'rgba(249, 115, 22, 0.4)' };
      case 'P3': return { bg: 'rgba(234, 179, 8, 0.2)', text: 'var(--color-risk-medium)', border: 'rgba(234, 179, 8, 0.4)' };
      default: return { bg: 'rgba(100, 116, 139, 0.2)', text: 'var(--color-text-secondary)', border: 'rgba(100, 116, 139, 0.4)' };
    }
  };

  const prioStyle = getPriorityBadgeStyle(incident.priority);

  // Border & shadow states
  let cardBorder = '1px solid var(--color-border-default)';
  let cardBg = 'var(--color-bg-secondary)';
  let cardAnimation = 'none';

  if (isCritical) {
    cardBorder = '1px solid rgba(220, 38, 38, 0.6)';
    cardBg = 'linear-gradient(180deg, rgba(220, 38, 38, 0.08) 0%, rgba(30, 41, 59, 1) 100%)';
    cardAnimation = 'pulseBorder 2.5s infinite';
  } else if (isSlaWarning) {
    cardAnimation = 'pulseWarning 2s infinite';
  }

  if (isSelected) {
    cardBorder = '2px solid var(--color-border-focus)';
    cardBg = 'var(--color-bg-elevated)';
  }

  return (
    <article
      onClick={() => onSelect && onSelect(incident.id)}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-3)',
        padding: 'var(--space-4)',
        background: cardBg,
        border: cardBorder,
        borderRadius: 'var(--radius-lg)',
        cursor: 'pointer',
        transition: 'transform var(--transition-fast), box-shadow var(--transition-fast), border-color var(--transition-fast)',
        position: 'relative',
        animation: cardAnimation,
      }}
      onMouseEnter={(e) => {
        if (!isSelected) {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = 'var(--shadow-md)';
          e.currentTarget.style.borderColor = 'var(--color-border-focus)';
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
          e.currentTarget.style.borderColor = isCritical ? 'rgba(220, 38, 38, 0.6)' : 'var(--color-border-default)';
        }
      }}
      role="article"
      aria-label={`Incidente ${incident.id}, Prioridade ${incident.priority}, Risco ${incident.risk_score}%, Squad ${incident.group}`}
      tabIndex={0}
    >
      {/* Header Row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--space-3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flex: 1 }}>
          <RiskBadge score={incident.risk_score} size="md" />
          {incident.risk_category && (
            <span
              title="Categoria econômica (τ* validado)"
              style={{
                fontSize: '10px',
                fontWeight: 'var(--font-weight-bold)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: incident.risk_category === 'CRITICAL'
                  ? 'rgba(220, 38, 38, 0.2)'
                  : incident.risk_category === 'WARNING'
                    ? 'rgba(202, 138, 4, 0.2)'
                    : 'rgba(22, 163, 74, 0.2)',
                color: incident.risk_category === 'CRITICAL'
                  ? 'var(--color-risk-critical)'
                  : incident.risk_category === 'WARNING'
                    ? 'var(--color-risk-medium)'
                    : 'var(--color-risk-low)',
              }}
            >
              {incident.risk_category}
              {incident.estimated_mttr_minutes != null && (
                <> · MTTR ~{incident.estimated_mttr_minutes >= 60
                  ? `${(incident.estimated_mttr_minutes / 60).toFixed(1)}h`
                  : `${Math.round(incident.estimated_mttr_minutes)}min`}</>
              )}
            </span>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span
                style={{
                  fontFamily: 'var(--font-family-mono)',
                  fontSize: 'var(--text-sm)',
                  fontWeight: 'var(--font-weight-bold)',
                  color: 'var(--color-text-primary)',
                }}
              >
                {incident.id}
              </span>

              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 'var(--font-weight-bold)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: prioStyle.bg,
                  color: prioStyle.text,
                  border: `1px solid ${prioStyle.border}`,
                }}
              >
                {incident.priority}
              </span>

              {incident.is_automated_fp && (
                <span
                  style={{
                    fontSize: '10px',
                    padding: '2px 6px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: 'rgba(59, 130, 246, 0.15)',
                    color: 'var(--color-border-focus)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                  title="Ticket automatizado sem intervenção humana (Falso Positivo identificado)"
                >
                  <Bot size={11} />
                  Falso Positivo NLP
                </span>
              )}

              {incident.status === 'in_progress' && (
                <span style={{ fontSize: '10px', color: 'var(--color-border-focus)', background: 'rgba(59, 130, 246, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                  Em Atendimento
                </span>
              )}
            </div>

            <h3
              style={{
                fontSize: 'var(--text-base)',
                fontWeight: 'var(--font-weight-semibold)',
                color: 'var(--color-text-primary)',
                lineHeight: '1.3',
              }}
            >
              {incident.title}
            </h3>
          </div>
        </div>

        {/* SLA Status Countdown */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: isSlaBreached
              ? 'rgba(220, 38, 38, 0.2)'
              : isSlaWarning
              ? 'rgba(202, 138, 4, 0.2)'
              : 'rgba(51, 65, 85, 0.5)',
            border: isSlaBreached
              ? '1px solid var(--color-sla-breach)'
              : isSlaWarning
              ? '1px solid var(--color-sla-warning)'
              : '1px solid var(--color-border-default)',
            color: isSlaBreached
              ? 'var(--color-sla-breach)'
              : isSlaWarning
              ? 'var(--color-sla-warning)'
              : 'var(--color-text-secondary)',
            fontSize: 'var(--text-xs)',
            fontWeight: 'var(--font-weight-medium)',
            whiteSpace: 'nowrap',
          }}
        >
          <Clock size={13} />
          <span>{isSlaBreached ? 'SLA VIOLADO' : incident.estimated_violation || `${incident.sla_remaining_minutes}min restantes`}</span>
        </div>
      </div>

      {/* Meta tags line */}
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Users size={13} color="var(--color-text-muted)" />
          <strong>Squad:</strong> {incident.group}
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Server size={13} color="var(--color-text-muted)" />
          <strong>Produto:</strong> {incident.product}
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Shield size={13} color="var(--color-text-muted)" />
          <strong>IC:</strong> {incident.config_item}
        </span>
      </div>

      {/* Description */}
      <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', lineHeight: '1.4' }}>
        {incident.description.length > 140 ? `${incident.description.substring(0, 140)}...` : incident.description}
      </p>

      {/* SHAP Factors Section (Top 3) */}
      {incident.shap_factors && incident.shap_factors.length > 0 && (
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.6)',
            padding: 'var(--space-2) var(--space-3)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
          }}
        >
          <span style={{ fontSize: '11px', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Principais Fatores de Risco (SHAP):
          </span>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
            {incident.shap_factors.slice(0, 3).map((factor, idx) => {
              const isPositive = factor.impact === 'positive' || factor.value > 0;
              const valFormatted = (factor.value > 0 ? `+${factor.value}` : `${factor.value}`);
              const barWidth = Math.min(100, Math.abs(factor.value) * 200);

              return (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flex: 1, minWidth: 0 }}>
                    {isPositive ? (
                      <ArrowUpRight size={13} color="var(--color-risk-critical)" />
                    ) : (
                      <ArrowDownRight size={13} color="var(--color-risk-low)" />
                    )}
                    <span style={{ color: 'var(--color-text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {factor.display_name || factor.feature}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: '110px', justifyContent: 'flex-end' }}>
                    {/* Progress indicator */}
                    <div style={{ width: '50px', height: '4px', background: 'var(--color-bg-elevated)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${barWidth}%`,
                          height: '100%',
                          backgroundColor: isPositive ? 'var(--color-risk-critical)' : 'var(--color-risk-low)',
                          borderRadius: '2px',
                        }}
                      />
                    </div>
                    <span
                      style={{
                        fontFamily: 'var(--font-family-mono)',
                        fontWeight: 'var(--font-weight-bold)',
                        color: isPositive ? 'var(--color-risk-critical)' : 'var(--color-risk-low)',
                      }}
                    >
                      {valFormatted}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Action Buttons Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: '2px',
          paddingTop: 'var(--space-2)',
          borderTop: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDetails && onDetails(incident.id);
            }}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '5px 10px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(59, 130, 246, 0.15)',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              color: 'var(--color-border-focus)',
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--font-weight-medium)',
              cursor: 'pointer',
            }}
            aria-label={`Ver explicabilidade SHAP para ${incident.id}`}
          >
            <Zap size={13} />
            Explicabilidade (SHAP)
          </button>

          {canAssign && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAssign && onAssign(incident.id);
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '5px 10px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border-default)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--text-xs)',
                fontWeight: 'var(--font-weight-medium)',
                cursor: 'pointer',
              }}
              aria-label={`Reatribuir incidente ${incident.id}`}
            >
              <UserCheck size={13} />
              Atribuir
            </button>
          )}

          {canEscalate && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEscalate && onEscalate(incident.id);
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '5px 10px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border-default)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--text-xs)',
                fontWeight: 'var(--font-weight-medium)',
                cursor: 'pointer',
              }}
              aria-label={`Escalar incidente ${incident.id}`}
            >
              Escalar
            </button>
          )}

          <button
            onClick={(e) => {
              e.stopPropagation();
              onNotify && onNotify(incident.id);
            }}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '5px 10px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--color-bg-elevated)',
              border: '1px solid var(--color-border-default)',
              color: 'var(--color-text-secondary)',
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--font-weight-medium)',
              cursor: 'pointer',
            }}
            title="Notificar NOC / Squad"
            aria-label={`Notificar equipe sobre ${incident.id}`}
          >
            <Bell size={13} />
          </button>
        </div>

        <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
          {new Date(incident.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </article>
  );
});
