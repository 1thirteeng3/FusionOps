import React, { useState } from 'react';
import { Users, BarChart3, AlertCircle, ArrowUpRight, CheckCircle, Calendar, ShieldCheck, Download } from 'lucide-react';
import { Forecast } from '../../types';
import { ForecastChart } from './ForecastChart';

interface TacticalViewProps {
  forecast: Forecast | null;
  horizon: 'D+1' | 'D+7';
  onHorizonChange: (h: 'D+1' | 'D+7') => void;
  onExportCsv: () => void;
}

export const TacticalView: React.FC<TacticalViewProps> = ({
  forecast,
  horizon,
  onHorizonChange,
  onExportCsv,
}) => {
  const [selectedSquad, setSelectedSquad] = useState<string>('all');

  // Demanda projetada por squad, medida do breakdown do forecast (sem teto
  // nominal por squad medido: percentuais de saturação não são afirmados).
  const groupPeaks = forecast?.breakdown_by_group
    ? Object.entries(forecast.breakdown_by_group).map(([name, pts]) => ({
        name,
        peak: Math.max(...pts.map((p) => p.value), 0),
      }))
    : [];
  const totalPeak = groupPeaks.reduce((s, g) => s + g.peak, 0);
  const d1Volume = forecast?.predicted?.[0]?.value;
  const demandSum = forecast?.predicted?.reduce((s, p) => s + p.value, 0) ?? 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', animation: 'fadeIn 300ms ease-out' }}>
      {/* Strategic KPI Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 'var(--space-4)',
        }}
      >
        <div className="glass-panel" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Previsão Volume D+1 (24h)
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: 'var(--text-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
              {d1Volume != null ? Math.round(d1Volume) : '—'}
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-risk-medium)', display: 'flex', alignItems: 'center' }}>
              <ArrowUpRight size={13} /> {forecast?.model_id ?? 'modelo ajustado'}
            </span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Projeção para próximo turno</span>
        </div>

        <div className="glass-panel" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Pico Semanal D+7
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: 'var(--text-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-risk-critical)' }}>
              {forecast?.peak_value ?? '—'}
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-risk-critical)', display: 'flex', alignItems: 'center' }}>
              em {forecast?.peak_date ?? '—'}
            </span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Alerta de capacidade ativa</span>
        </div>

        <div className="glass-panel" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Acurácia do Modelo (WAPE)
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: 'var(--text-3xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-risk-low)' }}>
              {forecast?.wape_accuracy ?? '—'}{forecast?.wape_accuracy != null ? '%' : ''}
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-risk-low)' }}>
              (WAPE holdout {forecast?.wape_holdout != null ? (forecast.wape_holdout * 100).toFixed(1) + '%' : '—'} &lt; 15%)
            </span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Backtest walk-forward • {forecast?.model_id ?? 'weekly-seasonal-fitted-v1'}</span>
        </div>

        <div className="glass-panel" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Demanda Projetada ({horizon})
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span style={{ fontSize: 'var(--text-3xl)', fontWeight: 'var(--font-weight-bold)', color: '#60A5FA' }}>
              {forecast ? Math.round(demandSum) : '—'}
            </span>
            <span style={{ fontSize: 'var(--text-xs)', color: '#60A5FA' }}>
              chamados no horizonte
            </span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Soma da curva projetada • {forecast?.model_id ?? 'modelo ajustado'}</span>
        </div>
      </div>

      {/* Main Forecast Chart */}
      <ForecastChart
        forecast={forecast}
        horizon={horizon}
        onHorizonChange={onHorizonChange}
        onExportCsv={onExportCsv}
      />

      {/* Capacity & Squad Workload Matrix */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: 'var(--space-5)',
        }}
      >
        {/* Squad Saturation Matrix */}
        <div className="glass-panel" style={{ padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h4 style={{ fontSize: 'var(--text-base)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
                Matriz de Capacidade por Squad
              </h4>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
                Balanço de tickets ativos vs limite operacional
              </span>
            </div>
            <Users size={18} color="var(--color-text-muted)" />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {groupPeaks.length === 0 && (
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
                Sem breakdown por squad (forecast indisponível).
              </span>
            )}
            {groupPeaks.map((squad, idx) => {
              const share = totalPeak > 0 ? (squad.peak / totalPeak) * 100 : 0;
              const isOver = share > 50;
              const isWarning = share > 20 && share <= 50;
              const barColor = isOver ? 'var(--color-risk-critical)' : isWarning ? 'var(--color-risk-medium)' : 'var(--color-risk-low)';

              return (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)' }}>
                    <span style={{ fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)' }}>
                      {squad.name}
                    </span>
                    <span style={{ fontFamily: 'var(--font-family-mono)', color: barColor, fontWeight: 'bold' }}>
                      pico {Math.round(squad.peak)}/dia ({share.toFixed(1)}% da demanda)
                    </span>
                  </div>

                  <div style={{ width: '100%', height: '8px', background: 'var(--color-bg-primary)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${Math.min(100, share)}%`,
                        height: '100%',
                        backgroundColor: barColor,
                        borderRadius: '4px',
                        transition: 'width 600ms ease-out',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
            Participação na demanda projetada — teto nominal por squad não medido; percentuais de saturação não são afirmados.
          </span>
        </div>

        {/* Capacity Planning & Shift Recommendation */}
        <div className="glass-panel" style={{ padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h4 style={{ fontSize: 'var(--text-base)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
                Recomendações Táticas de Alocação
              </h4>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
                Ações prescritivas baseadas no Forecast D+7
              </span>
            </div>
            <ShieldCheck size={18} color="var(--color-regime-recovery)" />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', fontSize: 'var(--text-xs)' }}>
            <div style={{ padding: 'var(--space-3)', background: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.3)', borderRadius: 'var(--radius-md)' }}>
                <strong style={{ color: 'var(--color-risk-critical)', display: 'block', marginBottom: '2px' }}>
                1. Reforço de Plantão na Squad Dominante
              </strong>
              <span style={{ color: 'var(--color-text-secondary)' }}>
                O pico de {forecast?.peak_value ?? '—'} chamados em {forecast?.peak_date ?? '—'} concentra-se na squad de maior participação acima. Recomenda-se remanejar analistas de squads ociosas antes do pico.
              </span>
            </div>

            <div style={{ padding: 'var(--space-3)', background: 'rgba(202, 138, 4, 0.1)', border: '1px solid rgba(202, 138, 4, 0.3)', borderRadius: 'var(--radius-md)' }}>
              <strong style={{ color: 'var(--color-risk-medium)', display: 'block', marginBottom: '2px' }}>
                2. Janela Preventiva de Triagem NOC
              </strong>
              <span style={{ color: 'var(--color-text-secondary)' }}>
                Ativar fila dedicada para surtos de DNS e Apache Busy Workers nos horários de pico observados no histórico para conter chamados de baixo impacto.
              </span>
            </div>

            <div style={{ padding: 'var(--space-3)', background: 'rgba(22, 163, 74, 0.1)', border: '1px solid rgba(22, 163, 74, 0.3)', borderRadius: 'var(--radius-md)' }}>
              <strong style={{ color: 'var(--color-risk-low)', display: 'block', marginBottom: '2px' }}>
                3. Otimização em Banco de Dados MySQL
              </strong>
              <span style={{ color: 'var(--color-text-secondary)' }}>
                Squads com menor participação na demanda projetada podem absorver triagens técnicas transversais — verificar disponibilidade no turno.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
