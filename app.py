import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# Função para gerar a escala
def gerar_escala(mes, ano, funcionarios):
    dias_uteis = []
    
    # Identificar os dias úteis do mês
    for dia in range(1, calendar.monthrange(ano, mes)[1] + 1):
        if datetime(ano, mes, dia).weekday() < 5:  # Segunda (0) a Sexta (4)
            dias_uteis.append(dia)
    
    escala = []
    turno = ["Matutino", "Vespertino"]
    
    i = 0  # Índice para alternar os funcionários
    for idx, dia in enumerate(dias_uteis):
        escala.append({
            "Data": f"{dia}/{mes}/{ano}",
            "Turno": turno[idx % 2],
            "Funcionário": funcionarios[i % len(funcionarios)]
        })
        i += 1
    
    return pd.DataFrame(escala)

# Interface do Streamlit
st.title("Gerador de Escala de Trabalho")

# Seleção do mês e ano
mes = st.selectbox("Selecione o mês", list(range(1, 13)), index=datetime.today().month - 1)
ano = st.selectbox("Selecione o ano", list(range(datetime.today().year, datetime.today().year + 5)))

# Inserção da lista de funcionários
funcionarios_input = st.text_area("Digite os nomes dos funcionários (um por linha)")
funcionarios = [f.strip() for f in funcionarios_input.split("\n") if f.strip()]

if st.button("Gerar Escala"):
    if not funcionarios:
        st.warning("Por favor, insira pelo menos um funcionário.")
    else:
        escala_df = gerar_escala(mes, ano, funcionarios)
        st.dataframe(escala_df)
        
        # Permitir download da escala
        csv = escala_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Baixar Escala como CSV",
            data=csv,
            file_name=f"escala_{mes}_{ano}.csv",
            mime="text/csv"
        )
