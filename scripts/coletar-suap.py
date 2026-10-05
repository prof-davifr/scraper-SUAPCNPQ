#!/usr/bin/env python3
"""Coleta produção do SUAP (via login_and_scrape) e sincroniza com o dashboard.

Uso:
  python scripts/coletar-suap.py [ano_inicio] [ano_fim] [--sincronizar]

Lê credenciais do .env (SUAP_USER, SUAP_PASS).
--sincronizar: após coletar, copia os master files para dashboard-prpgi/dados/
               (só os de sigla que o dashboard aceita — ver core/siglas.py)
"""
import os, sys, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load_env(path):
    if not path.exists():
        print(f"ERRO: {path} não encontrado. Crie com SUAP_USER (e SUAP_PASS, ou a senha no cofre).", file=sys.stderr)
        sys.exit(1)
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

load_env(ROOT / '.env')


def senha_do_cofre(usuario):
    """Senha do SUAP no cofre do sistema (servico 'suap'), se houver."""
    if not usuario:
        return None
    try:
        import keyring
        return keyring.get_password('suap', usuario)
    except Exception:
        return None


USER = os.environ.get('SUAP_USER')
PASS = os.environ.get('SUAP_PASS') or senha_do_cofre(USER)
if not USER or not PASS:
    print("ERRO: SUAP_USER ausente no .env, ou senha ausente (SUAP_PASS no .env ou "
          "'keyring set suap <matricula>')", file=sys.stderr)
    sys.exit(1)

YEAR_START = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else int(os.environ.get('SUAP_YEAR_START', '2024'))
YEAR_END = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else int(os.environ.get('SUAP_YEAR_END', '2026'))
SINCRONIZAR = '--sincronizar' in sys.argv
ANOS = None
if '--anos' in sys.argv:
    i = sys.argv.index('--anos')
    ANOS = [a for a in sys.argv[i + 1:] if a.isdigit()]
CAMPUS_FILTER = None
if '--campus' in sys.argv:
    CAMPUS_FILTER = sys.argv[sys.argv.index('--campus') + 1]

sys.path.insert(0, str(ROOT))
from core.scraper import login_and_scrape, fetch_campus_list, setup_dirs
from core.siglas import separar_para_sincronizar

def callback(status, campus=None):
    print(f"[{campus or '----'}] {status}", flush=True)

# 1. valida credenciais (login rápido)
print(f"Validando login SUAP ({USER})...", flush=True)
try:
    campi = fetch_campus_list(USER, PASS)
    print(f"Login OK — {len(campi)} campi disponíveis.", flush=True)
except Exception as e:
    print(f"FALHA NO LOGIN: {e}", file=sys.stderr)
    sys.exit(1)

# 2. coleta — por ano (período de 1 ano por vez, mais robusto)
if ANOS:
    for ano in ANOS:
        print(f"\n── Ano {ano} {'(' + CAMPUS_FILTER + ')' if CAMPUS_FILTER else ''} ────────────────────────", flush=True)
        login_and_scrape(USER, PASS, int(ano), int(ano), campus_filter=CAMPUS_FILTER, state_callback=callback)
else:
    print(f"\nColetando produção {YEAR_START}-{YEAR_END} para todos os campi...", flush=True)
    login_and_scrape(USER, PASS, YEAR_START, YEAR_END, campus_filter=CAMPUS_FILTER, state_callback=callback)

# 3. sincroniza com o dashboard
if SINCRONIZAR:
    _, processed = setup_dirs()
    dest = ROOT.parent / 'dashboard-prpgi' / 'dados' / 'scraper-SUAPCNPQ'
    dest.mkdir(parents=True, exist_ok=True)
    # Sigla antiga (FSA, PAF, VDC) ou desconhecida derruba o npm run build.
    copiar, ignorados = separar_para_sincronizar(sorted(Path(processed).glob('*.xlsx')))
    for f in copiar:
        shutil.copy2(f, dest / f.name)
    print(f"\nSincronizado: {len(copiar)} master files copiados para {dest}", flush=True)
    for f, motivo in ignorados:
        print(f"  AVISO: {f.name} não copiado — {motivo}.", flush=True)
    print("Agora rode: cd dashboard-prpgi && npm run build", flush=True)

print("\nColeta concluída.", flush=True)
