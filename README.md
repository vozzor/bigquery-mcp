# BigQuery MCP Server - Migração de Datasets

MCP Server para auxiliar na migração das consultas SQL de um dataset antigo (`dataset_antigo`) para um novo (`dataset_novo`) no Google BigQuery.

## Ferramentas Disponíveis

| Ferramenta | Descrição |
|------------|-----------|
| `run_query` | Executa consultas SELECT no BigQuery |
| `list_tables` | Lista tabelas de um ou ambos datasets |
| `get_schema` | Retorna schema completo de uma tabela |
| `compare_schemas` | Compara schemas entre datasets antigo e novo |
| `sample_data` | Retorna amostra de dados de uma tabela |
| `sample_json_field` | Analisa estrutura de campos JSON |

## Instalação

```bash
cd bigquery-mcp
pip install -r requirements.txt
```

## Configuração no Gemini Code Assist

Adicione ao arquivo de configuração MCP (`settings.json` ou similar):

```json
{
  "mcpServers": {
    "bigquery": {
      "command": "python",
      "args": ["./server.py"],
      "cwd": "/path/to/bigquery-mcp"
    }
  }
}
```

## Uso

Após configurado, as ferramentas estarão disponíveis para:
- Listar e comparar schemas
- Executar consultas com limite e dry_run
- Analisar campos JSON
- Migrar queries para o novo formato
