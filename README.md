# MIC - Monitoramento Inteligente de Consumo
**GoodWe**

Este projeto implementa um **agente de recomendação de consumo elétrico** utilizando a API **Google AI (Gemini)** em Python e Streamlit.  
O sistema analisa dados de consumo de dispositivos domésticos e fornece **alertas, recomendações e respostas a perguntas do usuário** sobre eficiência energética.  

A técnica de engenharia de prompt escolhida foi a **Chain of Verification (CoVe)**, garantindo confiabilidade nas respostas e recomendações geradas pelo modelo.

---

## Estrutura do Repositório

- `MIC/`  
  - `app_mic.py` → Aplicativo Streamlit de monitoramento e interação com o Gemini.  
  - `.env` → Arquivo para armazenar a chave da API Gemini.  
  - `requirements.txt` → Dependências necessárias para rodar o projeto.  

---

## Como Executar

1. Clone este repositório em sua IDE:
```bash
git clone <url-do-repositorio>
cd MIC
```
2. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
source .venv\bin\activate # Linux/Mac
.venv\Scripts\Activate # Windows
```
3. Instale as dependências:
```
pip install -r requirements.txt
```
4. Configure sua chave de API Gemini:
- Abra do arquivo .env
- Atualize a linha:
```bash
GEMINI_API_KEY = sua_chave_aqui
```
5. Execute o aplicativo
```bash
streamlit run app_mic.py
```

---

## Funcionalidades
- Exibição de **KPIs:** Tensão Média, corrente total, potência total e energia consumida.
- Gráficos interativos de **potência e energia por aparelho**.
- **Tabela de dados** completa e opção de download em CSV.
- **Alertas e recomendações automáticas** geradas pelo Gemini com base nos dados do mock.
- **Perguntas personalizadas do usuário** ao Gemini, permitindo respostas de mercado ou boas práticas quando os dados não forem suficientes.

---

## Colaboradores
- Lucas Werpp Franco - RM: 556044
- Lucas Alves Antunes Almeida - RM: 566362
- Lucca Rosseto Rezende - RM: 564180
- Massayoshi Bando Fogaça e Silva - RM: 561779

---
