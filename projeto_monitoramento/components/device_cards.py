import streamlit as st
from utils.style_utils import create_device_card

def render_device_cards(dispositivos):
    """Renderiza os cards dos dispositivos com tratamento seguro de dados"""
    
    st.markdown('<div class="device-section">', unsafe_allow_html=True)
    st.markdown("### Dispositivos Monitorados")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if not dispositivos:
        st.info("📭 Nenhum dispositivo encontrado.")
        return
    
    # Debug: mostrar estrutura dos dados
    st.markdown(f"<small>Encontrados {len(dispositivos)} dispositivos</small>", unsafe_allow_html=True)
    
    # Criar colunas responsivas
    cols = st.columns(len(dispositivos))
    
    for idx, dev in enumerate(dispositivos):
        with cols[idx]:
            try:
                # ✅ EXTRAÇÃO SEGURA DE DADOS
                device_name = extract_value(dev, ["Dispositivo", "Device", "Nome", "name"], f"Dispositivo {idx+1}")
                power_value = extract_numeric(dev, ["Power", "power", "Potência", "potencia"], 0.0)
                energy_value = extract_numeric(dev, ["Energy", "energy", "Energia", "energia"], 0.0)
                priority = extract_value(dev, ["Prioridade", "Priority", "prioridade"], "Média")
                
                st.markdown(
                    create_device_card(
                        device_name=device_name,
                        power=f"{power_value:.1f}",
                        energy=f"{energy_value:.3f}", 
                        priority=priority,
                        color="#E60012"
                    ), 
                    unsafe_allow_html=True
                )
                
            except Exception as e:
                st.error(f"Erro ao processar dispositivo {idx+1}")
                st.markdown(
                    create_device_card(
                        device_name=f"Dispositivo {idx+1}",
                        power="0.0",
                        energy="0.000", 
                        priority="Erro",
                        color="#E60012"
                    ), 
                    unsafe_allow_html=True
                )

def extract_value(data, possible_keys, default):
    """Extrai valor de dicionário tentando várias chaves possíveis"""
    for key in possible_keys:
        if key in data:
            return data[key]
    return default

def extract_numeric(data, possible_keys, default):
    """Extrai valor numérico de dicionário tentando várias chaves possíveis"""
    for key in possible_keys:
        if key in data:
            try:
                return float(data[key])
            except (ValueError, TypeError):
                continue
    return default
