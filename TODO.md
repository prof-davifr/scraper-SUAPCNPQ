# TODO — Coletor SUAP/CNPq (produção Lattes)

Coletor da produção declarada no Lattes, via SUAP/IFBA
(`cnpq/producao_por_campus_detalhado/`) — motor Playwright (`core/scraper.py`),
mesclagem incremental por campus (`core/processor.py`), interface Flask em três
etapas (`main.py` + `app/templates/`) e um modo CLI ainda fora do versionamento
(`scripts/coletar-suap.py`).

Alimenta as abas **Produção Científica**, **Produção Técnica** e **Orientações**
do `dashboard-prpgi`, através de `dados/scraper-SUAPCNPQ/{SIGLA}.xlsx`.

Onde termina a automação hoje (31/08/2026):

```
SUAP (relatório por campus)  →  data/processed/{SIGLA}.xlsx  →  dashboard-prpgi
        MANUAL/local                  AUTOMÁTICO                    MANUAL
 (credencial + rede do IFBA)      (merge incremental)          (cópia + build)
```

Última coleta: **21/08/2026** (2024–2026, 30 siglas). Último commit: **21/07/2026**.
A aba "Registros e Patentes" continua sendo baixada, mas o dashboard não a
consome mais — desde ago/2026 a aba de Inovação vem do INPI.

---

## 🟢 Concluído

### Coleta e consolidação
- [x] **`core/scraper.py`** — login no SUAP, leitura da lista de campi do
      `<select>`, filtro por sigla ou por `value`, seleção do período
      (`inicio_periodo`/`fim_periodo`), submit do relatório, download do `.xls`
      para `data/raw/{SIGLA}-{ini}-{fim}.xls` e **3 tentativas por campus**.
- [x] **`core/processor.py`** — `merge_production_data` acumula cada aba sobre o
      mestre `data/processed/{SIGLA}.xlsx`, deduplicando; `logs/run.log` mostra a
      mesclagem aba a aba ("combinando N novos com M existentes") para os 30
      mestres da rodada de 21/08.
- [x] **Interface Flask em três etapas** (login → setup → progresso) com
      execução em segundo plano (`core/background.py`) e `scripts/start.sh`
      criando venv, instalando dependências e o Chromium do Playwright.
- [x] **`AGENTS.md`** (commit `4f893a7`, 21/07/2026) — fonte, abas coletadas,
      lista de campi, saída e projeto consumidor.

### Rodada de 21/08/2026
- [x] **Coleta 2024–2026 concluída** — `data/raw/` tem 30 arquivos
      `*-2024-2026.xls` e `data/processed/` tem 30 mestres. IFBA (matriz) e PO
      não geram tabela: `logs/run.log` os registra como "sem produção".
- [x] **Mestres sincronizados com o dashboard** — os 30 `.xlsx` de
      `dashboard-prpgi/dados/scraper-SUAPCNPQ/` batem por md5 com
      `data/processed/` (conferido em FS e ITA). A cópia foi manual, arquivo a
      arquivo — ver backlog.
- [x] **Campus sem produção deixou de travar a coleta** — o `wait_for_selector`
      da tabela usava o limite de 120 min, três vezes; um campus sem produção
      nunca renderiza a tabela e segurava a fila por até 6 horas. Novo
      `TABLE_TIMEOUT` (10 min, ajustável por `SUAP_TABLE_TIMEOUT_MIN`) marca como
      "sem produção" e segue — validado em produção nas linhas de IFBA e PO do
      `run.log`. **A correção ainda não está commitada** (item 1 do backlog).
- [x] **Credencial nunca foi versionada** — `git log --all -- .env` volta vazio e
      o arquivo está em `600`. A regra correspondente no `.gitignore` ainda está
      fora do versionamento (item 1 do backlog).

---

## 📋 Backlog

- [x] **Decidir o destino das 4 alterações fora do versionamento — o `HANDOFF.md` guarda a credencial do SUAP em texto claro.**
      Resolvido em 20/09/2026. O `.gitignore`, o `core/scraper.py` e o
      `scripts/coletar-suap.py` foram commitados. O `HANDOFF.md` continua na
      máquina, agora sem a senha no texto e listado no `.gitignore`. A
      verificação confirmou que a credencial nunca entrou no histórico, nem
      aqui nem no remoto público. **Falta trocar a senha do SUAP**: ela ficou
      meses em arquivo de texto sem proteção. Registro original:
      - `.gitignore` — passa a ignorar o `.env`. Commitar.
      - `core/scraper.py` — o `TABLE_TIMEOUT` descrito acima. Commitar.
      - `scripts/coletar-suap.py` — modo CLI headless: lê usuário e senha do
        `.env`, valida o login com `fetch_campus_list`, coleta ano a ano
        (`--anos`, `--campus`) e, com `--sincronizar`, copia os mestres para o
        dashboard. É o que foi realmente usado na rodada de 21/08. Commitar
        depois de resolver o item seguinte.
      - `HANDOFF.md` — nota de passagem de 13/08 com o roteiro da coleta
        2023–2026. **Traz usuário e senha do SUAP em texto claro e não está no
        `.gitignore`**: um `git add -A` publicaria a credencial no repositório,
        que é público. Os passos que ele lista já foram concluídos em 21/08.
        Apagar ou mover para fora da árvore do repositório, e trocar a senha —
        ela circulou em arquivo de texto sem proteção.
- [x] **`--sincronizar` copia siglas obsoletas e derruba o build do dashboard.**
      Resolvido em 04/10/2026. O `--sincronizar` passa os mestres por
      `separar_para_sincronizar` (`core/siglas.py`): copia só os códigos de
      `CODIGOS_VALIDOS` e lista, com aviso, os que ficaram de fora — hoje
      `FSA`, `PAF` e `VDC` (27 de 30 mestres seguem para o dashboard). Registro
      original:
      `data/processed/` tem 30 mestres, entre eles `FSA`, `PAF` e `VDC` — siglas
      antigas de Feira de Santana, Paulo Afonso e Vitória da Conquista, cujo
      conteúdo já foi mesclado em `FS`, `PA` e `VC`. Nenhuma das três está em
      `CODIGOS_VALIDOS` (`dashboard-prpgi/scripts/validate-data.js`), então
      `npm run build` aborta. Foi por isso que a sincronização de 21/08 saiu à
      mão. Falta o script filtrar as siglas válidas antes de copiar.
- [x] **Não existe, em código, o mapa sigla do SUAP → código do dashboard.**
      Resolvido em 04/10/2026. `core/siglas.py` guarda `SUAP_PARA_DASHBOARD`
      (FSA→FS, PAF→PA, VDC→VC) e a cópia de `CODIGOS_VALIDOS`;
      `merge_production_data` grava o mestre já com o código do dashboard e
      registra `AVISO` no log para sigla fora dos dois. Testes em
      `tests/test_siglas.py`, rodados também no CI. Registro original:
      Quando o SUAP renomeou FS→FSA, PA→PAF e VC→VDC, o coletor abriu mestres
      novos, sem histórico, e o conserto (rodar `merge_production_data` dos
      arquivos antigos sobre os mestres) foi manual — o primeiro build do
      dashboard chegou a perder 1094 registros técnicos. Se o SUAP renomear de
      novo, a perda é silenciosa. Guardar o mapa em um lugar só e avisar quando
      aparecer sigla desconhecida.
- [ ] **A coleta continua manual e local — falta decidir cadência e onde roda.**
      Depende da credencial do SUAP e de rede que resolva `suap.ifba.edu.br` (a
      rodada de 08/08 perdeu campi com `ERR_NAME_NOT_RESOLVED`). O runner público
      do GitHub não alcança o SUAP: automatizar exige runner auto-hospedado na
      rede do IFBA guardando a credencial — a mesma decisão pendente no
      `scraper-DGP`, e o que o `dashboard-prpgi` registra como "Lattes/SUAP ainda
      exigem exportação manual por campus". Enquanto não se decide, definir de
      quanto em quanto tempo rodar `scripts/coletar-suap.py` à mão: a base do
      dashboard está congelada em 21/08/2026.
- [ ] **Sem CI e sem teste automatizado.** `.github/workflows/` não existe e não
      há suíte. Vale um workflow enxuto: importar os módulos (pega quebra de
      dependência e de assinatura, como o `xlrd` pela metade que já zerou uma
      exportação no `scraper-SUAPPos`) e rodar `merge_production_data` sobre um
      fixture pequeno e sem dado pessoal. Mudança de HTML do SUAP, essa só um
      runner dentro da rede institucional pegaria.
- [x] **A senha do SUAP é guardada na sessão do Flask (`main.py`).**
      Resolvido em 18/10/2026. A senha fica só na memória do processo
      (`_credenciais` em `main.py`) e o cookie leva apenas uma chave aleatória
      (`secrets.token_urlsafe`); novo login descarta a chave anterior e, com o
      servidor reiniciado, a chave antiga deixa de abrir o `/setup`.
      `tests/test_main.py` decodifica o cookie e confere que a senha não está
      lá, com credencial inventada e dublês no lugar do SUAP. Registro original:
      a sessão do Flask é assinada, não criptografada: quem tiver o cookie lê a senha. Guardar
      apenas um identificador do lado do servidor, ou entregar a credencial direto
      ao worker de segundo plano.
- [x] **Campus novo ainda derruba o build sem aviso prévio.**
      Resolvido em 18/10/2026. `siglas_fora_do_dashboard` (`core/siglas.py`)
      compara a lista de campi do SUAP com `CODIGOS_DASHBOARD` e o mapa; o
      `scripts/coletar-suap.py` mostra o aviso logo depois do login e repete no
      fim da coleta. Somado ao `AVISO` do `merge_production_data` e ao filtro do
      `--sincronizar`, campus novo não chega mais ao `npm run build`. A cópia de
      `CODIGOS_VALIDOS` bate com `CAMPUS_TO_CITY` do dashboard (conferido em
      18/10/2026, 26 códigos + IFBA, REI e PO). Teste em `tests/test_siglas.py`.
      Registro original: Itabuna (ITA) foi
      mapeado no dashboard em ago/2026, mas o SUAP já lista 29 campi e há outros
      em construção (Cajazeiras, Macaúbas, Poções). O coletor deveria terminar
      listando as siglas que o dashboard não conhece; hoje isso só aparece quando
      `npm run build` aborta, do outro lado da cerca.
- [x] **`AGENTS.md` e `README.md` desatualizados.**
      Resolvido em 18/10/2026. O `AGENTS.md` marca "Registros e Patentes" como
      baixada mas não consumida, traz ITA na lista de campi, o mapa de siglas e a
      seção "Execução" (CLI, web, `SUAP_TABLE_TIMEOUT_MIN`, testes). O
      `README.md` ganhou a URL real do clone, o `.env` e o cofre do sistema, o
      modo CLI com `--anos`/`--campus`/`--sincronizar`, o
      `SUAP_TABLE_TIMEOUT_MIN` e as abas que o dashboard consome. Registro
      original: o `AGENTS.md` anuncia
      "Registros e Patentes" como entregável, mas o dashboard passou a tirar
      Inovação do INPI e ignora essa aba. O `README.md` documenta só a interface
      web: não menciona o `.env`, o modo CLI, o `SUAP_TABLE_TIMEOUT_MIN` nem a
      sincronização com o dashboard, e ainda traz uma URL de clone genérica.
- [ ] **`data/raw/` acumula 158 `.xls` (~55 MB) sem política de expurgo** — seis
      períodos por campus (2000-2026, 2023-2023, 2024-2024, 2024-2026, 2025-2025,
      2026-2026). É só disco local, porque `data/` está no `.gitignore`, mas o
      reprocessamento em lote do `processor.py` varre tudo e recriaria os mestres
      com as siglas antigas. Decidir o que guardar e o que descartar.
