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
| Registros e Patentes | Registros de propriedade intelectual |
| Orientações Concluídas | Teses, dissertações, iniciação científica |
| Orientações em Andamento | Orientações vigentes |

## Campi (25 + Reitoria)

BAR, BRU, CAM, CFO, EC, EUN, FS, ILH, IRE, JAC, JAG, JEQ, JUA, LF, PA, PIS, PS, SAJ, SAM, SEA, SF, SSA, UBA, VAL, VC + Reitoria

## Saída

- `data/raw/` → `[SIGLA]-[ano_inicio]-[ano_fim].xls` (raw downloads)
- `data/processed/` → `[SIGLA].xlsx` (merged, deduplicado)

## Projetos Consumidores

- **dashboard-prpgi** → `dados/scraper-SUAPCNPQ/[SIGLA].xlsx` → `data.json`

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

