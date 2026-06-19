"""
MCP Server para BigQuery - Migração de Datasets
Permite executar consultas SQL no BigQuery via Model Context Protocol
"""

import json
import os
from typing import Any
from google.cloud import bigquery
from google.oauth2 import service_account
from mcp.server.fastmcp import FastMCP

# Configuração
CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")
PROJECT_ID = os.environ.get("BQ_PROJECT_ID", "meu-projeto")
DEFAULT_DATASET_OLD = "dataset_antigo"
DEFAULT_DATASET_NEW = "dataset_novo"

# Inicializa credenciais e cliente BigQuery
credentials = service_account.Credentials.from_service_account_file(
    CREDENTIALS_PATH,
    scopes=["https://www.googleapis.com/auth/bigquery.readonly"]
)
bq_client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

# Inicializa o servidor MCP
mcp = FastMCP("BigQuery MCP Server")


def format_results(rows, max_rows: int = 100) -> list[dict]:
    """Converte resultados do BigQuery para lista de dicionários."""
    results = []
    for i, row in enumerate(rows):
        if i >= max_rows:
            break
        results.append(dict(row))
    return results


@mcp.tool()
def run_query(sql: str, dry_run: bool = False, max_rows: int = 100) -> str:
    """
    Executa uma consulta SQL SELECT no BigQuery.
    
    Args:
        sql: Consulta SQL a ser executada (apenas SELECT permitido)
        dry_run: Se True, apenas valida a query e retorna bytes estimados
        max_rows: Número máximo de linhas a retornar (padrão: 100, máximo: 1000)
    
    Returns:
        Resultados da query em formato JSON ou informações do dry_run
    """
    # Validação de segurança - apenas SELECT
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
        return json.dumps({"error": "Apenas consultas SELECT ou WITH são permitidas"})
    
    # Limita max_rows
    max_rows = min(max_rows, 1000)
    
    try:
        job_config = bigquery.QueryJobConfig(dry_run=dry_run, use_query_cache=True)
        query_job = bq_client.query(sql, job_config=job_config)
        
        if dry_run:
            bytes_processed = query_job.total_bytes_processed
            return json.dumps({
                "dry_run": True,
                "bytes_processed": bytes_processed,
                "bytes_processed_readable": f"{bytes_processed / (1024*1024):.2f} MB",
                "query_valid": True
            }, indent=2)
        
        results = format_results(query_job.result(), max_rows)
        total_rows = query_job.result().total_rows
        
        return json.dumps({
            "rows_returned": len(results),
            "total_rows": total_rows,
            "truncated": total_rows > max_rows,
            "data": results
        }, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_tables(dataset: str = None) -> str:
    """
    Lista todas as tabelas de um dataset.
    
    Args:
        dataset: Nome do dataset (padrão: lista ambos dataset_antigo e dataset_novo)
    
    Returns:
        Lista de tabelas com informações básicas
    """
    try:
        datasets_to_list = [dataset] if dataset else [DEFAULT_DATASET_OLD, DEFAULT_DATASET_NEW]
        all_tables = {}
        
        for ds in datasets_to_list:
            dataset_ref = bq_client.dataset(ds)
            tables = list(bq_client.list_tables(dataset_ref))
            all_tables[ds] = [
                {
                    "table_id": t.table_id,
                    "table_type": t.table_type,
                    "full_id": f"{PROJECT_ID}.{ds}.{t.table_id}"
                }
                for t in tables
            ]
        
        return json.dumps(all_tables, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_schema(table_name: str, dataset: str = None) -> str:
    """
    Retorna o schema completo de uma tabela.
    
    Args:
        table_name: Nome da tabela
        dataset: Dataset onde a tabela está (padrão: busca em ambos datasets)
    
    Returns:
        Schema da tabela com tipos e modos
    """
    try:
        datasets_to_check = [dataset] if dataset else [DEFAULT_DATASET_NEW, DEFAULT_DATASET_OLD]
        
        for ds in datasets_to_check:
            try:
                table_ref = bq_client.dataset(ds).table(table_name)
                table = bq_client.get_table(table_ref)
                
                schema = [
                    {
                        "name": field.name,
                        "type": field.field_type,
                        "mode": field.mode,
                        "description": field.description or ""
                    }
                    for field in table.schema
                ]
                
                return json.dumps({
                    "table": f"{PROJECT_ID}.{ds}.{table_name}",
                    "num_rows": table.num_rows,
                    "num_bytes": table.num_bytes,
                    "created": str(table.created),
                    "modified": str(table.modified),
                    "schema": schema
                }, indent=2)
                
            except Exception:
                continue
        
        return json.dumps({"error": f"Tabela '{table_name}' não encontrada em nenhum dataset"})
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def compare_schemas(table_name: str) -> str:
    """
    Compara o schema de uma tabela entre o dataset antigo (dataset_antigo) e novo (dataset_novo).
    
    Args:
        table_name: Nome da tabela a comparar
    
    Returns:
        Diff mostrando colunas adicionadas, removidas e alteradas
    """
    try:
        # Busca schema do dataset antigo
        old_schema = {}
        try:
            table_ref = bq_client.dataset(DEFAULT_DATASET_OLD).table(table_name)
            table = bq_client.get_table(table_ref)
            old_schema = {f.name: {"type": f.field_type, "mode": f.mode} for f in table.schema}
        except Exception:
            pass
        
        # Busca schema do dataset novo
        new_schema = {}
        try:
            table_ref = bq_client.dataset(DEFAULT_DATASET_NEW).table(table_name)
            table = bq_client.get_table(table_ref)
            new_schema = {f.name: {"type": f.field_type, "mode": f.mode} for f in table.schema}
        except Exception:
            pass
        
        if not old_schema and not new_schema:
            return json.dumps({"error": f"Tabela '{table_name}' não encontrada em nenhum dataset"})
        
        # Calcula diferenças
        all_columns = set(old_schema.keys()) | set(new_schema.keys())
        diff = []
        
        for col in sorted(all_columns):
            old_info = old_schema.get(col)
            new_info = new_schema.get(col)
            
            if old_info is None:
                diff.append({
                    "column": col,
                    "status": "NOVA_COLUNA",
                    "new_type": new_info["type"],
                    "new_mode": new_info["mode"]
                })
            elif new_info is None:
                diff.append({
                    "column": col,
                    "status": "COLUNA_REMOVIDA",
                    "old_type": old_info["type"],
                    "old_mode": old_info["mode"]
                })
            elif old_info["type"] != new_info["type"]:
                diff.append({
                    "column": col,
                    "status": "TIPO_MUDOU",
                    "old_type": old_info["type"],
                    "new_type": new_info["type"]
                })
            elif old_info["mode"] != new_info["mode"]:
                diff.append({
                    "column": col,
                    "status": "MODO_MUDOU",
                    "old_mode": old_info["mode"],
                    "new_mode": new_info["mode"]
                })
        
        return json.dumps({
            "table": table_name,
            "old_dataset": DEFAULT_DATASET_OLD,
            "new_dataset": DEFAULT_DATASET_NEW,
            "old_columns_count": len(old_schema),
            "new_columns_count": len(new_schema),
            "differences": diff,
            "has_changes": len(diff) > 0
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def sample_data(table_name: str, dataset: str = None, limit: int = 5) -> str:
    """
    Retorna uma amostra de dados de uma tabela.
    
    Args:
        table_name: Nome da tabela
        dataset: Dataset onde buscar (padrão: dataset_novo)
        limit: Número de linhas a retornar (padrão: 5, máximo: 20)
    
    Returns:
        Amostra dos dados da tabela
    """
    ds = dataset or DEFAULT_DATASET_NEW
    limit = min(limit, 20)
    
    sql = f"SELECT * FROM `{PROJECT_ID}.{ds}.{table_name}` LIMIT {limit}"
    return run_query(sql, max_rows=limit)


@mcp.tool()
def sample_json_field(table_name: str, json_column: str, dataset: str = None, limit: int = 3) -> str:
    """
    Retorna amostras de um campo JSON específico para análise de estrutura.
    
    Args:
        table_name: Nome da tabela
        json_column: Nome da coluna JSON
        dataset: Dataset onde buscar (padrão: dataset_novo)
        limit: Número de amostras (padrão: 3)
    
    Returns:
        Amostras do campo JSON
    """
    ds = dataset or DEFAULT_DATASET_NEW
    limit = min(limit, 10)
    
    sql = f"""
    SELECT
        {json_column}
    FROM `{PROJECT_ID}.{ds}.{table_name}`
    WHERE {json_column} IS NOT NULL
    LIMIT {limit}
    """
    return run_query(sql, max_rows=limit)


if __name__ == "__main__":
    mcp.run()
