# LocaPredict SLA Guard v3 — FusionOps Intelligence Platform
> **Sprint 4 — Solução Final & Entrega Técnica**  
> **Turma:** 2TSCOA | **Grupo:** GKL | **Parceiro:** Locaweb  
> **AIOps & Machine Learning para Previsão Preditiva de OLA, Clusterização Semântica e Observabilidade MLOps**

---

## 📌 1. Visão Geral Executiva

O **LocaPredict SLA Guard v3** é uma plataforma corporativa de **AIOps (Artificial Intelligence for IT Operations)** concebida para antecipar, diagnosticar e mitigar riscos de quebra de acordos de nível de serviço operacional (**OLA/SLA**) no ecossistema de infraestrutura e hospedagem da **Locaweb**.

Construído a partir de **122.543 chamados reais** da operação de suporte e datacenter da Locaweb, o sistema substitui a triagem manual reativa por uma arquitetura preditiva orientada a Machine Learning, explicabilidade e observabilidade contínua.

### Principais Impactos Aferidos (Gate 7 — rótulos honestos):
- **Ruído operacional / falsos positivos:** **38.5%** de chamados efêmeros segregáveis — **projeção** até piloto controlado (taxa medida de `is_fp` na base: 65.6%).
- **MTTR:** **21.4%** de redução — **projeção** até piloto controlado (RCT/DiD/ITS).
- **Discriminação (validação honesta):** **ROC-AUC 0.85 em CV estratificada 5-fold** com IC95% bootstrap + PR-AUC + Brier (sem ressubstituição; o 0.989 de treino é banido como evidência).
- **Forecast (backtest walk-forward):** **WAPE de holdout ≈ 14% por horizonte** vs. baseline seasonal-naive, com teste de Diebold-Mariano (sem WAPE constante).

---

## 🏛️ 2. Arquitetura da Solução

```
 ┌─────────────────────────────────────────────────────────────┐
 │                LocaPredict SLA Guard v3                     │
 └──────────────────────────────┬──────────────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌───────────────────────────────┐     ┌────────────────────────────────┐
│   Frontend AIOps (React 18)   │     │    Backend API (FastAPI)       │
│  - TypeScript & Vite          │     │  - REST API & WebSockets       │
│  - Design System Glassmorphic │     │  - JWT Bearer Token Auth & RBAC│
│  - Visão Operacional (NOC)    │◄───►│  - SQLite Transacional & Audit │
│  - Visão Tática (Forecast)    │     │  - Parquet Ingestion (122k)    │
│  - Visão Engenharia (MLOps)   │     │  - Real-time Stream Engine     │
└───────────────────────────────┘     └───────────────┬────────────────┘
                                                      │
                       ┌──────────────────────────────┴──────────────────────────────┐
                       ▼                                                             ▼
        ┌─────────────────────────────┐                               ┌─────────────────────────────┐
        │   ML Inference & Explainer  │                               │    MLOps & Observability    │
│ - TF-IDF Vectorizer (NLP)   │                               │ - KS Drift c/ Holm (6 feats)  │
│ - Random Forest + Isotonic  │                               │ - HDBSCAN validado + DBCV     │
│ - SHAP TreeExplainer real   │                               │ - Regime versionado (v1)      │
│ - Forecaster sazonal+backtest│                              │ - Retreino versionado         │
        └─────────────────────────────┘                               └─────────────────────────────┘
```

---

## 💻 3. Como Executar a Solução

### Opção A — Execução Rápida em 1 Clique (Windows)
Basta clicar duas vezes no script:
```bash
start_all.bat
```
O script iniciará automaticamente o **Backend FastAPI** na porta `8000` e o **Frontend React** na porta `5173`.

---

### Opção B — Execução Manual

#### 1. Pré-requisitos
- Python 3.10+ instalado
- Node.js 18+ instalado

#### 2. Backend (FastAPI + ML Engine)
```bash
# Na raiz de LocaPredict
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

#### 3. Frontend (React 18 + Vite)
```bash
cd frontend
npm install
npm run dev
```
- Acesso à Aplicação: [http://localhost:5173](http://localhost:5173)

---

### Opção C — Execução Containerizada (Docker)
```bash
docker-compose up --build
```
- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend: [http://localhost:8000](http://localhost:8000)

---

## 🧪 4. Suíte de Testes Automatizados

A plataforma conta com uma suíte de testes unitários e de integração cobrindo autenticação e matriz RBAC, rotas de API, inferência calibrada de Machine Learning, fidelidade SHAP (TreeExplainer), backtest de forecast, reconciliação de clusters, drift Kolmogorov-Smirnov com correção de Holm, endurecimento de segurança e completude de auditoria:

```bash
pytest
```
*33 testes automatizados passando com 100% de sucesso.*

---

## 📊 5. As 3 Visões da Plataforma

1. **Visão Operacional (Triagem NOC / Fila Prioritária):**
   - Fila ordenada por risco calibrado de quebra de OLA (`round(100·p_calibrada)`).
   - Indicador dinâmico de **Regime Operacional** versionado (`regime-v1`).
   - **Explicabilidade SHAP verificada (Waterfall Modal):** atribuições `shap.TreeExplainer` com valor-base, versão e fidelidade top-k — sem tabelas fixas de pesos.
   - Ações táticas imediatas com recalibração e auditoria before/after: Reatribuição de squad, Notificação de alerta NOC e Escalação de prioridade.

2. **Visão Tática (Planejamento & Forecast de Demanda):**
   - Curvas de volume histórico vs projeção do forecaster sazonal ajustado, com WAPE de backtest vs. baseline, teste de Diebold-Mariano e intervalos de confiança de 95% (horizontes D+1 e D+7).
   - **Demanda projetada por Squad:** participação medida na demanda (sem teto nominal por squad medido — percentuais de saturação não são afirmados).
   - Prescrições táticas para remanejamento de analistas e janelas preventivas de plantão.

3. **Visão Engenharia (MLOps & Clusters):**
   - **Clusters validados por HDBSCAN:** taxonomia de 5 perfis com DBCV, estabilidade bootstrap, sobreposição de Jaccard e taxas de falsos positivos medidas (reconciliação ±1% com o loader).
   - **MLOps & Drift Observability:** testes de Kolmogorov-Smirnov com correção de Holm sobre 6 features reais, janelas simétricas versionadas.
   - **Retreinamento em 1 Clique:** pipeline idempotente e versionado (CV, PR-AUC, IC bootstrap, Brier, limiar, hash de artefato).

---

## 👥 6. Identificação do Grupo (FIAP ON)

- **Grupo:** GKL (FusionOps)
- **Turma:** 2TSCOA
- **Challenge:** Locaweb (2026)
