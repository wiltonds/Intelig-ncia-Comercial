# ============================================================
# DASHBOARD DE INTELIGÊNCIA COMERCIAL
# SESI + SENAI + SEBRAE | ALAGOAS
# ============================================================

import streamlit as st
import pandas as pd
import re
from pathlib import Path

try:
    import motor_aderencia
except ImportError:
    motor_aderencia = None


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Inteligência Comercial | SESI + SENAI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_MESTRE = BASE_DIR / "saida" / "BASE_MESTRE_COMERCIAL.csv"
ARQUIVO_AUDITORIA_RECEITA = BASE_DIR / "saida" / "AUDITORIA_RECEITA_GAP_INDUSTRIA.csv"
ARQUIVO_CORRECAO_UNIVERSO = BASE_DIR / "CORRECAO_UNIVERSO_CONFIRMADA.csv"

# ============================================================
# ESTILO CSS
# ============================================================

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .kpi {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        background: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        min-height: 110px;
    }
    .kpi-title { font-size: 13px; color: #666666; margin-bottom: 6px; font-weight: 600; }
    .kpi-value { font-size: 26px; font-weight: 700; color: #111111; }
    .kpi-sub { font-size: 12px; color: #888888; margin-top: 4px; }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FUNÇÕES DE TRATAMENTO DE DADOS (ROBUSTAS)
# ============================================================

def normalizar_cnpj(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    if texto.endswith(".0"):
        texto = texto[:-2]
    texto = "".join(c for c in texto if c.isdigit())
    return texto.zfill(14) if texto else ""

def converter_para_booleano(df, col_tem):
    """
    Verifica se a empresa é cliente SESI/SENAI com base na coluna
    TEM_SESI / TEM_SENAI ('True', 'SIM', '1', etc), calculada e validada
    no pipeline (construir_base_mestre.py) a partir da base oficial de
    relacionamento.

    Não usa as colunas brutas "SESI"/"SENAI" de industrias_ativas.xlsx —
    elas guardam números de CNPJ de um cruzamento antigo, não um flag de
    relacionamento, e usá-las como sinal infla a contagem incorretamente.
    """
    if col_tem not in df.columns:
        return pd.Series(False, index=df.index)

    val = df[col_tem].fillna("").astype(str).str.strip().str.upper()
    return val.isin(["TRUE", "1", "SIM", "S", "VERDADEIRO", "T", "YES"])

def numero(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except Exception:
        return "0"

def percentual(valor):
    try:
        return f"{float(valor):.2f}%".replace(".", ",")
    except Exception:
        return "0,00%"

def kpi(titulo, valor, subtitulo=""):
    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-title">{titulo}</div>
            <div class="kpi-value">{valor}</div>
            <div class="kpi-sub">{subtitulo}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# CARREGAMENTO DOS DADOS REAL
# ============================================================

@st.cache_data
def carregar_base():
    if not ARQUIVO_MESTRE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_MESTRE}")

    try:
        df = pd.read_csv(ARQUIVO_MESTRE, encoding="utf-8-sig", low_memory=False, dtype=str)
    except UnicodeDecodeError:
        df = pd.read_csv(ARQUIVO_MESTRE, encoding="latin1", low_memory=False, dtype=str)

    # Padronizar CNPJ
    if "cnpj" in df.columns:
        df["cnpj"] = df["cnpj"].apply(normalizar_cnpj)

    # Identificação REAL do relacionamento SESI e SENAI
    df["POSSUI_SESI"] = converter_para_booleano(df, "TEM_SESI")
    df["POSSUI_SENAI"] = converter_para_booleano(df, "TEM_SENAI")
    df["POSSUI_SESI_SENAI"] = df["POSSUI_SESI"] & df["POSSUI_SENAI"]

    # SEBRAE: elegibilidade real vem de STATUS_SEBRAE (ver mais abaixo);
    # aqui só sinaliza se a empresa já tem QUALQUER dado do SEBRAE.
    colunas_sebrae = [c for c in df.columns if c.startswith("SEBRAE_")]
    if colunas_sebrae:
        df["POSSUI_SEBRAE"] = df[colunas_sebrae].notna().any(axis=1) & (
            df[colunas_sebrae].apply(lambda s: s.astype(str).str.strip().str.upper()) .ne("").any(axis=1)
        )
    else:
        df["POSSUI_SEBRAE"] = False

    # Status textual de relacionamento (pra Visão Integrada / Auditoria)
    df["STATUS_RELACIONAMENTO_REAL"] = "Sem relacionamento"
    df.loc[df["POSSUI_SESI"] & ~df["POSSUI_SENAI"], "STATUS_RELACIONAMENTO_REAL"] = "Somente SESI"
    df.loc[~df["POSSUI_SESI"] & df["POSSUI_SENAI"], "STATUS_RELACIONAMENTO_REAL"] = "Somente SENAI"
    df.loc[df["POSSUI_SESI_SENAI"], "STATUS_RELACIONAMENTO_REAL"] = "SESI + SENAI"

    if "STATUS_SEBRAE" in df.columns:
        df["STATUS_SEBRAE"] = df["STATUS_SEBRAE"].fillna("SEM INFORMAÇÃO").replace("", "SEM INFORMAÇÃO")
    else:
        df["STATUS_SEBRAE"] = "SEM INFORMAÇÃO"

    # Preenchimento de Nulos
    if "Municipio" in df.columns:
        df["Municipio"] = df["Municipio"].fillna("NÃO INFORMADO")
    if "Porte" in df.columns:
        df["Porte"] = df["Porte"].fillna("NÃO INFORMADO")
    if "razao_social" in df.columns:
        df["razao_social"] = df["razao_social"].fillna("SEM RAZÃO SOCIAL")
    if "CNAE PRIMARIO" in df.columns:
        df["CNAE PRIMARIO"] = df["CNAE PRIMARIO"].fillna("NÃO INFORMADO")

    return df


@st.cache_data
def carregar_auditoria_cobertura():
    if not ARQUIVO_AUDITORIA_RECEITA.exists():
        return None

    auditoria = pd.read_csv(ARQUIVO_AUDITORIA_RECEITA, encoding="utf-8-sig")

    auditoria["divisao_cnae"] = (
        pd.to_numeric(auditoria["cnae_fiscal_codigo"], errors="coerce")
        .fillna(0).astype(int).astype(str).str.zfill(7).str[:2].astype(int)
    )
    auditoria["e_industria_hoje"] = auditoria["divisao_cnae"].between(10, 33)

    def classificar(linha):
        if linha["situacao_cadastral"] != "ATIVA":
            return "Baixada / inapta / suspensa"
        if linha["uf_receita"] != "AL":
            return "Ativa, mas fora de Alagoas"
        if not linha["e_industria_hoje"]:
            return "Ativa em AL, mudou de atividade"
        return "Confirmada e incluída no universo"

    auditoria["MOTIVO"] = auditoria.apply(classificar, axis=1)

    correcao = None
    if ARQUIVO_CORRECAO_UNIVERSO.exists():
        correcao = pd.read_csv(ARQUIVO_CORRECAO_UNIVERSO, encoding="utf-8-sig")

    return auditoria, correcao


try:
    df = carregar_base()
except Exception as erro:
    st.error("❌ Erro ao carregar o arquivo CSV Mestre.")
    st.code(str(erro))
    st.stop()


# ============================================================
# BARRA LATERAL - FILTROS & NAVEGAÇÃO
# ============================================================

st.sidebar.title("Navegação")
pagina = st.sidebar.radio(
    "Visões Disponíveis",
    [
        "📊 Visão Geral",
        "🏭 Mercado",
        "🔵 Visão SESI",
        "🟠 Visão SENAI",
        "🟢 Visão SEBRAE",
        "🔥 Visão Integrada",
        "🔄 Matriz Cross-sell",
        "🔎 Explorador de Empresas",
        "🩺 Diagnóstico por Empresa",
        "✅ Auditoria de Cobertura"
    ]
)

st.sidebar.divider()
st.sidebar.subheader("Filtros Globais")

# Filtro Município
municipios = sorted([m for m in df["Municipio"].unique() if m and m != "NÃO INFORMADO"])
municipio_filtro = st.sidebar.multiselect("Município", municipios)

# Filtro Porte
portes = sorted([p for p in df["Porte"].unique() if p and p != "NÃO INFORMADO"])
porte_filtro = st.sidebar.multiselect("Porte", portes)

# Aplicação dos Filtros
df_view = df.copy()
if municipio_filtro:
    df_view = df_view[df_view["Municipio"].isin(municipio_filtro)]
if porte_filtro:
    df_view = df_view[df_view["Porte"].isin(porte_filtro)]

# Totais das Métricas
mercado = len(df_view)
sesi = int(df_view["POSSUI_SESI"].sum())
senai = int(df_view["POSSUI_SENAI"].sum())
sebrae = int(df_view["POSSUI_SEBRAE"].sum())
ambos_sesi_senai = int(df_view["POSSUI_SESI_SENAI"].sum())
clientes_totais = int((df_view["POSSUI_SESI"] | df_view["POSSUI_SENAI"]).sum())
prospects = mercado - clientes_totais


# ============================================================
# CONTEÚDO PRINCIPAL
# ============================================================

st.title("📊 Inteligência Comercial - SESI | SENAI")
st.caption("Ecossistema de Negócios e Diagnóstico do Mercado Industrial de Alagoas")
st.divider()

# ------------------------------------------------------------
# 1. VISÃO GERAL
# ------------------------------------------------------------
if pagina == "📊 Visão Geral":
    st.header("Visão Geral do Mercado")
    
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi("Mercado Total", numero(mercado), "empresas")
    with c2: kpi("Clientes SESI", numero(sesi), percentual(sesi / mercado * 100) if mercado else "0%")
    with c3: kpi("Clientes SENAI", numero(senai), percentual(senai / mercado * 100) if mercado else "0%")
    with c4: kpi("SESI + SENAI", numero(ambos_sesi_senai), percentual(ambos_sesi_senai / mercado * 100) if mercado else "0%")
    with c5: kpi("Sem Relacionamento", numero(prospects), percentual(prospects / mercado * 100) if mercado else "0%")

    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribuição do Relacionamento Institucional")
        cobertura = pd.DataFrame({
            "Status": ["Somente SESI", "Somente SENAI", "SESI + SENAI", "Sem Relacionamento"],
            "Quantidade": [
                int((df_view["POSSUI_SESI"] & ~df_view["POSSUI_SENAI"]).sum()),
                int((df_view["POSSUI_SENAI"] & ~df_view["POSSUI_SESI"]).sum()),
                ambos_sesi_senai,
                prospects
            ]
        })
        st.bar_chart(cobertura.set_index("Status"))

    with col2:
        st.subheader("Distribuição por Porte")
        st.bar_chart(df_view["Porte"].value_counts())


# ------------------------------------------------------------
# 1B. MERCADO
# ------------------------------------------------------------
elif pagina == "🏭 Mercado":
    st.header("🏭 Mercado Industrial")
    st.write("Universo de empresas utilizado como base-mãe para as análises comerciais.")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Empresas", numero(len(df_view)))
    with c2: kpi("Municípios", numero(df_view["Municipio"].nunique()))
    with c3: kpi("CNAEs", numero(df_view["CNAE PRIMARIO"].nunique()) if "CNAE PRIMARIO" in df_view.columns else "0")
    with c4: kpi("Relacionadas", numero(clientes_totais))

    st.divider()
    st.subheader("Distribuição por município")
    st.bar_chart(df_view["Municipio"].value_counts().head(30))

    if "CNAE PRIMARIO" in df_view.columns:
        st.subheader("Principais atividades econômicas")
        cnae = (
            df_view["CNAE PRIMARIO"].value_counts().head(30)
            .rename_axis("CNAE").to_frame("Empresas")
        )
        st.dataframe(cnae, use_container_width=True)


# ------------------------------------------------------------
# 2. VISÃO SESI
# ------------------------------------------------------------
elif pagina == "🔵 Visão SESI":
    st.header("🔵 Visão Estratégica SESI")
    sem_sesi = mercado - sesi
    
    c1, c2, c3 = st.columns(3)
    with c1: kpi("Clientes SESI", numero(sesi), "empresas ativas")
    with c2: kpi("Taxa de Penetração", percentual(sesi / mercado * 100) if mercado else "0%")
    with c3: kpi("Oportunidades (Sem SESI)", numero(sem_sesi), "empresas a prospectar")

    st.divider()
    st.subheader("Base de Empresas sem SESI")
    cols = [c for c in ["cnpj", "razao_social", "Municipio", "Porte", "CNAE PRIMARIO"] if c in df_view.columns]
    st.dataframe(df_view[~df_view["POSSUI_SESI"]][cols].head(1000), use_container_width=True, hide_index=True)


# ------------------------------------------------------------
# 3. VISÃO SENAI
# ------------------------------------------------------------
elif pagina == "🟠 Visão SENAI":
    st.header("🟠 Visão Estratégica SENAI")
    sem_senai = mercado - senai
    
    c1, c2, c3 = st.columns(3)
    with c1: kpi("Clientes SENAI", numero(senai), "empresas ativas")
    with c2: kpi("Taxa de Penetração", percentual(senai / mercado * 100) if mercado else "0%")
    with c3: kpi("Oportunidades (Sem SENAI)", numero(sem_senai), "empresas a prospectar")

    st.divider()
    st.subheader("Base de Empresas sem SENAI")
    cols = [c for c in ["cnpj", "razao_social", "Municipio", "Porte", "CNAE PRIMARIO"] if c in df_view.columns]
    st.dataframe(df_view[~df_view["POSSUI_SENAI"]][cols].head(1000), use_container_width=True, hide_index=True)


# ------------------------------------------------------------
# 4. VISÃO SEBRAE
# ------------------------------------------------------------
elif pagina == "🟢 Visão SEBRAE":
    st.header("🟢 Visão Estratégica SEBRAE")
    st.caption("Inteligência de mercado do SEBRAE dentro do universo industrial de Alagoas.")

    distribuicao = df_view["STATUS_SEBRAE"].value_counts()
    nao_atendida = int(distribuicao.get("NÃO ATENDIDA", 0))
    fora_escopo = int(distribuicao.get("FORA DO ESCOPO SEBRAE", 0))
    sem_info = int(distribuicao.get("SEM INFORMAÇÃO", 0))

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Mercado", numero(mercado), "empresas")
    with c2: kpi("Não atendidas", numero(nao_atendida), "oportunidade SEBRAE")
    with c3: kpi("Fora do escopo", numero(fora_escopo), "não elegíveis")
    with c4: kpi("% não atendidas", percentual(nao_atendida / mercado * 100) if mercado else "0%", "do mercado")

    st.divider()
    st.subheader("Situação SEBRAE")
    st.bar_chart(distribuicao)

    st.divider()
    st.subheader("Empresas classificadas como NÃO ATENDIDA")
    df_oportunidade = df_view[df_view["STATUS_SEBRAE"] == "NÃO ATENDIDA"]
    cols = [c for c in ["cnpj", "razao_social", "Municipio", "Porte", "CNAE PRIMARIO", "POSSUI_SESI", "POSSUI_SENAI"] if c in df_oportunidade.columns]
    st.dataframe(df_oportunidade[cols].head(3000), use_container_width=True, hide_index=True)


# ------------------------------------------------------------
# 4B. VISÃO INTEGRADA
# ------------------------------------------------------------
elif pagina == "🔥 Visão Integrada":
    st.header("🔥 Visão Integrada")
    st.caption("Uma mesma empresa observada pelas três perspectivas: SESI, SENAI e SEBRAE.")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("SESI", numero(sesi))
    with c2: kpi("SENAI", numero(senai))
    with c3: kpi("SESI + SENAI", numero(ambos_sesi_senai))
    with c4: kpi("Sem SESI/SENAI", numero(prospects))

    st.divider()
    st.subheader("Cobertura SESI/SENAI")
    st.bar_chart(df_view["STATUS_RELACIONAMENTO_REAL"].value_counts())

    st.divider()
    st.subheader("SESI/SENAI × SEBRAE")
    cruzamento = pd.crosstab(df_view["STATUS_RELACIONAMENTO_REAL"], df_view["STATUS_SEBRAE"])
    st.dataframe(cruzamento, use_container_width=True)

    st.divider()
    st.subheader("Sem SESI/SENAI e não atendidas pelo SEBRAE")
    oportunidade_integrada = df_view[
        (df_view["STATUS_RELACIONAMENTO_REAL"] == "Sem relacionamento")
        & (df_view["STATUS_SEBRAE"] == "NÃO ATENDIDA")
    ]
    st.metric("Empresas nesse grupo", numero(len(oportunidade_integrada)))
    cols = [c for c in ["cnpj", "razao_social", "Municipio", "Porte", "CNAE PRIMARIO", "STATUS_SEBRAE"] if c in oportunidade_integrada.columns]
    st.dataframe(oportunidade_integrada[cols].head(3000), use_container_width=True, hide_index=True)
    st.caption("Importante: este grupo representa uma lacuna de cobertura institucional. Não significa, por si só, propensão de compra.")


# ------------------------------------------------------------
# 5. CROSS-SELL
# ------------------------------------------------------------
elif pagina == "🔄 Matriz Cross-sell":
    st.header("🔄 Matriz de Oportunidades Cross-sell")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Clientes SESI sem SENAI")
        sesi_sem_senai = df_view[df_view["POSSUI_SESI"] & ~df_view["POSSUI_SENAI"]]
        st.metric("Oportunidades para Oferta SENAI", len(sesi_sem_senai))
        cols = [c for c in ["cnpj", "razao_social", "Municipio", "Porte"] if c in sesi_sem_senai.columns]
        st.dataframe(sesi_sem_senai[cols].head(500), use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Clientes SENAI sem SESI")
        senai_sem_sesi = df_view[df_view["POSSUI_SENAI"] & ~df_view["POSSUI_SESI"]]
        st.metric("Oportunidades para Oferta SESI", len(senai_sem_sesi))
        cols = [c for c in ["cnpj", "razao_social", "Municipio", "Porte"] if c in senai_sem_sesi.columns]
        st.dataframe(senai_sem_sesi[cols].head(500), use_container_width=True, hide_index=True)


# ------------------------------------------------------------
# 5B. EXPLORADOR DE EMPRESAS
# ------------------------------------------------------------
elif pagina == "🔎 Explorador de Empresas":
    st.header("🔎 Explorador de Empresas")
    st.caption(f"{numero(len(df_view))} empresas no contexto atual.")

    busca = st.text_input(
        "Pesquisar por CNPJ ou razão social",
        placeholder="Digite parte do CNPJ ou nome da empresa"
    )

    resultado = df_view.copy()
    if busca:
        busca = busca.strip()
        mascara = pd.Series(False, index=resultado.index)
        if "cnpj" in resultado.columns:
            mascara |= resultado["cnpj"].astype(str).str.contains(busca, case=False, na=False, regex=False)
        if "razao_social" in resultado.columns:
            mascara |= resultado["razao_social"].astype(str).str.contains(busca, case=False, na=False, regex=False)
        resultado = resultado[mascara]

    st.metric("Empresas encontradas", numero(len(resultado)))

    tabela = resultado.copy()
    tabela["Possui SESI"] = tabela["POSSUI_SESI"].map({True: "SIM", False: "NÃO"})
    tabela["Possui SENAI"] = tabela["POSSUI_SENAI"].map({True: "SIM", False: "NÃO"})
    tabela["Possui SESI + SENAI"] = tabela["POSSUI_SESI_SENAI"].map({True: "SIM", False: "NÃO"})
    tabela["Status Relacionamento"] = tabela["STATUS_RELACIONAMENTO_REAL"]
    tabela["Status SEBRAE"] = tabela["STATUS_SEBRAE"]

    colunas_finais = [
        c for c in [
            "cnpj", "razao_social", "Municipio", "Porte", "CNAE PRIMARIO",
            "Possui SESI", "Possui SENAI", "Possui SESI + SENAI",
            "Status Relacionamento", "Status SEBRAE"
        ] if c in tabela.columns
    ]
    tabela_final = tabela[colunas_finais]

    st.dataframe(tabela_final, use_container_width=True, height=600, hide_index=True)

    st.download_button(
        "⬇️ Baixar resultado",
        data=tabela_final.to_csv(index=False, encoding="utf-8-sig"),
        file_name="empresas_filtradas.csv",
        mime="text/csv"
    )


# ------------------------------------------------------------
# 6. DIAGNÓSTICO POR EMPRESA
# ------------------------------------------------------------
elif pagina == "🩺 Diagnóstico por Empresa":
    st.header("🔎 Diagnóstico Detalhado & Recomendador de Portfólio")

    opcoes = df_view["razao_social"].dropna().unique()
    empresa_selecionada = st.selectbox("Selecione a Empresa para Diagnóstico:", options=sorted(opcoes))

    if empresa_selecionada:
        dados = df_view[df_view["razao_social"] == empresa_selecionada].iloc[0]

        st.markdown("---")
        st.subheader(f"🏢 {dados.get('razao_social', 'Empresa')}")

        c1, c2, c3, c4 = st.columns(4)
        c1.write(f"**CNPJ:** {dados.get('cnpj', 'N/D')}")
        c2.write(f"**Município:** {dados.get('Municipio', 'N/D')}")
        c3.write(f"**Porte:** {dados.get('Porte', 'N/D')}")
        c4.write(f"**CNAE Primário:** {dados.get('CNAE PRIMARIO', 'N/D')}")

        st.markdown("---")
        st.subheader("🎯 Diagnóstico do Motor de Aderência Real")

        cnae_bruto = str(dados.get("CNAE PRIMARIO", ""))
        cnae_numeros = "".join(filter(str.isdigit, cnae_bruto))
        cnae_code = cnae_numeros if cnae_numeros else cnae_bruto

        porte = str(dados.get("Porte", ""))
        ja_sesi = bool(dados.get("POSSUI_SESI", False))
        ja_senai = bool(dados.get("POSSUI_SENAI", False))

        # Execução Direta do Motor de Aderência sem simulação ou atalhos
        if motor_aderencia and hasattr(motor_aderencia, "diagnosticar"):
            try:
                res = motor_aderencia.diagnosticar(
                    cnae_code=cnae_code,
                    porte=porte,
                    ja_sesi=ja_sesi,
                    ja_senai=ja_senai
                )
                
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric(
                        "Estratégia Recomendada",
                        res.get("rota_comercial", "N/D"),
                        help=res.get("rota_detalhe", "")
                    )
                with m2:
                    st.metric(
                        "Aderência Máxima",
                        f"{res.get('aderencia_maxima', 0)}%",
                        help=res.get("principal_area", "")
                    )
                with m3:
                    st.metric(
                        "Potencial Cross-Sell",
                        res.get("cross_sell", "N/D"),
                        help=res.get("cross_sell_detalhe", "")
                    )

                st.write("### Áreas do Portfólio Ranqueadas")
                areas = res.get("areas_ranqueadas")
                if isinstance(areas, pd.DataFrame) and not areas.empty:
                    st.dataframe(areas, use_container_width=True, hide_index=True)
                elif isinstance(areas, list) and len(areas) > 0:
                    st.write(areas)
                else:
                    st.info("Nenhuma área ranqueada para este CNAE/Porte no motor.")

            except Exception as err:
                st.error(f"⚠️ Erro ao executar o motor_aderencia.diagnosticar(): {err}")
        else:
            st.warning("⚠️ Módulo 'motor_aderencia.py' não encontrado na pasta raiz.")


# ------------------------------------------------------------
# 7. AUDITORIA DE COBERTURA
# ------------------------------------------------------------
elif pagina == "✅ Auditoria de Cobertura":
    st.header("✅ Auditoria de Cobertura SESI/SENAI")
    st.caption(
        "Por que o número de clientes SESI/SENAI no dashboard não é igual "
        "ao total bruto do cadastro de relacionamento — e por que agora "
        "dá para confiar nele."
    )

    resultado_auditoria = carregar_auditoria_cobertura()
    if resultado_auditoria is None:
        st.info("Auditoria ainda não foi gerada para esta base.")
        st.stop()

    auditoria, correcao = resultado_auditoria
    total_bruto = len(auditoria)
    total_confirmado = auditoria["MOTIVO"].eq("Confirmada e incluída no universo").sum()

    st.markdown(
        "O cadastro de relacionamento do SESI/SENAI aponta um total de "
        "empresas maior do que o que aparece no mercado industrial de "
        "Alagoas. Auditamos **cada uma** dessas empresas direto na "
        "Receita Federal para separar o que é exclusão correta do que é "
        "lacuna real de cobertura."
    )
    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Empresas auditadas", numero(total_bruto), "cadastradas como indústria, fora do mercado")
    with c2:
        kpi(
            "Fora de Alagoas / baixadas",
            numero(auditoria["MOTIVO"].isin(["Ativa, mas fora de Alagoas", "Baixada / inapta / suspensa"]).sum()),
            "exclusão correta, confirmada"
        )
    with c3:
        kpi(
            "Mudou de atividade",
            numero(auditoria["MOTIVO"].eq("Ativa em AL, mudou de atividade").sum()),
            "não é mais indústria hoje"
        )
    with c4:
        kpi("Gap real confirmado", numero(total_confirmado), "recuperadas para o universo")

    st.divider()
    st.subheader("Como se explica a diferença")
    st.bar_chart(auditoria["MOTIVO"].value_counts())
    st.caption(
        "Cada empresa foi checada individualmente na Receita Federal: "
        "situação cadastral, município/UF de registro e CNAE em vigor."
    )

    st.divider()
    st.subheader("Impacto por carteira")
    impacto = auditoria.groupby(["COBERTURA", "MOTIVO"]).size().unstack(fill_value=0)
    st.dataframe(impacto, use_container_width=True)

    st.divider()
    st.subheader("Empresas recuperadas para o seu radar comercial")
    st.caption(
        "Já são clientes SESI e/ou SENAI, estão ativas em Alagoas com "
        "CNAE de indústria — agora aparecem nas demais páginas do dashboard."
    )

    if correcao is not None and not correcao.empty:
        tabela_recuperadas = correcao[["razao_social", "Municipio", "Porte", "CNAE PRIMARIO"]].rename(
            columns={"razao_social": "Empresa", "Municipio": "Município", "CNAE PRIMARIO": "Atividade"}
        )
        st.dataframe(tabela_recuperadas, use_container_width=True, height=350, hide_index=True)
    else:
        st.info("Nenhuma empresa recuperada nesta versão da base.")

    st.caption(
        "Metodologia: cruzamento de CNPJ contra consulta pública de dados "
        "da Receita Federal (situação cadastral, município/UF e CNAE "
        "fiscal principal). Considerado indústria de transformação quando "
        "o CNAE em vigor está nas divisões 10 a 33."
    )