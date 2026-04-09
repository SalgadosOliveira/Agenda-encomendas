import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta
import os
import urllib.parse

ARQUIVO = 'encomendas.csv'
USUARIOS = 'usuarios.csv'

st.set_page_config(page_title="Agenda de Encomendas", layout="wide")

# FUNÇÕES DE DADOS
def carregar_dados():
    if os.path.exists(ARQUIVO):
        df = pd.read_csv(ARQUIVO)
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        return df
    else:
        return pd.DataFrame(columns=[
            'Cliente', 'Telefone', 'Endereco', 'Produto', 'Sabor', 'Quantidade',
            'Data_Entrega', 'Hora_Entrega', 'Forma_Pagamento', 'Valor', 'Status',
            'Data_Pedido', 'Obs', 'Avisado'
        ])

def salvar_dados(df):
    df.to_csv(ARQUIVO, index=False)

def carregar_usuarios():
    if os.path.exists(USUARIOS):
        return pd.read_csv(USUARIOS)
    else:
        df_user = pd.DataFrame([{'usuario': 'admin', 'senha': 'admin123'}])
        df_user.to_csv(USUARIOS, index=False)
        return df_user

def gerar_link_whatsapp(telefone, mensagem):
    tel_limpo = ''.join(filter(str.isdigit, telefone))
    if not tel_limpo.startswith('55'):
        tel_limpo = '55' + tel_limpo
    msg_encoded = urllib.parse.quote(mensagem)
    return f"https://wa.me/{tel_limpo}?text={msg_encoded}"

def gerar_comanda(row):
    comanda_html = f"""
    <div style="border:2px dashed #000; padding:20px; width:350px; font-family:monospace;">
        <h2 style="text-align:center; margin:0;">COMANDA</h2>
        <p style="text-align:center; margin:0;">Pedido #{row.name}</p>
        <hr>
        <p><strong>Cliente:</strong> {row['Cliente']}</p>
        <p><strong>Telefone:</strong> {row['Telefone']}</p>
        <p><strong>Endereço:</strong> {row['Endereco']}</p>
        <hr>
        <p><strong>Produto:</strong> {row['Produto']}</p>
        <p><strong>Sabor:</strong> {row['Sabor']}</p>
        <p><strong>Qtd:</strong> {row['Quantidade']}</p>
        <p><strong>Valor:</strong> R$ {row['Valor']:.2f}</p>
        <p><strong>Pagamento:</strong> {row['Forma_Pagamento']}</p>
        <hr>
        <p><strong>Entrega:</strong> {row['Data_Entrega']} às {row['Hora_Entrega']}</p>
        <p><strong>Status:</strong> {row['Status']}</p>
        {f"<p><strong>Obs:</strong> {row['Obs']}</p>" if pd.notna(row['Obs']) and row['Obs'] else ""}
        <hr>
        <p style="font-size:10px; text-align:center;">Pedido: {row['Data_Pedido']}</p>
    </div>
    """
    return comanda_html

# SISTEMA DE LOGIN
def login():
    st.title("🔐 Login - Agenda de Encomendas")
    usuarios_df = carregar_usuarios()

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar", type="primary", use_container_width=True):
            if not usuarios_df[(usuarios_df['usuario'] == usuario) & (usuarios_df['senha'] == senha)].empty:
                st.session_state['logado'] = True
                st.session_state['usuario'] = usuario
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
        st.caption("Primeiro acesso? Use: admin / admin123")

# APP PRINCIPAL
def app_principal():
    df = carregar_dados()

    # Lembrete de pedidos novos
    if 'ultimo_total' not in st.session_state:
        st.session_state['ultimo_total'] = len(df)

    if len(df) > st.session_state['ultimo_total']:
        novos = len(df) - st.session_state['ultimo_total']
        st.toast(f"🔔 {novos} novo(s) pedido(s) recebido(s)!", icon="🎉")
        st.session_state['ultimo_total'] = len(df)

    # CABEÇALHO
    col1, col2 = st.columns([5,1])
    col1.title("📦 Agenda de Encomendas")
    if col2.button("Sair"):
        st.session_state['logado'] = False
        st.rerun()

    st.caption(f"Logado como: {st.session_state['usuario']}")
    st.divider()

    menu = st.sidebar.radio("Menu", ["Dashboard", "Nova Encomenda", "Ver Agenda", "Exportar", "Gerenciar Usuários"])

    # DASHBOARD
    if menu == "Dashboard":
        st.subheader("📊 Dashboard de Faturamento")

        if df.empty:
            st.info("Nenhuma encomenda cadastrada ainda.")
        else:
            df['Data_Entrega_dt'] = pd.to_datetime(df['Data_Entrega'], format='%d/%m/%Y', errors='coerce')
            hoje = date.today()
            inicio_semana = hoje - timedelta(days=hoje.weekday())

            col1, col2, col3, col4 = st.columns(4)

            # Gráfico por dia - versão corrigida
df_grafico = df[df['Status']!= 'Entregue'].copy()
df_grafico = df_grafico[df_grafico['Data_Entrega'].notna()]  # remove datas vazias
if not df_grafico.empty:
    df_chart = df_grafico.groupby('Data_Entrega')['Valor'].sum().reset_index()
    st.bar_chart(df_chart.set_index('Data_Entrega'))
else:
    st.info("Sem dados para exibir no gráfico ainda.")
        
