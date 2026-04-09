import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Agenda de Encomendas",
    page_icon="📦",
    layout="wide"
)

ARQUIVO_CSV = "encomendas.csv"

# FUNÇÕES AUXILIARES
def carregar_dados():
    if os.path.exists(ARQUIVO_CSV):
        return pd.read_csv(ARQUIVO_CSV)
    else:
        df_vazio = pd.DataFrame(columns=[
            'Data_Pedido', 'Cliente', 'Telefone', 'Produto', 'Quantidade',
            'Valor', 'Data_Entrega', 'Hora_Entrega', 'Status', 'Observacoes'
        ])
        df_vazio.to_csv(ARQUIVO_CSV, index=False)
        return df_vazio

def salvar_dados(df):
    df.to_csv(ARQUIVO_CSV, index=False)

# TELA DE LOGIN
def login():
    st.title("📦 Agenda de Encomendas")
    st.subheader("Faça login para continuar")

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
    st.sidebar.title(f"Bem-vinda!")
    menu = st.sidebar.selectbox("Menu", ["Dashboard", "Nova Encomenda", "Ver Encomendas", "Editar Status", "Excluir Encomenda"])

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
                valor = st.number_input("Valor Total R$*", min_value=0.0, step=0.50, format="%.2f")
                data_entrega = st.date_input("Data de Entrega*", value=date.today())
                hora_entrega = st.time_input("Hora de Entrega*")

            observacoes = st.text_area("Observações")

            enviado = st.form_submit_button("Salvar Encomenda")

            if enviado:
                if cliente and produto and quantidade > 0 and valor > 0:
                    df = carregar_dados()
                    nova_linha = pd.DataFrame([{
                        'Data_Pedido': datetime.now().strftime('%d/%m/%Y %H:%M'),
                        'Cliente': cliente,
                        'Telefone': telefone,
                        'Produto': produto,
                        'Quantidade': quantidade,
                        'Valor': valor,
                        'Data_Entrega': data_entrega.strftime('%d/%m/%Y'),
                        'Hora_Entrega': hora_entrega.strftime('%H:%M'),
                        'Status': 'Pendente',
                        'Observacoes': observacoes
                    }])
                    df = pd.concat([df, nova_linha], ignore_index=True)
                    salvar_dados(df)
                    st.success(f"Encomenda de {cliente} salva com sucesso!")
                else:
                    st.error("Preencha todos os campos com *")

    # VER ENCOMENDAS
    elif menu == "Ver Encomendas":
        st.subheader("📋 Todas as Encomendas")
        df = carregar_dados()

        if df.empty:
            st.info("Nenhuma encomenda cadastrada ainda.")
        else:
            filtro_status = st.multiselect(
                "Filtrar por Status",
                options=['Pendente', 'Em produção', 'Pronto', 'Entregue'],
                default=['Pendente', 'Em produção', 'Pronto']
            )
            df_filtrado = df[df['Status'].isin(filtro_status)]
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    # EDITAR STATUS
    elif menu == "Editar Status":
        st.subheader("✏️ Atualizar Status da Encomenda")
        df = carregar_dados()

        if df.empty:
            st.info("Nenhuma encomenda para editar.")
        else:
            df['Opcao'] = df.index.astype(str) + " - " + df['Cliente'] + " - " + df['Produto'] + " - " + df['Data_Entrega']

            encomenda_selecionada = st.selectbox("Selecione a encomenda", df['Opcao'])
            index = int(encomenda_selecionada.split(" - ")[0])

            st.write(f"**Cliente:** {df.loc[index, 'Cliente']}")
            st.write(f"**Produto:** {df.loc[index, 'Produto']}")
            st.write(f"**Status Atual:** {df.loc[index, 'Status']}")

            novo_status = st.selectbox(
                "Novo Status",
                ['Pendente', 'Em produção', 'Pronto', 'Entregue'],
                index=['Pendente', 'Em produção', 'Pronto', 'Entregue'].index(df.loc[index, 'Status'])
            )

            if st.button("Atualizar Status"):
                df.loc[index, 'Status'] = novo_status
                salvar_dados(df)
                st.success("Status atualizado com sucesso!")
                st.rerun()

    # EXCLUIR ENCOMENDA
    elif menu == "Excluir Encomenda":
        st.subheader("🗑️ Excluir Encomenda")
        st.warning("Atenção: Esta ação não pode ser desfeita!")

        df = carregar_dados()

        if df.empty:
            st.info("Nenhuma encomenda para excluir.")
        else:
            df['Opcao'] = df.index.astype(str) + " - " + df['Cliente'] + " - " + df['Produto'] + " - " + df['Data_Entrega'] + " - R$ " + df['Valor'].astype(str)

            encomenda_selecionada = st.selectbox("Selecione a encomenda para excluir", df['Opcao'])
            index = int(encomenda_selecionada.split(" - ")[0])

            st.divider()
            st.write("**Dados da encomenda selecionada:**")
            col1, col2 = st.columns(2)
            col1.write(f"**Cliente:** {df.loc[index, 'Cliente']}")
            col1.write(f"**Produto:** {df.loc[index, 'Produto']}")
            col1.write(f"**Quantidade:** {df.loc[index, 'Quantidade']}")
            col2.write(f"**Valor:** R$ {df.loc[index, 'Valor']:.2f}")
            col2.write(f"**Data Entrega:** {df.loc[index, 'Data_Entrega']}")
            col2.write(f"**Status:** {df.loc[index, 'Status']}")

            st.divider()

            confirmar = st.checkbox("Sim, tenho certeza que quero excluir esta encomenda")

            if st.button("🗑️ Excluir Definitivamente", type="primary", disabled=not confirmar):
                df = df.drop(index).reset_index(drop=True)
                salvar_dados(df)
                st.success(f"Encomenda de {df.loc[index, 'Cliente']} excluída com sucesso!")
                st.rerun()

# CONTROLE DE LOGIN
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if st.session_state['logado']:
    app_principal()
else:
    login()
