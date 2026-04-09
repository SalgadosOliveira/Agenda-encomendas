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
        st.info("💡 Encomendas são marcadas como 'Entregue' automaticamente após a data/hora passar.")

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
                nome_cliente = df.loc[index, 'Cliente']
                df = df.drop(index).reset_index(drop=True)
                salvar_dados(df)
                st.success(f"Encomenda de {nome_cliente} excluída com sucesso!")
                st.rerun()

    # IMPRIMIR SEMANA
    elif menu == "Imprimir Semana":
        st.subheader("🖨️ Relatório de Entregas")

        df = carregar_dados()

        if df.empty:
            st.info("Nenhuma encomenda cadastrada ainda.")
        else:
            df['Data_Entrega_dt'] = pd.to_datetime(df['Data_Entrega'], format='%d/%m/%Y', errors='coerce')

            hoje = date.today()

            tipo_relatorio = st.radio(
                "Tipo de Relatório:",
                ["Por Semana", "Por Mês"],
                horizontal=True
            )

            if tipo_relatorio == "Por Semana":
                inicio_semana_atual = hoje - timedelta(days=hoje.weekday())
                fim_semana_atual = inicio_semana_atual + timedelta(days=6)

                opcao_semana = st.radio(
                    "Selecione a semana:",
                    ["Semana Atual", "Próxima Semana", "Escolher Data"],
                    horizontal=True
                )

                if opcao_semana == "Semana Atual":
                    inicio_semana = inicio_semana_atual
                    fim_semana = fim_semana_atual
                elif opcao_semana == "Próxima Semana":
                    inicio_semana = inicio_semana_atual + timedelta(days=7)
                    fim_semana = inicio_semana + timedelta(days=6)
                else:
                    data_escolhida = st.date_input("Escolha qualquer data da semana", value=hoje)
                    inicio_semana = data_escolhida - timedelta(days=data_escolhida.weekday())
                    fim_semana = inicio_semana + timedelta(days=6)

                st.write(f"**Período:** {inicio_semana.strftime('%d/%m/%Y')} até {fim_semana.strftime('%d/%m/%Y')}")

                df_filtrado = df[
                    (df['Data_Entrega_dt'].dt.date >= inicio_semana) &
                    (df['Data_Entrega_dt'].dt.date <= fim_semana) &
                    (df['Status'].isin(['Pendente', 'Em produção', 'Pronto']))
                ].copy()

                relatorio_texto = gerar_relatorio_semana(df, inicio_semana, fim_semana)

            else: # Por Mês
                col1, col2 = st.columns(2)
                mes_selecionado = col1.selectbox("Mês", range(1, 13), index=hoje.month-1, format_func=lambda x: f"{x:02d}")
                ano_selecionado = col2.number_input("Ano", min_value=2020, max_value=2030, value=hoje.year)

                df_filtrado = df[
                    (df['Data_Entrega_dt'].dt.month == mes_selecionado) &
                    (df['Data_Entrega_dt'].dt.year == ano_selecionado) &
                    (df['Status'].isin(['Pendente', 'Em produção', 'Pronto']))
                ].copy()

                relatorio_texto = gerar_relatorio_mes(df, mes_selecionado, ano_selecionado)

            if df_filtrado.empty:
                st.info("Nenhuma entrega pendente para este período.")
            else:
                df_filtrado = df_filtrado.sort_values(['Data_Entrega_dt', 'Hora_Entrega'])

                st.divider()

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("🖨️ Gerar Relatório para Impressão", type="primary", use_container_width=True):
                        st.markdown("""
                            <style>
                            @media print {
                            .stButton,.stRadio, header, footer, #MainMenu {display: none;}
                            }
                            </style>
                            """, unsafe_allow_html=True)

                        if os.path.exists(LOGO_PATH):
                            st.image(LOGO_PATH, width=150)

                        st.markdown(relatorio_texto.replace('\n', ' \n'))
                        st.info("💡 Para imprimir: aperte Ctrl+P ou Cmd+P no teclado")

                with col2:
                    mensagem_encoded = urllib.parse.quote(relatorio_texto)
                    link = f"https://wa.me/?text={mensagem_encoded}"
                    st.link_button("📱 Compartilhar no WhatsApp", link, use_container_width=True)

    # LEMBRETES WHATSAPP
    elif menu == "Lembretes WhatsApp":
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

    # CONFIGURAÇÕES
    elif menu == "Configurações":
        st.subheader("⚙️ Configurações do App")

        st.write("### Logo da Empresa")

        if os.path.exists(LOGO_PATH):
            st.write("**Logo atual:**")
            st.image(LOGO_PATH, width=200)
            if st.button("Remover Logo Atual"):
                os.remove(LOGO_PATH)
                st.success("Logo removida! Atualize a página.")
                st.rerun()

        st.divider()

        uploaded_file = st.file_uploader("Enviar nova logo", type=['png', 'jpg', 'jpeg'])

        if uploaded_file is not None:
            with open(LOGO_PATH, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("Logo enviada com sucesso! Atualize a página para ver.")
            st.rerun()

        st.info("💡 Dica: Use uma imagem PNG com fundo transparente, tamanho 400x400px fica perfeito.")

        st.divider()
        st.write("### Números para Lembretes WhatsApp")
        st.write("Mensagens são enviadas para:")
        for num in NUMEROS_PRODUCAO:
            st.write(f"📱 +{num}")

# CONTROLE DE LOGIN
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if st.session_state['logado']:
    app_principal()
else:
    login()
