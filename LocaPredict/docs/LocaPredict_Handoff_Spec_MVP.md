# LocaPredict SLA Guard v3 — Handoff Specification MVP

> **Documento de Handoff para Desenvolvedores**
> Versão: 1.0 | Data: 25/08/2026 (planejamento histórico)
> Status: Substituído onde conflitar com a implementação remediada (Constituição v1.1.0, 2026-09-24).
> Stack vigente: React 18 + Vite (sem Streamlit) + FastAPI + RF + TF-IDF + shap.TreeExplainer + HDBSCAN-validação + KS com Holm. Verdade vigente: código-fonte + `specs/001-locapredict-sla-guard/`.

---

## Sumário

1. [Design Tokens](#1-design-tokens)
2. [Layout do Dashboard](#2-layout-do-dashboard)
3. [Componentes](#3-componentes)
4. [Interações e Animações](#4-interações-e-animações)
5. [Regras de Conteúdo](#5-regras-de-conteúdo)
6. [Assets](#6-assets)
7. [Edge Cases](#7-edge-cases)
8. [Acessibilidade](#8-acessibilidade)
9. [Integrações com API](#9-integrações-com-api)
10. [Performance](#10-performance)

---

## 1. Design Tokens

### 1.1 Cores

```
// Paleta Primária
--color-risk-critical: #DC2626    // Risco ≥80% (vermelho)
--color-risk-high: #EA580C        // Risco 60-79% (laranja)
--color-risk-medium: #CA8A04      // Risco 40-59% (amarelo)
--color-risk-low: #16A34A         // Risco 20-39% (verde)
--color-risk-minimal: #22C55E     // Risco <20% (verde claro)

// Regime Operacional
--color-regime-normal: #16A34A
--color-regime-stress: #CA8A04
--color-regime-saturation: #EA580C
--color-regime-crisis: #DC2626
--color-regime-recovery: #2563EB

// Superfícies
--color-bg-primary: #0F172A       // Fundo principal (slate-900)
--color-bg-secondary: #1E293B     // Cards laterais (slate-800)
--color-bg-elevated: #334155      // Cards elevados (slate-700)
--color-bg-hover: #475569         // Hover states (slate-600)

// Texto
--color-text-primary: #F8FAFC     // Texto principal (slate-50)
--color-text-secondary: #94A3B8   // Texto secundário (slate-400)
--color-text-muted: #64748B       // Texto desabilitado (slate-500)

// Bordas
--color-border-default: #334155   // Bordas padrão (slate-700)
--color-border-focus: #3B82F6     // Foco azul (blue-500)

// Status SLA
--color-sla-ok: #16A34A
--color-sla-warning: #CA8A04
--color-sla-breach: #DC2626
```

### 1.2 Tipografia

```
// Fonte Principal
--font-family-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif

// Escala de Tamanhos
--text-xs: 0.75rem    // 12px — labels auxiliares
--text-sm: 0.875rem   // 14px — corpo secundário
--text-base: 1rem     // 16px — corpo padrão
--text-lg: 1.125rem   // 18px — títulos menores
--text-xl: 1.25rem    // 20px — títulos de seção
--text-2xl: 1.5rem    // 24px — títulos de card
--text-3xl: 1.875rem  // 30px — KPIs grandes
--text-4xl: 2.25rem   // 36px — KPIs hero

// Pesos
--font-weight-normal: 400
--font-weight-medium: 500
--font-weight-semibold: 600
--font-weight-bold: 700

// Line Heights
--leading-tight: 1.25
--leading-normal: 1.5
--leading-relaxed: 1.75
```

### 1.3 Espaçamento

```
// Escala base: 4px
--space-1: 0.25rem   // 4px
--space-2: 0.5rem    // 8px
--space-3: 0.75rem   // 12px
--space-4: 1rem      // 16px
--space-5: 1.25rem   // 20px
--space-6: 1.5rem    // 24px
--space-8: 2rem      // 32px
--space-10: 2.5rem   // 40px
--space-12: 3rem     // 48px

// Bordas e Arredondamento
--radius-sm: 0.25rem   // 4px
--radius-md: 0.5rem    // 8px
--radius-lg: 0.75rem   // 12px
--radius-xl: 1rem      // 16px
--radius-full: 9999px  // Circular

// Sombras
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3)
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4)
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.5)
--shadow-glow-risk: 0 0 20px rgba(220, 38, 38, 0.3)  // Glow crítico
```

---

## 2. Layout do Dashboard

### 2.1 Estrutura Principal

```
┌──────────────────────────────────────────────────────────────┐
│ Header (h: 64px)                                            │
│ [Logo] [LocaPredict SLA Guard]  [Modo: Operacional ▼] [⚙] │
├──────────────┬───────────────────────────────────────────────┤
│              │                                               │
│  Sidebar     │  Main Content Area                           │
│  (w: 320px)  │  (flex: 1)                                   │
│              │                                               │
│  [Filtros]   │  ┌─────────┬─────────┬─────────┬─────────┐  │
│  [Filtros]   │  │ KPI 1   │ KPI 2   │ KPI 3   │ KPI 4   │  │
│  [Filtros]   │  └─────────┴─────────┴─────────┴─────────┘  │
│              │                                               │
│  [Ações]     │  ┌────────────────────┬────────────────────┐ │
│              │  │ Forecast Chart     │ Regime Indicator   │ │
│              │  │                    │                    │ │
│              │  └────────────────────┴────────────────────┘ │
│              │                                               │
│              │  ┌──────────────────────────────────────────┐ │
│              │  │ Incident Cards List                      │ │
│              │  │ ┌──────────────────────────────────────┐ │ │
│              │  │ │ IncidentCard                         │ │ │
│              │  │ └──────────────────────────────────────┘ │ │
│              │  │ ┌──────────────────────────────────────┐ │ │
│              │  │ │ IncidentCard                         │ │ │
│              │  │ └──────────────────────────────────────┘ │ │
│              │  └──────────────────────────────────────────┘ │
│              │                                               │
├──────────────┴───────────────────────────────────────────────┤
│ Footer (h: 48px)  [Status: Atualizado há 2min] [v3.0.0]   │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Breakpoints

| Breakpoint | Largura | Comportamento |
|------------|---------|----------------|
| Mobile     | < 768px | Sidebar colapsa, cards empilham verticalmente |
| Tablet     | 768-1024px | Sidebar recolhível (64px), 2 colunas de KPIs |
| Desktop    | > 1024px | Layout completo, 4 colunas de KPIs |

### 2.3 Grid Responsivo

```css
/* Container Principal */
.dashboard {
  display: grid;
  grid-template-columns: 320px 1fr;
  grid-template-rows: 64px 1fr 48px;
  height: 100vh;
}

/* KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
}

@media (max-width: 1024px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .dashboard { grid-template-columns: 1fr; }
  .sidebar { display: none; }
  .kpi-grid { grid-template-columns: 1fr; }
}
```

---

## 3. Componentes

### 3.1 DashboardLayout

**Props:**
```typescript
interface DashboardLayoutProps {
  mode: 'operations' | 'tactical' | 'engineering';
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
}
```

**Especificações:**
- Altura total: `100vh`
- Header: `h: 64px`, `bg: --color-bg-secondary`, `border-bottom: 1px solid --color-border-default`
- Sidebar: `w: 320px`, `bg: --color-bg-secondary`, `overflow-y: auto`
- Main: `flex: 1`, `bg: --color-bg-primary`, `padding: --space-6`
- Footer: `h: 48px`, `bg: --color-bg-secondary`, `border-top: 1px solid --color-border-default`

**Modos:**
| Modo | Sidebar | KPIs Visíveis | Ações Disponíveis |
|------|---------|---------------|-------------------|
| Operacional | Filtros + Triagem | Todos | Atribuir, Escalar, Notificar |
| Tático | Filtros + Análise | Volume + Previsão | Exportar, Agendar Revisão |
| Engenharia | Filtros + Debug | Todos | Retreinar, Depurar SHAP |

---

### 3.2 IncidentCard

**Props:**
```typescript
interface IncidentCardProps {
  id: string;
  title: string;
  category: string;
  priority: 'P1' | 'P2' | 'P3' | 'P4';
  riskScore: number;          // 0-100
  slaDeadline: string;        // ISO timestamp
  slaRemaining: number;       // minutos
  cluster?: string;
  shapFactors: SHAPFactor[];
  status: 'open' | 'in_progress' | 'escalated';
  onAssign?: (id: string) => void;
  onEscalate?: (id: string) => void;
  onClick?: (id: string) => void;
}

interface SHAPFactor {
  feature: string;
  value: number;
  impact: 'positive' | 'negative';
}
```

**Especificações Visuais:**
```
┌──────────────────────────────────────────────────────────────┐
│ ┌─────┐                                                     │
│ │ 87% │  INC-2026-084721                                    │
│ │ 🔴  │  Timeout na fila de processamento                   │
│ └─────┘  P1 • Infraestrutura • SLA: 2h 15min restantes    │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Fatores SHAP:                                            │ │
│ │ ████████████ crítico (0.42)                              │ │
│ │ ████████     file_size (0.28)                            │ │
│ │ ████         horário_pico (0.15)                         │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ [Atribuir]  [Escalar]  [Notificar]                          │
└──────────────────────────────────────────────────────────────┘
```

**Espaçamento:**
- Padding interno: `--space-4` (16px)
- Gap entre elementos: `--space-3` (12px)
- Gap entre botões: `--space-2` (8px)
- Margem entre cards: `--space-4` (16px)

**Tipografia:**
- Título: `--text-lg`, `font-weight: --font-weight-semibold`
- Subtítulo: `--text-sm`, `color: --color-text-secondary`
- Badge KPI: `--text-xs`, `font-weight: --font-weight-bold`

**Bordas e Sombras:**
- Border: `1px solid --color-border-default`
- Border-radius: `--radius-lg`
- Shadow: `--shadow-sm`
- Hover: `shadow: --shadow-md`, `border-color: --color-border-focus`

**Estados:**
| Estado | Visual |
|--------|--------|
| Default | Bordas neutras, fundo --color-bg-secondary |
| Hover | Sombra elevada, borda azul |
| Selected | Borda azul sólida, fundo --color-bg-elevated |
| SLA Warning (<30min) | Borda amarela pulsante |
| SLA Breach | Borda vermelha, badge "ATRASADO" |

---

### 3.3 RiskBadge

**Props:**
```typescript
interface RiskBadgeProps {
  score: number;        // 0-100
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showLabel?: boolean;
  animated?: boolean;
}
```

**Especificações Visuais:**
```
Tamanhos:
- sm: 32x32px (sidebar)
- md: 48x48px (card)
- lg: 64x64px (destaque)
- xl: 96x96px (dashboard hero)

Cores por Faixa:
- < 20%: --color-risk-minimal (verde claro)
- 20-39%: --color-risk-low (verde)
- 40-59%: --color-risk-medium (amarelo)
- 60-79%: --color-risk-high (laranja)
- ≥ 80%: --color-risk-critical (vermelho)

Anel de Progresso:
- Stroke-width: 4px (sm/md), 6px (lg/xl)
- Background: --color-bg-elevated
- Progresso: cor do risco
- Stroke-linecap: round
```

**Animações:**
- Entrada: `scale-in` de 0.8 para 1, duração 300ms, ease-out
- Risco ≥80%: `pulse` infinito, duração 2s, opacity alterna 0.7-1.0
- Mudança de cor: `transition: all 500ms ease-in-out`

---

### 3.4 ForecastChart

**Props:**
```typescript
interface ForecastChartProps {
  historical: DataPoint[];
  forecast: DataPoint[];
  confidenceInterval: [number, number][];
  horizon: 'D+1' | 'D+7';
  onHorizonChange?: (h: 'D+1' | 'D+7') => void;
}

interface DataPoint {
  timestamp: string;
  value: number;
}
```

**Especificações Visuais:**
```
┌──────────────────────────────────────────────────────────────┐
│ Previsão de Volume                    [D+1] [D+7]           │
├──────────────────────────────────────────────────────────────┤
│  120 ┤                                                       │
│      │                    ┌─────────────────────            │
│  100 ┤           ╱╲      ╱│  Intervalo de Confiança        │
│      │         ╱  ╲    ╱  │  (preenchimento semi-transparente)
│   80 ┤───────╱────╲──╱────┼───────────────────             │
│      │     ╱       ╲╱     │                                │
│   60 ┤   ╱                 │  ── Previsão                   │
│      │ ╱                   │  ── Histórico                  │
│   40 ┤                     │                                │
│      └─────┬─────┬─────┬──┴─────┬─────┬─────┬─────         │
│          Seg   Ter   Qua   Qui   Sex   Sáb   Dom           │
└──────────────────────────────────────────────────────────────┘
```

**Espaçamento:**
- Padding do container: `--space-6`
- Margem do gráfico: `--space-4` por lado
- Gap entre título e toggle: `--space-4`

**Cores:**
- Linha histórica: `--color-text-primary`, stroke-width: 2px
- Linha de previsão: `--color-regime-stress`, stroke-width: 2px, stroke-dasharray: 8 4
- Intervalo de confiança: `--color-regime-stress` com opacity 0.2
- Grid: `--color-border-default` com opacity 0.3
- Labels: `--color-text-secondary`, `--text-xs`

**Interatividade:**
- Hover: Tooltip com valor exato, fundo --color-bg-elevated
- Toggle D+1/D+7: Tabs com indicador de underline animado
- Zoom: Scroll do mouse (mínimo 7 dias, máximo 30 dias)

---

### 3.5 OperationalRegimeIndicator

**Props:**
```typescript
interface OperationalRegimeProps {
  regime: 'normal' | 'stress' | 'saturation' | 'crisis' | 'recovery';
  confidence: number;         // 0-1
  transitionFrom?: string;    // regime anterior (para animação)
  showDetails?: boolean;
}
```

**Especificações Visuais:**
```
┌─────────────────────────────────────┐
│ Regime Operacional                  │
│ ┌─────────────────────────────────┐ │
│ │         🟡                      │ │
│ │       ESTRESSE                  │ │
│ │    Confiança: 87%              │ │
│ │                                 │ │
│ │ Tendência: ↑ piorando          │ │
│ │ Última mudança: há 45min       │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘

Cores por Regime:
- Normal: --color-regime-normal, ícone ● verde
- Estresse: --color-regime-stress, ícone ● amarelo
- Saturação: --color-regime-saturation, ícone ● laranja
- Crise: --color-regime-crisis, ícone ● vermelho
- Recuperação: --color-regime-recovery, ícone ● azul
```

**Animações:**
- Transição entre regimes: `background-color 800ms ease-in-out`
- Ícone: `rotate 360ms` na mudança
- Badge "Crise": `pulse 1.5s infinite` + `box-shadow glow vermelho`

---

### 3.6 SHAPWaterfall

**Props:**
```typescript
interface SHAPWaterfallProps {
  factors: SHAPFactor[];
  baseValue: number;
  prediction: number;
  maxFactors?: number;        // default: 8
  onFactorClick?: (factor: SHAPFactor) => void;
}

interface SHAPFactor {
  feature: string;
  value: number;
  impact: 'positive' | 'negative';
  displayName?: string;
}
```

**Especificações Visuais:**
```
┌──────────────────────────────────────────────────────────────┐
│ Fatores de Impacto (SHAP)                                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Base: 45%          ───────●──────                          │
│                                                              │
│ crítico             ████████████████↗ +22%                  │
│ file_size           ██████████↗ +14%                        │
│ horário_pico        ██████↗ +8%                             │
│ fila_tamanho        ████↗ +5%                               │
│ ───────────────────────────────────────────────────────────  │
│ species_rocha       ███↘ -4%                                │
│ ───────────────────────────────────────────────────────────  │
│                                                              │
│ Predição: 87%         ───────●──────                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Espaçamento:**
- Altura da barra: 24px
- Gap entre barras: `--space-2`
- Padding interno: `--space-4`
- Largura mínima da barra: 8px (para fatores com impacto baixo)

**Cores:**
- Impacto positivo: `--color-risk-critical` (vermelho)
- Impacto negativo: `--color-risk-low` (verde)
- Base/predição: `--color-text-primary`
- Labels: `--color-text-secondary`
- Valor: `--color-text-primary`, `font-weight: --font-weight-bold`

**Interatividade:**
- Hover na barra: Tooltip com valor exato e descrição do feature
- Click: Abre modal com detalhes do feature (tipo, distribuição, exemplos)

---

### 3.7 ClusterPanel

**Props:**
```typescript
interface ClusterPanelProps {
  clusters: Cluster[];
  selectedCluster?: string;
  onClusterSelect?: (id: string) => void;
}

interface Cluster {
  id: string;
  name: string;           // Nome NLP gerado
  count: number;
  avgRisk: number;
  topFeatures: string[];
  trend: 'growing' | 'stable' | 'declining';
}
```

**Especificações Visuais:**
```
┌──────────────────────────────────────────────────────────────┐
│ Clusters Ativos (5)                                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ 🔴 Timeout de fila (12 incidents) ↑ crescendo         │  │
│ │    Risco médio: 78% • P1: 5 • P2: 7                  │  │
│ │    Top: crítico, file_size, fila_tamanho               │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ 🟡 Lentidão frontend (8 incidents) → estável          │  │
│ │    Risco médio: 52% • P2: 3 • P3: 5                  │  │
│ │    Top: latency, bundle_size, user_agent               │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Espaçamento:**
- Gap entre clusters: `--space-3`
- Padding interno do card: `--space-4`
- Gap entre elementos internos: `--space-2`

**Cores por Trend:**
- Crescendo: `--color-risk-high` com ícone ↑
- Estável: `--color-risk-medium` com ícone →
- Declinando: `--color-risk-low` com ícone ↓

---

## 4. Interações e Animações

### 4.1 Transições Globais

```css
/* Transição padrão */
--transition-fast: 150ms ease-in-out;
--transition-normal: 300ms ease-in-out;
--transition-slow: 500ms ease-in-out;

/* Propriedades */
transition: background-color var(--transition-fast),
            border-color var(--transition-fast),
            box-shadow var(--transition-fast),
            transform var(--transition-normal),
            opacity var(--transition-normal);
```

### 4.2 Micro-interações

| Elemento | Trigger | Animação | Duração |
|----------|---------|----------|---------|
| IncidentCard | Hover | translateY(-2px) + shadow-elevated | 200ms |
| IncidentCard | Click | scale(0.98) | 100ms |
| RiskBadge | Mudança de valor | stroke-dashoffset animado | 800ms |
| RiskBadge | Crise (≥80%) | pulse infinito | 2000ms |
| ForecastChart | Troca D+1/D+7 | Fade out/in | 300ms |
| Botão | Hover | bg lighten 10% | 150ms |
| Botão | Click | scale(0.95) | 100ms |
| Sidebar | Toggle | width 320px ↔ 64px | 300ms |
| Toast | Entrada | slideInRight + fade | 400ms |
| Toast | Saída | slideOutRight + fade | 300ms |

### 4.3 Loading States

```
Skeleton Loading:
- Cor: --color-bg-elevated com shimmer animation
- Shimmer: gradiente linear de --color-bg-elevated para --color-bg-hover
- Animação: translateX de -100% para 100%, duração 1.5s, infinite
- Formato: retângulos arredondados que espelham a estrutura do componente
```

### 4.4 Keyboard Navigation

| Tecla | Ação |
|-------|------|
| Tab | Move foco entre elementos interativos |
| Shift+Tab | Move foco para trás |
| Enter/Space | Ativa botão ou link selecionado |
| Escape | Fecha modais, cancela ação |
| Arrow keys | Navega entre cards na lista |
| ? | Abre overlay de atalhos |

---

## 5. Regras de Conteúdo

### 5.1 Limites de Caracteres

| Elemento | Limite | Comportamento |
|----------|--------|---------------|
| Título do incidente | 80 chars | Truncamento com ellipsis |
| Descrição SHAP | 40 chars | Truncamento com ellipsis |
| Nome do cluster | 60 chars | Truncamento com ellipsis |
| KPI value | 6 dígitos | Formatação compacta (1.2k, 3.4M) |
| SLA remaining | — | Formato: "Xh Ymin" ou "Ymin" |

### 5.2 Formatação de Dados

```typescript
// Formatação de números
const formatNumber = (n: number): string => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toString();
};

// Formatação de SLA
const formatSLA = (minutes: number): string => {
  if (minutes < 60) return `${minutes}min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}min` : `${h}h`;
};

// Formatação de risco
const formatRisk = (score: number): string => `${score}%`;
```

### 5.3 Estados de Conteúdo

| Estado | Mensagem | Ação |
|--------|----------|------|
| Vazio (sem incidentes) | "Nenhum incidente ativo no momento" | Botão "Atualizar" |
| Loading | Skeleton shimmer | — |
| Erro | "Erro ao carregar dados. Tente novamente." | Botão "Retry" |
| Sem resultado de busca | "Nenhum incidente encontrado para os filtros aplicados" | Botão "Limpar Filtros" |

### 5.4 Localização

- **Idioma padrão:** pt-BR
- **Formatação de datas:** DD/MM/YYYY HH:mm
- **Formatação de moeda:** R$ X.XXX,XX
- **Separador decimal:** vírgula
- **Textos expansão:** +30% espaço reservado para tradução

---

## 6. Assets

### 6.1 Ícones

| Nome | Caminho | Uso |
|------|---------|-----|
| `icon-logo.svg` | `/assets/icons/` | Logo LocaPredict |
| `icon-risk-critical.svg` | `/assets/icons/status/` | Risco crítico |
| `icon-risk-high.svg` | `/assets/icons/status/` | Risco alto |
| `icon-risk-medium.svg` | `/assets/icons/status/` | Risco médio |
| `icon-risk-low.svg` | `/assets/icons/status/` | Risco baixo |
| `icon-escalate.svg` | `/assets/icons/actions/` | Botão escalar |
| `icon-assign.svg` | `/assets/icons/actions/` | Botão atribuir |
| `icon-notify.svg` | `/assets/icons/actions/` | Botão notificar |
| `icon-settings.svg` | `/assets/icons/` | Configurações |
| `icon-filter.svg` | `/assets/icons/` | Filtros |
| `icon-refresh.svg` | `/assets/icons/` | Atualizar |

**Especificações de Ícones:**
- Formato: SVG inline (currentColor)
- Tamanho padrão: 20x20px
- Tamanho sm: 16x16px
- Tamanho lg: 24x24px
- Cor: herda do pai via `currentColor`

### 6.2 Fontes

```css
/* Inter - Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Fallback */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### 6.3 Imagens

| Asset | Resolução | Formato | Uso |
|-------|-----------|---------|-----|
| `bg-pattern.svg` | — | SVG | Fundo decorativo (opcional) |
| `empty-state.svg` | 240x240px | SVG | Estado vazio |

---

## 7. Edge Cases

### 7.1 Conteúdo Mínimo/Máximo

| Cenário | Comportamento |
|---------|---------------|
| 0 incidentes | Card vazio com estado de空 |
| 1 incidente | Card único sem scroll |
| 50+ incidentes | Scroll virtualizado (virtualized list) |
| Título muito longo | Truncamento com ellipsis + tooltip completo |
| SHAP com 0 fatores | Mensagem "Sem fatores de impacto disponíveis" |
| Risco = 0% ou 100% | Badge com cor sólida, sem gradiente |
| SLA negativo (atrasado) | Badge "ATRASADO" com cor vermelha + ícone ⚠ |

### 7.2 Comportamento Responsivo

| Breakpoint | Sidebar | KPIs | Cards | Gráfico |
|------------|---------|------|-------|---------|
| < 768px | Oculta (toggle) | 1 coluna | Empilhados | Mini (sem hover) |
| 768-1024px | Recolhível (64px) | 2 colunas | 2 por linha | Médio |
| > 1024px | Completa (320px) | 4 colunas | Lista | Completo |

### 7.3 Browser/Device

| Browser | Versão Mínima | Notas |
|---------|---------------|-------|
| Chrome | 90+ | Suporte completo |
| Firefox | 88+ | Suporte completo |
| Safari | 14+ | Testar WebKit animations |
| Edge | 90+ | Suporte completo |
| IE 11 | — | Não suportado |

**Mobile:**
- iOS Safari 14+
- Android Chrome 90+
- Touch: min 44x44px para alvos de toque

### 7.4 Acessibilidade

| Requisito | Implementação |
|-----------|---------------|
| Contraste de cores | WCAG AA (4.5:1 para texto, 3:1 para UI) |
| Navegação por teclado | Tab order lógico, focus visible |
| Screen reader | Labels ARIA em todos os componentes interativos |
| Redução de movimento | `prefers-reduced-motion` desativa animações |
| Zoom do navegador | Até 200% sem quebra de layout |

**Exemplos ARIA:**
```html
<!-- RiskBadge -->
<div role="status" aria-label="Risco: 87%, Crítico">
  <span aria-hidden="true">87%</span>
</div>

<!-- IncidentCard -->
<article aria-labelledby="incident-84721-title" tabindex="0">
  <h3 id="incident-84721-title">Timeout na fila</h3>
</article>

<!-- ForecastChart -->
<div role="img" aria-label="Previsão de volume para os próximos 7 dias">
  <svg>...</svg>
</div>
```

---

## 8. Integrações com API

### 8.1 Endpoints MVP

| Método | Endpoint | Uso | Frequência |
|--------|----------|-----|------------|
| GET | `/api/v1/incidents` | Lista de incidentes | Polling 30s |
| GET | `/api/v1/incidents/{id}` | Detalhes do incidente | On-demand |
| GET | `/api/v1/forecast` | Previsão D+1/D+7 | Polling 5min |
| GET | `/api/v1/regime` | Regime operacional | Polling 1min |
| GET | `/api/v1/clusters` | Clusters com validação HDBSCAN medida + proveniência | Polling 5min |
| POST | `/api/v1/incidents/{id}/assign` | Atribuir incidente | On-demand |
| POST | `/api/v1/incidents/{id}/escalate` | Escalar incidente | On-demand |

### 8.2 Estruturas de Dados

```typescript
// Incidente
interface Incident {
  id: string;
  title: string;
  description: string;
  category: string;
  priority: 'P1' | 'P2' | 'P3' | 'P4';
  status: 'open' | 'in_progress' | 'escalated' | 'resolved';
  risk_score: number;
  sla_deadline: string;         // ISO 8601
  sla_remaining_minutes: number;
  cluster_id?: string;
  shap_factors: SHAPFactor[];
  created_at: string;
  updated_at: string;
}

// Previsão
interface Forecast {
  historical: DataPoint[];
  predicted: DataPoint[];
  confidence_lower: number[];
  confidence_upper: number[];
  horizon: 'D+1' | 'D+7';
  generated_at: string;
}

// Regime
interface Regime {
  current: 'normal' | 'stress' | 'saturation' | 'crisis' | 'recovery';
  confidence: number;
  previous?: string;
  changed_at: string;
  trend: 'improving' | 'stable' | 'worsening';
}

// Cluster
interface Cluster {
  id: string;
  name: string;
  incident_count: number;
  avg_risk_score: number;
  top_features: string[];
  trend: 'growing' | 'stable' | 'declining';
  incident_ids: string[];
}
```

### 8.3 Tratamento de Erros

```typescript
// Error States
interface APIError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// Retry Logic
const retryConfig = {
  maxRetries: 3,
  backoff: 'exponential',
  initialDelay: 1000,
  maxDelay: 30000,
};

// Error UI
if (error.code === 'NETWORK_ERROR') {
  show toast 'Sem conexão. Tentando novamente...'
} else if (error.code === 'TIMEOUT') {
  show toast 'Servidor sem resposta. Tente novamente.'
} else {
  show toast 'Erro inesperado. Contate o suporte.'
}
```

---

## 9. Performance

### 9.1 Métricas Alvo

| Métrica | Alvo | Medição |
|---------|------|---------|
| First Contentful Paint | < 1.5s | Lighthouse |
| Largest Contentful Paint | < 2.5s | Lighthouse |
| Time to Interactive | < 3.5s | Lighthouse |
| Total Bundle Size | < 500KB | Webpack bundle analyzer |
| TTI (Time to Interactive) | < 3s | Performance API |

### 9.2 Otimizações

| Técnica | Aplicação |
|---------|-----------|
| Code splitting | Lazy load de SHAPWaterfall e ForecastChart |
| Memoização | React.memo em IncidentCard |
| Virtualização | Lista de incidentes (react-window) |
| Debounce | Filtros (300ms) |
| Throttle | Polling de dados (mínimo 30s) |
| Cache | Service Worker para assets estáticos |
| Imagem | SVG inline, sem bitmap |

### 9.3 Bundle Size Estimado

```
Bundle Principal:
- React + ReactDOM: ~130KB
- Chart.js / Recharts: ~80KB
- Custom components: ~90KB
- Total: ~300KB (gzipped: ~100KB)
- (Streamlit removido: frontend vigente é React 18 + Vite + Nginx.)
```

---

## 10. Checklist de Implementação

### 10.1 Pré-Implementação

- [ ] Setup do projeto (React + TypeScript + Vite)
- [ ] Instalação de dependências
- [ ] Configuração de Design Tokens
- [ ] Setup de ESLint + Prettier
- [ ] Configuração de testes (Jest + React Testing Library)

### 10.2 Componentes

- [ ] DashboardLayout
- [ ] Header
- [ ] Sidebar
- [ ] KPI Cards
- [ ] IncidentCard
- [ ] RiskBadge
- [ ] ForecastChart
- [ ] OperationalRegimeIndicator
- [ ] SHAPWaterfall
- [ ] ClusterPanel
- [ ] Toast/Notifications
- [ ] Modal de confirmação

### 10.3 Integração

- [ ] Serviço de API (axios/fetch)
- [ ] Hook useIncidents
- [ ] Hook useForecast
- [ ] Hook useRegime
- [ ] Hook useClusters
- [ ] WebSocket para updates em tempo real
- [ ] Error boundary

### 10.4 Testes

- [ ] Testes unitários dos componentes
- [ ] Testes de integração
- [ ] Testes de acessibilidade (axe-core)
- [ ] Testes visuais (Storybook)
- [ ] Testes de performance (Lighthouse)

### 10.5 Documentação

- [ ] Storybook com todos os componentes
- [ ] README com setup instructions
- [ ] Guia de contribuição
- [ ] Changelog

---

## Apêndice A: Referências

- [Design Tokens Spec](./design-tokens.md)
- [Component Specs](./LocaPredict_Component_Specs.md)
- [API Documentation](./api-docs.md) (futuro)
- [Storybook](./storybook-url) (futuro)

---

**Documento preparado para handoff de desenvolvimento.**
**Versão: 1.0 | Data: 25/08/2026**
