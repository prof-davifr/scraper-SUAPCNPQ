"""
Siglas de campus: a que o SUAP exibe e o código que o dashboard-prpgi aceita.

O SUAP renomeou FS, PA e VC para FSA, PAF e VDC. O dashboard continua com os
códigos antigos. Gravar o mestre com a sigla nova abre um arquivo sem histórico
e derruba o `npm run build` do dashboard, porque o validate-data.js recusa
código desconhecido. Este é o único lugar do coletor que conhece essa
correspondência: o processor.py o usa para gravar os mestres e o
scripts/coletar-suap.py, para decidir o que sincronizar.
"""
from pathlib import Path
from utils.logger import log_msg

# Sigla do SUAP (o que vem entre parênteses no <select> de campus) → código do
# dashboard. Se o SUAP renomear outro campus, acrescente a linha aqui.
SUAP_PARA_DASHBOARD = {
    "FSA": "FS",  # Feira de Santana
    "PAF": "PA",  # Paulo Afonso
    "VDC": "VC",  # Vitória da Conquista
}

# Cópia de CODIGOS_VALIDOS em dashboard-prpgi/scripts/validate-data.js: as
# chaves de CAMPUS_TO_CITY (src/shared.js) mais IFBA, REI e PO, códigos legados
# de planilhas vazias. Campus novo precisa entrar lá e aqui.
CODIGOS_DASHBOARD = frozenset({
    "BAR", "BRU", "CAM", "CFO", "EC", "EUN", "FS", "ILH", "IRE", "ITA", "JAC",
    "JAG", "JEQ", "JUA", "LF", "PA", "PIS", "PS", "SAJ", "SAM", "SEA", "SF",
    "SSA", "UBA", "VAL", "VC",
    "IFBA", "REI", "PO",
})


def codigo_dashboard(sigla_suap):
    """
    Converte a sigla do SUAP no código do dashboard.
    Sigla renomeada volta ao código antigo; sigla desconhecida passa como veio,
    com um aviso no log, para que a perda de histórico não seja silenciosa.
    """
    sigla = sigla_suap.strip()
    if sigla in SUAP_PARA_DASHBOARD:
        return SUAP_PARA_DASHBOARD[sigla]
    if sigla not in CODIGOS_DASHBOARD:
        log_msg(f"AVISO: sigla '{sigla}' do SUAP desconhecida — não está em CODIGOS_DASHBOARD "
                f"nem em SUAP_PARA_DASHBOARD (core/siglas.py). O mestre será {sigla}.xlsx, "
                f"sem histórico anterior, e o --sincronizar não o copia para o dashboard. "
                f"Se o SUAP renomeou um campus, acrescente a sigla ao mapa; se é campus novo, "
                f"cadastre-o em CAMPUS_TO_CITY no dashboard e em CODIGOS_DASHBOARD.")
    return sigla


def separar_para_sincronizar(mestres):
    """
    Divide os mestres (caminhos `{SIGLA}.xlsx`) entre os que o dashboard aceita
    e os que ficam de fora. Retorna (copiar, ignorados), sendo `ignorados` uma
    lista de (caminho, motivo).
    """
    copiar, ignorados = [], []
    for mestre in mestres:
        mestre = Path(mestre)
        sigla = mestre.stem
        if sigla in CODIGOS_DASHBOARD:
            copiar.append(mestre)
        elif sigla in SUAP_PARA_DASHBOARD:
            ignorados.append((mestre, f"sigla antiga do SUAP; os dados vão para "
                                      f"{SUAP_PARA_DASHBOARD[sigla]}.xlsx"))
        else:
            ignorados.append((mestre, "sigla desconhecida pelo dashboard; "
                                      "derrubaria o npm run build"))
    return copiar, ignorados


def siglas_fora_do_dashboard(campi):
    """
    Siglas da lista de campi do SUAP (dicts de `fetch_campus_list`, com a chave
    'sigla') que não têm código no dashboard, nem direto nem pelo mapa.
    Campus novo no SUAP aparece aqui antes de chegar ao `npm run build`.
    """
    desconhecidas = []
    for campus in campi:
        sigla = str(campus.get("sigla", "")).strip()
        if (sigla and sigla not in CODIGOS_DASHBOARD
                and sigla not in SUAP_PARA_DASHBOARD and sigla not in desconhecidas):
            desconhecidas.append(sigla)
    return desconhecidas
