# AGENTS.md — Scraper SUAP CNPq (Produção Lattes)

## Fonte de Dados

- **Sistema**: SUAP/IFBA (módulo CNPq - Produção por Campus Detalhado)
- **URL**: `https://suap.ifba.edu.br/cnpq/producao_por_campus_detalhado/`
- **Autenticação**: Login SUAP (username + password)
- **Tecnologia**: Playwright (headless Chromium)

## Dados Coletados

Planilhas Excel por campus com abas:
| Aba | Conteúdo |
|-----|----------|
| Produções Bibliográficas | Artigos, livros, capítulos, trabalhos em eventos |
| Produções Técnicas | Software, patentes, consultorias, extensão |
| Registros e Patentes | Registros de propriedade intelectual — ainda baixada, mas o dashboard não a consome desde ago/2026 (Inovação vem do INPI) |
| Orientações Concluídas | Teses, dissertações, iniciação científica |
| Orientações em Andamento | Orientações vigentes |

## Campi (26 + Reitoria)

BAR, BRU, CAM, CFO, EC, EUN, FS, ILH, IRE, ITA, JAC, JAG, JEQ, JUA, LF, PA, PIS, PS, SAJ, SAM, SEA, SF, SSA, UBA, VAL, VC + REI (e IFBA, PO, códigos legados de planilhas vazias)

O SUAP exibe FS, PA, VC e PS como FSA, PAF, VDC e PSG. `core/siglas.py` guarda o mapa
(`SUAP_PARA_DASHBOARD`) e a cópia de `CODIGOS_VALIDOS` do dashboard
(`CODIGOS_DASHBOARD`); campus novo precisa entrar lá e em `CAMPUS_TO_CITY` do
`dashboard-prpgi`.

## Execução

- **CLI** (usado nas coletas reais): `python scripts/coletar-suap.py [ini] [fim]
  [--anos A B ...] [--campus SIGLA] [--sincronizar]`. Lê `SUAP_USER` (e
  `SUAP_PASS`, ou a senha no cofre do sistema, serviço `suap`) do `.env`.
- **Web**: `./start.sh` → Flask em `http://localhost:5000`. A senha fica só na
  memória do processo, nunca no cookie de sessão.
- `SUAP_TABLE_TIMEOUT_MIN` (padrão 10): espera pela tabela antes de marcar o
  campus como "sem produção".
- Testes sem rede: `python -m pytest -q` (também no CI, `.github/workflows/ci.yml`).

## Saída

- `data/raw/` → `[SIGLA]-[ano_inicio]-[ano_fim].xls` (raw downloads)
- `data/processed/` → `[SIGLA].xlsx` (merged, deduplicado, já com o código do dashboard)

## Projetos Consumidores

- **dashboard-prpgi** → `dados/scraper-SUAPCNPQ/[SIGLA].xlsx` → `data.json`
  (abas Produção Científica, Produção Técnica e Orientações). O `--sincronizar`
  copia só os mestres de código aceito pelo dashboard.

## Fluxo

```
SUAP (suap.ifba.edu.br) → [Playwright login + download] → .xls raw
                                                              ↓
                                              processor.py → .xlsx merged
                                                              ↓
                                              dashboard-prpgi/build.js → data.json
```

## TODO.md

Este projeto mantém um `TODO.md` na raiz com o planejamento e acompanhamento das tarefas.
O agente é responsável por criar e manter este arquivo atualizado.

O arquivo `TODO.md` da raiz de `/home/davi/projetos/` consolida automaticamente os TODOs de todos os subprojetos.
Execute `python3 /home/davi/projetos/_gen_sumula.py` para regenerar a súmula consolidada após alterações neste TODO.md.

