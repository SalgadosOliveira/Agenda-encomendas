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
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    :root {
        --primary: #FF6B35;
        --secondary: #F7931E;
        --success: #00C851;
        --danger: #ff4444;
        --dark: #2E2E2E;
    }

  .main {
        background: linear-gradient(135deg, #FFF5F0 0%, #FFE8D6 100%);
    }

  .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid var(--primary);
        margin-bottom: 15px;
    }

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

    h1 {
        color: #2E2E2E;
        font-weight: 700;
    }

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
        if row['Status'] not in ['Entregue', 'Cancelada']:
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
            relatorio += f"- {row['Hora_Entrega']} | {row['Cliente']} | {row['Quantidade']}x {row['Produto']} | R$ {row['Valor']:.2f}\n"
        relatorio += "\n"

    return relatorio

def gerar_relatorio_canceladas(df, inicio, fim):
    df_canceladas = df[
        (df['Data_Entrega_dt'].dt.date >= inicio) &
        (df['Data_Entrega_dt'].dt.date <= fim) &
        (df['Status'] == 'Cancelada')
    ].copy()

    if df_canceladas.empty:
        return "Nenhuma encomenda cancelada neste período."

    df_canceladas = df_canceladas.sort_values(['Data_Entrega_dt', 'Hora_Entrega'])
    total = df_canceladas['Valor'].sum()

    relatorio = f"*RELATÓRIO CANCELADAS ({inicio.strftime('%d/%m')} a {fim.strftime('%d/%m')})*\n"
    relatorio += f"Total: {len(df_canceladas)} pedidos | R$ {total:.2f}\n\n"

    for data, grupo in df_canceladas.groupby('Data_Entrega'):
        relatorio += f"📅 {data}\n"
        for _, row in grupo.iterrows():
            relatorio += f"- {row['Hora_Entrega']} | {row['Cliente']} | {row['Quantidade']}x {row['Produto']} | R$ {row['Valor']:.2f}\n"
        relatorio += "\n"

    return relatorio

# TELA DE LOGIN
def login():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=150)

        st.markdown("<h1 style='text-align: center; color: #FF6B35;'>🥟 Salgados Oliveira</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>Sistema de Gestão de Encomendas</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("login_form"):
            usuario = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            senha = st.text_input("🔒 Senha", type="password", placeholder="Digite sua senha")
            entrar = st.form_submit_button("Entrar", use_container_width=True)

            if entrar:
                if usuario == "admin" and senha == "admin123":
                    st.session_state['logado'] = True
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos!")

        st.markdown('</div>', unsafe_allow_html=True)

# APP PRINCIPAL
def app_principal():
    # HEADER
    col1, col2, col3 = st.columns([1,3,1])
    with col1:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=80)
    with col2:
        st.markdown("<h1 style='text-align: center; margin: 0;'>🥟 Salgados Oliveira</h1>", unsafe_allow_html=True)
    with col3:
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state['logado'] = False
            st.rerun()

    st.markdown("---")

    # ABAS DE NAVEGAÇÃO
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "📊 Dashboard",
        "➕ Nova",
        "📋 Ver",
        "✏️ Editar",
        "🗑️ Excluir",
        "✅ Entregues",
        "🚫 Canceladas",
        "🖨️ Relatório",
        "📱 Lembretes",
        "⚙️ Config"
    ])

    # ABA 1 - DASHBOARD
    with tab1:
        df = carregar_dados()

        if df.empty:
            st.info("📭 Nenhuma encomenda cadastrada ainda. Vá em 'Nova' para começar.")
        else:
            df['Data_Entrega_dt'] = pd.to_datetime(df['Data_Entrega'], format='%d/%m/%Y', errors='coerce')
            hoje = date.today()
            inicio_semana = hoje - timedelta(days=hoje.weekday())

            fat_hoje = df[(df['Data_Entrega_dt'].dt.date == hoje) & (df['Status']!= 'Entregue') & (df['Status']!= 'Cancelada')]['Valor'].sum()
            fat_semana = df[(df['Data_Entrega_dt'].dt.date >= inicio_semana) & (df['Status']!= 'Entregue') & (df['Status']!= 'Cancelada')]['Valor'].sum()
            fat_total = df[df['Status'] == 'Entregue']['Valor'].sum()
            pedidos_pendentes = len(df[df['Status'].isin(['Pendente', 'Em produção', 'Pronto'])])

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                card_metrica("Hoje", f"R$ {fat_hoje:.2f}", "💰", "#FF6B35")
            with col2:
                card_metrica("Semana", f"R$ {fat_semana:.2f}", "📈", "#F7931E")
            with col3:
                card_metrica("Entregue", f"R$ {fat_total:.2f}", "✅", "#00C851")
            with col4:
                card_metrica("Pendentes", str(pedidos_pendentes), "⏰", "#ff4444")

            st.markdown("<br>", unsafe_allow_html=True)

            col1, col2 = st.columns([2,1])

            with col1:
                st.subheader("📊 Faturamento por Data")
                df_grafico = df[(df['Status']!= 'Entregue') & (df['Status']!= 'Cancelada')].copy()
                df_grafico = df_grafico[df_grafico['Data_Entrega'].notna()]
                if not df_grafico.empty:
                    df_chart = df_grafico.groupby('Data_Entrega')['Valor'].sum().reset_index()
                    st.bar_chart(df_chart.set_index('Data_Entrega'))
                else:
                    st.info("Sem dados para exibir ainda.")

            with col2:
                st.subheader("🔔 Próximas Entregas")
                proximas = df[df['Status'].isin(['Pendente', 'Em produção', 'Pronto'])].sort_values('Data_Entrega_dt').head(5)
                if not proximas.empty:
                    for _, row in proximas.iterrows():
                        st.markdown(f"""
                        <div style='background: white; padding: 12px; border-radius: 10px; margin-bottom: 10px; border-left: 3px solid #FF6B35;'>
                            <strong>{row['Cliente']}</strong><br>
                            <span style='color: #888; font-size: 13px;'>📅 {row['Data_Entrega']} às {row['Hora_Entrega']}</span><br>
                            <span style='color: #FF6B35; font-weight: 600;'>R$ {row['Valor']:.2f}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Nenhuma entrega pendente.")

    # ABA 2 - NOVA ENCOMENDA
    with tab2:
        st.subheader("➕ Cadastrar Nova Encomenda")

        with st.form("nova_encomenda", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Dados do Cliente**")
                cliente = st.text_input("Nome*", placeholder="Nome completo")
                telefone = st.text_input("WhatsApp", placeholder="(87) 99999-9999")
                produto = st.text_input("Produto*", placeholder="Ex: Coxinha, Pastel")
            with col2:
                st.markdown("**Detalhes do Pedido**")
                quantidade = st.number_input("Quantidade*", min_value=1, step=1)
                valor = st.number_input("Valor Total R$*", min_value=0.0, step=0.50, format="%.2f")
                data_entrega = st.date_input("Data de Entrega*", value=date.today())
                hora_entrega = st.time_input("Hora de Entrega*")

            observacoes = st.text_area("📝 Observações", placeholder="Alguma observação especial?")

            enviado = st.form_submit_button("💾 Salvar Encomenda", use_container_width=True)

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
                    st.success(f"✅ Encomenda de {cliente} salva com sucesso!")
                    st.balloons()
                else:
                    st.error("❌ Preencha todos os campos com *")

    # ABA 3 - VER ENCOMENDAS
    with tab3:
        st.subheader("📋 Todas as Encomendas")
        df = carregar_dados()

        if df.empty:
            st.info("📭 Nenhuma encomenda cadastrada ainda.")
        else:
            filtro_status = st.multiselect(
                "Filtrar por Status",
                options=['Pendente', 'Em produção', 'Pronto', 'Entregue', 'Cancelada'],
                default=['Pendente', 'Em produção', 'Pronto']
            )
            df_filtrado = df[df['Status'].isin(filtro_status)]
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True, height=400)

    # ABA 4 - EDITAR STATUS
    with tab4:
        st.subheader("✏️ Atualizar Status")
        st.info("💡 Encomendas são marcadas como 'Entregue' automaticamente após a data/hora passar.")

        df = carregar_dados()

        if df.empty:
            st.info("📭 Nenhuma encomenda para editar.")
        else:
            df['Opcao'] = df.index.astype(str) + " - " + df['Cliente'] + " - " + df['Produto'] + " - " + df['Data_Entrega']

            encomenda_selecionada = st.selectbox("Selecione a encomenda", df['Opcao'])
            index = int(encomenda_selecionada.split(" - ")[0])

            col1, col2, col3 = st.columns(3)
            col1.metric("Cliente", df.loc[index, 'Cliente'])
            col2.metric("Produto", df.loc[index, 'Produto'])
            col3.metric("Status Atual", df.loc[index, 'Status'])

            novo_status = st.selectbox(
                "Novo Status",
                ['Pendente', 'Em produção', 'Pronto', 'Entregue', 'Cancelada'],
                index=['Pendente', 'Em produção', 'Pronto', 'Entregue', 'Cancelada'].index(df.loc[index, 'Status'])
            )

            if st.button("✅ Atualizar Status", use_container_width=True):
                df.loc[index, 'Status'] = novo_status
                salvar_dados(df)
                st.success("Status atualizado com sucesso!")
                st.rerun()

    # ABA 5 - EXCLUIR
    with tab5:
        st.subheader("🗑️ Excluir Encomenda")
        st.warning("⚠️ Atenção: Esta ação não pode ser desfeita!")

        df = carregar_dados()

        if df.empty:
            st.info("📭 Nenhuma encomenda para excluir.")
        else:
            df['Opcao'] = df.index.astype(str) + " - " + df['Cliente'] + " - " + df['Produto'] + " - " + df['Data_Entrega']

            encomenda_selecionada = st.selectbox("Selecione a encomenda para excluir", df['Opcao'])
            index = int(encomenda_selecionada.split(" - ")[0])

            st.markdown("---")
            col1, col2 = st.columns(2)
            col1.write(f"**Cliente:** {df.loc[index, 'Cliente']}")
            col1.write(f"**Produto:** {df.loc[index, 'Produto']}")
            col2.write(f"**Valor:** R$ {df.loc[index, 'Valor']:.2f}")
            col2.write(f"**Data:** {df.loc[index, 'Data_Entrega']}")

            st.markdown("---")

            confirmar = st.checkbox("Sim, tenho certeza que quero excluir esta encomenda")

            if st.button("🗑️ Excluir Definitivamente", use_container_width=True, disabled=not confirmar):
                nome_cliente = df.loc[index, 'Cliente']
                df = df.drop(index).reset_index(drop=True)
                salvar_dados(df)
                st.success(f"Encomenda de {nome_cliente} excluída!")
                st.rerun()

    # ABA 6 - ENTREGUES
    with tab6:
        st.subheader("✅ Encomendas Entregues")
        df = carregar_dados()

        if df.empty:
            st.info("📭 Nenhuma encomenda cadastrada ainda.")
        else:
            df['Data_Entrega_dt'] = pd.to_datetime(df['Data_Entrega'], format='%d/%m/%Y', errors='coerce')
            hoje = date.today()
            inicio = hoje - timedelta(days=30)
            fim = hoje

            col1, col2 = st.columns(2)
            inicio = col1.date_input("De", value=inicio)
            fim = col2.date_input("Até", value=fim)

            df_entregues = df[
                (df['Data_Entrega_dt'].dt.date >= inicio) &
                (df['Data_Entrega_dt'].dt.date <= fim) &
                (df['Status'] == 'Entregue')
            ]

            if df_entregues.empty:
                st.info("Nenhuma entrega registrada neste período.")
            else:
                total_entregue = df_entregues['Valor'].sum()
                st.write(f"**Total:** {len(df_entregues)} entregas | **R$ {total_entregue:.2f}**")
                st.dataframe(df_entregues, use_container_width=True, hide_index=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🖨️ Gerar Relatório", use_container_width=True):
                        relatorio = gerar_relatorio_entregues(df, inicio, fim)
                        st.markdown(relatorio.replace('\n', ' \n'))
                        st.info("💡 Aperte Ctrl+P para imprimir")

                with col2:
                    relatorio = gerar_relatorio_entregues(df, inicio, fim)
                    link = f"https://wa.me/?text={urllib.parse.quote(relatorio)}"
                    st.link_button("📱 Compartilhar WhatsApp", link, use_container_width=True)

    # ABA 7 - CANCELADAS
    with tab7:
        st.subheader("🚫 Encomendas Canceladas")
        df = carregar_dados()

        if df.empty:
            st.info("📭 Nenhuma encomenda cadastrada ainda.")
        else:
            df['Data_Entrega_dt'] = pd.to_datetime(df['Data_Entrega'], format='%d/%m/%Y', errors='coerce')
            hoje = date.today()
            inicio = hoje - timedelta(days=30)
            fim = hoje

            col1, col2 = st.columns(2)
            inicio = col1.date_input("De", value=inicio, key="canc_de")
            fim = col2.date_input("Até", value=fim, key="canc_ate")

            df_canceladas = df[
                (df['Data_Entrega_dt'].dt.date >= inicio) &
                (df['Data_Entrega_dt'].dt.date <= fim) &
                (df['Status'] == 'Cancelada')
            ]

            if df_canceladas.empty:
                st.info("Nenhuma encomenda cancelada neste período.")
            else:
                total_cancelado = df_canceladas['Valor'].sum()
                st.write(f"**Total:** {len(df_canceladas)} canceladas | **R$ {total_cancelado:.2f}**")
                st.dataframe(df_canceladas, use_container_width=True, hide_index=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🖨️ Gerar Relatório", use_container_width=True, key="rel_canc"):
                        relatorio = gerar_relatorio_canceladas(df, inicio, fim)
                        st.markdown(relatorio.replace('\n', ' \n'))
                        st.info("💡 Aperte Ctrl+P para imprimir")

                with col2:
                    relatorio = gerar_relatorio_canceladas(df, inicio, fim)
                    link = f"https://wa.me/?text={urllib.parse.quote(relatorio)}"
                    st.link_button("📱 Compartilhar WhatsApp", link, use_container_width=True)

    # ABA 8 - RELATÓRIO
    with tab8:
        st.subheader("🖨️ Gerar Relatório")

        df = carregar_dados()

        if df.empty:
            st.info("📭 Nenhuma encomenda cadastrada ainda.")
        else:
            df['Data_Entrega_dt'] = pd.to_datetime(df['Data_Entrega'], format='%d/%m/%Y', errors='coerce')
            hoje = date.today()

            tipo = st.radio("Tipo:", ["📅 Por Semana", "📆 Por Mês"], horizontal=True)

            if tipo == "📅 Por Semana":
                inicio = hoje - timedelta(days=hoje.weekday())
                fim = inicio + timedelta(days=6)
                st.write(f"**Período:** {inicio.strftime('%d/%m/%Y')} até {fim.strftime('%d/%m/%Y')}")

                df_filtrado = df[
                    (df['Data_Entrega_dt'].dt.date >= inicio) &
                    (df['Data_Entrega_dt'].dt.date <= fim) &
                    (df['Status'].isin(['Pendente', 'Em produção', 'Pronto']))
                ].copy()

                relatorio = gerar_relatorio_semana(df, inicio, fim)
            else:
                col1, col2 = st.columns(2)
                mes = col1.selectbox("Mês", range(1, 13), index=hoje.month-1, format_func=lambda x: f"{x:02d}")
                ano = col2.number_input("Ano", min_value=2020, max_value=2030, value=hoje.year)

                df_filtrado = df[
                    (df['Data_Entrega_dt'].dt.month == mes) &
                    (df['Data_Entrega_dt'].dt.year == ano) &
                    (df['Status'].isin(['Pendente', 'Em produção', 'Pronto']))
                ].copy()

                relatorio = gerar_relatorio_mes(df, mes, ano)

            if df_filtrado.empty:
                st.info("Nenhuma entrega pendente para este período.")
            else:
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("🖨️ Imprimir", use_container_width=True):
                        if os.path.exists(LOGO_PATH):
                            st.image(LOGO_PATH, width=150)
                        st.markdown(relatorio.replace('\n', ' \n'))
                        st.info("💡 Aperte Ctrl+P ou Cmd+P para imprimir")

                with col2:
                    link = f"https://wa.me/?text={urllib.parse.quote(relatorio)}"
                    st.link_button("📱 Compartilhar WhatsApp", link, use_container_width=True)

    # ABA 9 - LEMBRETES WHATSAPP
    with tab9:
        st.subheader("📱 Lembretes para Produção")
        st.write("Envia mensagem 10h antes da entrega para os números cadastrados.")

        df = carregar_dados()

        if df.empty:
            st.info("Nenhuma encomenda cadastrada.")
        else:
            agora = datetime.now()
            limite = agora + timedelta(hours=10)

            df_lembretes = df[df['Status'].isin(['Pendente', 'Em produção'])].copy()
            df_lembretes['Data_Entrega_dt'] = pd.to_datetime(
                df_lembretes['Data_Entrega'] + ' ' + df_lembretes['Hora_Entrega'],
                format='%d/%m/%Y %H:%M',
                errors='coerce'
            )

            df_lembretes = df_lembretes[
                (df_lembretes['Data_Entrega_dt'] > agora) &
                (df_lembretes['Data_Entrega_dt'] <= limite)
            ].sort_values('Data_Entrega_dt')

            if df_lembretes.empty:
                st.success("✅ Nenhum lembrete necessário agora. Nenhuma encomenda nas próximas 10 horas.")
            else:
                st.warning(f"⚠️ {len(df_lembretes)} encomenda(s) precisa(m) ser produzida(s) nas próximas 10h!")

                for _, row in df_lembretes.iterrows():
                    tempo_restante = row['Data_Entrega_dt'] - agora
                    horas = int(tempo_restante.total_seconds() // 3600)
                    minutos = int((tempo_restante.total_seconds() % 3600) // 60)

                    with st.expander(f"🔔 {row['Cliente']} - Entrega em {horas}h {minutos}min"):
                        st.write(f"**Cliente:** {row['Cliente']}")
                        st.write(f"**Produto:** {row['Quantidade']}x {row['Produto']}")
                        st.write(f"**Entrega:** {row['Data_Entrega']} às {row['Hora_Entrega']}")
                        st.write(f"**Telefone Cliente:** {row['Telefone']}")
                        if pd.notna(row['Observacoes']):
                            st.write(f"**Obs:** {row['Observacoes']}")

                        mensagem = f"""🔔 *LEMBRETE DE PRODUÇÃO - Salgados Oliveira*

*Cliente:* {row['Cliente']}
*Produto:* {row['Quantidade']}x {row['Produto']}
*Entrega:* {row['Data_Entrega']} às {row['Hora_Entrega']}
*Telefone:* {row['Telefone']}

⏰ Faltam {horas}h {minutos}min para a entrega!

{f"Obs: {row['Observacoes']}" if pd.notna(row['Observacoes']) else ""}"""

                        mensagem_encoded = urllib.parse.quote(mensagem)

                        st.divider()
                        col1, col2 = st.columns(2)

                        for idx, numero in enumerate(NUMEROS_PRODUCAO):
                            link = f"https://wa.me/{numero}?text={mensagem_encoded}"
                            coluna = col1 if idx == 0 else col2
                            coluna.link_button(
                                f"📱 Enviar para {numero[-9:]}",
                                link,
                                use_container_width=True
                            )

    # ABA 10 - CONFIGURAÇÕES
    with tab10:
        st.subheader("⚙️ Configurações")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Logo da Empresa**")
            if os.path.exists(LOGO_PATH):
                st.image(LOGO_PATH, width=200)
                if st.button("Remover Logo"):
                    os.remove(LOGO_PATH)
                    st.success("Logo removida!")
                    st.rerun()
            else:
                st.info("Nenhuma logo enviada")

            uploaded = st.file_uploader("Enviar logo", type=['png', 'jpg', 'jpeg'])
            if uploaded:
                with open(LOGO_PATH, "wb") as f:
                    f.write(uploaded.getbuffer())
                st.success("Logo enviada!")
                st.rerun()

        with col2:
            st.markdown("**Lembretes WhatsApp**")
            st.info("Mensagens são enviadas para:")
            for num in NUMEROS_PRODUCAO:
                st.write(f"📱 +{num}")

            st.markdown("---")
            st.markdown("**Sobre o App**")
            st.write("Versão: 3.0")
            st.write("Desenvolvido para Salgados Oliveira")

# CONTROLE DE LOGIN
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if st.session_state['logado']:
    app_principal()
else:
    login()
import streamlit as st
from openai import OpenAI

# Coloca a chave da OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Adiciona uma aba no sidebar
with st.sidebar:
    aba = st.sidebar.tabs(["Encomendas", "Atendimento"])

    with aba[0]:
        # Seu app antigo aqui
        st.write("Aqui fica o app de encomendas")

    with aba[1]:
        st.title("🥟 Atendente Virtual")
        st.write("Fala comigo para fazer um pedido!")

        if "chat" not in st.session_state:
            st.session_state.chat = [
                {"role": "assistant", "content": "Oi! Sou do Salgados Oliveira. O que você quer?"}
            ]

        # Mostra a conversa
        for msg in st.session_state.chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input do usuário
        if prompt := st.chat_input("Digite aqui..."):
            st.session_state.chat.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Resposta da IA
            with st.chat_message("assistant"):
                with st.spinner("Digitando..."):
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=st.session_state.chat
                    )
                    resposta = response.choices[0].message.content
                    st.session_state.chat.append({"role": "assistant", "content": resposta})
                    st.markdown(resposta)
