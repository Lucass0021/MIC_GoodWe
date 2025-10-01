import streamlit as st
import time
import pandas as pd

# Importações
from utils.style_utils import apply_custom_style
from components.header import render_header
from components.sidebar import render_sidebar
from components.device_cards import render_device_cards
from components.kpi_cards import render_kpi_cards
from components.charts import render_charts
from services.data_service import DataService
from Cypher.agent import gerar_recomendacoes, fetch_devices_data

# Configuração
st.set_page_config(page_title="Smart Energy Monitor", layout="wide", page_icon="⚡")
apply_custom_style()

# Serviços
data_service = DataService()

# Interface
render_header()
mostrar_grafico, mostrar_tabela, limite_registros = render_sidebar()

# ✅ DADOS MOCK (SEMPRE FUNCIONA)
dispositivos = data_service.get_dispositivos_mock()
historico = data_service.fetch_historico(limit=limite_registros)

# Componentes
render_device_cards(dispositivos)
render_kpi_cards(historico)
render_charts(historico, mostrar_grafico)

# ✅ BOTÃO DE COLETA DE DADOS (AGORA NA POSIÇÃO CORRETA)
st.markdown("### 🔌 Coleta de Dados")
if st.button("📡 **OBTER DADOS TUYA (MOCK)**", use_container_width=True, key="btn_tuya_mock"):
    with st.spinner('🔄 Coletando dados dos dispositivos...'):
        time.sleep(1.5)
        for dev in dispositivos:
            dados = data_service.tuya_mock_status(dev["Device_ID"], dev["Dispositivo"], dev["Prioridade"])
            data_service.save_to_firebase(dados)
    st.success('✅ Dados coletados e salvos com sucesso no Firebase!')
    st.balloons()
    st.rerun()

# ✅ TABELA DE DADOS COMPLETOS (CORRIGIDA)
if mostrar_tabela:
    with st.expander("📊 Ver tabela completa de dados", expanded=False):
        if historico:
            # Criar DataFrame para exibição
            df_display = pd.DataFrame(historico)
            
            # Formatar colunas de data/hora
            if 'time' in df_display.columns:
                df_display['time'] = pd.to_datetime(df_display['time'], errors='coerce')
                df_display['Data/Hora'] = df_display['time'].dt.strftime('%d/%m/%Y %H:%M')
                df_display = df_display.drop('time', axis=1)
            
            # Ordenar por data (se existir)
            if 'Data/Hora' in df_display.columns:
                df_display = df_display.sort_values('Data/Hora', ascending=False)
            
            # Selecionar e renomear colunas para exibição
            colunas_display = [
                'Data/Hora', 'Dispositivo', 'Device_ID', 'Voltage', 'Current', 
                'Power', 'Energy', 'Frequency', 'PF', 'Prioridade'
            ]
            
            # Manter apenas colunas que existem no DataFrame
            colunas_existentes = [col for col in colunas_display if col in df_display.columns]
            df_display = df_display[colunas_existentes]
            
            # Formatar números
            styled_df = df_display.style.format({
                'Voltage': '{:.1f} V',
                'Current': '{:.2f} A', 
                'Power': '{:.1f} W',
                'Energy': '{:.3f} kWh',
                'Frequency': '{:.1f} Hz',
                'PF': '{:.2f}'
            }, na_rep='-')
            
            st.dataframe(styled_df, use_container_width=True, height=400)
            
            # ✅ CORREÇÃO: Estatísticas com formatação segura
            total_registros = len(df_display)
            total_dispositivos = df_display['Dispositivo'].nunique() if 'Dispositivo' in df_display.columns else 0
            
            # Calcular energia total de forma segura
            if 'Energy' in df_display.columns:
                try:
                    energia_total = df_display['Energy'].sum()
                    energia_texto = f"{energia_total:.2f} kWh"
                except:
                    energia_texto = "N/A"
            else:
                energia_texto = "N/A"
            
            st.markdown(f"""
                <div style='
                    background: #1E1E1E;
                    padding: 1rem;
                    border-radius: 8px;
                    border-left: 4px solid #E60012;
                    margin-top: 1rem;
                    border: 1px solid #333333;
                '>
                    <strong style='color: #E60012;'>📈 Estatísticas do Período:</strong> 
                    <span style='color: #B0B0B0;'>
                    {total_registros} registros • 
                    {total_dispositivos} dispositivos • 
                    Energia total: {energia_texto}
                    </span>
                </div>
            """, unsafe_allow_html=True)
            
        else:
            st.info("ℹ️ Nenhum dado disponível para exibição. Clique em 'OBTER DADOS TUYA' para gerar dados simulados.")

# 🤖 CYPHER - Agente Gemini
st.markdown("---")
st.header("🤖 Assistente de Eficiência Energética")

if st.button("🎯 Obter Recomendações Inteligentes", key="btn_recomendacoes"):
    with st.spinner("🔍 Analisando consumo dos dispositivos..."):
        try:
            # Buscar dados reais do Firebase
            dispositivos_reais = fetch_devices_data()
            
            # Gerar recomendações
            recomendacoes = gerar_recomendacoes(dispositivos_reais)
            
            st.success("✅ Análise concluída!")
            
            # Exibir recomendações em um container estilizado
            st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, #1E1E1E 0%, #2A2A2A 100%);
                    padding: 1.5rem;
                    border-radius: 10px;
                    border-left: 5px solid #E60012;
                    margin: 1rem 0;
                    border: 1px solid #333333;
                '>
                    <h4 style='color: #E60012; margin-top: 0;'>💡 Recomendações do Especialista</h4>
                    <div style='color: #B0B0B0; line-height: 1.6; white-space: pre-line;'>{recomendacoes}</div>
                </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Erro ao gerar recomendações: {e}")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #B0B0B0; padding: 2rem 1rem;'>
        <div style='display: flex; justify-content: center; align-items: center; gap: 10px; margin-bottom: 0.5rem;'>
            <span style='color: #E60012;'>⚡</span>
            <strong style='color: #E60012;'>Smart Energy Monitor v2.0</strong>
            <span style='color: #E60012;'>⚡</span>
        </div>
        <small>Sistema de monitoramento energético | Desenvolvido para demonstração</small>
    </div>
""", unsafe_allow_html=True)
