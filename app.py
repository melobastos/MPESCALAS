import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# Função para gerar a escala considerando exceções
def gerar_escala(mes, ano, funcionarios, excecoes):
    dias_uteis = []
    
    # Identificar os dias úteis do mês
    for dia in range(1, calendar.monthrange(ano, mes)[1] + 1):
        if datetime(ano, mes, dia).weekday() < 5:  # Segunda (0) a Sexta (4)
            dias_uteis.append(dia)
    
    escala = []
    
    i = 0  # Índice para alternar os funcionários
    for dia in dias_uteis:
        turno_matutino = None
        turno_vespertino = None
        
        # Encontrar funcionários disponíveis para cada turno
        disponiveis = [f for f in funcionarios if f not in excecoes.get((dia, "Matutino"), [])]
        if disponiveis:
            turno_matutino = disponiveis[i % len(disponiveis)]
            i += 1
        
        disponiveis = [f for f in funcionarios if f not in excecoes.get((dia, "Vespertino"), [])]
        if disponiveis:
            turno_vespertino = disponiveis[i % len(disponiveis)]
            i += 1
        
        escala.append({
            "Data": f"{dia}/{mes}/{ano}",
            "Turno Matutino": turno_matutino,
            "Turno Vespertino": turno_vespertino
        })
    
    return pd.DataFrame(escala)

# Interface do Streamlit
st.title("Gerador de Escala de Trabalho")

# Seleção do mês e ano
mes = st.selectbox("Selecione o mês", list(range(1, 13)), index=datetime.today().month - 1)
ano = st.selectbox("Selecione o ano", list(range(datetime.today().year, datetime.today().year + 5)))

# Inserção da lista de funcionários
funcionarios_input = st.text_area("Digite os nomes dos funcionários (um por linha)")
funcionarios = [f.strip() for f in funcionarios_input.split("\n") if f.strip()]

# Inserção de exceções
st.subheader("Exceções")
excecoes = {}
if funcionarios:
    for funcionario in funcionarios:
        st.write(f"Exceções para {funcionario}:")
        datas_excecoes = st.text_input(f"Digite as datas que {funcionario} não pode trabalhar (formato: dia, separado por vírgula)", key=f"data_{funcionario}")
        turnos_excecoes = st.multiselect(f"Turnos que {funcionario} não pode trabalhar", ["Matutino", "Vespertino"], key=f"turno_{funcionario}")
        
        if datas_excecoes:
            datas_excecoes = [int(d.strip()) for d in datas_excecoes.split(",") if d.strip().isdigit()]
            for data in datas_excecoes:
                for turno in turnos_excecoes:
                    excecoes.setdefault((data, turno), []).append(funcionario)

if st.button("Gerar Escala"):
    if not funcionarios:
        st.warning("Por favor, insira pelo menos um funcionário.")
    else:
        escala_df = gerar_escala(mes, ano, funcionarios, excecoes)
        st.dataframe(escala_df)
        
        # Permitir download da escala
        csv = escala_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Baixar Escala como CSV",
            data=csv,
            file_name=f"escala_{mes}_{ano}.csv",
            mime="text/csv"
        )
