# Briefing — Vídeo Pitch da Solução (hands-on, ~5 min)
## Para: responsável pela gravação | LocaPredict SLA Guard v3 — FusionOps, Grupo GKL

---

## 1. O que é este vídeo

Um **pitch de 5 minutos** que apresenta o PPT da Sprint 4 **com a solução rodando
de verdade ao lado**: metade apresentação, metade demonstração hands-on. Quem
assiste precisa terminar entendendo o problema, a solução, vendo-a funcionar e
acreditando nos números — porque cada número mostrado tem prova.

**Coerência com as Sprints 1–3 (obrigatório citar):**
- Sprint 1 → o desafio Locaweb e a base de 122.543 chamados (origem de tudo).
- Sprint 2 → o MVP: fila, forecast, clusters, SHAP, MLOps (o que foi construído).
- Sprint 3 → evidências do MVP funcionando (slides 32–37 do deck).
- Sprint 4 (este vídeo) → **auditoria + correções + prova**. Frase-âncora:
  *"Sprint 3 provou que funciona. Sprint 4 prova que é verdade."*

---

## 2. Setup técnico (antes de gravar)

- **Tela:** 1920×1080, navegador em tela cheia (F11), zoom 100–110%.
- **Áudio:** microfone próximo, ambiente silencioso; grave 10 s de teste e ouça.
- **Abas preparadas:** (1) App `http://localhost:5173` logado como **operator**;
  (2) Swagger `http://127.0.0.1:8000/docs` (reserva, só se precisar provar a API).
- **Estado da base:** apague `LocaPredict/locapredict.db` e reinicie o backend antes
  de gravar (fila canônica de 50 incidentes, sem sujeira de testes).
- **Ferramenta:** OBS ou gravador nativo; capture só a janela do navegador.
- **Plano B:** se a demo travar, continue narrando sobre os prints do PPT —
  *"e se a demo cair, os testes continuam passando"* (fala pronta, ensaie).

---

## 3. Roteiro fala-a-fala (5:00)

### Bloco 1 — Abertura e contextualização (≈30s) | Slides 1–2 do deck
> "A Locaweb opera milhares de serviços 24 por 7. Cada minuto de incidente fora
> de controle ameaça acordos de nível operacional — OLA e SLA. E a triagem ainda
> era manual: fila por ordem de chegada, sem saber onde o próximo estouro vai
> acontecer. Foi esse o desafio que recebemos na Sprint 1 — com 122 mil chamados
> reais para aprender."

### Bloco 2 — Objetivo (≈30s) | Slide de objetivo
> "Nosso objetivo: trocar reação por antecipação. Prever quais chamados vão
> estourar, projetar a demanda da semana, separar o ruído do sinal — e explicar
> cada decisão, porque ninguém confia em caixa-preta operando infraestrutura."

### Bloco 3 — Proposta de solução (≈1min) | Slides de arquitetura + placar
> "O LocaPredict SLA Guard v3 é uma plataforma AIOps em três visões: triagem com
> risco calibrado e SHAP verificado; forecast D+1 e D+7 com backtest; e MLOps com
> clusters validados e drift monitorado. E aqui a honestidade: na Sprint 3
> reportamos AUC 0,989 — era métrica de treino. A auditoria da Sprint 4 refez
> tudo: CV 0,85 com intervalo de confiança, SHAP de verdade, forecast comparado
> contra baseline. O placar honesto está na tela — e cada célula tem teste atrás."

### Bloco 4 — DEMO hands-on (≈2min) | App ao vivo, 3 cliques
1. **Fila (40s):** *"Cinquenta incidentes ordenados por probabilidade calibrada.
   Abro o INC8654273: o modal mostra base, versão do explicador e fidelidade —
   não tabela fixa."* (aponte os 3 campos com o mouse)
2. **Tático D+7 (40s):** *"WAPE de backtest contra baseline, teste de
   superioridade, pico datado pelo modelo. Nada digitado à mão."*
3. **Engenharia (40s):** *"Clusters com algoritmo e validade medidos; drift com
   p ajustado; e o retreino versionado — como admin. Como viewer, a mesma ação
   dá 403: governança de verdade."*

### Bloco 5 — Benefícios (≈30s) | Slide de impacto
> "Com triagem por risco, o ruído de 65% de chamados efêmeros vira fila
> automática; com forecast, escala se planeja antes do pico; com explicabilidade,
> operador confia e age. As reduções de 38% e 21% são projeções declaradas —
> o piloto controlado que vai medi-las é o próximo passo, não uma promessa."

### Bloco 6 — Conclusão e próximos passos (≈30s) | Slide final
> "Sólido não é perfeito — sólido é incapaz de mentir. Próximos passos: piloto
> com a operação, holdout de dezembro e medição causal dos ganhos. FusionOps:
> prever antes, provar sempre. Obrigado."

---

## 4. Checklist de gravação

- [ ] DB resetado (`locapredict.db` apagado + backend reiniciado + health `healthy`)
- [ ] Logado como operator; senha de admin à mão p/ o retreino da demo
- [ ] Notificações do SO desligadas; abas extras fechadas
- [ ] Ensaio cronometrado: 5:00 + margem (corte em 5:30 estoura)
- [ ] Revisão: números ditos = números do placar (0,85 / 0,84 / 13,4% / testes)
- [ ] Nomear o arquivo `Pitch_Final_FusionOps_GKL.mp4` e conferir áudio antes de enviar

## 5. Erros que derrubam a nota (evitar)

1. Dizer "AUC 0,989" ou "88,2%" sem o contexto da correção.
2. Chamar clusters de "HDBSCAN" sem dizer que a taxonomia não foi certificada.
3. Demo sem narrar o que está clicando (vídeo mudo de mouse não prova nada).
4. Prometer os −38,5%/−21,4% como resultado medido.
5. Estourar o tempo — ensaie com cronômetro, corte no bloco 5 se atrasar.
