import streamlit as st
import plotly.express as px
import pandas as pd

def render_charts(historico, mostrar_grafico):
    if mostrar_grafico and historico:
        st.markdown("### 📈 Evolução do Consumo Energético")
        
        df_historico = pd.DataFrame(historico)
        df_historico["time"] = pd.to_datetime(df_historico["time"], errors="coerce")
        
        fig = px.line(
            df_historico,
            x="time",
            y="Energy",
            color="Dispositivo",
            markers=True,
            title=""
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#FFFFFF', size=12),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(30, 30, 30, 0.8)',
                bordercolor='rgba(51, 51, 51, 0.3)',
                borderwidth=1,
                font=dict(color='#FFFFFF')
            ),
            xaxis=dict(
                gridcolor='rgba(51, 51, 51, 0.5)',
                title=dict(text='Data/Hora', font=dict(size=14, color='#FFFFFF')),
                tickfont=dict(color='#FFFFFF')
            ),
            yaxis=dict(
                gridcolor='rgba(51, 51, 51, 0.5)',
                title=dict(text='Energia (kWh)', font=dict(size=14, color='#FFFFFF')),
                tickfont=dict(color='#FFFFFF')
            )
        )
        
        # ✅ CORREÇÃO: Adicionar key único para evitar erro de duplicação
        st.plotly_chart(fig, use_container_width=True, key="energy_consumption_chart")

# Função adicional para gráfico de potência (se quiser adicionar mais gráficos)
def render_power_chart(historico):
    if historico:
        df_historico = pd.DataFrame(historico)
        df_historico["time"] = pd.to_datetime(df_historico["time"], errors="coerce")
        
        fig = px.line(
            df_historico,
            x="time",
            y="Power",
            color="Dispositivo",
            markers=True,
            title="Potência por Dispositivo"
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#FFFFFF', size=12)
        )
        
        # ✅ KEY único para cada gráfico
        st.plotly_chart(fig, use_container_width=True, key="power_chart")
