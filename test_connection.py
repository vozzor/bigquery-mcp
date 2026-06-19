"""
Script de teste para verificar conexão com BigQuery
"""
import os
import sys

# Adiciona o diretório ao path
sys.path.insert(0, os.path.dirname(__file__))

from google.cloud import bigquery
from google.oauth2 import service_account

CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")
PROJECT_ID = os.environ.get("BQ_PROJECT_ID", "meu-projeto")

print("=" * 50)
print("Teste de Conexão BigQuery MCP Server")
print("=" * 50)

try:
    print(f"\n1. Carregando credenciais de: {CREDENTIALS_PATH}")
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=["https://www.googleapis.com/auth/bigquery.readonly"]
    )
    print("   ✓ Credenciais carregadas com sucesso!")
    
    print(f"\n2. Conectando ao projeto: {PROJECT_ID}")
    client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
    print("   ✓ Cliente BigQuery criado!")
    
    print("\n3. Listando datasets...")
    datasets = list(client.list_datasets())
    for ds in datasets:
        print(f"   - {ds.dataset_id}")
    
    print("\n4. Testando consulta simples (dry_run)...")
    query = "SELECT 1 as test"
    job_config = bigquery.QueryJobConfig(dry_run=True)
    job = client.query(query, job_config=job_config)
    print(f"   ✓ Query válida! Bytes: {job.total_bytes_processed}")
    
    print("\n5. Listando tabelas do dataset dataset_novo...")
    tables = list(client.list_tables("dataset_novo"))
    for t in tables[:10]:
        print(f"   - {t.table_id}")
    if len(tables) > 10:
        print(f"   ... e mais {len(tables) - 10} tabelas")
    
    print("\n" + "=" * 50)
    print("✓ TODOS OS TESTES PASSARAM!")
    print("  O MCP Server está pronto para uso.")
    print("=" * 50)
    
except Exception as e:
    print(f"\n✗ ERRO: {e}")
    import traceback
    traceback.print_exc()
