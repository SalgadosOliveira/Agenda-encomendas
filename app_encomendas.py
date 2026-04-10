import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os
import urllib.parse

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Salgados Oliveira",
    page_icon="🥟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS CUSTOMIZADO - DESIGN PREMIUM
st.markdown("""
<style>
    /* Esconder menu padrão do streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Cores principais */
    :root {
        --primary: #FF6B35;
        --secondary: #F7931E;
        --success: #00C851;
        --danger: #ff4444;
        --dark: #2E2E2E;
    }

    /* Container principal */
   .main {
        background: linear-gradient(135deg, #FFF5F0 0%, #FFE8D6 100%);
    }

    /* Cards */
   .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid var(--primary);
        margin-bottom: 15px;
    }

    /* Botões */
   .stButton>button {
        border-radius: 10px;
        border: none;
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
        color: white;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.3s;
    }

   .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(255,107,53,0.3);
    }

    /* Abas */
   .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: white;
        padding: 10px;
        border-radius: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

   .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
    }

   .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
        color: white;
    }

    /* Título */
    h1 {
        color: #2E2E2E;
        font-weight: 700;
    }

    /* Login card */
   .login-container {
        max-width: 400px;
        margin: 50px auto;
        padding: 40px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

ARQUIVO_CSV = "encomendas.csv"
LOGO_PATH = "logo.png"
NUMEROS_PRODUCAO = ["5587999968632", "5587935001939"]

# FUNÇÕES AUXILIARES
def atualizar_status_automatico(df):
    if df.empty:
        return df
    agora = datetime.now()
    alterou = False
    for idx, row in df.iterrows():
        if row['Status']!= 'Entregue' and row['Status']!= 'Cancelada':
            try:
                data_str = f"{row['Data_Entrega']} {row['Hora_Entrega']}"
                data_entrega = datetime.strptime(data_str, '%d/%m/%Y %H:%M')
                if agora > data_entrega:
                    df.loc[idx, 'Status'] = 'Entregue'
                    alterou = True
            except:
                pass
    if alterou:
        salvar_dados(df)
    return df

def carregar_dados():
    if os.path.exists(ARQUIVO_CSV):
        df = pd.read_csv(ARQUIVO_CSV)
        df = atualizar_status_automatico(df)
        return df
    else:
        df_vazio = pd.DataFrame(columns=[
            'Data_Pedido', 'Cliente', 'Telefone', 'Produto', 'Quantidade',
            'Valor', 'Data_Entrega', 'Hora_Entrega', 'Status', 'Observacoes'
        ])
        df_vazio.to_csv(ARQUIVO_CSV, index=False)
        return df_vazio

def salvar_dados(df):
    df.to_csv(ARQUIVO_CSV, index=False)

def card_metrica(titulo, valor, icone, cor):
    st.markdown(f"""
        <div class="metric-card" style="border-left-color: {cor};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <p style="color: #888; font-size: 14px; margin: 0;">{titulo}</p>
                    <h2 style="color: #2E2E2E; margin: 5px 0 0 0;">{valor}</h2>
                </div>
                <div style="font-size: 40px;">{icone}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def gerar_relatorio_semana(df, inicio_semana, fim_semana):
    df_semana = df[
        (df['Data_Entrega_dt'].dt.date >= inicio_semana) &
        (df['Data_Entrega_dt'].dt.date <= fim_semana) &
        (df['Status'].isin(['Pendente', 'Em produção', 'Pronto']))
    ].copy()

    if df_semana.empty:
        return "Nenhuma entrega pendente para esta semana."

    df_semana = df_semana.sort_values(['Data_Entrega_dt', 'Hora_Entrega'])
    total_semana = df_semana['Valor'].sum()

    relatorio = f"*RELATÓRIO SEMANA {inicio_semana.strftime('%d/%m')} a {fim_semana.strftime('%d/%m')}*\n"
    relatorio += f"Total: {len(df_semana)} pedidos | R$ {total_semana:.2f}\n\n"

    for data, grupo in df_semana.groupby('Data_Entrega'):
        relatorio += f"📅 {data}\n"
        for _, row in grupo.iterrows():
            relatorio += f"- {row['Hora_Entrega']} | {row['Cliente']} | {row['Quantidade']}x {row['Produto']} | R$ {row['Valor']:.2f}\n"
        relatorio += "\n"

    return relatorio

def gerar_relatorio_mes(df, mes, ano):
    df_mes = df[
        (df['Data_Entrega_dt'].dt.month == mes) &
        (df['Data_Entrega_dt'].dt.year == ano) &
        (df['Status'].isin(['Pendente', 'Em produção', 'Pronto']))
    ].copy()

    if df_mes.empty:
        return "Nenhuma entrega pendente para este mês."

    df_mes = df_mes.sort_values(['Data_Entrega_dt', 'Hora_Entrega'])
    total_mes = df_mes['Valor'].sum()

    relatorio = f"*RELATÓRIO MÊS {mes}/{ano}*\n"
    relatorio += f"Total: {len(df_mes)} pedidos | R$ {total_mes:.2f}\n\n"

    for data, grupo in df_mes.groupby('Data_Entrega'):
        relatorio += f"📅 {data}\n"
        for _, row in grupo.iterrows():
            relatorio += f"- {row['Hora_Entrega']} | {row['Cliente']} | {row['Quantidade']}x {row['Produto']} | R$ {row['Valor']:.2f}\n"
        relatorio += "\n"

    return relatorio

def gerar_relatorio_entregues(df, inicio, fim):
    df_entregues = df[
        (df['Data_Entrega_dt'].dt.date >= inicio) &
        (df['Data_Entrega_dt'].dt.date <= fim) &
        (df['Status'] == 'Entregue')
    ].copy()

    if df_entregues.empty:
        return "Nenhuma entrega registrada neste período."

    df_entregues = df_entregues.sort_values(['Data_Entrega_dt', 'Hora_Entrega'])
    total = df_entregues['Valor'].sum()

    relatorio = f"*RELATÓRIO ENTREGUES ({inicio.strftime('%d/%m')} a {fim.strftime('%d/%m')})*\n"
    relatorio += f"Total: {len(df_entregues)} pedidos | R$ {total:.2f}\n\n"

    for data, grupo in df_entregues.groupby('Data_Entrega'):
        relatorio += f"📅 {data}\n"
        for _, row in grupo.iterrows():
            relatorio += f"- {
