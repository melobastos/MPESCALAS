import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date
import altair as alt

# Configuração da página
st.set_page_config(
    page_title="Gerador de Escala de Trabalho",
    page_icon="📅",
    layout="wide"
)

# Função para gerar a escala considerando exceções e alocações fixas
def gerar_escala(mes, ano, funcionarios, excecoes, alocacoes_fixas, considerar_carga=True):
    # Dicionário para controlar a carga de trabalho de cada funcionário
    carga_trabalho = {f: 0 for f in funcionarios}
    
    # Identificar os dias úteis do mês
    dias_uteis = []
    dias_semana_no_mes = {}  # Mapear dias do mês para dias da semana
    
    for dia in range(1, calendar.monthrange(ano, mes)[1] + 1):
        data = date(ano, mes, dia)
        dia_semana = data.weekday()
        dias_semana_no_mes[dia] = dia_semana
        if dia_semana < 5:  # Segunda (0) a Sexta (4)
            dias_uteis.append(dia)
    
    escala = []
    
    # Para cada dia útil, alocar funcionários aos turnos
    for dia in dias_uteis:
        data = date(ano, mes, dia)
        dia_semana = calendar.day_name[data.weekday()]
        dia_semana_num = data.weekday()  # 0 = Segunda, 1 = Terça, ...
        
        # Verificar alocações fixas primeiro
        turno_matutino = None
        turno_vespertino = None
        
        # Verificar alocações fixas por dia da semana
        for funcionario, detalhes in alocacoes_fixas.get('dia_semana', {}).items():
            if dia_semana_num in detalhes.get('dias', []) and funcionario in funcionarios:
                if 'Matutino' in detalhes.get('turnos', []) and not turno_matutino:
                    turno_matutino = funcionario
                if 'Vespertino' in detalhes.get('turnos', []) and not turno_vespertino:
                    turno_vespertino = funcionario
        
        # Verificar alocações fixas por dias específicos do mês
        for funcionario, detalhes in alocacoes_fixas.get('dias_especificos', {}).items():
            if dia in detalhes.get('dias', []) and funcionario in funcionarios:
                if 'Matutino' in detalhes.get('turnos', []) and not turno_matutino:
                    turno_matutino = funcionario
                if 'Vespertino' in detalhes.get('turnos', []) and not turno_vespertino:
                    turno_vespertino = funcionario
        
        # Encontrar funcionários disponíveis para cada turno (excluindo os que têm exceções)
        disponiveis_matutino = []
        disponiveis_vespertino = []
        
        for funcionario in funcionarios:
            # Verificar exceções por dia específico
            excepcao_dia = (dia, funcionario) in excecoes.get('dias_especificos', {})
            
            # Verificar exceções por intervalo de dias
            excepcao_intervalo = False
            for intervalo in excecoes.get('intervalos', {}).get(funcionario, []):
                if intervalo[0] <= dia <= intervalo[1]:
                    excepcao_intervalo = True
                    break
            
            # Verificar exceções por dia da semana
            excepcao_dia_semana = dia_semana_num in excecoes.get('dias_semana', {}).get(funcionario, [])
            
            # Verificar exceções por turno específico
            excepcao_turno_matutino = funcionario in excecoes.get('turnos', {}).get((dia, 'Matutino'), [])
            excepcao_turno_vespertino = funcionario in excecoes.get('turnos', {}).get((dia, 'Vespertino'), [])
            
            # Adicionar às listas de disponíveis se não tiver exceções
            if not excepcao_dia and not excepcao_intervalo and not excepcao_dia_semana and not excepcao_turno_matutino:
                if not turno_matutino:  # Se não tiver alocação fixa
                    disponiveis_matutino.append(funcionario)
                    
            if not excepcao_dia and not excepcao_intervalo and not excepcao_dia_semana and not excepcao_turno_vespertino:
                if not turno_vespertino:  # Se não tiver alocação fixa
                    disponiveis_vespertino.append(funcionario)
        
        # Se considerar carga de trabalho, ordenar funcionários pelo menor número de turnos alocados
        if considerar_carga:
            disponiveis_matutino.sort(key=lambda f: carga_trabalho[f])
            disponiveis_vespertino.sort(key=lambda f: carga_trabalho[f])
        
        # Alocar funcionários aos turnos que ainda não foram alocados fixamente
        if not turno_matutino and disponiveis_matutino:
            turno_matutino = disponiveis_matutino[0]
        
        # Atualizar carga se alocou alguém
        if turno_matutino:
            carga_trabalho[turno_matutino] += 1
            
            # Tentar não alocar o mesmo funcionário para os dois turnos do mesmo dia
            if turno_matutino in disponiveis_vespertino and len(disponiveis_vespertino) > 1 and not turno_vespertino:
                disponiveis_vespertino.remove(turno_matutino)
        
        # Alocar para o turno vespertino se ainda não foi alocado fixamente
        if not turno_vespertino and disponiveis_vespertino:
            turno_vespertino = disponiveis_vespertino[0]
            if turno_vespertino:
                carga_trabalho[turno_vespertino] += 1
        
        escala.append({
            "Data": f"{dia:02d}/{mes:02d}/{ano}",
            "Dia da Semana": dia_semana,
            "Turno Matutino": turno_matutino,
            "Turno Vespertino": turno_vespertino
        })
    
    df = pd.DataFrame(escala)
    
    # Adicionar estatísticas de carga de trabalho
    estatisticas = pd.DataFrame({
        "Funcionário": list(carga_trabalho.keys()),
        "Total de Turnos": list(carga_trabalho.values())
    })
    
    return df, estatisticas

# Interface do Streamlit
st.title("🗓️ Gerador de Escala de Trabalho")

# Criar layout com colunas principais
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Configurações")
    
    # Seleção do mês e ano
    mes = st.selectbox("Selecione o mês", list(range(1, 13)), 
                       index=datetime.today().month - 1, 
                       format_func=lambda x: calendar.month_name[x])
    ano = st.selectbox("Selecione o ano", 
                       list(range(datetime.today().year - 1, datetime.today().year + 5)))
    
    # Opções adicionais
    st.subheader("Opções")
    equilibrar_carga = st.checkbox("Equilibrar carga de trabalho entre funcionários", value=True)
    
    # Inserção da lista de funcionários
    st.subheader("Funcionários")
    funcionarios_input = st.text_area("Digite os nomes dos funcionários (um por linha)")
    funcionarios = [f.strip() for f in funcionarios_input.split("\n") if f.strip()]
    
    # Mostrar número de funcionários e dias úteis
    if funcionarios:
        dias_uteis = sum(1 for dia in range(1, calendar.monthrange(ano, mes)[1] + 1) 
                        if datetime(ano, mes, dia).weekday() < 5)
        st.info(f"Total de funcionários: {len(funcionarios)}")
        st.info(f"Dias úteis no mês: {dias_uteis}")
        st.info(f"Total de turnos a serem preenchidos: {dias_uteis * 2}")

with col2:
    # Inicialização das estruturas de exceções e alocações fixas
    excecoes = {
        'dias_especificos': {},  # Exceções para dias específicos
        'intervalos': {},        # Exceções para intervalos de dias
        'dias_semana': {},       # Exceções para dias da semana
        'turnos': {}             # Exceções para turnos específicos
    }
    
    alocacoes_fixas = {
        'dia_semana': {},       # Alocações fixas por dia da semana
        'dias_especificos': {}  # Alocações fixas para dias específicos
    }
    
    if funcionarios:
        # Tabs para separar exceções e alocações fixas
        tab_excecoes, tab_fixas = st.tabs(["Exceções", "Alocações Fixas"])
        
        with tab_excecoes:
            st.subheader("Configurar Exceções")
            
            for funcionario in funcionarios:
                with st.expander(f"Exceções para {funcionario}"):
                    st.write(f"**{funcionario}**")
                    
                    # Exceções por dia da semana
                    st.write("Dias da semana que não pode trabalhar:")
                    dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
                    dias_semana_selecionados = []
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        if st.checkbox("Segunda", key=f"seg_{funcionario}"):
                            dias_semana_selecionados.append(0)
                    with col2:
                        if st.checkbox("Terça", key=f"ter_{funcionario}"):
                            dias_semana_selecionados.append(1)
                    with col3:
                        if st.checkbox("Quarta", key=f"qua_{funcionario}"):
                            dias_semana_selecionados.append(2)
                    with col4:
                        if st.checkbox("Quinta", key=f"qui_{funcionario}"):
                            dias_semana_selecionados.append(3)
                    with col5:
                        if st.checkbox("Sexta", key=f"sex_{funcionario}"):
                            dias_semana_selecionados.append(4)
                    
                    if dias_semana_selecionados:
                        excecoes['dias_semana'][funcionario] = dias_semana_selecionados
                    
                    st.divider()
                    
                    # Exceções por dias específicos
                    dias_especificos = st.text_input(
                        f"Dias específicos que não pode trabalhar (ex: 1, 2, 15)",
                        key=f"dias_esp_{funcionario}"
                    )
                    
                    if dias_especificos:
                        try:
                            dias_list = [int(d.strip()) for d in dias_especificos.split(",") if d.strip().isdigit()]
                            for dia in dias_list:
                                excecoes['dias_especificos'][(dia, funcionario)] = True
                        except ValueError:
                            st.error(f"Formato inválido para os dias de {funcionario}")
                    
                    st.divider()
                    
                    # Exceções por intervalo de dias
                    col_inicio, col_fim = st.columns(2)
                    with col_inicio:
                        inicio_intervalo = st.number_input(
                            "Início do intervalo",
                            min_value=1,
                            max_value=calendar.monthrange(ano, mes)[1],
                            value=1,
                            key=f"inicio_{funcionario}"
                        )
                    
                    with col_fim:
                        fim_intervalo = st.number_input(
                            "Fim do intervalo",
                            min_value=1,
                            max_value=calendar.monthrange(ano, mes)[1],
                            value=calendar.monthrange(ano, mes)[1],
                            key=f"fim_{funcionario}"
                        )
                    
                    if st.checkbox(f"Não pode trabalhar do dia {inicio_intervalo} ao {fim_intervalo}", key=f"intervalo_{funcionario}"):
                        if funcionario not in excecoes['intervalos']:
                            excecoes['intervalos'][funcionario] = []
                        excecoes['intervalos'][funcionario].append((inicio_intervalo, fim_intervalo))
                    
                    st.divider()
                    
                    # Exceções por turno
                    turnos_excecoes = st.multiselect(
                        f"Turnos que não pode trabalhar",
                        ["Matutino", "Vespertino"],
                        key=f"turno_{funcionario}"
                    )
                    
                    if turnos_excecoes and dias_especificos:
                        for dia in dias_list:
                            for turno in turnos_excecoes:
                                excecoes['turnos'].setdefault((dia, turno), []).append(funcionario)
        
        with tab_fixas:
            st.subheader("Configurar Alocações Fixas")
            
            for funcionario in funcionarios:
                with st.expander(f"Alocações fixas para {funcionario}"):
                    st.write(f"**{funcionario}**")
                    
                    # Alocações fixas por dia da semana
                    st.write("Dias da semana com alocação fixa:")
                    dias_semana_fixos = []
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        if st.checkbox("Segunda", key=f"seg_fixo_{funcionario}"):
                            dias_semana_fixos.append(0)
                    with col2:
                        if st.checkbox("Terça", key=f"ter_fixo_{funcionario}"):
                            dias_semana_fixos.append(1)
                    with col3:
                        if st.checkbox("Quarta", key=f"qua_fixo_{funcionario}"):
                            dias_semana_fixos.append(2)
                    with col4:
                        if st.checkbox("Quinta", key=f"qui_fixo_{funcionario}"):
                            dias_semana_fixos.append(3)
                    with col5:
                        if st.checkbox("Sexta", key=f"sex_fixo_{funcionario}"):
                            dias_semana_fixos.append(4)
                    
                    # Alocações fixas por turno
                    st.write("Turnos com alocação fixa:")
                    turnos_fixos = []
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.checkbox("Matutino", key=f"mat_fixo_{funcionario}"):
                            turnos_fixos.append("Matutino")
                    with col2:
                        if st.checkbox("Vespertino", key=f"ves_fixo_{funcionario}"):
                            turnos_fixos.append("Vespertino")
                    
                    if dias_semana_fixos and turnos_fixos:
                        alocacoes_fixas['dia_semana'][funcionario] = {
                            'dias': dias_semana_fixos,
                            'turnos': turnos_fixos
                        }
                    
                    st.divider()
                    
                    # Alocações fixas por dias específicos
                    dias_fixos = st.text_input(
                        f"Dias específicos com alocação fixa (ex: 1, 2, 15)",
                        key=f"dias_fixos_{funcionario}"
                    )
                    
                    # Turnos fixos para dias específicos
                    turnos_dias_fixos = st.multiselect(
                        f"Turnos fixos para os dias especificados",
                        ["Matutino", "Vespertino"],
                        key=f"turnos_dias_fixos_{funcionario}"
                    )
                    
                    if dias_fixos and turnos_dias_fixos:
                        try:
                            dias_fixos_list = [int(d.strip()) for d in dias_fixos.split(",") if d.strip().isdigit()]
                            alocacoes_fixas['dias_especificos'][funcionario] = {
                                'dias': dias_fixos_list,
                                'turnos': turnos_dias_fixos
                            }
                        except ValueError:
                            st.error(f"Formato inválido para os dias fixos de {funcionario}")

    # Botão para gerar escala
    if st.button("Gerar Escala", type="primary"):
        if not funcionarios:
            st.warning("Por favor, insira pelo menos um funcionário.")
        else:
            with st.spinner("Gerando escala..."):
                escala_df, estatisticas_df = gerar_escala(mes, ano, funcionarios, excecoes, alocacoes_fixas, equilibrar_carga)
                
                # Mostrar resultados em tabs
                tab1, tab2, tab3 = st.tabs(["Escala", "Estatísticas", "Visualização"])
                
                with tab1:
                    st.dataframe(escala_df, use_container_width=True)
                    
                    # Opção de download de CSV
                    csv = escala_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📄 Baixar como CSV",
                        data=csv,
                        file_name=f"escala_{mes}_{ano}.csv",
                        mime="text/csv"
                    )
                
                with tab2:
                    st.subheader("Distribuição de turnos por funcionário")
                    st.dataframe(estatisticas_df, use_container_width=True)
                    
                    # Gráfico de barras para visualizar distribuição de turnos
                    chart = alt.Chart(estatisticas_df).mark_bar().encode(
                        x=alt.X('Funcionário', sort='-y'),
                        y=alt.Y('Total de Turnos'),
                        color=alt.Color('Funcionário', legend=None)
                    ).properties(
                        height=300
                    )
                    st.altair_chart(chart, use_container_width=True)
                
                with tab3:
                    st.subheader("Visualização da Escala")
                    
                    # Preparar dados para visualização do calendário
                    cal_data = []
                    for i, row in escala_df.iterrows():
                        data = row['Data']
                        dia = int(data.split('/')[0])
                        cal_data.append({
                            'Dia': dia,
                            'Turno': 'Matutino',
                            'Funcionário': row['Turno Matutino'] or '-'
                        })
                        cal_data.append({
                            'Dia': dia,
                            'Turno': 'Vespertino',
                            'Funcionário': row['Turno Vespertino'] or '-'
                        })
                    
                    cal_df = pd.DataFrame(cal_data)
                    
                    # Criar um heatmap da escala
                    heatmap = alt.Chart(cal_df).mark_rect().encode(
                        x=alt.X('Dia:O', title='Dia do Mês'),
                        y=alt.Y('Turno:N', title=None),
                        color=alt.Color('Funcionário:N', legend=alt.Legend(orient='bottom')),
                        tooltip=['Dia', 'Turno', 'Funcionário']
                    ).properties(
                        title=f"Escala de {calendar.month_name[mes]} de {ano}",
                        width=600
                    )
                    
                    # Adicionar rótulos
                    text = alt.Chart(cal_df).mark_text().encode(
                        x=alt.X('Dia:O'),
                        y=alt.Y('Turno:N'),
                        text='Funcionário',
                        color=alt.condition(
                            alt.datum.Funcionário == '-',
                            alt.value('red'),
                            alt.value('white')
                        )
                    )
                    
                    st.altair_chart(heatmap + text, use_container_width=True)
                    
                    # Adicionar legenda de turnos
                    st.info("**Matutino**: Turno da manhã | **Vespertino**: Turno da tarde")
