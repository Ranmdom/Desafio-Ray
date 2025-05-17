# F1 Highlights ETL & Dashboard

Este repositório reúne todo o código necessário para extrair, transformar e carregar (ETL) dados de vídeos de highlights de Fórmula 1 (ano 2024) a partir de uma playlist do YouTube para um banco Supabase/Postgres.


## Pré-requisitos

1. Python 3.8+
2. Conta no Supabase com tabela `public.f1_highlights`.
3. Chave de API do YouTube (YouTube Data API v3).
4. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

   ```
   YOUTUBE_API_KEY=AIza...
   SUPABASE_DB_URL=postgresql://<usuário>:<senha>@<host>:5432/<database>
   YOUTUBE_PLAYLIST_ID=<ID_da_playlist_YouTube>
   ```

---

## Instalação

1. Clone este repositório e entre na pasta:

   ```
   git clone https://github.com/SEU_USUARIO/SEU_REPO.git
   cd SEU_REPO
   ```

2. Crie e ative um ambiente virtual:

   * Windows

     ```
     python -m venv venv
     .\venv\Scripts\activate
     ```
   * macOS/Linux

     ```
     python -m venv venv
     source venv/bin/activate
     ```

3. Instale as dependências:

   ```
   pip install python-dotenv pandas google-api-python-client SQLAlchemy psycopg2-binary streamlit streamlit-option-menu altair plotly

   ```

---

## Validando o Ambiente

### 1. Verificar variáveis de ambiente

```bash
python test_env.py
```

Saída esperada:

```
arquivo .env encontrado em: /caminho/para/.env
load_dotenv retornou: True
SUPABASE_DB_URL = postgresql://...
```

### 2. Testar conexão ao banco

```bash
python test_db.py
```

Saída esperada:

```
Conexão OK: [(1,)]
```

---

## ETL: pipeline.py

Este script faz todo o pipeline ETL:

1. Lê variáveis de ambiente.
2. Puxa IDs de vídeos de 2024 de uma playlist do YouTube.
3. Obtém detalhes (views, likes, comentários, localização, piloto, região).
4. Upsert na tabela `public.f1_highlights`.
5. Cria materialized views em schema `reporting`:
   * `f1_monthly_summary`

Como rodar:

```
python pipeline.py
```

---

## Dashboard em PowerBI:


* **Overview** – KPIs, smart narrative, linha do tempo e top 5 circuitos
* **Evolução Mensal** – coluna de vídeos, área de taxa de likes, matrix por circuito e gráfico de crescimento no ano

Vou deixar o arquivo do projeto no github, mas por precaução também vou mandar via e-mail


**Observação:** Geralmente não se deve em hipotese alguma subir o .env no github, por se tratar do coração do projeto, porém para vocês obterem os dados, eu precisei subir o .env.



