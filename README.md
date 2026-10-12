# Zion Smart DCA — protótipo educacional para Bitcoin

Criado por **Rony Costa (Zion)**, fundador do [CriptoZion](https://criptozion.xyz). Metodologia e projeto de software em evolução para organização de aportes, gestão de caixa e decisões baseadas em regras.

Este repositório público reúne um motor em Python, um dashboard HTML e arquivos de simulação e backtesting. O projeto foi preparado para o contexto do BNB Hack 2026; isso não comprova premiação, auditoria ou operação financeira autônoma em produção.

## O que existe e qual é o estágio

| Componente | Evidência nos arquivos | Estágio e limite |
|---|---|---|
| Motor de decisão | [src/strategy.py](src/strategy.py) e [entrada CLI](src/zion_dca_skill.py) | Calcula decisões a partir dos sinais recebidos; não comprova execução de ordens reais. |
| Dashboard educacional | [dashboard/index.html](dashboard/index.html) | Consulta preço/Fear & Greed em APIs públicas; RSI e indicadores on-chain são simulados. Valores de contingência e visualizações não devem ser confundidos com dados atuais validados. |
| Backtesting | [backtest/](backtest/) | Experimento histórico com cache de preços e índice de sentimento real ou proxy. Exige revisão de premissas antes de comparar estratégias. |
| Adaptador de dados | [src/mcp_client.py](src/mcp_client.py) | Usa APIs REST; o handshake MCP está marcado como TODO. Não é integração MCP completa. |
| API e jobs de agentes | [src/server.py](src/server.py) e [src/commerce.py](src/commerce.py) | Protótipos. O código descreve verificação e liberação de escrow como etapas de uma implementação completa futura. |

## Comece pelo dashboard

O link para o HTML no GitHub mostra o código-fonte. Para ver a interface, baixe ou clone o projeto e sirva a pasta localmente. Não é necessário instalar as dependências da aplicação Python para esse caminho.

```sh
git clone https://github.com/Fealtycripto/zion-smart-dca-skill.git
cd zion-smart-dca-skill
python -m http.server 8765 --bind 127.0.0.1
```

Abra [http://127.0.0.1:8765/dashboard/](http://127.0.0.1:8765/dashboard/) no navegador. O dashboard usa fontes/CDNs e APIs externas; não é totalmente offline. Encerre o servidor com `Ctrl+C`.

**Validação documental em 12/10/2026:** o caminho de servidor estático e a renderização local foram conferidos. Isso não valida os cálculos da estratégia, a disponibilidade de cada API ou a atualidade de todos os indicadores.

## CLI e API Python — instruções ainda não revalidadas

O código declara Python 3.11+ e dependências em [requirements.txt](requirements.txt), atualmente sem versões fixadas. A instalação completa e a execução com serviços externos não foram revalidadas nesta revisão documental.

Se for avaliar a CLI, use um ambiente virtual local:

```sh
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

No Linux/macOS, use `source .venv/bin/activate` e `cp .env.example .env`. O [.env.example](.env.example) existe; preencha somente sua configuração local. Não envie `.env`, chaves ou credenciais ao GitHub.

Comandos presentes na interface do código, **não executados nesta revisão**:

```sh
python src/zion_dca_skill.py --budget 100 --frequency weekly
python src/zion_dca_skill.py --budget 50 --frequency daily
python backtest/backtest.py --budget 100 --start 2021-01-01
```

O backtest pode consultar fontes externas e sobrescrever relatórios locais. Leia o código e preserve os resultados existentes antes de executá-lo. Registro on-chain, conexão de carteiras e pagamento de jobs não fazem parte deste início rápido.

## Simulação, dados e versões

Os [resultados históricos](backtest/results_summary.json), o [relatório](backtest/report.md) e a [simulação de período](docs/live_simulation.json) são artefatos experimentais. Dados reais de mercado como entrada não transformam uma simulação em histórico de investimentos reais ou paper trading acompanhado em tempo real.

Há uma divergência de versão pública a resolver: a apresentação dos pilares abaixo usa **v4.2**, enquanto o resultado salvo e partes do Python identificam **v4.0**. O resultado salvo declara divisão **70/30**; o texto v4.2 descreve o multiplicador aplicado à base integral. Os aportes totais das estratégias comparadas no JSON também diferem. Portanto, esse resultado não comprova desempenho da v4.2 nem uma comparação com fluxos de caixa equivalentes.

Antes de tirar conclusões, documente versão, período, origem e qualidade dos dados, proxy de sentimento, capital/reserva, frequência, taxas e slippage. Custos, execução e comparabilidade não foram auditados nesta revisão.

## Referência técnica existente

Os pilares, multiplicadores, limites e as 12 regras a seguir foram preservados do README anterior. Descrevem a versão apresentada pelo projeto e não são recomendação personalizada nem validação das divergências acima. Esta revisão altera somente documentação.

### Pillar 1 — Smart DCA (F&G Multiplier)

The F&G multiplier applies **directly** to your full DCA base amount. Surplus/deficit flows to and from the Buildup Reserve automatically.

| Signal | F&G Range | Multiplier | DCA (base $100) | Reserve Flow |
|--------|-----------|------------|-----------------|--------------|
| 😱 Extreme Fear | 0–24 | **2.0x** | $200 | Extra FROM Reserve |
| 😰 Fear | 25–44 | **1.5x** | $150 | Extra FROM Reserve |
| 😐 Neutral | 45–55 | **1.0x** | $100 | No movement |
| 😊 Greed | 56–74 | **0.75x** | $75 | Surplus TO Reserve |
| 🤑 Extreme Greed | 75–100 | **0.5x** | $50 | Surplus TO Reserve |

> **v4.2 Change:** No more 70/30 budget split. The multiplier applies to 100% of your DCA base. Surplus from greed periods flows directly to the Buildup Reserve. Deficit during fear is funded from the reserve.

### Pillar 2 — Buildup Reserve (Double-Layer Confirmation)

Buildup activates only when **both conditions** are met:
1. **RSI daily < 35** (oversold)
2. **Context filters pass** — at least one of: price above 200WMA, MVRV < 1.0, ATH drop > 50%

**Execution rules:**
- Max 3 orders per week
- Max 1 order per day
- 2.5% gap between limit orders
- Limit orders only (no market orders)

### Pillar 3 — Scaling Out (Dual Confirmation)

Scaling out requires **both**:
1. **RSI weekly > 70** (overbought on weekly timeframe)
2. **Secondary confirmation** — at least one of: Pi Cycle Top, MVRV > 7, BTC Dominance < 40%

- Sell 10–20% per signal
- Max 2 signals per month
- 14-day cooldown between sells

### Pillar 4 — Meta Reversa Calculator

Work backwards from your BTC goal. Set a target (e.g., 0.5 BTC), timeline (e.g., 4 years), and your weekly budget — the engine calculates exactly what you need, factoring in Smart DCA boosts, and shows how current market conditions accelerate or slow your progress.

---

## The 12 Rules

1. **DCA Base** — fixed amount per period (daily/weekly/biweekly/monthly), no excuses
2. **RSI Buildup Trigger** — RSI < 35 + context filters (200WMA, MVRV, ATH%) activates Buildup mode
3. **F&G Multiplier Scale** — 0.5x to 2.0x applied directly to full DCA base (v4.2)
4. **Buildup Reserve** — surplus from greed periods flows to reserve; deficit in fear draws from reserve
5. **Never Sell Below PM** — never sell below average buy price (non-negotiable)
6. **Income Scaling** — extra income ÷ 4 = DCA increase
7. **BTC Floor (50%)** — portfolio never goes below 50% BTC
8. **Zero Leverage** — no margin, no futures, no exceptions
9. **Limit Orders Only** — Buildup buys use limit orders for best execution
10. **No Emotion** — system decides, not feelings
11. **Mandatory Logging** — every trade recorded with full context
12. **Monthly Review** — adjust budget, check reserve, verify allocation

## Black Swan Protocol

4 types of black swan events with specific responses:

| Type | Trigger | Response |
|------|---------|----------|
| 🔴 Exchange Collapse | Major CEX insolvency | Withdraw all to cold storage, halt DCA 7 days |
| 🟠 Regulatory Shock | Major country ban/restriction | Reduce position 50%, wait for clarity |
| 🟡 Flash Crash | BTC drops >30% in 24h | Deploy 100% reserve immediately |
| ⚫ Black Monday | Crypto + TradFi simultaneous crash | Full defensive — cash only for 14 days |

## Limitações e próximos passos

- Reconciliar v4.0/v4.2 e identificar exatamente qual implementação gerou cada resultado, sem mudar parâmetros silenciosamente.
- Rotular dados reais, proxies e simulações também no dashboard e nos relatórios gerados.
- Validar custos, reserva e fluxos de caixa comparáveis antes de divulgar conclusões de backtest.
- Validar MCP e jobs ponta a ponta antes de declarar integração completa ou pagamentos on-chain disponíveis.
- Revalidar qualquer regra tributária com fontes oficiais atuais; os textos fiscais históricos do projeto não comprovam aplicabilidade.

As imagens em [docs/screenshots/](docs/screenshots/) são capturas já existentes do protótipo, não evidência de resultados financeiros reais. A documentação técnica da skill está em [SKILL.md](SKILL.md).

## Tecnologias e licença

Python, pandas, NumPy, requests, python-dotenv, yfinance, matplotlib, FastAPI e bnbagent constam dos arquivos/dependências. O dashboard usa HTML/CSS/JavaScript e Chart.js.

Licença existente: [MIT](LICENSE). Preserve o aviso de copyright e os termos da licença nas reutilizações pertinentes. Serviços de dados têm termos próprios.

## Autor e links

**Rony Costa (Zion)** ([@Fealtycripto](https://github.com/Fealtycripto)), conhecido também como Fealty. Empreendedor, criador de conteúdo, fundador do [CriptoZion](https://criptozion.xyz) e criador da **Zion Smart DCA**, metodologia e projeto de software em evolução.

Versão editorial **BIO-1.0**. [Minicurrículo público](https://github.com/Fealtycripto/Fealtycripto/blob/main/MINICURRICULO.md). A versão editorial não altera a versão operacional ou as regras do projeto.

**English:** Experimental Bitcoin DCA tools: Python engine, educational dashboard and historical simulations. Some indicators are simulated; MCP and on-chain job settlement are incomplete. Saved backtests require version and cash-flow reconciliation before performance claims.

Conteúdo educacional. Backtests não garantem retorno e não comprovam resultados reais.
