# Informações Adicionais - MIC (Monitoramento Inteligente de Consumo)

## Proposta do Projeto

O **MIC - Monitoramento de Consumo Inteligente** tem como proposta desenvolver um sistema capaz de **monitorar, analisar e recomendar melhorias no consumo de energia elétrica** de aparelhos domésticos.  

A ideia central é que o usuário consiga acompanhar em tempo real o desempenho dos dispositivos conectados, recebendo **alertas automáticos** sobre consumo elevado e **recomendações personalizadas** de economia, com apoio de Inteligência Artificial (Google Gemini).  

Assim, o projeto busca:
- Tornar o consumo de energia mais transparente e compreensível.  
- Auxiliar na redução de gastos com energia elétrica.  
- Incentivar práticas de eficiência energética.  

---

## Como Funciona a Simulação

O aplicativo em Streamlit utiliza um conjunto de **dados simulados (mock)** de dispositivos domésticos, que representam leituras típicas de:

- Tensão (V)  
- Corrente (A)  
- Potência (W)  
- Energia (kWh)  
- Frequência (Hz)  
- Fator de Potência (PF)  

Esses dados alimentam dashboards interativos e servem como insumo para o modelo Gemini gerar **alertas e recomendações inteligentes**.

---

## Protótipo Wokwi

Para simulação de cenários eletrônicos, foi criado um protótipo no Wokwi:  

[🔗 Acessar protótipo Wokwi](https://wokwi.com/projects/439836639430771713)

---

## Site Firebase

O sistema também prevê integração com Firebase para envio de notificações em tempo real:  

[🔗 Acessar site Firebase]([https://wokwi.com/projects/442107050312564737](https://console.firebase.google.com/u/0/project/mic-9d88e/database/mic-9d88e-default-rtdb/data/~2F)

---

## O que já foi feito

✅ Aplicativo em **Streamlit** para visualização de consumo.  
✅ Criação de **mock de dados** representando aparelhos domésticos.  
✅ Exibição de **KPIs e gráficos interativos** (tensão, corrente, potência, energia).  
✅ Integração com **Google Gemini**, fornecendo alertas, recomendações e respostas a perguntas.  
✅ Estruturação inicial da documentação (README e informações adicionais).  

---

## O que ainda falta ser desenvolvido

🔲 Substituir os dados mockados por leituras reais dos dispositivos (integração com hardware).  
🔲 Refinar a interface do usuário com recursos visuais (ícones, cores e alertas destacados).  
🔲 Implementar sistema de **notificações automáticas via Webhook**.  
🔲 Expandir a base de dados para incluir **mais dispositivos e cenários de consumo**.  
🔲 Criar relatórios exportáveis (PDF, gráficos comparativos etc.).  
🔲 Testes de desempenho e validação com usuários finais.  

---

> Esse documento será atualizado conforme o avanço do projeto.
