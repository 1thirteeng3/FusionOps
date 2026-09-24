# Component Specifications — LocaPredict SLA Guard v3 MVP

> **AVISO DE CONFORMIDADE — Constituição v1.1.0 (2026-09-24).** Artefato
> histórico de planejamento, **substituído** onde conflitar com a
> implementação: Random Forest + calibração isotônica com validação honesta
> (sem ressubstituição); `shap.TreeExplainer` verificado (sem pesos fixos);
> forecaster sazonal ajustado com backtest (sem Prophet/senóide); clusters com
> validação HDBSCAN medida (sem HDBSCAN declarado); frontend React 18 + Vite
> (sem Streamlit); sem MLflow/Evidently/LightGBM; ganhos −38,5%/−21,4% são
> projeções. Verdade vigente: código-fonte + `specs/001-locapredict-sla-guard/`.

Baseado no: `LocaPredict_SLA_Guard_v3_Reestruturado.md`
Stack: React 18 + Vite + FastAPI + scikit-learn (RF + TF-IDF) + shap.TreeExplainer + HDBSCAN (validação) + SciPy KS

---

## 1. DashboardLayout

### Overview

| Campo | Valor |
| --- | --- |
| **Nome** | `DashboardLayout` |
| **Descrição** | Container principal que organiza os três modos de visualização do dashboard (Operação, Gestão Tática, Engenharia) com sidebar de navegação e header de status do sistema. |
| **Usar quando** | Abrir o dashboard, alternar entre modos de visualização, acessar filtros globais. |
| **Não usar quando** | Dentro de um componente específico — usar sub-componentes internos. |

### Anatomy

```
┌─────────────────────────────────────────────────────────────────┐
│ Header: Logo + Título + RegimeOperacionalIndicator + Relógio   │
├────────────┬────────────────────────────────────────────────────┤
│            │                                                    │
│  Sidebar   │  ContentArea                                       │
│  (filtros  │  (renderiza conforme modo selecionado)             │
│   + nav)   │                                                    │
│            │                                                    │
│  ┌───────┐ │  ┌──────────────────────────────────────────────┐  │
│  │ 🔍    │ │  │                                              │  │
│  │ Filtros│ │  │  Conteúdo do modo selecionado               │  │
│  │        │ │  │  (Cards de Incidentes / Forecast / SHAP)    │  │
│  │ ────── │ │  │                                              │  │
│  │ 📊    │ │  │                                              │  │
│  │ Modos  │ │  └──────────────────────────────────────────────┘  │
│  │        │ │                                                    │
│  └───────┘ │                                                    │
├────────────┴────────────────────────────────────────────────────┤
│ Footer: Status da API + Última atualização + DriftIndicator    │
└─────────────────────────────────────────────────────────────────┘
```

**Elementos obrigatórios:**
- `Header` — barra superior com logo, título, regime operacional e relógio
- `Sidebar` — painel esquerdo com filtros globais e modos de visualização
- `ContentArea` — área principal de renderização
- `Footer` — barra inferior com status do sistema

**Elementos opcionais:**
- `NotificationBanner` — alertas de drift ou regime crítico
- `QuickActions` — botões de ação rápida (exportar, refresh)

### Variants

| Variant | Uso |
| --- | --- |
| `operations` | Modo focado em triagem de incidentes e score de risco |
| `tactical` | Modo focado em forecasting, capacity planning e heatmaps |
| `engineering` | Modo focado em clusters técnicos, NLP e análise de causa raiz |

### Props/API

| Nome | Tipo | Default | Obrigatório | Descrição |
| --- | --- | --- | --- | --- |
| `activeMode` | `'operations' \| 'tactical' \| 'engineering'` | `'operations'` | Não | Modo de visualização ativo |
| `onModeChange` | `(mode: string) => void` | — | Não | Callback ao trocar modo |
| `operationalRegime` | `'normal' \| 'stress' \| 'crisis' \| 'recovery'` | `'normal'` | Sim | Regime operacional atual |
| `filters` | `FilterState` | `{}` | Não | Filtros globais ativos |
| `onFilterChange` | `(filters: FilterState) => void` | — | Não | Callback ao alterar filtros |
| `lastUpdate` | `Date` | — | Sim | Timestamp da última atualização dos dados |
| `apiStatus` | `'healthy' \| 'degraded' \| 'down'` | `'healthy'` | Sim | Status da API FastAPI |

### States

| Estado | Aparência | Comportamento |
| --- | --- | --- |
| `default` | Layout completo com sidebar e content area | Navegação livre entre modos |
| `loading` | Skeleton no content area; sidebar funcional | Dados carregando da API |
| `error` | Banner de erro no content area; botão retry | API indisponível ou dados corrompidos |
| `crisis-mode` | Header e footer com borda vermelha pulsante | Regime de crise ativo — alerta visual permanente |
| `compact` | Sidebar oculta; apenas content area | Para telas < 1024px ou modo fullscreen |

### Behavior

- **Modos de visualização:** Toggle entre os três modos preserva filtros ativos. Cada modo renderiza um conjunto diferente de componentes no ContentArea.
- **Filtros globais:** Disponíveis na Sidebar — data range, prioridade (P2/P3), grupo designado, produto. Filtros são aplicados a todos os componentes do modo atual.
- **Regime operacional:** Quando regime muda para `crisis`, um `NotificationBanner` aparece no topo com animação de pulso. Banner persiste até regime voltar para `normal`.
- **Auto-refresh:** Dados são atualizados automaticamente a cada 5 minutos (configurável). Indicador visual no footer mostra "Última atualização: HH:MM".
- **Edge case — dados indisponíveis:** Se a API retornar erro, mostrar placeholder com mensagem amigável e botão de retry. Manter último estado válido em cache por 15 minutos.

### Accessibility

- `role="application"` no container principal
- Header: `role="banner"`, `aria-label="LocaPredict SLA Guard — Painel de controle"`
- Sidebar: `role="navigation"`, `aria-label="Filtros e navegação"`
- ContentArea: `role="main"`, `aria-live="polite"` para atualizações
- Footer: `role="contentinfo"`, `aria-label="Status do sistema"`
- Modos: `role="tablist"` no seletor; cada modo: `role="tab"`, `aria-selected`
- Screen reader anuncia: "Dashboard LocaPredict SLA Guard. Modo: Operações. Regime: Normal. 42 tickets ativos."

### Usage Guidelines

**Do:**
- Manter sidebar colapsável para maximizar espaço do content area
- Mostrar indicador visual quando dados estão sendo atualizados
- Preservar estado dos filtros ao trocar de modo

**Don't:**
- Não esconder o regime operacional — sempre visível no header
- Não permitir mais de 3 modos de visualização (sobrecarga cognitiva)
- Não auto-ocultar o sidebar sem feedback visual de onde ele foi

---

## 2. IncidentCard

### Overview

| Campo | Valor |
| --- | --- |
| **Nome** | `IncidentCard` |
| **Descrição** | Card individual que representa um incidente na fila de triagem. Exibe número do ticket, prioridade, grupo, descrição, score de risco OLA e principais fatores SHAP. |
| **Usar quando** | Visualizar, priorizar e tomar decisão sobre um incidente específico na fila de triagem. |
| **Não usar quando** | Para visualização consolidada (usar MetricsCard) ou forecast (usar ForecastChart). |

### Anatomy

```
┌─────────────────────────────────────────────────────────────┐
│ [RiskBadge: 89%]  INC92341                    [⏱️ 2h 14min] │
├─────────────────────────────────────────────────────────────┤
│ Prioridade: P2 — Alta          Grupo: Team14               │
│ Produto: Hosting Linux         IC: IC00001                 │
├─────────────────────────────────────────────────────────────┤
│ Descrição: Apache Busy Workers — servidor web9.locaweb...  │
├─────────────────────────────────────────────────────────────┤
│ ⚠️ Fatores de Risco (SHAP verificado — valores ilustrativos antigos removidos; │
│ o modal exibe atribuições shap.TreeExplainer com base, versão e fidelidade):│
├─────────────────────────────────────────────────────────────┤
│ [👁️ Detalhes] [🔄 Reatribuir] [📈 Histórico]  Aberto: 14:32│
└─────────────────────────────────────────────────────────────┘
```

**Elementos obrigatórios:**
- `RiskBadge` — badge com score de risco OLA (0-100%)
- `TicketHeader` — número do ticket + tempo estimado de violação
- `TicketMeta` — prioridade, grupo, produto, IC
- `Description` — descrição truncada do incidente
- `SHAPFactors` — top 3 fatores de risco com contribution values
- `ActionBar` — botões de ação + timestamp de abertura

**Elementos opcionais:**
- `SimilarityBadge` — indicador de tickets similares históricos
- `ClusterTag` — tag do cluster ao qual pertence
- `DriftWarning` — aviso se modelo está com drift para essa feature

### Variants

| Variant | Uso |
| --- | --- |
| `default` | Card padrão na fila de triagem |
| `expanded` | Card expandido mostrando SHAP completo e histórico |
| `compact` | Versão comprimida para listas grandes (sem SHAP) |
| `highlighted` | Card com borda dourada — ticket selecionado pelo usuário |
| `critical` | Card com fundo vermelho claro — risco > 85% |

### Props/API

| Nome | Tipo | Default | Obrigatório | Descrição |
| --- | --- | --- | --- | --- |
| `ticketId` | `string` | — | Sim | Número do ticket (ex: INC92341) |
| `priority` | `1 \| 2 \| 3 \| 4` | — | Sim | Prioridade do incidente (1=Crítica, 4=Baixa) |
| `riskScore` | `number` (0-100) | — | Sim | Score de risco OLA em percentual |
| `group` | `string` | — | Sim | Grupo designado |
| `product` | `string` | — | Sim | Produto afetado |
| `configItem` | `string` | — | Sim | Item de configuração |
| `description` | `string` | — | Sim | Descrição do incidente |
| `createdAt` | `Date` | — | Sim | Data/hora de abertura |
| `estimatedViolation` | `string \| null` | `null` | Não | Tempo estimado até violação (ex: "2h 14min") |
| `shapFactors` | `SHAPFactor[]` | `[]` | Sim | Top fatores de risco com contribution |
| `similarTickets` | `string[]` | `[]` | Não | IDs de tickets similares históricos |
| `clusterId` | `string \| null` | `null` | Não | ID do cluster ao qual pertence |
| `isSelected` | `boolean` | `false` | Não | Se card está selecionado |
| `onSelect` | `(ticketId: string) => void` | — | Não | Callback ao selecionar card |
| `onDetails` | `(ticketId: string) => void` | — | Não | Callback ao clicar "Detalhes" |
| `onReassign` | `(ticketId: string) => void` | — | Não | Callback ao clicar "Reatribuir" |
| `onHistory` | `(ticketId: string) => void` | — | Não | Callback ao clicar "Histórico" |

### States

| Estado | Aparência | Comportamento |
| --- | --- | --- |
| `default` | Card com borda cinza clara, fundo branco | Clique seleciona; hover eleva sombra |
| `hover` | Sombra aumenta; borda fica azul clara | Cursor pointer |
| `selected` | Borda azul sólida 2px; fundo azul muito claro | Card destacado na lista |
| `critical` | Borda vermelha; fundo vermelho 5% opacity; RiskBadge pulsando | Alerta visual para risco > 85% |
| `loading` | Skeleton com 5 linhas pulsantes | Dados carregando |
| `dragging` | Card com sombra projetada; opacidade 80% | Durante drag-and-drop (futuro) |

### Behavior

- **Seleção:** Clique único seleciona o card e abre painel de detalhes à direita (futuro). Shift+click permite seleção múltipla.
- **Expansão:** Duplo-clique expande o card mostrando SHAP completo com gráfico waterfall e histórico de tickets similares.
- **Ações:** Botões na ActionBar disparam callbacks para o pai. "Reatribuir" abre modal de seleção de grupo. "Histórico" abre modal com timeline do ticket.
- **Truncamento de descrição:** Descrições > 120 caracteres são truncadas com "..." e tooltip completo no hover.
- **SHAP Factors:** Cada fator mostra: nome do feature, contribution value (+/-), e ícone de direção (↑ para positivo, ↓ para negativo).
- **Edge case — sem SHAP:** Se `shapFactors` estiver vazio, mostrar "Explicação indisponível — modelo sem dados suficientes".
- **Edge case — risco > 85%:** Card entra em estado `critical` com RiskBadge animado e borda vermelha pulsante.

### Accessibility

- `role="article"` no card
- `aria-label`: "Incidente INC92341, Prioridade P2, Risco 89%, Grupo Team14"
- RiskBadge: `role="meter"`, `aria-valuenow="89"`, `aria-valuemin="0"`, `aria-valuemax="100"`, `aria-label="Risco de violação OLA: 89 por cento"`
- SHAPFactors: `role="list"`, cada fator: `role="listitem"`, `aria-label="Backlog do grupo, contribuição positiva 0.34"`
- Navegação: `Tab` entre cards; `Enter` seleciona; `Space` expande; `Shift+Tab` volta
- Screen reader announce: "Incidente INC92341 selecionado. Risco 89 por cento. Principais fatores: backlog do grupo, horário crítico, reincidência técnica."

### Usage Guidelines

**Do:**
- Manter RiskBadge sempre visível — é o elemento mais importante para triagem
- Mostrar SHAP factors mesmo quando risco é baixo (transparência)
- Usar cores consistentes para prioridade: P1=vermelho, P2=laranja, P3=amarelo, P4=cinza

**Don't:**
- Não ocultar SHAP factors — é diferencial competitivo do produto
- Não usar mais de 3 SHAP factors no card (usar "ver mais" para completos)
- Não permitir scroll horizontal no card — conteúdo deve quebrar linha

---

## 3. RiskBadge

### Overview

| Campo | Valor |
| --- | --- |
| **Nome** | `RiskBadge` |
| **Descrição** | Badge circular que indica visualmente o nível de risco de violação OLA de um incidente. Combina cor, número e animação para comunicação rápida. |
| **Usar quando** | Sempre que for necessário comunicar o score de risco de um incidente (cards, tabelas, detalhes). |
| **Não usar quando** | Para indicadores que não são scores de risco (usar StatusBadge genérico). |

### Anatomy

```
    ┌─────────┐
   ╱   89%    ╲
  │  ████████  │   ← Anel de progresso (cor muda conforme risco)
  │  ████████  │
   ╲          ╱
    └─────────┘
```

**Elementos obrigatórios:**
- `ProgressRing` — anel circular que preenche conforme o score
- `ScoreText` — número central (0-100%)
- `ColorMapping` — cor muda automaticamente por faixa de risco

**Elementos opcionais:**
- `PulseAnimation` — animação de pulso para risco crítico
- `Tooltip` — detalhes do cálculo no hover

### Variants

| Variant | Tamanho | Uso |
| --- | --- | --- |
| `sm` | 32x32px | Inline em tabelas e listas compactas |
| `md` | 48x48px | Padrão em IncidentCards |
| `lg` | 64x64px | Em painéis de detalhes e dashboards executivos |
| `xl` | 96x96px | Em visões de overview eRelatórios |

### Props/API

| Nome | Tipo | Default | Obrigatório | Descrição |
| --- | --- | --- | --- | --- |
| `score` | `number` (0-100) | — | Sim | Score de risco em percentual |
| `size` | `'sm' \| 'md' \| 'lg' \| 'xl'` | `'md'` | Não | Tamanho do badge |
| `animated` | `boolean` | `true` | Não | Se deve animar mudanças de valor |
| `showLabel` | `boolean` | `true` | Não | Se deve mostrar label "Risco" abaixo |
| `onHover` | `(score: number) => void` | — | Não | Callback ao hover (para tooltip externo) |

### States

| Estado | Aparência | Comportamento |
| --- | --- | --- |
| `low` (0-39%) | Cor verde (#22C55E); anel 39% preenchido | Estático |
| `medium` (40-69%) | Cor amarela (#EAB308); anel 69% preenchido | Estático |
| `high` (70-84%) | Cor laranja (#F97316); anel 84% preenchido | Estático |
| `critical` (85-100%) | Cor vermelha (#EF4444); anel 100% preenchido | Animação de pulso contínuo |
| `loading` | Cor cinza (#9CA3AF); anel girando | Indeterminate spinner |

### Behavior

- **Transições de cor:** Ao mudar de faixa, a cor transiciona suavemente (200ms ease-in-out).
- **Animação de pulso:** Em estado `critical`, o anel pulsa (scale 1.0 → 1.05 → 1.0) a cada 1.5 segundos.
- **Tooltip no hover:** Ao hover, mostra tooltip com risco calibrado (`round(100·p_calibrada)`) e os 5 maiores fatores do `shap.TreeExplainer` com base, versão e fidelidade (pesos fixos banidos).
- **Anel de progresso:** O preenchimento do anel é proporcional ao score (0% = vazio, 100% = completo).
- **Edge case — score null/undefined:** Mostrar badge cinza com "—" no centro.

### Accessibility

- `role="meter"`, `aria-valuenow` com o score, `aria-valuemin="0"`, `aria-valuemax="100"`
- `aria-label`: "Risco de violação OLA: 89 por cento"
- Cores atendem WCAG 2.1 AA para contraste (verde #22C55E em fundo branco = 4.5:1)
- Animação de pulso pode ser desativada via `prefers-reduced-motion`
- Screen reader: "Badge de risco. 89 por cento. Nível crítico."

### Usage Guidelines

**Do:**
- Usar sempre que precisar comunicar score de risco — é o elemento visual mais importante
- Manter tamanhos consistentes dentro de um contexto (todos `md` em cards, todos `sm` em tabelas)
- Permitir desativar animação para usuários com preferência `prefers-reduced-motion`

**Don't:**
- Não usar cores inconsistentes (verde sempre = baixo, vermelho sempre = crítico)
- Não colocar RiskBadge em locais onde o score não é o foco principal
- Não usar animação de pulso em mais de 3 badges simultâneos (sobrecarga visual)

---

## 4. ForecastChart

### Overview

| Campo | Valor |
| --- | --- |
| **Nome** | `ForecastChart` |
| **Descrição** | Gráfico de série temporal que mostra a previsão de volume de incidentes para D+1 e D+7, com intervalo de confiança e histórico recente. |
| **Usar quando** | Visualizar tendência de demanda, planejar capacity, antecipar picos. |
| **Não usar quando** | Para análise de um ticket individual (usar IncidentCard) ou SHAP (usar SHAPWaterfall). |

### Anatomy

```
┌─────────────────────────────────────────────────────────────┐
│ Forecast de Volume — P2/P3                    [D+1] [D+7]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Vol.  │                                                     │
│  120 ──┤                     ╭─────╮                        │
│        │                    ╱       ╲   ← Previsão          │
│  100 ──┤         ╭────╮   ╱    ░░░░░╲░░░░ ← Intervalo 95%  │
│        │        ╱      ╲ ╱    ░░░░░░░░░░░░                  │
│   80 ──┤───────╱────────╳────░░░░░░░░░░░░── Histórico       │
│        │      ╱          ╲                                  │
│   60 ──┤─────╱────────────╲────────────────                 │
│        │                                                     │
│   40 ──┤                                                     │
│        └────┬────┬────┬────┬────┬────┬────┬────┬────┬────▶  │
│            Hoje  +1d  +2d  +3d  +4d  +5d  +6d  +7d         │
│                                                             │
│  📊 Pico previsto: 120 incidentes em +2d                    │
│  ⚠️  Capacidade atual: 95/dia — risco de excesso            │
├─────────────────────────────────────────────────────────────┤
│ [Exportar] [Ver detalhes por grupo] [Configurar alertas]    │
└─────────────────────────────────────────────────────────────┘
```

**Elementos obrigatórios:**
- `ChartHeader` — título, seletor D+1/D+7, legenda
- `TimeSeriesChart` — gráfico com linha histórica + previsão + intervalo de confiança
- `InsightBar` — resumo dos principais insights (pico, risco de capacidade)

**Elementos opcionais:**
- `GroupBreakdown` — toggle para ver previsão por grupo designado
- `ProductBreakdown` — toggle para ver previsão por produto
- `AlertThreshold` — linha horizontal indicando capacidade máxima

### Variants

| Variant | Uso |
| --- | --- |
| `default` | Previsão consolidada (todos os grupos) |
| `byGroup` | Previsão desagrupada por grupo designado |
| `byProduct` | Previsão desagrupada por produto |
| `compact` | Versão simplificada sem intervalo de confiança (para embeddings) |

### Props/API

| Nome | Tipo | Default | Obrigatório | Descrição |
| --- | --- | --- | --- | --- |
| `historicalData` | `TimeSeriesPoint[]` | — | Sim | Dados históricos (últimos 30 dias) |
| `forecastData` | `TimeSeriesPoint[]` | — | Sim | Dados previstos (D+1 ou D+7) |
| `confidenceInterval` | `[number, number][]` | — | Sim | Intervalo de confiança 95% |
| `horizon` | `'D+1' \| 'D+7'` | `'D+7'` | Não | Horizonte de previsão ativo |
| `onHorizonChange` | `(horizon: string) => void` | — | Não | Callback ao trocar horizonte |
| `capacityThreshold` | `number \| null` | `null` | Não | Capacidade máxima por dia (para alerta) |
| `groupBy` | `'consolidated' \| 'group' \| 'product'` | `'consolidated'` | Não | Modo de desagregação |
| `onGroupByChange` | `(groupBy: string) => void` | — | Não | Callback ao trocar modo |
| `priority` | `'P2' \| 'P3' \| 'all'` | `'all'` | Não | Filtrar por prioridade |
| `onExport` | `(format: 'csv' \| 'png') => void` | — | Não | Callback ao exportar |

### States

| Estado | Aparência | Comportamento |
| --- | --- | --- |
| `default` | Gráfico renderizado com dados completos | Interativo: hover mostra valores |
| `loading` | Skeleton do gráfico (eixos + linhas tracejadas) | Dados carregando |
| `error` | Mensagem "Erro ao carregar previsão" + botão retry | API com erro |
| `no-data` | "Dados insuficientes para previsão. Mínimo: 14 dias históricos." | Histórico < 14 dias |
| `over-capacity` | Linha de capacidade vermelha; área acima destacada em vermelho | Previsão > capacidade |
| `forecast-available` | Linha de previsão sólida; intervalo sombreado | Dados de forecast carregados |

### Behavior

- **Alternância D+1/D+7:** Toggle no header alterna entre horizontes. Dados são carregados da API sem recarregar a página.
- **Hover interativo:** Ao hover em qualquer ponto, tooltip mostra: data, valor previsto, intervalo de confiança, comparação com histórico.
- **Zoom/Pan:** Scroll para zoom no eixo X; drag para pan. Duplo-clique para resetar zoom.
- **Alerta de capacidade:** Se `capacityThreshold` definido e previsão > threshold, linha horizontal vermelha aparece com label "Capacidade: XX/dia".
- **Exportação:** Botão "Exportar" permite baixar CSV (dados brutos) ou PNG (imagem do gráfico).
- **Edge case — previsão > 7 dias:** D+7 usa o forecaster sazonal ajustado com intervalos mais largos. Mostrar aviso "Previsão de longo prazo tem margem maior de erro".
- **Edge case — sazonalidade:** Se dados mostram padrão semanal claro, destacar fins de semana com fundo cinza claro.

### Accessibility

- `role="img"` no container do gráfico (renderizado via Plotly/Matplotlib)
- `aria-label`: "Gráfico de previsão de volume. Previsão para +7 dias: tendência de alta, pico estimado 120 incidentes em +2 dias."
- Dados tabulados disponíveis para screen readers (tabela abaixo do gráfico, visível only via aria)
- Navegação por teclado: `←→` entre pontos; `Enter` mostra detalhes; `Escape` fecha tooltip
- Cores atendem contraste WCAG 2.1 AA; padrão também funciona em escala de cinza

### Usage Guidelines

**Do:**
- Sempre mostrar intervalo de confiança — transparência sobre incerteza
- Incluir linha de capacidade quando disponível — contexto para decisão
- Mostrar insight resumido abaixo do gráfico (pico, risco)

**Don't:**
- Não esconder dados históricos — previsão sem contexto é inútil
- Não usar mais de 5 séries no mesmo gráfico (sobrecarga visual)
- Não plotar previsão < 1 dia sem aviso de margem de erro

---

## 5. OperationalRegimeIndicator

### Overview

| Campo | Valor |
| --- | --- |
| **Nome** | `OperationalRegimeIndicator` |
| **Descrição** | Badge compacto no header que indica o regime operacional atual (Normal, Stress, Saturação, Crise, Recuperação). Muda cor e animação conforme severidade. |
| **Usar quando** | Sempre visível no header do dashboard — indicador de "temperatura" da operação. |
| **Não usar quando** | Para indicar status de um componente individual (usar StatusBadge). |

### Anatomy

```
┌─────────────────────────────────┐
│ 🟢 Normal        [最近: 14:32]  │
└─────────────────────────────────┘

ou

┌─────────────────────────────────┐
│ 🔴 CRISE         [⚠️ Ativo]    │
│    Incidentes: +45% acima da   │
│    média semanal               │
└─────────────────────────────────┘
```

**Elementos obrigatórios:**
- `RegimeIcon` — ícone/cor que muda conforme regime
- `RegimeLabel` — texto "Normal", "Stress", "Saturação", "Crise", "Recuperação"
- `Timestamp` — última mudança de regime

**Elementos opcionais:**
- `Description` — texto curto explicando por que o regime foi detectado
- `TrendIndicator` — seta indicando se regime está piorando ou melhorando

### Variants

| Variant | Tamanho | Uso |
| --- | --- | --- |
| `inline` | Compacto, sem descrição | No header do dashboard |
| `detailed` | Com descrição e trend | Em painéis de overview |
| `alert` | Com animação de pulso | Quando regime muda para crise |

### Props/API

| Nome | Tipo | Default | Obrigatório | Descrição |
| --- | --- | --- | --- | --- |
| `regime` | `'normal' \| 'stress' \| 'saturation' \| 'crisis' \| 'recovery'` | `'normal'` | Sim | Regime operacional atual |
| `since` | `Date` | — | Sim | Timestamp da mudança de regime |
| `description` | `string \| null` | `null` | Não | Explicação do regime |
| `trend` | `'improving' \| 'stable' \| 'worsening'` | `'stable'` | Não | Tendência do regime |
| `size` | `'inline' \| 'detailed' \| 'alert'` | `'inline'` | Não | Variante visual |
| `onClick` | `() => void` | — | Não | Callback ao clicar (abre detalhes) |

### States

| Estado | Cor | Ícone | Animação |
| --- | --- | --- | --- |
| `normal` | Verde (#22C55E) | ● (ponto verde) | Nenhuma |
| `stress` | Amarela (#EAB308) | ▲ (triângulo amarelo) | Nenhuma |
| `saturation` | Laranja (#F97316) | ◆ (diamante laranja) | Nenhuma |
| `crisis` | Vermelha (#EF4444) | ⚠️ (alerta vermelho) | Pulso contínuo (1.5s) |
| `recovery` | Azul (#3B82F6) | ↗ (seta recovery) | Nenhuma |

### Behavior

- **Mudança de regime:** Quando regime muda, animação de transição de cor (300ms ease). Se mudar para `crisis`, `NotificationBanner` aparece no topo do dashboard.
- **Tooltip no hover:** Mostra detalhes: "Regime: Crise. Detectado às 14:32. Incidentes P2: +45% acima da média semanal. Tendência: piorando."
- **Clique:** Abre painel lateral com análise detalhada do regime (histórico de regimes, métricas que causaram a mudança).
- **Persistência:** Regime é recalculado a cada 5 minutos. Mudanças são logadas para auditoria.
- **Edge case — transição rápida:** Se regime mudar 3+ vezes em 10 minutos, mostrar aviso "Regime instável — operação oscilando".

### Accessibility

- `role="status"`, `aria-live="polite"` (anuncia mudanças)
- `aria-label`: "Regime operacional: Crise. Ativo desde 14:32."
- Cor + ícone (não apenas cor) para daltonismo
- Animação de pulso pode ser desativada via `prefers-reduced-motion`
- Screen reader: "Regime operacional mudou para Crise. Incidentes P2 45 por cento acima da média."

### Usage Guidelines

**Do:**
- Manter sempre visível no header — é indicador crítico
- Usar cor + ícone (nunca apenas cor) para comunicação
- Logar todas as mudanças de regime para auditoria

**Don't:**
- Não ocultar regime operacional — é informação de segurança
- Não usar animação de pulso para regimes não-críticos
- Não permitir override manual do regime (é calculado automaticamente)

---

## 6. SHAPWaterfall

### Overview

| Campo | Valor |
| --- | --- |
| **Nome** | `SHAPWaterfall` |
| **Descrição** | Gráfico waterfall que visualiza a contribuição de cada feature para o score de risco de um incidente específico. Explica "por que" o modelo tomou essa decisão. |
| **Usar quando** | Detalhar explicabilidade de um incidente específico (após clicar "Detalhes" no IncidentCard). |
| **Não usar quando** | Para visão consolidada de SHAP (usar SHAPSummary) ou para previsão (usar ForecastChart). |

### Anatomy

```
┌─────────────────────────────────────────────────────────────┐
│ Explicabilidade — INC92341                    [Fechar] [📥] │
├─────────────────────────────────────────────────────────────┤
│ Score Final: 89% ████████████████████████████████████████  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Feature                    Contribuição     Valor          │
│  ─────────────────────────────────────────────────────────  │
│  Backlog do grupo           +34%  ████████████████  Alto    │
│  Horário de abertura        +22%  ███████████       14:32   │
│  Reincidência técnica       +18%  █████████         3x      │
│  Produto (Hosting)          +12%  ██████            Linux   │
│  IC (IC00001)               +8%   ████              Web9    │
│  ─────────────────────────────────────────────────────────  │
│  Base (média histórica)     +15%                    —       │
│  ─────────────────────────────────────────────────────────  │
│  TOTAL                      89%                           │
├─────────────────────────────────────────────────────────────┤
│ 💡 Insight: O principal driver é o backlog elevado do       │
│    Team14. Tickets similares violaram OLA em 78% dos casos. │
├─────────────────────────────────────────────────────────────┤
│ [🔄 Reatribuir para grupo com menos backlog]                │
│ [📈 Ver histórico de violações do grupo]                    │
└─────────────────────────────────────────────────────────────┘
```

**Elementos obrigatórios:**
- `ScoreHeader` — score final com barra de progresso
- `WaterfallChart` — barras horizontais com contribuição de cada feature
- `FeatureTable` — tabela com feature, contribuição e valor atual
- `InsightText` — resumo em linguagem natural do principal driver

**Elementos opcionais:**
- `ComparisonChart` — comparação com tickets similares históricos
- `ActionRecommendations` — recomendações de ação baseadas nos fatores

### Variants

| Variant | Uso |
| --- | --- |
| `default` | Waterfall completo com top 10 features |
| `compact` | Apenas top 3 features (para embedding em cards) |
| `comparison` | Lado a lado: este ticket vs. ticket similares |

### Props/API

| Nome | Tipo | Default | Obrigatório | Descrição |
| --- | --- | --- | --- | --- |
| `ticketId` | `string` | — | Sim | ID do incidente |
| `riskScore` | `number` (0-100) | — | Sim | Score final de risco |
| `features` | `SHAPFeature[]` | — | Sim | Array de features com contribution e value |
| `baseValue` | `number` | — | Sim | Valor base (média histórica) |
| `insight` | `string` | — | Não | Resumo em linguagem natural |
| `similarTickets` | `SimilarTicket[]` | `[]` | Não | Tickets similares para comparação |
| `onReassign` | `(ticketId: string) => void` | — | Não | Callback para reatribuição |
| `onClose` | `() => void` | — | Sim | Callback para fechar painel |

### States

| Estado | Aparência | Comportamento |
| --- | --- | --- |
| `default` | Waterfall renderizado com todas as features | Interativo: hover mostra detalhes |
| `loading` | Skeleton do gráfico | SHAP sendo calculado |
| `error` | "Erro ao calcular explicabilidade" + retry | Modelo indisponível |
| `partial` | Apenas 3 features visíveis; "Ver mais" link | Modo compacto |
| `comparison` | Dois waterfalls lado a lado | Tickets comparando |

### Behavior

- **Ordenação:** Features são ordenadas por contribution (maior para menor). Feature negativa (reduz risco) aparece na parte inferior com cor azul.
- **Hover:** Ao hover em uma barra, tooltip mostra: nome da feature, valor numérico, contribution exata, e comparativo com a média histórica.
- **Insight automático:** Se `insight` não fornecido, gerar automaticamente: "O principal driver é [feature com maior contribution]. [Descrição do impacto]."
- **Ações contextuais:** Botões "Reatribuir" e "Ver histórico" aparecem baseados nos fatores dominantes.
- **Edge case — feature com contribution negativa:** Se alguma feature reduz risco (ex: "Grupo com SLA bom"), mostrar barra azul abaixo da linha de base.
- **Edge case — modelo sem confiança:** Se confidence < 70%, mostrar aviso "Explicabilidade com baixa confiança — modelo treinado com dados limitados para esse padrão."

### Accessibility

- `role="img"` no gráfico; `aria-label` descreve o conteúdo
- Tabela de features: `role="table"`, `role="row"`, `role="cell"`
- Cada barra: `role="meter"`, `aria-valuenow`, `aria-valuemin="-50"`, `aria-valuemax="50"`
- Navegação por teclado: `↑↓` entre features; `Enter` expande detalhes
- Screen reader: "Explicabilidade do incidente INC92341. Score: 89 por cento. Principal fator: backlog do grupo, contribuição positiva 34 por cento."

### Usage Guidelines

**Do:**
- Sempre mostrar o score final no topo — contexto para o waterfall
- Incluir insight em linguagem natural — não todos são analistas de ML
- Permitir exportar como imagem para relatórios

**Don't:**
- Não mostrar mais de 10 features — sobrecarga cognitiva
- Não esconder contribution negativa — transparência total
- Não usar SHAP sem contexto — sempre mostrar valor atual da feature

---

## 7. ClusterPanel

### Overview

| Campo | Valor |
| --- | --- |
| **Nome** | `ClusterPanel` |
| **Descrição** | Painel que visualiza clusters de incidentes com validação HDBSCAN medida (DBCV, estabilidade, sobreposição) e contagens/FP medidos do loader. |
| **Usar quando** | Analisar padrões de reincidência, identificar surtos, detectar falsos positivos. |
| **Não usar quando** | Para análise de ticket individual (usar IncidentCard) ou forecasting (usar ForecastChart). |

### Anatomy

```
┌─────────────────────────────────────────────────────────────┐
│ Clusters Operacionais — 5 clusters detectados    [🔄] [⚙️] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ 🔴 Cluster #1   │  │ 🟡 Cluster #2   │  │ 🟢 Cluster #3│ │
│  │ "Apache Busy    │  │ "DNS Failure    │  │ "DB Timeout  │ │
│  │  Workers"       │  │  pós-deploy"    │  │  noturno"    │ │
│  │                 │  │                 │  │             │ │
│  │ Tickets: 47     │  │ Tickets: 23     │  │ Tickets: 12 │ │
│  │ Taxa falsos +:  │  │ Taxa falsos:    │  │ Taxa falsos: │ │
│  │   89%           │  │   12%           │  │   5%        │ │
│  │ Tendência: 📈   │  │ Tendência: 📉   │  │ Tendência: ➡ │ │
│  │                 │  │                 │  │             │ │
│  │ [Ver tickets]   │  │ [Ver tickets]   │  │ [Ver tickets]│ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ 💡 Insight: Cluster #1 (Apache Busy Workers) representa    │
│    89% de falsos positivos — considere automatizar triagem. │
└─────────────────────────────────────────────────────────────┘
```

**Elementos obrigatórios:**
- `ClusterGrid` — grid de cards de cluster
- `ClusterCard` — card individual com nome, contagem, taxa de falsos positivos, tendência
- `InsightBar` — resumo dos principais padrões detectados

**Elementos opcionais:**
- `ClusterDetail` — painel lateral com lista de tickets do cluster
- `NLPKeywords` — palavras-chave extraídas por NLP que definem o cluster
- `TimelineView` — visualização temporal de quando o cluster aparece

### Variants

| Variant | Uso |
| --- | --- |
| `default` | Grid de clusters com cards |
| `list` | Lista vertical para muitos clusters (>10) |
| `detail` | Painel completo com um cluster selecionado |

### Props/API

| Nome | Tipo | Default | Obrigatório | Descrição |
| --- | --- | --- | --- | --- |
| `clusters` | `Cluster[]` | — | Sim | Array de clusters detectados |
| `selectedClusterId` | `string \| null` | `null` | Não | Cluster selecionado para detalhes |
| `onSelectCluster` | `(clusterId: string) => void` | — | Não | Callback ao selecionar cluster |
| `onViewTickets` | `(clusterId: string) => void` | — | Não | Callback ao ver tickets do cluster |
| `sortBy` | `'size' \| 'falsePositiveRate' \| 'trend'` | `'size'` | Não | Ordenação dos clusters |
| `onSortChange` | `(sortBy: string) => void` | — | Não | Callback ao trocar ordenação |
| `minClusterSize` | `number` | `5` | Não | Tamanho mínimo para mostrar cluster |

### States

| Estado | Aparência | Comportamento |
| --- | --- | --- |
| `default` | Grid de clusters renderizados | Cards clicáveis |
| `loading` | Skeleton de 3-5 cards | Validação HDBSCAN processando |
| `empty` | "Nenhum cluster significativo detectado" | — |
| `detail` | Painel lateral com tickets do cluster | Cluster selecionado |
| `error` | "Erro ao detectar clusters" + retry | Algoritmo falhou |

### Behavior

- **Detecção:** A validação HDBSCAN roda sob demanda com `min_cluster_size=50` e `min_samples=5`, reportando DBCV, estabilidade bootstrap e sobreposição de Jaccard por família (ver Constituição IV).
- **NLP:** Cada cluster recebe nome automático baseado nas top 3 palavras das descrições (ex: "Apache Busy Workers").
- **Taxa de falsos positivos:** Calculada como % de tickets no cluster que foram encerrados sem intervenção humana em < 60 segundos.
- **Tendência:** Comparação com semana anterior — 📈 (crescendo), 📉 (diminuindo), ➡ (estável).
- **Detalhes:** Ao clicar em "Ver tickets", painel lateral abre com lista de todos os tickets do cluster, ordenados por data.
- **Edge case — cluster muito grande:** Se cluster > 200 tickets, mostrar apenas os 20 mais recentes com "Ver todos (200)" link.
- **Edge case — cluster com 1 ticket:** Clusters com apenas 1 ticket são ocultados (ruído).

### Accessibility

- `role="list"` no grid de clusters
- Cada card: `role="listitem"`, `aria-label="Cluster Apache Busy Workers, 47 tickets, 89 por cento falsos positivos"`
- Detalhes: `role="complementary"`, `aria-label="Detalhes do cluster selecionado"`
- Navegação: `Tab` entre cards; `Enter` seleciona; `Escape` fecha detalhes
- Screen reader: "5 clusters detectados. Maior cluster: Apache Busy Workers com 47 tickets."

### Usage Guidelines

**Do:**
- Nomear clusters automaticamente via NLP — melhora reconhecimento
- Mostrar taxa de falsos positivos — é insight acionável
- Permitir drill-down para tickets individuais

**Don't:**
- Não mostrar clusters < 5 tickets (ruído)
- Não ocultar taxa de falsos positivos — é diferencial competitivo
- Não permitir ação direta nos tickets do cluster (apenas visualização)

---

*Document created: 2026-08-25 (planejamento histórico; stack vigente: React 18 + Vite + FastAPI + RF + TF-IDF + shap.TreeExplainer + HDBSCAN-validação + KS — ver aviso de conformidade no topo). All components follow WCAG 2.1 AA.*
