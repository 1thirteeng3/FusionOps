import React from 'react';

interface RiskBadgeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showLabel?: boolean;
  animated?: boolean;
}

export const getRiskColor = (score: number): string => {
  if (score >= 80) return 'var(--color-risk-critical)';
  if (score >= 60) return 'var(--color-risk-high)';
  if (score >= 40) return 'var(--color-risk-medium)';
  if (score >= 20) return 'var(--color-risk-low)';
  return 'var(--color-risk-minimal)';
};

export const getRiskSeverity = (score: number): string => {
  if (score >= 80) return 'Crítico';
  if (score >= 60) return 'Alto';
  if (score >= 40) return 'Médio';
  if (score >= 20) return 'Baixo';
  return 'Mínimo';
};

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  score,
  size = 'md',
  showLabel = false,
  animated = true,
}) => {
  const sizeMap = {
    sm: { dimension: 34, stroke: 3.5, font: '0.75rem', radius: 13 },
    md: { dimension: 48, stroke: 4.5, font: '0.875rem', radius: 18 },
    lg: { dimension: 64, stroke: 5.5, font: '1.125rem', radius: 24 },
    xl: { dimension: 96, stroke: 7.0, font: '1.5rem', radius: 36 },
  };

  const config = sizeMap[size];
  const color = getRiskColor(score);
  const isCritical = score >= 80;
  
  // Circumference calculation
  const circumference = 2 * Math.PI * config.radius;
  const strokeDashoffset = circumference - (Math.min(100, Math.max(0, score)) / 100) * circumference;

  return (
    <div
      style={{
        display: 'inline-flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
      }}
      role="meter"
      aria-valuenow={score}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Score de Risco OLA: ${score}%, Nível ${getRiskSeverity(score)}`}
      title={`Risco OLA: ${score}% (${getRiskSeverity(score)})`}
    >
      <div
        style={{
          position: 'relative',
          width: `${config.dimension}px`,
          height: `${config.dimension}px`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          animation: animated && isCritical ? 'pulseRisk 2s infinite ease-in-out' : 'none',
          boxShadow: isCritical && size !== 'sm' ? 'var(--shadow-glow-risk)' : 'none',
          borderRadius: '50%',
        }}
      >
        <svg
          width={config.dimension}
          height={config.dimension}
          viewBox={`0 0 ${config.dimension} ${config.dimension}`}
          style={{ transform: 'rotate(-90deg)', overflow: 'visible' }}
        >
          {/* Background track */}
          <circle
            cx={config.dimension / 2}
            cy={config.dimension / 2}
            r={config.radius}
            fill="none"
            stroke="var(--color-bg-elevated)"
            strokeWidth={config.stroke}
          />
          {/* Active progress stroke */}
          <circle
            cx={config.dimension / 2}
            cy={config.dimension / 2}
            r={config.radius}
            fill="none"
            stroke={color}
            strokeWidth={config.stroke}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              transition: animated ? 'stroke-dashoffset 800ms ease-out, stroke 400ms ease' : 'none',
            }}
          />
        </svg>

        {/* Center score percentage */}
        <span
          style={{
            position: 'absolute',
            fontSize: config.font,
            fontWeight: 'var(--font-weight-bold)',
            color: 'var(--color-text-primary)',
            fontFamily: 'var(--font-family-primary)',
            letterSpacing: '-0.02em',
          }}
        >
          {score}%
        </span>
      </div>

      {showLabel && (
        <span
          style={{
            marginTop: '4px',
            fontSize: 'var(--text-xs)',
            fontWeight: 'var(--font-weight-medium)',
            color: color,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          {getRiskSeverity(score)}
        </span>
      )}
    </div>
  );
};
