import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.markdown("""
            <div style='
                background: #1E1E1E;
                padding: 1rem;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 1rem;
                border: 1px solid #333333;
            '>
                <h3 style='margin: 0; color: #E60012;'>⚙️ Controles</h3>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("**🔧 Configurações de Exibição**")
        
        mostrar_grafico = st.checkbox("Mostrar Gráfico", value=True)
        mostrar_tabela = st.checkbox("Mostrar Tabela", value=True)
        limite_registros = st.slider("Registros no Histórico", 10, 100, 30)
        
        st.markdown("---")
        st.markdown("**ℹ️ Sobre o Sistema**")
        
        # Card de informações com cores ajustadas
        st.markdown("""
            <div style='
                background: #1E1E1E;
                padding: 1rem;
                border-radius: 10px;
                border: 1px solid #333333;
            '>
                <h4 style='color: #E60012; margin-top: 0;'>Versão 2.0</h4>
                <p style='color: #B0B0B0; margin: 0;'>
                Sistema de monitoramento energético com IA integrada.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        return mostrar_grafico, mostrar_tabela, limite_registros
