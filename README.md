# Coletor-SUAP 📑

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Playwright](https://img.shields.io/badge/Playwright-1.49.0-green.svg)](https://playwright.dev/python/)

O **Coletor-SUAP** é uma ferramenta de automação robusta desenvolvida para facilitar a extração e consolidação de dados de produção de pesquisa do IFBA (Instituto Federal da Bahia).

## ✨ Funcionalidades

- **Fluxo em Etapas**: Interface intuitiva dividida em Login, Configuração e Monitoramento.
- **Automação Inteligente**: Login e navegação automática no sistema SUAP via Playwright.
- **Filtro por Campus**: Escolha baixar dados de um campus específico (via sigla) ou de toda a instituição.
- **Coleta Incremental**: Suporte para download de períodos curtos com integração automática na base acumulada.
- **Deduplicação Automática**: Mesclagem de novos dados com arquivos existentes, eliminando duplicatas e organizando registros.
- **Interface Premium**: Design elegante em preto e branco com tipografia Garamond e suporte a atalhos de período.
- **Monitoramento Real-time**: Acompanhamento detalhado do status da automação e tempo decorrido.

## 🛠️ Pré-requisitos

- Python 3.8 ou superior.
- Navegador Chromium (instalado automaticamente via Playwright).

## 🚀 Instalação e Configuração

### 1. Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/coletor-suap.git
cd coletor-suap
```

### 2. Inicialização Automática
O sistema conta com um script que configura o ambiente virtual e instala as dependências:
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

## 📁 Estrutura do Projeto

O projeto utiliza uma arquitetura organizada e modular:

- `main.py`: Ponto de entrada e rotas da aplicação.
- `app/`: Componentes do Frontend (Templates e Static).
- `core/`: Lógica central de automação e processamento.
  - `scraper.py`: Motor Playwright para extração de dados.
  - `processor.py`: Utilitário de mesclagem e deduplicação de Excel.
  - `background.py`: Orquestrador de tarefas assíncronas.
- `utils/`: Ferramentas de suporte (Logger).
- `data/`: Armazenamento de resultados.
  - `raw/`: Planilhas originais baixadas do SUAP.
  - `processed/`: Planilhas acumuladas e limpas (Master Files).
- `logs/`: Histórico técnico de execuções.

## 📖 Como Usar

1. Inicie o sistema através do `./start.sh`.
2. Acesse `http://localhost:5000`.
3. **Passo 1 (Login)**: Entre com sua matrícula e senha do SUAP.
4. **Passo 2 (Configuração)**:
   - Digite a sigla de um campus para filtrar ou deixe vazio para coletar todos.
   - Use os botões de atalho (ex: "Últimos 3 Anos") ou defina o intervalo manualmente.
5. **Passo 3 (Progresso)**: Acompanhe a coleta. Os arquivos finais estarão em `data/processed/`.

## ⚠️ Isenção de Responsabilidade

Esta ferramenta foi desenvolvida para fins de produtividade institucional. O uso deve respeitar as políticas de segurança do sistema SUAP e do IFBA. O desenvolvedor não se responsabiliza pelo uso indevido da ferramenta.

## 📄 Licença

Este projeto está sob a licença MIT.
