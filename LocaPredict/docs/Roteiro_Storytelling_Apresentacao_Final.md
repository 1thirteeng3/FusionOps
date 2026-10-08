# Storytelling — Apresentação Final (Sprint 4) — Conteúdo integral dos slides
## LocaPredict SLA Guard v3 — FusionOps | Grupo GKL, 2TSCOA, Locaweb 2026

> Adicionar após o slide 37 do deck Sprint 3. Tempo total: **10–12 min**.
> Convenção: **TÍTULO** = texto do topo; *Subtítulo* = linha de apoio;
> corpo = texto literal dos blocos; 🎙 = fala do apresentador (não vai no slide).

---

## Arco e transição (igual à v1 do roteiro)

**Frase-âncora:** *"Sprint 3 provou que o MVP funciona. Sprint 4 prova que os números são verdade."*

🎙 Ponte (30s): *"Na Sprint 3 mostramos o MVP funcionando: fila, forecast, clusters, SHAP e MLOps. Nesta sprint fizemos a pergunta mais difícil: esses números são verdade? Auditamos o próprio trabalho, linha por linha. Achamos furos. E é sobre eles — e sobre como cada um foi corrigido com prova — que vamos falar agora."*

---

## SLIDE 38 — Abertura do ato

**Layout:** seção plena, mesma identidade do slide 32.
**TÍTULO:** DA EVIDÊNCIA À PROVA
*Subtítulo:* O que a Sprint 4 fez com o MVP da Sprint 3.
**Corpo (3 blocos):**
- PRODUTO FUNCIONANDO — mantido: FastAPI + React + SQLite + 122.543 chamados reais.
- FLUXOS REAIS — mantidos: triagem, forecast D+1/D+7, clusters, drift, retreino.
- NÚMEROS AUDITADOS — **novo**: cada métrica refeita com protocolo, incerteza e teste.
**Rodapé:** FusionOps · Sprint 4 · Constituição v1.1.0
🎙 (30s): *"Evidência mostra que funciona. Prova mostra que é verdade. Este bloco é a prova."*

---

## SLIDE 39 — O susto honesto

**TÍTULO:** Auditamos a nós mesmos. Achamos 7 furos.
*Subtítulo:* Nenhum varrido para debaixo do tapete — cada um virou tarefa com teste e gate.
**Corpo (tabela, 3 colunas):**

| Alegação Sprint 3 | Achado da auditoria | Status hoje |
|---|---|---|
| AUC 0,989 | Métrica de treino, não generalização | CV 0,8475 com IC95% — Seção V |
| SHAP / Prophet / HDBSCAN | Atalhos de implementação no MVP | Refeitos de verdade — Slides 41–43 |
| −38,5% FP / −21,4% MTTR | Projeções sem desenho causal | Rotuladas como projeção — Slide 47 |
| Login sem senha, bypass anônimo | RBAC de teatro | 401 / 403 / 429 testados — Slide 44 |

🎙 (60s): *"Listamos tudo numa tabela pública dentro do repositório. Sete furos graves, três achados severos. A pergunta que nos fizemos: preferimos um pôster bonito ou um sistema que passa numa auditoria? Escolhemos a auditoria."*

---

## SLIDE 40 — O método

**TÍTULO:** Correção com método, não no improviso.
*Subtítulo:* Governança versionada + critérios congelados antes do teste.
**Corpo (funil + selos):**
- SPEC → PLAN → TASKS → IMPLEMENT — **42/42 tarefas concluídas e marcadas.**
- Constituição v1.1.0 — **7 princípios** (validação honesta, SHAP real, forecast com backtest, clusters medidos, risco calibrado, drift com correção, auth zero-trust).
- ACR-001 (AUC ≥ 0,85) · ACR-002 (recall ≥ 0,80) · ACR-003 (WAPE < 15%) — **congelados em 24/09, antes de olhar os dados de teste.**
- Gates 4–7: validação, evidência, segurança, revisão de alegações.
🎙 (45s): *"Congelamos os critérios antes de olhar os dados — como um laboratório faz. Só então implementamos. Quem define a régua depois do jogo sempre passa; nós definimos antes."*

---

## SLIDE 41 — Risco calibrado + SHAP real (US1)

**TÍTULO:** 87% agora significa 87 de cada 100.
*Subtítulo:* Risco = probabilidade calibrada. Explicação = modelo, não tabela.
**Corpo (antes × depois):**
- ANTES (riscado): `risco = 55·p + bônus de prioridade + bônus de squad`.
- DEPOIS: `risco = round(100 · p_calibrada)` — Random Forest + calibração isotônica.
- Recall **0,838** a τ=0,04 · PR-AUC **0,251** · Brier **0,0815**.
- Modal SHAP: atribuições `shap.TreeExplainer` com **valor-base, versão e fidelidade top-k**; reatribuição recalibra e audita before/after.
**Rodapé:** Print do modal SHAP real ao lado.
🎙 (60s): *"Antes, um 87% era uma soma com bônus. Hoje, 87% significa que 87 de cada 100 casos iguais estouram — e o modal prova de onde veio cada ponto, com teste de fidelidade automatizado rodando atrás."*

---

## SLIDE 42 — Forecast com backtest (US2)

**TÍTULO:** Previsão que venceu um adversário, 28 vezes.
*Subtítulo:* Modelo sazonal ajustado vs. baseline ingênuo, dia a dia.
**Corpo:**
- WAPE holdout **13,44%** vs. baseline **14,14%** — **Diebold-Mariano p = 0,0029** (superioridade significativa).
- 28 origens de backtest, horizontes D+1/D+7, IC 95% do resíduo.
- Pico e limiar **datados pelo modelo** — nenhum número hardcoded.
- Participação por squad **medida** (sem saturação % fabricada: teto por squad não medido, não afirmado).
**Rodapé:** Curva prevista × baseline ao lado.
🎙 (45s): *"Trocamos a curva decorativa por um modelo ajustado e o colocamos contra um baseline ingênuo 28 vezes. Ele venceu com significância. É assim que se prova forecast."*

---

## SLIDE 43 — O sistema que se recusou a mentir (US3, CLÍMAX)

**TÍTULO:** Rodamos o HDBSCAN de verdade. Ele reprovou a nossa taxonomia.
*Subtítulo:* E o sistema fez o certo: recusou o selo.
**Corpo (destaque duplo):**
- HDBSCAN sobre 3.000 títulos: DBCV **0,4858** · estabilidade **0,8532** · ruído **15,07%**.
- Sobreposição mediana com as 5 famílias: **0,038** (critério ≥ 0,40) → algoritmo rotulado **`keyword-baseline`**, claim **projeção**.
- O que É medido e exibido: contagens do loader (100.634 · 16.679 · 3.184 · 1.427 · 619), FP por cluster (66,6% · 63,9% · 66,6% · 16,7% · 58,6%), reconciliação ±1% testada.
🎙 (60s): *"Esse é o slide mais importante. O algoritmo disse: vossas 5 famílias não se sustentam como densidade. Então recusamos o selo HDBSCAN. Um modelo que se recusa a mentir vale mais que um dashboard bonito."*

---

## SLIDE 44 — MLOps que apita certo + auth que tranca (US4/US5)

**TÍTULO:** Drift sem falso-alarme. Auth sem teatro.
*Subtítulo:* Seis features reais. Três códigos de negação, cada um testado.
**Corpo (duas colunas):**
- MLOPS: KS com **correção de Holm** (sem ela, 26% de falso-alarme por ciclo) · janelas simétricas versionadas · retreino idempotente com **hash de artefato**.
- AUTH: sem token → **401** · sem senha → **401** · sem permissão → **403** · abuso → **429** · revogação por token · segredo fail-closed.
🎙 (40s): *"Drift sem correção apita à toa; corrigimos. Segurança: antes qualquer um entrava; hoje cada negação tem um teste com nome e sobrenome."*

---

## SLIDE 45 — O placar honesto

**TÍTULO:** Antes × depois, célula por célula.
*Subtítulo:* Cada célula tem um teste, um script e um commit atrás dela.
**Corpo (tabela):**

| Alegação | Antes (inválido) | Depois (honesto) |
|---|---|---|
| AUC | 0,989 (treino) | CV 0,8475 · IC95% [0,81; 0,88] |
| Recall | 0,821 (treino) | 0,838 @ τ=0,04 |
| Risco 0–100 | 55·p + bônus | round(100·p_calibrada) |
| SHAP | 5 pesos fixos | TreeExplainer + fidelidade |
| Forecast | senóide + WAPE const. | ajustado + backtest, DM p=0,0029 |
| Clusters | regras "HDBSCAN" | HDBSCAN real; taxonomia não-certificada |
| Drift | 2 p-valores fictícios | 6 features + Holm |
| Auth | bypass anônimo | 401/403/429 testados |

**Rodapé:** 33/33 testes · tsc limpo · 42/42 tarefas.
🎙 (45s): *"Este é o placar. Nada aqui é slogan."*

---

## SLIDE 46 — Demo ao vivo (slide-divisor + roteiro)

**TÍTULO:** Ao vivo, em 3 cliques.
*Subtítulo:* Se a demo cair, os testes continuam passando.
**Corpo (passo a passo numerado na tela):**
1. Fila → **INC8654273** → modal SHAP — apontar base, versão, fidelidade.
2. Tático **D+7** — apontar WAPE holdout vs. baseline + p do DM.
3. Engenharia → clusters (algoritmo + DBCV) → **retreino como admin**.
🎙 (2 min + fala de segurança): *"E se a demo cair, a prova não depende do palco: os 33 testes continuam verdes."*

---

## SLIDE 47 — O que ainda NÃO provamos

**TÍTULO:** Maturidade é listar o que falta.
*Subtítulo:* Produção segue bloqueada — por decisão nossa, documentada.
**Corpo:**
- −38,5% / −21,4% aguardam **piloto controlado** (RCT/DiD/ITS).
- ACR-001 exige **holdout de dezembro** (CV 0,8475 o tangencia; o IC o contém).
- Precisão 0,165 = **preço declarado** da cobertura (recall 0,838, prevalência 5%).
- P1 tem **n = 1** — sem generalização, e dizemos isso na tela.
🎙 (40s): *"Time maduro não promete o que não mediu — mostra o caminho medido até lá."*

---

## SLIDE 48 — Encerramento

**Layout:** frase-âncora em destaque + identificação + QR do repositório.
**TÍTULO:** Sólido não é perfeito. Sólido é incapaz de mentir.
*Subtítulo:* FusionOps — prever antes, provar sempre. Grupo GKL · 2TSCOA · Locaweb 2026.
🎙 (30s): *"Obrigado."*

---

## Apêndice — Q&A (não vai no slide; cola do apresentador)

| # | Pergunta dura | Resposta pronta |
|---|---|---|
| 1 | "AUC caiu de 0,989 para 0,85?" | "0,989 era treino. O honesto sempre foi ~0,85 — agora com IC95%, PR-AUC e Brier. Subiu a honestidade, não caiu o modelo." |
| 2 | "Precision só 0,165?" | "Preço declarado de recall 0,838 sob prevalência de 5%. Triagem prefere alarme falso a breach perdido." |
| 3 | "Clusters não são HDBSCAN?" | "Exato — e foi o próprio sistema que recusou o selo. Contagens e FP medidos; densidade reprovada com DBCV na mesa." |
| 4 | "38,5% não é resultado?" | "Correto, é projeção rotulada. Efeito causal exige piloto — roadmap com RCT/DiD." |
| 5 | "P1 com risco baixo?" | "Probabilidade ≠ severidade contratual. Severidade viaja no badge P1; P1 real tem n=1, e dizemos isso na tela." |
| 6 | "Por que 42 tarefas?" | "Rastreabilidade: cada furo virou tarefa, cada tarefa tem teste, cada teste tem gate." |

## Checklist de montagem
- [ ] Slides 38–48 na identidade do deck (fundo/texto do slide 32).
- [ ] Prints reais das 3 telas + modal SHAP.
- [ ] Números antigos aparecem UMA vez (slide 39), sempre acompanhados da correção.
- [ ] Ensaio com cronômetro: 11 min + 4 min de Q&A.
