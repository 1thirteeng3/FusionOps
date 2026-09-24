import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by ErrorBoundary:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            height: '100vh',
            width: '100vw',
            backgroundColor: 'var(--color-bg-primary)',
            color: 'var(--color-text-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--space-6)',
          }}
        >
          <div
            className="glass-modal"
            style={{
              maxWidth: '520px',
              width: '100%',
              padding: 'var(--space-8)',
              borderRadius: 'var(--radius-xl)',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 'var(--space-4)',
              border: '1px solid rgba(220, 38, 38, 0.4)',
            }}
          >
            <div
              style={{
                width: '56px',
                height: '56px',
                borderRadius: '50%',
                backgroundColor: 'rgba(220, 38, 38, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-risk-critical)',
              }}
            >
              <AlertTriangle size={32} />
            </div>

            <h2 style={{ fontSize: 'var(--text-xl)', fontWeight: 'bold' }}>
              Ocorreu um erro na interface do LocaPredict
            </h2>

            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', lineHeight: '1.5' }}>
              {this.state.error?.message || 'Falha inesperada na renderização de componentes.'}
            </p>

            <button
              onClick={() => window.location.reload()}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-border-focus)',
                border: 'none',
                color: '#fff',
                fontSize: 'var(--text-sm)',
                fontWeight: 'bold',
                cursor: 'pointer',
                marginTop: 'var(--space-2)',
              }}
            >
              <RefreshCw size={16} />
              Recarregar Aplicação
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
