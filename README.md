# BigQuery MCP Server

Servidor MCP (Model Context Protocol) que expõe ferramentas de consulta e análise do Google BigQuery para assistentes de IA como Claude, Gemini e Cursor. Permite que o assistente navegue pelo schema, execute queries e compare datasets sem sair da conversa.

> **MCP (Model Context Protocol)** é o padrão aberto da Anthropic para conectar modelos de linguagem a fontes de dados e ferramentas externas. Com um servidor MCP rodando, o assistente de IA pode chamar as ferramentas diretamente durante a conversa.

## Ferramentas disponíveis

| Ferramenta | O que faz |
|------------|-----------|
| `run_query` | Executa SELECT no BigQuery com suporte a `dry_run` e limite de linhas |
| `list_tables` | Lista tabelas de um ou ambos os datasets |
| `get_schema` | Schema completo de uma tabela: tipos, modos, total de linhas e tamanho |
| `compare_schemas` | Diff entre dois datasets — colunas adicionadas, removidas e com tipo alterado |
| `sample_data` | Amostra de N linhas de qualquer tabela |
| `sample_json_field` | Inspeciona a estrutura de campos JSON/STRING que guardam objetos |

## Exemplo de uso

Com o servidor configurado, você pode perguntar ao assistente de IA:

```
Você: quais tabelas existem no dataset novo?

IA: [chama list_tables] Encontrei 12 tabelas: pedidos, clientes,
    produtos, estoque...

Você: compare o schema da tabela pedidos entre os dois datasets

IA: [chama compare_schemas] A tabela pedidos tem 3 diferenças:
    - coluna "status_pagamento" adicionada (STRING)
    - coluna "dt_entrega" removida
    - coluna "valor" mudou de FLOAT para NUMERIC

Você: mostre 5 linhas de pedidos no dataset novo

IA: [chama sample_data] ...
```

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

Crie um arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env   # se existir, ou defina as variáveis manualmente
```

Variáveis necessárias:

```env
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/service-account.json
BQ_PROJECT_ID=seu-projeto-gcp
```

> A Service Account precisa da role IAM `roles/bigquery.dataViewer` (leitura de dados e metadados) no projeto. Além disso, o servidor restringe o acesso no nível do OAuth ao escopo `bigquery.readonly`, então mesmo que a role concedida seja mais ampla, nenhuma operação de escrita é possível. **Nunca commite o `service-account.json`** — ele já está no `.gitignore`.

## Configuração no Claude Desktop / Gemini Code Assist

Adicione ao arquivo de configuração MCP do seu assistente:

```json
{
  "mcpServers": {
    "bigquery": {
      "command": "python",
      "args": ["./server.py"],
      "cwd": "/caminho/para/bigquery-mcp"
    }
  }
}
```

## Testar a conexão

```bash
python test_connection.py
```

Verifica credenciais, conexão com o projeto e lista as tabelas do dataset configurado.

## Stack

| | |
|--|--|
| Protocolo | MCP (Model Context Protocol) via `fastmcp` |
| Dados | Google BigQuery |
| Auth | Service Account (google-auth) |
| Runtime | Python 3.10+ |
