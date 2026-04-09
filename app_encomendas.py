import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os
import urllib.parse

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Salgados Oliveira - Agenda",
    page_icon="📦",
    layout="wide"
)

ARQUIVO_CSV = "encomendas.csv"
LOGO_PATH = "logo.png"

# NÚMEROS PARA LEMBRETE WHATSAPP
NUMEROS_PRODUCAO = ["5587999968632", "5587935001939"]

# FUNÇÕES AUXILIARES
def atualizar_status_automatico(df):
    """Marca como Entregue automaticamente se passou da data/hora"""
    if df.empty:
        return df

    agora = datetime.now()
    alterou = False

    for idx, row in df.iterrows():
        if row['Status']!= 'Entregue':
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

# TELA DE LOGIN
def login():
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=200)

    st.title("📦 Agenda de Encomendas")
    st.subheader("Salgados Oliveira")
    st.write("Faça login para continuar")

    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

        if entrar:
            if usuario == "admin" and senha == "admin123":
                st.session_state['logado'] = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos!")

# APP PRINCIPAL
def app_principal():
    if os.path.exists(LOGO_PATH):
        st.sidebar.image(LOGO_PATH, use_column_width=True)

    st.sidebar.title("Salgados Oliveira")
    menu = st.sidebar.selectbox("Menu", ["Dashboard", "Nova Encomenda", "Ver Encomendas", "Editar Status", "Excluir Encomenda", "Imprimir Semana", "Lembretes WhatsApp", "Configurações"])

    if st.sidebar.button("Sair"):
        st.session_state['logado'] = False
        st.rerun()

    # DASHBOARD
    if menu == "Dashboard":
        st.subheader("📊 Dashboard de Faturamento")

        df = carregar_dados()

        if df.empty:
            st.info("Nenhuma encomenda cadastrada ainda. Vá em 'Nova Encomenda' para começar.")
        else:
            df['Data_Entrega_dt'] = pd.to_datetime(df['Data_Entrega'], format='%d/%m/%Y', errors='coerce')
            hoje = date.today()
            inicio_semana = hoje - timedelta(days=hoje.weekday())

            col1, col2, col3, col4 = st.columns(4)

            fat_hoje = df[(df['Data_Entrega_dt'].dt.date == hoje) & (df['Status']!= 'Entregue')]['Valor'].sum()
            fat_semana = df[(df['Data_Entrega_dt'].dt.date >= inicio_semana) & (df['Status']!= 'Entregue')]['Valor'].sum()
            fat_total = df[df['Status'] == 'Entregue']['Valor'].sum()
            pedidos_pendentes = len(df[df['Status'].isin(['Pendente', 'Em produção', 'Pronto'])])

            col1.metric("Faturamento Hoje", f"R$ {fat_hoje:.2f}")
            col2.metric("Faturamento Semana", f"R$ {fat_semana:.2f}")
            col3.metric("Total Já Entregue", f"R$ {fat_total:.2f}")
            col4.metric("Pedidos Pendentes", pedidos_pendentes)

            st.divider()

            st.subheader("Entregas por Data")
            df_grafico = df[df['Status']!= 'Entregue'].copy()
            df_grafico = df_grafico[df_grafico['Data_Entrega'].notna()]
            if not df_grafico.empty:
                df_chart = df_grafico.groupby('Data_Entrega')['Valor'].sum().reset_index()
                st.bar_chart(df_chart.set_index('Data_Entrega'))
            else:
                st.info("Sem dados para exibir no gráfico ainda.")

            st.subheader("Próximas 5 Entregas")
            proximas = df[df['Status'].isin(['Pendente', 'Em produção', 'Pronto'])].sort_values('Data_Entrega_dt').head(5)
            if not proximas.empty:
                for _, row in proximas.iterrows():
                    st.write(f"📅 {row['Data_Entrega']} às {row['Hora_Entrega']} - {row['Cliente']} - R$ {row['Valor']:.2f}")
            else:
                st.info("Nenhuma entrega pendente.")

    # NOVA ENCOMENDA
    elif menu == "Nova Encomenda":
        st.subheader("➕ Cadastrar Nova Encomenda")

        with st.form("nova_encomenda", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                cliente = st.text_input("Nome do Cliente*")
                telefone = st.text_input("Telefone/WhatsApp")
                produto = st.text_input("Produto*")
            with col2:
                quantidade = st.number_input("Quantidade*", min_value=1, step=1)
                valor =
