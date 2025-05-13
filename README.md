# Desafio Técnico - Consumo de API + Visualização de dados


# F1 Highlights CSV Exporter

Este script consome a YouTube Data API v3, filtra vídeos de "highlights" da temporada 2024 do canal oficial da F1, e exporta um CSV para você importar no excel ou power BI

## Pré-requisitos

- Python 3.7+
- Conta no Google Cloud com YouTube Data API v3 habilitada
- Variável de ambiente `YOUTUBE_API_KEY` configurada

## Passo a passo

1. **Clone este repositório**  
   ```bash
   git clone https://github.com/SEU_USUARIO/seu-repo.git
   cd seu-repo

2. Este código está usando o .env para deixar a API utilizada bem mais segura 
    **Crie um .env** 
    Ao criar o .env, colocar o seguinte lá dentro YOUTUBE_API_KEY = "AIzaSyDkskors7j22HbgwddSz1hZz3pg90IfnWE" -> Chave API utilizada

3. **Instale as dependências**
    pip install google-api-python-client pandas python-dotenv

4. **Execute o Script** 
    python exportF1.py


## Por que gerar um CSV em vez de conectar direto ao Power BI?

Conectar o Power BI diretamente à YouTube Data API pode:
- Tornar a atualização de dados muito lenta ou sujeita a erros de timeout.
- Trazer colunas mal formatadas, exigindo mais limpeza dentro do próprio Power BI.

Ao exportar um CSV:
1. **Desempenho otimizado**: o Power BI lê um arquivo local, sem sobrecarga de requisições HTTP.  
2. **Tratamento prévio de dados**: todas as validações e ajustes (tipos, nomes de colunas, ordenações) são feitos no Python, garantindo que o CSV chegue “pronto para uso”.

Dessa forma, você ganha velocidade nas consultas e mais controle sobre a qualidade dos dados importados.


## Decisões Técnicas 
    - Python + Pandas: Usei para facilitar a manipulação de tabelas e conversão para CSV
    - Paginação manual: A API retorna até 50 itens por chamada, então implementei um loop com pageToken para trazer todos os highlights 2024 
    - .env + python-dotenv: Segura a chave da API longe do código e facilita o setup por outros devs 

## Desafios Enfrentados 
    - Limite de itens por requisição: Precisei particionar as chamadas de vídeo até 50 lotes 
    - Formato de datas: A API retorna publishedAt em ISO 8601, então mantive o padrão para facilitar o parsing no BI. 
    - Ausência de dislike: a API deixou de expor esse campo, então removi do payload final. 
