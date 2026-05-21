# ObAIAL Pipeline

Pipeline diário do **Observatório das Autonomias Indígenas na América Latina
(ObAIAL)**: coleta Google Alerts via Gmail → scraping do texto completo →
RAG dinâmico → classificação multi-ação com Claude AI → grava na Google Sheet.

Roda **uma vez por dia** em uma função **AWS Lambda**, agendada por EventBridge.

---

## ⚠️ Segurança — leia antes de qualquer commit

Este repositório **NÃO contém segredos**. Toda credencial vem do
**AWS Secrets Manager** em tempo de execução.

O [`.gitignore`](.gitignore) bloqueia `.env`, tokens e chaves. **Confirme** que
nenhum segredo será enviado antes do primeiro push:

```bash
git status --ignored        # os arquivos de segredo devem aparecer como "ignored"
git add -A && git status    # revise: nada de .env / *.json de credencial na lista
```

### Credenciais que devem ser ROTACIONADAS

Os arquivos abaixo existiam em texto puro nesta pasta (que está sincronizada
pelo OneDrive). Trate-os como **comprometidos** e gere novas credenciais:

| Arquivo local            | Credencial                       | Ação |
|--------------------------|----------------------------------|------|
| `.env`                   | Chave da API Anthropic           | Revogar em console.anthropic.com e gerar nova |
| `obial-gcp.json`         | Chave da service account GCP     | Apagar a chave no Google Cloud IAM e gerar nova |
| `client_secret.json`     | OAuth client secret do Google    | Rotacionar no Google Cloud Console se exposto |
| `token.json`             | Token OAuth do Gmail             | Regerar (ver abaixo) |

Depois de rotacionar, guarde as **novas** credenciais apenas no Secrets Manager.

---

## Estrutura

```
.
├── src/
│   ├── obAIAL_pipeline_merged.py   # código final (CLI + lambda_handler)
│   ├── config/field_map.yml        # mapeamento de campos -> colunas da Sheet
│   └── requirements.txt            # dependências (usado por `sam build`)
├── template.yaml                   # infraestrutura AWS SAM (Lambda + schedule + IAM)
├── .env.example                    # modelo de configuração local
├── .gitignore
└── _legacy/                        # versões antigas (ignoradas pelo git)
```

---

## Segredos no AWS Secrets Manager

Crie três segredos na região `sa-east-1` (ajustável via parâmetro do SAM):

```bash
# 1. Chave da API Anthropic (string pura OU JSON {"ANTHROPIC_API_KEY":"..."})
aws secretsmanager create-secret --region sa-east-1 \
  --name anthropic/obaial/api_key \
  --secret-string 'sk-ant-...'

# 2. Service account do Google Sheets (conteúdo do JSON da SA)
aws secretsmanager create-secret --region sa-east-1 \
  --name gcp/sheets_service_account \
  --secret-string file://nova-service-account.json

# 3. Token OAuth do Gmail (conteúdo do token.json)
aws secretsmanager create-secret --region sa-east-1 \
  --name gmail/obaial/token \
  --secret-string file://token.json
```

> A Lambda tem permissão de `PutSecretValue` **apenas** no segredo do Gmail,
> para regravar o token quando o `refresh_token` é renovado.

### Regerar o `token.json` do Gmail

Localmente, com o `client_secret.json` do projeto:

```python
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0)
open("token.json", "w").write(creds.to_json())
```

Envie o `token.json` resultante para o Secrets Manager (passo 3 acima).

---

## Execução local

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r src/requirements.txt

cp .env.example .env        # preencha ANTHROPIC_API_KEY
# As credenciais AWS vêm do seu perfil (`aws configure`); Gmail/Sheets ainda
# são lidos do Secrets Manager.

python src/obAIAL_pipeline_merged.py --dry-run    # teste sem chamar Claude/Sheet
python src/obAIAL_pipeline_merged.py --limit 3    # execução real, 3 itens
```

---

## Deploy na AWS (SAM)

Pré-requisitos: [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
e credenciais AWS configuradas.

```bash
sam build
sam deploy --guided        # primeira vez: salva escolhas em samconfig.toml
```

No `--guided`, confirme/ajuste os parâmetros (região dos segredos, IDs,
`ScheduleExpression`). Deploys seguintes:

```bash
sam build && sam deploy
```

O `template.yaml` provisiona:

- a função Lambda (`python3.12`, timeout 600 s, 512 MB);
- o agendamento diário via EventBridge (`cron(0 9 * * ? *)` = 06:00 BRT);
- política IAM de **privilégio mínimo** — acesso somente aos 3 segredos do projeto;
- grupo de logs no CloudWatch com retenção de 90 dias.

### Testar a função publicada

```bash
aws lambda invoke --function-name obaial-pipeline-diario \
  --payload '{"dry_run": true}' --cli-binary-format raw-in-base64-out out.json
cat out.json
```

---

## Observações operacionais

- **Cache de geocoding:** no Lambda só `/tmp` é gravável; o código usa
  `/tmp/geocode_cache.json` automaticamente. Esse cache não persiste entre
  execuções (cada run diária é um *cold start*) — aceitável dado o volume baixo.
- **Idempotência:** o pipeline deduplica por URL canônica e por hash `sha256`,
  então reexecuções no mesmo dia não geram linhas duplicadas.
- **Falhas:** exceções são propagadas para o Lambda registrar o erro no
  CloudWatch. Configure um alarme em `Errors` da função para ser notificado.
