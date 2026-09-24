# FusionOps — LocaPredict SLA Guard v3

Plataforma **AIOps** (AI for IT Operations) construída sobre **122.543 chamados reais**
de ITSM da **Locaweb**: em vez de triagem manual reativa, o sistema **prevê risco de
quebra de OLA/SLA**, **projeta demanda (D+1/D+7)**, **agrupa ruído operacional** e
**explica cada previsão** — com validação honesta auditável (Constituição v1.1.0).

**Em uma frase:** dados históricos de incidentes viram fila priorizada por probabilidade
calibrada, forecast com backtest e clusters medidos — tudo com proveniência exibida na tela.

---

## 1. As 3 visões (o que você vai ver)

| Visão | Para quem | O que entrega |
|---|---|---|
| **Operacional** (Triagem NOC) | Operadores/NOC | Fila por risco calibrado, modal SHAP verificado (`TreeExplainer`), reatribuição/escalação com auditoria |
| **Tática** (Forecast) | Gestores | Demanda D+1/D+7 com WAPE de backtest vs. baseline, teste de Diebold-Mariano, participação por squad |
| **Engenharia** (MLOps) | SRE/dados | Clusters com validação HDBSCAN, drift KS com correção de Holm, retreino versionado |

**Números honestos (não slogans):** ROC-AUC 0,85 em CV 5-fold (IC95% bootstrap),
recall 0,84 @ τ=0,04, WAPE de backtest ≈13,4%, 36/36 testes. Ganhos de −38,5% (FP)
e −21,4% (MTTR) são **projeções rotuladas**, pendentes de piloto controlado.

---

## 2. Pré-requisitos

- **Python 3.10+** (`python --version`) · **Node.js 18+** (`node --version`) · Git (para o deploy)
- Portas livres: **8000** (API) e **5173** (interface)
- Opcional p/ Docker: Docker Desktop

---

## 3. Instalação e execução local

### Opção A — 1 clique (Windows, recomendado p/ avaliar)

```cmd
cd LocaPredict
start_all.bat
```

Abre backend (`http://127.0.0.1:8000`) e frontend (`http://localhost:5173`).
Na primeira vez, instale as dependências (Opção B, passos 1–2) antes.

### Opção B — Manual (qualquer SO)

```bash
cd LocaPredict

# 1. Backend
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
# -> Swagger: http://127.0.0.1:8000/docs | Health: http://127.0.0.1:8000/api/v1/health

# 2. Frontend (outro terminal)
cd frontend
npm install
npm run dev
# -> App: http://localhost:5173
```

No primeiro boot o backend ingere o Parquet, treina (CV + calibração + backtest,
~15–60 s) e recalibra a fila — aguarde o `health` responder `healthy`.

### Opção C — Docker (serviço único: API + SPA na mesma URL)

```bash
cd LocaPredict
docker build -t locapredict .
docker run -p 8000:8000 -e ENV=production -e JWT_SECRET=<segredo-32+-bytes> locapredict
# -> App + API em http://localhost:8000  (SPA servido na raiz, /docs intacto)
```

> Sem Docker na máquina? O build também roda no Render (ver `Dockerfile` na raiz de `LocaPredict`).

---

## 4. Primeiro acesso (login + tour de 5 min)

Login exige **usuário qualquer + senha do papel** (ambiente local usa as senhas de
demonstração; sem senha = 401):

| Papel | Senha (dev) | Pode |
|---|---|---|
| `admin` | `dev-only-admin-passphrase-change-me` | tudo, incl. retreino |
| `operator` | `dev-only-operator-passphrase-change-me` | triagem, reatribuir, escalar |
| `viewer` | `dev-only-viewer-passphrase-change-me` | somente leitura (mutações = 403) |

**Tour:** ① fila → modal SHAP do `INC8654273` (base, versão, fidelidade) →
② Tático D+7 (WAPE holdout vs. baseline) → ③ Engenharia (algoritmo/DBCV dos
clusters, p-ajustado do drift) → ④ **Simular Chamado** → reatribua e veja o risco
recalibrar → ⑤ exporte o CSV.

---

## 5. Validar que está tudo certo

```bash
cd LocaPredict
python -m pytest backend/tests -q        # 36 testes (auth, API, ML, drift, segurança)
cd frontend && ./node_modules/.bin/tsc --noEmit   # ou: npm run build
```

---

## 6. Estrutura do repositório

```
FusionOps/
├── LocaPredict/                 # aplicação (código que roda)
│   ├── backend/                 # FastAPI: api/, auth/, core/, db/, models/, services/, tests/
│   ├── frontend/                # React 18 + Vite + TypeScript
│   ├── data/                    # locaweb_clean.parquet (6,9 MB) + LW-DATASET.xlsx
│   ├── docs/                    # artigo, relatório de remediação (PDFs), roteiro da apresentação
│   ├── specs/ (raiz)            # especificação, plano, tarefas e Constituição v1.1.0
│   ├── Dockerfile               # imagem single-service (Render)
│   └── start_all.bat            # 1 clique no Windows
├── specs/001-locapredict-sla-guard/  # spec, plan, research, tasks, contracts, quickstart
└── .specify/                    # Constituição v1.1.0 e governança
```

Documentação funda: `LocaPredict/docs/Relatorio_Rigoroso_Remediacao_LocaPredict.pdf`
(como cada furo foi provado e corrigido) e `Roteiro_Storytelling_Apresentacao_Final.md`.

---

## 7. Solução de problemas

| Sintoma | Causa provável | Correção |
|---|---|---|
| Porta 8000/5173 ocupada | uvicorn/vite residual | Encerre o processo antigo e suba de novo |
| Boot lento no 1º acesso | treino + HDBSCAN lazy | Normal (~1 min); `health` avisa quando pronto |
| Fila zerada após testes | banco local com estado mutado | Apague `LocaPredict/locapredict.db` e reinicie (reingestão + recalibração automáticas) |
| `JWT_SECRET ... Startup refused` | `ENV=production` sem segredo | Exporte `JWT_SECRET` (32+ bytes) — fail-closed proposital |
| Demo role-switch falha em prod | `/auth/demo-token` retorna 404 em produção | Comportamento esperado; use login com senha |
| Riscos baixos (1–17%) | fila atual é ~100% ruído FP — saída correta | Ordenação continua válida; simule P1/P2 p/ ver sinais altos |
| Cold start na nuvem free | plano free dorme | ~1–3 min no 1º acesso; auditoria SQLite zera a cada restart (declarado) |
