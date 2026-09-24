# Feature Specification: LocaPredict SLA Guard v3 — FusionOps Intelligence Platform

**Feature Branch**: `001-locapredict-sla-guard`

**Created**: 2026-09-24

**Status**: Ready for Planning

**Input**: User description: "Especificação completa da Solução Final da Sprint 4 do Challenge Locaweb (FusionOps): Plataforma AIOps orientada por Machine Learning para previsão preditiva de OLA/SLA, explicabilidade SHAP, forecast tático de demanda, clusterização de ruído e observabilidade MLOps."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Triagem e Priorização Preditiva de Incidentes com Explicabilidade (Priority: P1)

Como um operador do NOC ou analista de suporte técnico N2, quero visualizar uma fila de incidentes priorizada por probabilidade de quebra de OLA (Operating Level Agreement) e inspecionar os fatores de contribuição de cada chamado, para que eu possa atuar preventivamente antes do estouro do prazo regulatório.

**Why this priority**: A mitigação de multas contratuais e a manutenção da disponibilidade dos serviços críticos da Locaweb dependem diretamente da capacidade de identificar incidentes com risco iminente de rompimento de OLA antes que alcancem o limite de tempo estipulado.

**Independent Test**: Pode ser testado visualizando a fila de incidentes, selecionando um ticket de alta prioridade (como INC8654273) e abrindo o detalhamento de explicabilidade, atestando a presença do score de risco calibrado e a decomposição dos fatores que elevaram a criticidade do chamado.

**Acceptance Scenarios**:

1. **Given** um incidente classificado com risco crítico (≥ 80%), **When** o operador abre a tela operacional, **Then** o chamado é exibido no topo da fila com sinalização visual de alerta e tempo restante de SLA calculado.
2. **Given** um operador inspecionando um chamado de risco, **When** ele aciona a visualização de explicabilidade, **Then** o sistema exibe os fatores que influenciaram o score (volume do backlog da squad, horário de pico, reincidência técnica do ativo e classificação de ruído).
3. **Given** um incidente sob risco de estouro, **When** o operador executa a reatribuição para uma squad especializada ou eleva a prioridade, **Then** o sistema recalcula o risco operacional e registra a ação com justificativa na trilha de auditoria.

---

### User Story 2 - Planejamento Tático de Demanda e Matriz de Capacidade por Squad (Priority: P1)

Como um gestor de operações de TI ou líder técnico de infraestrutura, quero acompanhar projeções preditivas de volume de incidentes em horizontes de curto (D+1) e médio prazo (D+7) comparadas à capacidade nominal de cada equipe, para que eu possa remanejar analistas e planejar escalas de plantão antes de sobrecargas operacionais.

**Why this priority**: A sobrecarga da squad de Hosting Linux (Team14) e do NOC em dias de pico gera gargalos sistêmicos de atendimento. Antecipar picos semanais com intervalo de confiança permite uma gestão proativa de recursos humanos e técnicos.

**Independent Test**: Pode ser testado alternando entre as projeções D+1 e D+7, verificando o gráfico de tendência temporal com limites estatísticos de 95% e conferindo se a saturação percentual de cada squad reflete a capacidade operacional planejada.

**Acceptance Scenarios**:

1. **Given** a visão tática ativa, **When** o gestor seleciona a projeção semanal (D+7), **Then** o sistema exibe o pico previsto de incidentes no dia crítico acompanhado da margem de erro estatística.
2. **Given** a previsão de demanda indicando saturação acima de 100% para uma determinada squad, **When** o painel de capacidade é consultado, **Then** o sistema destaca a equipe em estado crítico e sugere prescrições operacionais para mitigação (ex: remanejamento de analistas ociosos).
3. **Given** a alternância para o horizonte de 24 horas (D+1), **When** a solicitação é processada, **Then** o sistema atualiza as metas de triagem para o próximo turno com detalhamento por categoria de serviço.

---

### User Story 3 - Identificação de Clusters Semânticos e Supressão de Falsos Positivos (Priority: P2)

Como um engenheiro de confiabilidade (SRE) ou analista de monitoramento, quero identificar padrões recorrentes de incidentes automatizados e chamados sem intervenção humana, para que seja possível reduzir o ruído na operação e automatizar a resolução de eventos de curta duração.

**Why this priority**: Mais de 60% dos registros históricos da operação representam alarmes transitórios de monitoramento (como saturação efêmera de workers ou verificações de rotina) que consomem atenção indevida dos operadores.

**Independent Test**: Pode ser testado acessando o painel de engenharia e inspecionando os agrupamentos temáticos de incidentes, comprovando a identificação da taxa de falsos positivos e a recomendação de auto-resolução para alarmes de curta duração.

**Acceptance Scenarios**:

1. **Given** a análise histórica dos chamados, **When** o painel de clusters é carregado, **Then** o sistema agrupa os incidentes em perfis recorrentes (ex: Apache Busy Workers, saturação de conexões de banco, latência SMTP, limites de armazenamento e falhas DNS).
2. **Given** um cluster com taxa de falso positivo superior a 60%, **When** o analista seleciona o agrupamento, **Then** o sistema detalha o tempo médio de encerramento sem intervenção e prescreve regras de auto-resolução.
3. **Given** a lista de chamados de um cluster específico, **When** o usuário realiza um drill-down, **Then** o sistema lista os tickets vinculados para validação técnica direta.

---

### User Story 4 - Observabilidade Contínua de MLOps e Detecção de Drift (Priority: P2)

Como um engenheiro de Machine Learning ou administrador da plataforma, quero monitorar o comportamento das distribuições de dados e a performance dos modelos de predição ao longo do tempo, para que eu possa detectar desvios operacionais (drift) e disparar o retreinamento com rastreabilidade.

**Why this priority**: Ambientes de datacenter e hosting sofrem mutações constantes em infraestrutura, atualizações de software e comportamento de clientes. Detectar desvios estatísticos garante a confiabilidade permanente dos scores de risco.

**Independent Test**: Pode ser testado acessando o painel de MLOps, verificando o status dos testes de drift de Kolmogorov-Smirnov sobre as variáveis operacionais e executando um ciclo de retreinamento de modelo com atualização de versão.

**Acceptance Scenarios**:

1. **Given** a operação em produção, **When** o módulo de observabilidade compara as amostras correntes contra a base de referência, **Then** o sistema apresenta o p-valor estatístico de cada variável e sinaliza se houve detecção de drift.
2. **Given** métricas de acurácia (ROC-AUC, Recall, WAPE) em acompanhamento, **When** o painel de governança é exibido, **Then** os indicadores de saúde do modelo são validados contra os limites mínimos contratuais.
3. **Given** um usuário com privilégios de administração, **When** o comando de retreinamento é disparado, **Then** o sistema executa o ajuste dos modelos, incrementa a versão sem interrupção de serviço e registra o evento na trilha de auditoria.

---

### User Story 5 - Controle de Acesso Baseado em Papéis, Exportação e Auditoria (Priority: P3)

Como um auditor de compliance ou gestor de segurança, quero que o acesso às operações críticas da plataforma seja segregado por perfil e que toda ação realizada seja auditável e exportável em formato estruturado.

**Why this priority**: A conformidade com governança corporativa exige que ações que alterem prioridades de atendimento ou reatribuam filas de clientes tenham autoria conhecida e que relatórios executivos possam ser extraídos com integridade.

**Independent Test**: Pode ser testado alternando entre os perfis de Administrador, Operador e Visualizador, atestando o bloqueio de operações não autorizadas para perfis de leitura e gerando uma exportação em CSV com cabeçalhos de segurança.

**Acceptance Scenarios**:

1. **Given** um usuário autenticado com perfil Visualizador, **When** ele tenta acionar o retreinamento do modelo ou reatribuir um chamado, **Then** o sistema bloqueia a ação informando restrição de permissão.
2. **Given** um operador ou administrador autenticado, **When** ele solicita a exportação de dados, **Then** o sistema gera um arquivo CSV sanitizado contendo os incidentes filtrados com controle de limite de linhas.
3. **Given** ações de modificação de estado operacional, **When** inspecionadas no banco de auditoria, **Then** cada registro contém carimbo de data/hora, identificador do usuário, ação executada e parâmetros antes/depois.

---

### Edge Cases

- O que acontece se o volume de chamados simulados atingir um pico repentino em curto intervalo? O sistema deve aplicar throttling suave e processar a esteira mantendo a integridade dos buffers de telemetria sem perda de dados.
- O que acontece se um incidente for registrado com campos textuais incompletos ou em branco? O pipeline de vetorização deve tratar campos ausentes com fallbacks semânticos padronizados sem interromper a inferência.
- O que acontece se a conexão de telemetria em tempo real for interrompida? O cliente web deve alternar para modo de polling com reconexão exponencial automática mantendo o último estado estável em cache.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE calcular um Score de Risco de Quebra de OLA (escala de 0 a 100%) para cada incidente ativo utilizando modelo supervisionado treinado sobre dados históricos de ITSM.
- **FR-002**: O sistema DEVE fornecer para cada predição de risco uma lista ordenada de Fatores SHAP contendo nome amigável da variável, impacto (positivo/negativo), valor de peso e diagnóstico textual.
- **FR-003**: O sistema DEVE manter uma fila operacional ordenada decrescentemente por risco, permitindo filtragem por prioridade (P1 a P4), squad responsável, produto, item de configuração e faixa de score.
- **FR-004**: O sistema DEVE possibilitar a reatribuição de incidentes entre squads com reavaliação imediata de risco e registro em log de auditoria.
- **FR-005**: O sistema DEVE suportar a escalação de prioridade de incidentes acompanhada de justificativa obrigatória.
- **FR-006**: O sistema DEVE calcular e exibir o Regime Operacional corrente (Normal, Stress, Saturação, Crise, Recuperação) com base no volume de chamados críticos e tendências de demanda.
- **FR-007**: O sistema DEVE gerar projeções de volume de chamados para os horizontes D+1 (24 horas) e D+7 (semanal) com intervalos de confiança bicaudais de 95%.
- **FR-008**: O sistema DEVE calcular a Matriz de Capacidade por Squad comparando a carga projetada com o teto operacional de cada equipe.
- **FR-009**: O sistema DEVE apresentar recomendações prescritivas de balanceamento de analistas quando a saturação projetada ultrapassar 100%.
- **FR-010**: O sistema DEVE categorizar a totalidade dos registros históricos em clusters semânticos temáticos com identificação de frequência e taxa percentual de falsos positivos.
- **FR-011**: O sistema DEVE executar testes de hipótese de Kolmogorov-Smirnov (KS-Test) de duas amostras para monitorar drift estatístico em features-chave da esteira operacional.
- **FR-012**: O sistema DEVE disponibilizar rotina de retreinamento de modelo sob demanda com geração de nova versão de pipeline e atualização de métricas de validação (ROC-AUC, Recall, WAPE).
- **FR-013**: O sistema DEVE autenticar sessões via tokens criptográficos assinados e aplicar controle de acesso segregado entre perfis de Administrador, Operador e Visualizador.
- **FR-014**: O sistema DEVE exportar listagens operacionais em formato CSV delimitado com controle de volume máximo de linhas.
- **FR-015**: O sistema DEVE sincronizar atualizações de fila e métricas de regime com a interface web via canal bidirecional de baixa latência em tempo real.

---

### Key Entities

- **Incident**: Representa o chamado operacional de infraestrutura ou suporte (identificador, título, produto, prioridade, squad responsável, item de configuração, duração, status de falso positivo, score preditivo de risco, prazo regulatório de SLA e fatores de explicabilidade SHAP).
- **OperationalRegime**: Representa o estado sistêmico da infraestrutura (classificação atual, índice de confiança, histórico recente de transições e gatilhos operacionais ativos).
- **ForecastProjection**: Representa a curva temporal de demanda projetada (série histórica, valores preditos por dia, limites inferior e superior de confiança estatística, acurácia WAPE e detalhamento por equipe).
- **SemanticCluster**: Representa o agrupamento temático de falhas recorrentes (nome descritivo, volume de chamados associados, taxa de falsos positivos, termos característicos e recomendação técnica preventiva).
- **DriftMetric**: Representa o monitoramento de distribuição de uma variável de entrada (nome da feature, estatística KS, p-valor bicaudal, média de referência e diagnóstico de estabilidade).
- **AuditLog**: Representa o registro imutável de governança (carimbo temporal, identificador do incidente, tipo de ação, usuário responsável e metadados de contexto).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O modelo preditivo de risco de quebra de OLA DEVE atingir ROC-AUC superior a 0.850 e Recall superior a 0.800 sobre a base de validação de incidentes da Locaweb.
- **SC-002**: A projeção tática de demanda DEVE apresentar erro percentual absoluto ponderado (WAPE) inferior a 15.0% (acurácia superior a 85.0%).
- **SC-003**: A plataforma DEVE demonstrar capacidade de identificar e segregar pelo menos 35% de chamados automatizados efêmeros como ruído/falso positivo operacional.
- **SC-004**: O tempo de resposta para carregamento das telas operacionais e visualização dos fatores de explicabilidade SHAP DEVE ser inferior a 1 segundo na rede local.
- **SC-005**: A suíte de testes automatizados de backend DEVE manter taxa de aprovação de 100% cobrindo rotas, autenticação, inferência preditiva e testes de drift.
- **SC-006**: 100% das ações operacionais de reatribuição, escalação e retreinamento DEVEM ser registradas com rastreabilidade na trilha de auditoria.

---

## Assumptions

- O dataset histórico consolidado de 122.543 registros fornecido pela Locaweb reflete adequadamente a sazonalidade e os padrões de incidentes de hospedagem e cloud corporativa.
- A distribuição de prioridades de catálogo adota como base os limites contratuais de SLA padrão (P1: 4 horas; P2: 4 horas; P3: 12 horas; P4: 24 horas).
- O ambiente operacional do usuário dispõe de navegador moderno compatível com padrões web atuais (HTML5, ECMAScript 2020+, WebSockets).
- A infraestrutura de backend utiliza persistência relacional SQLite ACID embarcada para armazenamento de estados, permitindo portabilidade sem dependência externa de serviços gerenciados durante avaliações locais.
