# SolarInspect AI Backend

SolarInspect AI is an AI-assisted inspection triage system for photovoltaic operations.

Este backend foi criado para o MVP do hackathon na trilha de Vision & Multimodal AI. A proposta do sistema e apoiar a triagem inicial de inspecoes de paineis fotovoltaicos usando upload de imagens, processamento assíncrono, classificacao mockada, explicacoes mockadas e geracao de relatorio Markdown para revisao humana.

Importante: o SolarInspect AI nao substitui uma inspecao tecnica profissional. Todos os achados sao sinais de triagem assistida por IA e exigem revisao humana.

## O Que O Sistema Possui Hoje

- API FastAPI pronta para integracao com frontend.
- Swagger/OpenAPI disponivel em `/docs`.
- CORS configurado para permitir chamadas do frontend.
- Upload multiplo de imagens via `multipart/form-data`.
- Validacao de extensoes de imagem: `.jpg`, `.jpeg`, `.png`, `.webp`, `.tif`, `.tiff`.
- Criacao de `inspection_id` no formato `insp_YYYYMMDD_HHMMSS_xxxxxx`.
- Armazenamento local de uploads em `storage/uploads/{inspection_id}/`.
- Processamento assíncrono com `FastAPI BackgroundTasks`.
- Estado das inspecoes em memoria para o MVP.
- Atualizacao de status: `queued`, `processing`, `completed`, `failed`.
- Contador de progresso com `processed_images` e `progress`.
- Classificador mockado com saida compativel com o frontend.
- Servico VLM mockado para explicacoes, acoes recomendadas e incerteza.
- Estrutura preparada para trocar mock por classificador real.
- Estrutura preparada para integrar VLM via endpoint OpenAI-like, como vLLM.
- Resultados por imagem ordenados por prioridade.
- Geracao de relatorio Markdown.
- Servir arquivos estaticos de `storage/` via `/storage/...`.
- Testes basicos com `pytest` e `TestClient`.

## Stack

- FastAPI
- Python
- Pydantic
- PyTorch-ready services
- Qwen2.5-VL-ready service
- Local storage
- Pytest
- HTTPX/TestClient

## Estrutura Do Projeto

```text
api/
  main.py
  schemas.py
  services/
    __init__.py
    classifier.py
    inspections.py
    reports.py
    storage.py
    vlm.py

tests/
  test_api.py

storage/
  uploads/
  outputs/
  reports/
```

### Principais Arquivos

- `api/main.py`: cria a aplicacao FastAPI, configura CORS, monta `/storage` e registra endpoints.
- `api/schemas.py`: contratos Pydantic usados nas respostas da API.
- `api/services/storage.py`: cria pastas locais, valida extensoes e salva imagens.
- `api/services/inspections.py`: cria inspecoes, guarda estado em memoria, processa imagens e retorna status/resultados.
- `api/services/classifier.py`: classificador em modo `mock` ou `model`.
- `api/services/vlm.py`: explicador em modo `mock` ou `api`.
- `api/services/reports.py`: gera relatorio Markdown.
- `tests/test_api.py`: testes basicos da API e do fluxo principal.

## Como Instalar

Crie a virtualenv:

```bash
python -m venv .venv
```

Ative no Linux/macOS:

```bash
source .venv/bin/activate
```

Ative no Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependencias:

```bash
pip install -r requirements.txt
```

## Como Rodar

```bash
uvicorn api.main:app --reload
```

Depois acesse:

```text
http://127.0.0.1:8000/docs
```

Se a porta `8000` estiver ocupada:

```bash
uvicorn api.main:app --reload --port 8001
```

## Como Testar

```bash
pytest
```

No Windows, usando explicitamente a virtualenv:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Os testes cobrem:

- `GET /health`
- `GET /ready`
- erro ao criar inspecao sem arquivo
- criacao de inspecao com arquivo fake
- consulta de status
- `404` para `inspection_id` inexistente
- fluxo com resultados, relatorio e arquivos estaticos via `/storage`

## Endpoints Disponiveis

### `GET /health`

Health check simples.

Resposta:

```json
{
  "status": "ok",
  "service": "solarinspect-api"
}
```

### `GET /ready`

Readiness check da API e dos servicos internos.

Resposta:

```json
{
  "status": "ready",
  "storage_ready": true,
  "classifier_ready": true,
  "vlm_ready": true
}
```

### `POST /api/v1/inspections`

Cria uma inspecao e dispara o processamento assíncrono.

Campos `multipart/form-data`:

- `plant_name`: nome da planta solar.
- `inspection_type`: `thermal`, `rgb` ou `mixed`.
- `files`: uma ou mais imagens.

Exemplo com `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/inspections" \
  -F "plant_name=Demo Solar Plant" \
  -F "inspection_type=thermal" \
  -F "files=@./samples/panel_001.jpg" \
  -F "files=@./samples/panel_002.jpg"
```

Resposta:

```json
{
  "inspection_id": "insp_20260507_153000_ab12cd",
  "status": "queued",
  "plant_name": "Demo Solar Plant",
  "inspection_type": "thermal",
  "total_images": 2,
  "message": "Inspection created successfully."
}
```

### `GET /api/v1/inspections/{inspection_id}`

Consulta status e progresso da inspecao.

Resposta:

```json
{
  "inspection_id": "insp_20260507_153000_ab12cd",
  "plant_name": "Demo Solar Plant",
  "inspection_type": "thermal",
  "status": "completed",
  "progress": 100,
  "total_images": 2,
  "processed_images": 2,
  "created_at": "2026-05-07T15:30:00",
  "updated_at": "2026-05-07T15:30:01",
  "error_message": null
}
```

### `GET /api/v1/inspections/{inspection_id}/results`

Retorna os achados por imagem, ordenados por prioridade crescente.

Prioridades:

- `critical`: `0`
- `high`: `1`
- `medium`: `2`
- `low`: `3`
- `healthy`: `4`
- `unknown`: `5`

Resposta resumida:

```json
{
  "inspection_id": "insp_20260507_153000_ab12cd",
  "status": "completed",
  "results": [
    {
      "image_id": "img_001",
      "filename": "001_panel_001.jpg",
      "image_type": "thermal",
      "raw_label": "hotspot",
      "category": "electrical_fault",
      "severity": "high",
      "priority": 1,
      "confidence": 0.87,
      "bbox": {
        "x": 120,
        "y": 80,
        "width": 60,
        "height": 45
      },
      "evidence": "Localized high-intensity region detected in the panel area.",
      "explanation": "The image may show a localized thermal anomaly compatible with a possible hotspot or electrical imbalance.",
      "recommended_action": "Prioritize human review and inspect electrical connections or affected string.",
      "uncertainty": "AI-assisted triage only. Human review is required.",
      "image_url": "/storage/uploads/insp_20260507_153000_ab12cd/001_panel_001.jpg",
      "annotated_image_url": null
    }
  ]
}
```

### `POST /api/v1/inspections/{inspection_id}/report`

Gera um relatorio Markdown em `storage/reports/{inspection_id}.md`.

Resposta:

```json
{
  "inspection_id": "insp_20260507_153000_ab12cd",
  "report_status": "generated",
  "report_url": "/storage/reports/insp_20260507_153000_ab12cd.md"
}
```

O relatorio inclui:

- titulo `SolarInspect AI Report`
- dados da inspecao
- quantidade de achados por severidade
- lista de achados ordenada por prioridade
- evidencia, explicacao e acao recomendada
- disclaimer de human-in-the-loop

## Arquivos E URLs Estaticas

A API monta:

```python
app.mount("/storage", StaticFiles(directory="storage"), name="storage")
```

Isso permite acessar:

```text
/storage/uploads/{inspection_id}/{filename}
/storage/reports/{inspection_id}.md
```

A aplicacao cria automaticamente:

```text
storage/uploads/
storage/outputs/
storage/reports/
```

## Serviços Mockados E Integração Futura

Nesta etapa, o classificador e o VLM estao prontos para integracao, mas rodam em modo mock por padrao.

### Classifier

Arquivo: `api/services/classifier.py`

Variavel:

```text
CLASSIFIER_MODE=mock
```

Modos:

- `mock`: retorna um achado fake de hotspot.
- `model`: tenta carregar `models/classifier.pt` e `models/label_map.json`.

Labels normalizadas para categorias operacionais:

- `healthy`
- `surface_obstruction`
- `structural_fault`
- `electrical_fault`
- `unknown`

### VLM

Arquivo: `api/services/vlm.py`

Variaveis:

```text
VLM_MODE=mock
VLM_API_URL=http://localhost:8001/v1/chat/completions
VLM_MODEL_NAME=qwen2.5-vl-7b
```

Modos:

- `mock`: retorna explicacao e recomendacao fake.
- `api`: prepara chamada OpenAI-like para vLLM ou outro servico compativel.

Se a chamada ao VLM falhar, o backend retorna fallback seguro e nao derruba o processamento da inspecao.

## Limites Conhecidos Do MVP

- Nao ha banco de dados ainda.
- O estado das inspecoes fica em memoria e se perde ao reiniciar o servidor.
- Nao ha PDF ainda.
- Nao ha treinamento de modelo neste repositorio.
- O classificador real ainda nao esta conectado.
- O Qwen2.5-VL real ainda nao esta conectado.
- O objetivo e triagem assistida por IA, nao diagnostico tecnico definitivo.

## Proximos Passos

- Conectar classificador real.
- Conectar Qwen2.5-VL via vLLM/OpenAI-compatible API.
- Adicionar persistencia SQLite.
- Melhorar o relatorio Markdown e futuramente exportar PDF.
- Criar frontend Next.js ou Gradio.
- Preparar deploy em Hugging Face Spaces ou alternativa simples.
