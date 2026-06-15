import pandas as pd
import os
from utils.logger import log_msg

def read_excel_sheets(filepath):
    """
    Lê todas as abas de um arquivo Excel e retorna um dicionário {sheet_name: DataFrame}.
    """
    sheets_dict = {}
    xl = pd.ExcelFile(filepath)
    
    for sheet_name in xl.sheet_names:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        
        # Ajustar cabeçalho se necessário
        if not df.empty and str(df.iloc[0, 0]).strip() == "#":
            df.columns = df.iloc[0]
            df = df[1:].copy()
        
        # Limpar espaços em branco nos nomes das colunas
        df.columns = [str(c).strip() for c in df.columns]
        
        sheets_dict[sheet_name] = df
    
    return sheets_dict

def merge_sheet_data(df_new, df_master=None):
    """
    Faz merge de novos dados com dados mestre existentes para uma única aba.
    Remove duplicatas e ordena.
    """
    if df_master is not None:
        # Concatenar
        df_combined = pd.concat([df_master, df_new], ignore_index=True)
    else:
        df_combined = df_new
    
    if df_combined.empty:
        return None
    
    # Remover duplicatas
    potential_keys = ["Publicação", "Ano", "Servidor", "Tipo"]
    subset_cols = [c for c in potential_keys if c in df_combined.columns]
    
    if not subset_cols:
        subset_cols = [c for c in df_combined.columns if c != "#"]
    
    # Garantir tipos consistentes
    for col in subset_cols:
        df_combined[col] = df_combined[col].astype(str).str.strip()
    
    df_combined = df_combined.drop_duplicates(subset=subset_cols, keep='last')
    
    # Ordenar
    if "Ano" in df_combined.columns:
        df_combined["Ano"] = pd.to_numeric(df_combined["Ano"], errors='coerce')
        df_combined = df_combined.sort_values(by=["Ano", "Servidor"], ascending=[False, True])
    
    # Recriar a coluna de índice '#'
    df_combined["#"] = range(1, len(df_combined) + 1)
    
    # Reordenar colunas
    cols = ["#"] + [c for c in df_combined.columns if c != "#"]
    df_combined = df_combined[cols]
    
    return df_combined

def merge_production_data(new_file_path, campus_sigla, downloads_dir):
    """
    Lê o novo arquivo baixado (todas as abas), carrega o arquivo mestre existente,
    combina aba por aba, remove duplicatas e salva o resultado com múltiplas abas.
    """
    master_filename = f"{campus_sigla}.xlsx"
    master_path = os.path.join(downloads_dir, master_filename)
    
    try:
        log_msg(f"Processando integração de dados para {campus_sigla}...")
        
        # 1. Ler o novo arquivo (todas as abas)
        new_sheets = read_excel_sheets(new_file_path)
        
        # 2. Ler arquivo mestre se existir
        master_sheets = {}
        if os.path.exists(master_path):
            master_sheets = read_excel_sheets(master_path)
            log_msg(f"Arquivo mestre encontrado com {len(master_sheets)} abas.")
        
        # 3. Fazer merge aba por aba
        result_sheets = {}
        all_sheet_names = set(list(new_sheets.keys()) + list(master_sheets.keys()))
        
        for sheet_name in all_sheet_names:
            df_new = new_sheets.get(sheet_name)
            df_master = master_sheets.get(sheet_name)
            
            if df_new is not None and df_master is not None:
                log_msg(f"Aba '{sheet_name}': combinando {len(df_new)} novos com {len(df_master)} existentes.")
                df_result = merge_sheet_data(df_new, df_master)
            elif df_new is not None:
                log_msg(f"Aba '{sheet_name}': criando nova com {len(df_new)} registros.")
                df_result = merge_sheet_data(df_new)
            else:
                df_result = df_master
            
            if df_result is not None and not df_result.empty:
                result_sheets[sheet_name] = df_result
        
        # 4. Salvar como XLSX com múltiplas abas
        with pd.ExcelWriter(master_path, engine='openpyxl') as writer:
            for sheet_name, df in result_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        total_records = sum(len(df) for df in result_sheets.values())
        log_msg(f"Sucesso: {master_path} atualizado ({total_records} registros totais em {len(result_sheets)} abas).")
        
        return master_path
        
    except Exception as e:
        log_msg(f"ERRO ao mesclar dados de {campus_sigla}: {str(e)}")
        import traceback
        log_msg(traceback.format_exc())
        return None

def process_all_raw_data(raw_dir, processed_dir, state_callback=None):
    """
    Processa todos os arquivos brutos, agrupando por campus e criando arquivos mestres.
    """
    import re
    from collections import defaultdict
    
    # Agrupar arquivos por campus
    campus_files = defaultdict(list)
    for filename in os.listdir(raw_dir):
        if filename.endswith(".xls"):
            match = re.match(r'^([A-Z]+)-', filename)
            if match:
                sigla = match.group(1)
                campus_files[sigla].append(os.path.join(raw_dir, filename))
    
    total = len(campus_files)
    processed = 0
    
    for sigla, files in campus_files.items():
        processed += 1
        if state_callback:
            state_callback(f"Processando {sigla} ({processed}/{total})", sigla)
        
        log_msg(f"Processando campus {sigla} com {len(files)} arquivos...")
        
        # Ler todas as abas de todos os arquivos deste campus
        all_sheets = {}
        for filepath in files:
            try:
                sheets = read_excel_sheets(filepath)
                for sheet_name, df in sheets.items():
                    if sheet_name not in all_sheets:
                        all_sheets[sheet_name] = []
                    all_sheets[sheet_name].append(df)
            except Exception as e:
                log_msg(f"Erro ao ler {filepath}: {e}")
        
        if not all_sheets:
            log_msg(f"Nenhum dado válido para {sigla}")
            continue
        
        # Combinar todas as abas
        combined_sheets = {}
        for sheet_name, df_list in all_sheets.items():
            combined_sheets[sheet_name] = pd.concat(df_list, ignore_index=True)
        
        # Salvar temporariamente como xlsx com múltiplas abas
        temp_path = os.path.join(raw_dir, f"temp_{sigla}.xlsx")
        with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
            for sheet_name, df in combined_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Usar merge_production_data para fazer o merge com o arquivo mestre existente
        result = merge_production_data(temp_path, sigla, processed_dir)
        
        # Remover arquivo temporário
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    if state_callback:
        state_callback("Processo finalizado", None)
    
    log_msg("Processamento de todos os dados brutos concluído.")
