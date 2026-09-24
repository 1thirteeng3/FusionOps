import React, { useState } from 'react';
import { Download, AlertTriangle, TrendingUp, Calendar, Layers, Check } from 'lucide-react';
import { Forecast } from '../../types';

interface ForecastChartProps {
  forecast: Forecast | null;
  horizon: 'D+1' | 'D+7';
  onHorizonChange: (h: 'D+1' | 'D+7') => void;
  onExportCsv?: () => void;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  forecast,
  horizon,
  onHorizonChange,
  onExportCsv,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<{ label: string; value: number; type: 'hist' | 'pred'; lower?: number; upper?: number } | null>(null);
  const [selectedGroup, setSelectedGroup] = useState<string>('all');
  const [selectedProduct, setSelectedProduct] = useState<string>('all');

  if (!forecast) {
    return (
      <div className="glass-panel" style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
        Carregando projeções de séries temporais...
      </div>
    );
  }

  // Combine historical and predicted for plotting
  const histData = forecast.historical || [];
  const predData = forecast.predicted || [];

  // Chart dimensions & scaling
  const chartWidth = 720;
  const chartHeight = 280;
  const padding = { top: 30, right: 30, bottom: 40, left: 45 };
  const plotWidth = chartWidth - padding.left - padding.right;
  const plotHeight = chartHeight - padding.top - padding.bottom;

  // Compute domain
  const allValues = [
    ...histData.map((d) => d.value),
    ...predData.map((d) => d.value),
    ...forecast.confidence_upper,
    forecast.capacity_threshold,
  ];
  const minY = Math.floor(Math.min(...allValues) / 20) * 20 - 10;
  const maxY = Math.ceil(Math.max(...allValues) / 20) * 20 + 20;

  const totalPoints = histData.length + predData.length - 1; // Anchor overlap

  const getX = (index: number) => padding.left + (index / totalPoints) * plotWidth;
  const getY = (val: number) => padding.top + plotHeight - ((val - minY) / (maxY - minY)) * plotHeight;

  // Build Historical SVG path
  let histPath = '';
  histData.forEach((d, i) => {
    const x = getX(i);
    const y = getY(d.value);
    histPath += i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  });

  // Build Predicted SVG path (starts from last historical point)
  const lastHistIndex = histData.length - 1;
  const lastHistVal = histData[lastHistIndex]?.value || 90;
  let predPath = `M ${getX(lastHistIndex)} ${getY(lastHistVal)}`;
  predData.forEach((d, i) => {
    const x = getX(lastHistIndex + 1 + i);
    const y = getY(d.value);
    predPath += ` L ${x} ${y}`;
  });

  // Build Confidence Interval Area Path
  let confAreaPath = `M ${getX(lastHistIndex)} ${getY(lastHistVal)}`;
  // Top curve
  predData.forEach((_, i) => {
    const x = getX(lastHistIndex + 1 + i);
    const yUpper = getY(forecast.confidence_upper[i] || 100);
    confAreaPath += ` L ${x} ${yUpper}`;
  });
  // Bottom curve in reverse
  for (let i = predData.length - 1; i >= 0; i--) {
    const x = getX(lastHistIndex + 1 + i);
    const yLower = getY(forecast.confidence_lower[i] || 50);
    confAreaPath += ` L ${x} ${yLower}`;
  }
  confAreaPath += ` L ${getX(lastHistIndex)} ${getY(lastHistVal)} Z`;

  const capacityY = getY(forecast.capacity_threshold);

  return (
    <div
      className="glass-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-4)',
        padding: 'var(--space-5)',
      }}
    >
      {/* Header with Title and Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-text-primary)' }}>
              Previsão de Demanda Operacional (P2 / P3)
            </h3>
            <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: 'rgba(202, 138, 4, 0.15)', color: '#FBBF24', border: '1px solid rgba(202, 138, 4, 0.3)' }}>
              WAPE holdout: {forecast.wape_holdout != null ? (forecast.wape_holdout * 100).toFixed(1) + '%' : forecast.wape_accuracy + '% ref'} (baseline {forecast.wape_baseline != null ? (forecast.wape_baseline * 100).toFixed(1) + '%' : '—'})
            </span>
          </div>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
            {forecast.model_id ?? 'weekly-seasonal-fitted-v1'} ajustado • Backtest walk-forward{forecast.dm_pvalue != null ? ` • DM p=${forecast.dm_pvalue}` : ''} • IC 95%
          </span>
        </div>

        {/* Controls: D+1 / D+7 Toggle & Export */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          {/* Horizon Tabs */}
          <div style={{ display: 'flex', background: 'var(--color-bg-primary)', padding: '2px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border-default)' }}>
            <button
              onClick={() => onHorizonChange('D+1')}
              style={{
                padding: '4px 12px',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: horizon === 'D+1' ? 'var(--color-border-focus)' : 'transparent',
                color: horizon === 'D+1' ? '#fff' : 'var(--color-text-secondary)',
                fontSize: 'var(--text-xs)',
                fontWeight: 'var(--font-weight-semibold)',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
              }}
            >
              D+1 (24h)
            </button>
            <button
              onClick={() => onHorizonChange('D+7')}
              style={{
                padding: '4px 12px',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                background: horizon === 'D+7' ? 'var(--color-border-focus)' : 'transparent',
                color: horizon === 'D+7' ? '#fff' : 'var(--color-text-secondary)',
                fontSize: 'var(--text-xs)',
                fontWeight: 'var(--font-weight-semibold)',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
              }}
            >
              D+7 (Semanal)
            </button>
          </div>

          {onExportCsv && (
            <button
              onClick={onExportCsv}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border-default)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--text-xs)',
                cursor: 'pointer',
              }}
              title="Exportar dados de previsão em CSV"
            >
              <Download size={13} />
              Exportar
            </button>
          )}
        </div>
      </div>

      {/* SVG Interactive Time Series Chart */}
      <div style={{ position: 'relative', width: '100%', overflowX: 'auto' }}>
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          style={{ width: '100%', height: 'auto', minWidth: '600px' }}
          role="img"
          aria-label={`Gráfico de previsão de chamados para ${horizon}`}
        >
          <defs>
            <linearGradient id="forecastGlow" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="var(--color-regime-stress)" stopOpacity="0.35" />
              <stop offset="100%" stopColor="var(--color-regime-stress)" stopOpacity="0.05" />
            </linearGradient>
          </defs>

          {/* Grid lines & Y-Axis labels */}
          {[minY, (minY + maxY) / 2, maxY].map((val, idx) => {
            const y = getY(val);
            return (
              <g key={idx}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={chartWidth - padding.right}
                  y2={y}
                  stroke="var(--color-border-default)"
                  strokeOpacity="0.4"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  fill="var(--color-text-muted)"
                  fontSize="10"
                  textAnchor="end"
                  fontFamily="var(--font-family-mono)"
                >
                  {Math.round(val)}
                </text>
              </g>
            );
          })}

          {/* Capacity Threshold Line */}
          <line
            x1={padding.left}
            y1={capacityY}
            x2={chartWidth - padding.right}
            y2={capacityY}
            stroke="var(--color-risk-critical)"
            strokeWidth="1.5"
            strokeDasharray="6 4"
            opacity="0.85"
          />
          <text
            x={chartWidth - padding.right}
            y={capacityY - 6}
            fill="var(--color-risk-critical)"
            fontSize="10"
            fontWeight="bold"
            textAnchor="end"
          >
            Limiar de Capacidade: {forecast.capacity_threshold}/dia
          </text>

          {/* Confidence Interval Semi-transparent Area */}
          <path d={confAreaPath} fill="url(#forecastGlow)" />

          {/* Historical Series Path */}
          <path
            d={histPath}
            fill="none"
            stroke="var(--color-text-primary)"
            strokeWidth="2.2"
            strokeLinecap="round"
          />

          {/* Predicted Series Path */}
          <path
            d={predPath}
            fill="none"
            stroke="var(--color-regime-stress)"
            strokeWidth="2.2"
            strokeDasharray="6 4"
            strokeLinecap="round"
          />

          {/* Historical Data Points */}
          {histData.map((d, i) => {
            const x = getX(i);
            const y = getY(d.value);
            const isToday = i === lastHistIndex;

            return (
              <circle
                key={`hist-${i}`}
                cx={x}
                cy={y}
                r={isToday ? 5 : 3.5}
                fill={isToday ? 'var(--color-border-focus)' : 'var(--color-text-primary)'}
                stroke="var(--color-bg-primary)"
                strokeWidth="1.5"
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredPoint({ label: d.label, value: d.value, type: 'hist' })}
                onMouseLeave={() => setHoveredPoint(null)}
              />
            );
          })}

          {/* Predicted Data Points */}
          {predData.map((d, i) => {
            const x = getX(lastHistIndex + 1 + i);
            const y = getY(d.value);
            const isPeak = d.value === forecast.peak_value;

            return (
              <circle
                key={`pred-${i}`}
                cx={x}
                cy={y}
                r={isPeak ? 6 : 4}
                fill={isPeak ? 'var(--color-risk-critical)' : 'var(--color-regime-stress)'}
                stroke="var(--color-bg-primary)"
                strokeWidth="1.5"
                style={{ cursor: 'pointer' }}
                onMouseEnter={() =>
                  setHoveredPoint({
                    label: d.label,
                    value: d.value,
                    type: 'pred',
                    lower: forecast.confidence_lower[i],
                    upper: forecast.confidence_upper[i],
                  })
                }
                onMouseLeave={() => setHoveredPoint(null)}
              />
            );
          })}

          {/* X-Axis labels */}
          {histData.filter((_, i) => i % 3 === 0).map((d, i) => {
            const actualIndex = i * 3;
            const x = getX(actualIndex);
            return (
              <text
                key={`xlabel-hist-${i}`}
                x={x}
                y={chartHeight - 12}
                fill="var(--color-text-secondary)"
                fontSize="10"
                textAnchor="middle"
              >
                {d.label}
              </text>
            );
          })}

          {predData.map((d, i) => {
            const x = getX(lastHistIndex + 1 + i);
            return (
              <text
                key={`xlabel-pred-${i}`}
                x={x}
                y={chartHeight - 12}
                fill="var(--color-regime-stress)"
                fontSize="10"
                fontWeight="600"
                textAnchor="middle"
              >
                {d.label}
              </text>
            );
          })}
        </svg>

        {/* Tooltip Hover Overlay */}
        {hoveredPoint && (
          <div
            className="glass-modal"
            style={{
              position: 'absolute',
              top: '10px',
              right: '20px',
              padding: '8px 12px',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--text-xs)',
              pointerEvents: 'none',
            }}
          >
            <div style={{ fontWeight: 'bold', color: 'var(--color-text-primary)' }}>{hoveredPoint.label}</div>
            <div style={{ color: hoveredPoint.type === 'pred' ? 'var(--color-regime-stress)' : 'var(--color-text-primary)' }}>
              Volume: <strong>{hoveredPoint.value} incidentes</strong>
            </div>
            {hoveredPoint.lower !== undefined && hoveredPoint.upper !== undefined && (
              <div style={{ color: 'var(--color-text-muted)', fontSize: '10px' }}>
                95% IC: [{hoveredPoint.lower} - {hoveredPoint.upper}]
              </div>
            )}
          </div>
        )}
      </div>

      {/* Chart Legend */}
      <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '16px', height: '2.5px', backgroundColor: 'var(--color-text-primary)' }} />
          Histórico Real
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '16px', height: '2.5px', backgroundColor: 'var(--color-regime-stress)', borderTop: '2px dashed var(--color-regime-stress)' }} />
          Previsão {forecast.model_id ?? 'Ajustada'}
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '14px', height: '10px', backgroundColor: 'rgba(202, 138, 4, 0.25)', borderRadius: '2px' }} />
          Intervalo de Confiança 95%
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '16px', height: '2px', backgroundColor: 'var(--color-risk-critical)' }} />
          Capacidade Squads ({forecast.capacity_threshold}/dia)
        </span>
      </div>

      {/* Insight Summary Banner */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 'var(--space-3)',
          background: forecast.is_over_capacity ? 'rgba(220, 38, 38, 0.12)' : 'rgba(22, 163, 74, 0.12)',
          border: `1px solid ${forecast.is_over_capacity ? 'rgba(220, 38, 38, 0.35)' : 'rgba(22, 163, 74, 0.35)'}`,
          padding: 'var(--space-3) var(--space-4)',
          borderRadius: 'var(--radius-lg)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp size={18} color="var(--color-regime-stress)" />
          <div>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'block' }}>Pico Previsto de Demanda</span>
            <strong style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-primary)' }}>
              {forecast.peak_value} chamados em {forecast.peak_date}
            </strong>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={18} color={forecast.is_over_capacity ? 'var(--color-risk-critical)' : 'var(--color-risk-low)'} />
          <div>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'block' }}>Balanço de Capacidade</span>
            <strong style={{ fontSize: 'var(--text-sm)', color: forecast.is_over_capacity ? 'var(--color-risk-critical)' : 'var(--color-risk-low)' }}>
              {forecast.is_over_capacity ? 'Risco de Saturação (+27% acima do limiar)' : 'Capacidade Adequada'}
            </strong>
          </div>
        </div>
      </div>
    </div>
  );
};
