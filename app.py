# ============================================================
# DASHBOARD DE INTELIGÊNCIA COMERCIAL
# SESI + SENAI + SEBRAE | ALAGOAS
#
# V1 - VALIDAÇÃO + VISUALIZAÇÃO
# Sem IA / Sem Machine Learning
# ============================================================

import streamlit as st
import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Inteligência Comercial | SESI + SENAI + SEBRAE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CAMINHO DA BASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ARQUIVO_MESTRE = (
    BASE_DIR
    / "saida"
    / "BASE_MESTRE_COMERCIAL.csv"
)


# ============================================================
# ESTILO
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .kpi {
        border: 1px solid #dddddd;
        border-radius: 10px;
        padding: 16px;
        background: white;
        min-height: 110px;
    }

    .kpi-title {
        font-size: 13px;
        color: #666666;
        margin-bottom: 7px;
    }

    .kpi-value {
        font-size: 27px;
        font-weight: 700;
        color: #111111;
    }

    .kpi-sub {
        font-size: 12px;
        color: #777777;
        margin-top: 5px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================

def normalizar_cnpj(valor):

    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if texto.endswith(".0"):
        texto = texto[:-2]

    texto = "".join(
        caractere
        for caractere in texto
        if caractere.isdigit()
    )

    if not texto:
        return ""

    return texto.zfill(14)


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


def selecionar_colunas_existentes(df, colunas):

    return [
        coluna
        for coluna in colunas
        if coluna in df.columns
    ]


# ============================================================
# CARREGAMENTO DA BASE
# ============================================================

@st.cache_data
def carregar_base():

    # --------------------------------------------------------
    # VERIFICA ARQUIVO
    # --------------------------------------------------------

    if not ARQUIVO_MESTRE.exists():

        raise FileNotFoundError(
            f"""
Arquivo não encontrado:

{ARQUIVO_MESTRE}

Verifique se a Base Mestre está em:

saida/BASE_MESTRE_COMERCIAL.csv
"""
        )

    # --------------------------------------------------------
    # LEITURA
    # --------------------------------------------------------

    try:

        df = pd.read_csv(
            ARQUIVO_MESTRE,
            encoding="utf-8-sig",
            low_memory=False
        )

    except UnicodeDecodeError:

        df = pd.read_csv(
            ARQUIVO_MESTRE,
            encoding="latin1",
            low_memory=False
        )

    # --------------------------------------------------------
    # CNPJ
    # --------------------------------------------------------

    if "cnpj" in df.columns:

        df["cnpj"] = (
            df["cnpj"]
            .apply(normalizar_cnpj)
        )

    # --------------------------------------------------------
    # NORMALIZAÇÃO DE TEXTOS
    # --------------------------------------------------------

    colunas_texto = [
        "razao_social",
        "Municipio",
        "Porte",
        "CNAE PRIMARIO",
        "TEM_SESI",
        "TEM_SENAI",
        "TEM_SESI_SENAI",
        "STATUS_RELACIONAMENTO",
        "SEBRAE_OPORTUNIDADE",
        "SEBRAE_ELEGIVEL",
    ]

    for coluna in colunas_texto:

        if coluna in df.columns:

            df[coluna] = (
                df[coluna]
                .fillna("")
                .astype(str)
                .str.upper()
                .str.strip()
            )

    # ========================================================
    # RELACIONAMENTO SESI / SENAI
    #
    # A Base Mestre possui:
    #
    # TEM_SESI = TRUE / FALSE
    # TEM_SENAI = TRUE / FALSE
    #
    # Criamos flags próprias para o dashboard.
    # NÃO alteramos a Base Mestre.
    # ========================================================

    if "TEM_SESI" in df.columns:

        df["POSSUI_SESI"] = (
            df["TEM_SESI"]
            .astype(str)
            .str.strip()
            .str.upper()
            .eq("TRUE")
        )

    else:

        df["POSSUI_SESI"] = False


    if "TEM_SENAI" in df.columns:

        df["POSSUI_SENAI"] = (
            df["TEM_SENAI"]
            .astype(str)
            .str.strip()
            .str.upper()
            .eq("TRUE")
        )

    else:

        df["POSSUI_SENAI"] = False


    # --------------------------------------------------------
    # SESI + SENAI
    # --------------------------------------------------------

    df["POSSUI_SESI_SENAI"] = (
        df["POSSUI_SESI"]
        &
        df["POSSUI_SENAI"]
    )


    # --------------------------------------------------------
    # STATUS REAL DE RELACIONAMENTO
    # --------------------------------------------------------

    df["STATUS_RELACIONAMENTO_REAL"] = (
        "Sem relacionamento"
    )

    df.loc[
        df["POSSUI_SESI"] &
        ~df["POSSUI_SENAI"],
        "STATUS_RELACIONAMENTO_REAL"
    ] = "Somente SESI"

    df.loc[
        ~df["POSSUI_SESI"] &
        df["POSSUI_SENAI"],
        "STATUS_RELACIONAMENTO_REAL"
    ] = "Somente SENAI"

    df.loc[
        df["POSSUI_SESI_SENAI"],
        "STATUS_RELACIONAMENTO_REAL"
    ] = "SESI + SENAI"


    # ========================================================
    # STATUS SEBRAE
    # ========================================================

    if "SEBRAE_OPORTUNIDADE" in df.columns:

        df["STATUS_SEBRAE"] = (
            df["SEBRAE_OPORTUNIDADE"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        df.loc[
            df["STATUS_SEBRAE"] == "",
            "STATUS_SEBRAE"
        ] = "SEM INFORMAÇÃO"

    else:

        df["STATUS_SEBRAE"] = "SEM INFORMAÇÃO"


    # ========================================================
    # GARANTIA DE MUNICÍPIO / PORTE
    # ========================================================

    if "Municipio" in df.columns:

        df["Municipio"] = (
            df["Municipio"]
            .replace("", "NÃO INFORMADO")
        )

    if "Porte" in df.columns:

        df["Porte"] = (
            df["Porte"]
            .replace("", "NÃO INFORMADO")
        )


    return df


# ============================================================
# CARREGAMENTO DA AUDITORIA DE COBERTURA
# ============================================================

ARQUIVO_AUDITORIA_RECEITA = (
    BASE_DIR
    / "saida"
    / "AUDITORIA_RECEITA_GAP_INDUSTRIA.csv"
)

ARQUIVO_CORRECAO_UNIVERSO = (
    BASE_DIR
    / "CORRECAO_UNIVERSO_CONFIRMADA.csv"
)


@st.cache_data
def carregar_auditoria_cobertura():

    if not ARQUIVO_AUDITORIA_RECEITA.exists():
        return None

    auditoria = pd.read_csv(
        ARQUIVO_AUDITORIA_RECEITA,
        encoding="utf-8-sig"
    )

    auditoria["divisao_cnae"] = (
        pd.to_numeric(
            auditoria["cnae_fiscal_codigo"],
            errors="coerce"
        )
        .fillna(0)
        .astype(int)
        .astype(str)
        .str.zfill(7)
        .str[:2]
        .astype(int)
    )

    auditoria["e_industria_hoje"] = (
        auditoria["divisao_cnae"]
        .between(10, 33)
    )

    def classificar(linha):

        if linha["situacao_cadastral"] != "ATIVA":
            return "Baixada / inapta / suspensa"

        if linha["uf_receita"] != "AL":
            return "Ativa, mas fora de Alagoas"

        if not linha["e_industria_hoje"]:
            return "Ativa em AL, mudou de atividade"

        return "Confirmada e incluída no universo"

    auditoria["MOTIVO"] = auditoria.apply(
        classificar,
        axis=1
    )

    correcao = None

    if ARQUIVO_CORRECAO_UNIVERSO.exists():

        correcao = pd.read_csv(
            ARQUIVO_CORRECAO_UNIVERSO,
            encoding="utf-8-sig"
        )

    return auditoria, correcao


# ============================================================
# CARREGAR BASE
# ============================================================

try:

    df = carregar_base()

except Exception as erro:

    st.error("Erro ao carregar a Base Mestre.")

    st.code(str(erro))

    st.stop()


# ============================================================
# VALIDAÇÃO BÁSICA
# ============================================================

colunas_obrigatorias = [
    "cnpj",
    "razao_social",
    "Municipio",
    "Porte",
    "CNAE PRIMARIO",
    "POSSUI_SESI",
    "POSSUI_SENAI",
    "POSSUI_SESI_SENAI",
    "STATUS_RELACIONAMENTO_REAL",
    "STATUS_SEBRAE",
]

colunas_faltantes = [
    coluna
    for coluna in colunas_obrigatorias
    if coluna not in df.columns
]

if colunas_faltantes:

    st.error(
        "A Base Mestre não possui todas as colunas necessárias."
    )

    st.write("Colunas faltantes:")

    st.code(
        "\n".join(colunas_faltantes)
    )

    st.stop()


# ============================================================
# CABEÇALHO
# ============================================================

st.title("📊 Inteligência Comercial")

st.caption(
    "Mercado Industrial de Alagoas | "
    "SESI + SENAI + SEBRAE"
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Navegação")

pagina = st.sidebar.radio(
    "Visão",
    [
        "📊 Visão Geral",
        "🏭 Mercado",
        "🔵 SESI",
        "🟠 SENAI",
        "🟢 SEBRAE",
        "🔥 Visão Integrada",
        "🔄 Cross-sell",
        "🔎 Empresas",
        "✅ Auditoria de Cobertura"
    ]
)


# ============================================================
# FILTROS
# ============================================================

st.sidebar.divider()

st.sidebar.subheader("Filtros")


# ------------------------------------------------------------
# MUNICÍPIO
# ------------------------------------------------------------

municipios = sorted(
    df["Municipio"]
    .dropna()
    .astype(str)
    .unique()
)

municipio_filtro = st.sidebar.multiselect(
    "Município",
    municipios
)


# ------------------------------------------------------------
# PORTE
# ------------------------------------------------------------

portes = sorted(
    df["Porte"]
    .dropna()
    .astype(str)
    .unique()
)

porte_filtro = st.sidebar.multiselect(
    "Porte",
    portes
)


# ------------------------------------------------------------
# APLICA FILTROS
# ------------------------------------------------------------

df_view = df.copy()


if municipio_filtro:

    df_view = df_view[
        df_view["Municipio"].isin(
            municipio_filtro
        )
    ]


if porte_filtro:

    df_view = df_view[
        df_view["Porte"].isin(
            porte_filtro
        )
    ]


# ============================================================
# MÉTRICAS GERAIS
# ============================================================

mercado = len(df_view)

sesi = (
    df_view["POSSUI_SESI"]
    .sum()
)

senai = (
    df_view["POSSUI_SENAI"]
    .sum()
)

ambos = (
    df_view["POSSUI_SESI_SENAI"]
    .sum()
)

clientes = (
    df_view["POSSUI_SESI"]
    |
    df_view["POSSUI_SENAI"]
).sum()

sem_relacionamento = (
    ~(
        df_view["POSSUI_SESI"]
        |
        df_view["POSSUI_SENAI"]
    )
).sum()


# ============================================================
# VISÃO GERAL
# ============================================================

if pagina == "📊 Visão Geral":

    st.header("Visão Geral do Mercado")

    st.caption(
        "Primeira camada de leitura: tamanho do mercado, "
        "cobertura institucional e distribuição."
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)


    with c1:

        kpi(
            "Mercado",
            numero(mercado),
            "indústrias"
        )


    with c2:

        kpi(
            "SESI",
            numero(sesi),
            percentual(
                sesi / mercado * 100
            ) if mercado else "0%"
        )


    with c3:

        kpi(
            "SENAI",
            numero(senai),
            percentual(
                senai / mercado * 100
            ) if mercado else "0%"
        )


    with c4:

        kpi(
            "SESI + SENAI",
            numero(ambos),
            percentual(
                ambos / mercado * 100
            ) if mercado else "0%"
        )


    with c5:

        kpi(
            "Relacionadas",
            numero(clientes),
            percentual(
                clientes / mercado * 100
            ) if mercado else "0%"
        )


    with c6:

        kpi(
            "Sem relacionamento",
            numero(sem_relacionamento),
            percentual(
                sem_relacionamento / mercado * 100
            ) if mercado else "0%"
        )


    st.divider()


    # --------------------------------------------------------
    # COBERTURA
    # --------------------------------------------------------

    col1, col2 = st.columns(2)


    with col1:

        st.subheader(
            "Cobertura institucional"
        )

        cobertura = pd.DataFrame(
            {
                "Categoria": [
                    "Somente SESI",
                    "Somente SENAI",
                    "SESI + SENAI",
                    "Sem relacionamento"
                ],

                "Empresas": [

                    (
                        df_view["POSSUI_SESI"]
                        &
                        ~df_view["POSSUI_SENAI"]
                    ).sum(),

                    (
                        df_view["POSSUI_SENAI"]
                        &
                        ~df_view["POSSUI_SESI"]
                    ).sum(),

                    ambos,

                    sem_relacionamento
                ]
            }
        )

        st.bar_chart(
            cobertura.set_index(
                "Categoria"
            )
        )


    # --------------------------------------------------------
    # PORTE
    # --------------------------------------------------------

    with col2:

        st.subheader(
            "Mercado por porte"
        )

        porte = (
            df_view["Porte"]
            .value_counts()
            .rename_axis("Porte")
            .to_frame("Empresas")
        )

        st.bar_chart(porte)


    # --------------------------------------------------------
    # MUNICÍPIOS
    # --------------------------------------------------------

    st.subheader(
        "Principais municípios"
    )

    municipio = (
        df_view["Municipio"]
        .value_counts()
        .head(20)
        .rename_axis("Município")
        .to_frame("Empresas")
    )

    st.bar_chart(municipio)


# ============================================================
# MERCADO
# ============================================================

elif pagina == "🏭 Mercado":

    st.header("🏭 Mercado Industrial")

    st.write(
        "Universo de empresas utilizado como base-mãe "
        "para as análises comerciais."
    )

    c1, c2, c3, c4 = st.columns(4)


    with c1:

        kpi(
            "Empresas",
            numero(len(df_view))
        )


    with c2:

        kpi(
            "Municípios",
            numero(
                df_view["Municipio"]
                .nunique()
            )
        )


    with c3:

        kpi(
            "CNAEs",
            numero(
                df_view["CNAE PRIMARIO"]
                .nunique()
            )
        )


    with c4:

        kpi(
            "Relacionadas",
            numero(clientes)
        )


    st.divider()


    # --------------------------------------------------------
    # MUNICÍPIO
    # --------------------------------------------------------

    st.subheader(
        "Distribuição por município"
    )

    municipio = (
        df_view["Municipio"]
        .value_counts()
        .head(30)
        .rename_axis("Município")
        .to_frame("Empresas")
    )

    st.bar_chart(municipio)


    # --------------------------------------------------------
    # CNAE
    # --------------------------------------------------------

    st.subheader(
        "Principais atividades econômicas"
    )

    cnae = (
        df_view["CNAE PRIMARIO"]
        .fillna("NÃO INFORMADO")
        .value_counts()
        .head(30)
        .rename_axis("CNAE")
        .to_frame("Empresas")
    )

    st.dataframe(
        cnae,
        use_container_width=True
    )


# ============================================================
# SESI
# ============================================================

elif pagina == "🔵 SESI":

    st.header("🔵 Visão SESI")

    st.caption(
        "Cobertura, penetração e gap comercial do SESI."
    )

    sem_sesi = (
        ~df_view["POSSUI_SESI"]
    ).sum()

    penet = (
        sesi / mercado * 100
        if mercado
        else 0
    )

    c1, c2, c3 = st.columns(3)


    with c1:

        kpi(
            "Possui SESI",
            numero(sesi),
            "empresas"
        )


    with c2:

        kpi(
            "Penetração",
            percentual(penet)
        )


    with c3:

        kpi(
            "Sem SESI",
            numero(sem_sesi),
            "gap de cobertura"
        )


    st.divider()


    # --------------------------------------------------------
    # PENETRAÇÃO POR MUNICÍPIO
    # --------------------------------------------------------

    st.subheader(
        "Penetração SESI por município"
    )

    if mercado:

        municipio_sesi = (
            df_view
            .groupby("Municipio")
            .agg(
                Mercado=("cnpj", "count"),
                SESI=("POSSUI_SESI", "sum")
            )
            .reset_index()
        )

        municipio_sesi["Penetração"] = (
            municipio_sesi["SESI"]
            /
            municipio_sesi["Mercado"]
            *
            100
        )

        municipio_sesi = (
            municipio_sesi
            .sort_values(
                "Penetração",
                ascending=False
            )
        )

        st.dataframe(
            municipio_sesi,
            use_container_width=True,
            height=500
        )


    # --------------------------------------------------------
    # EMPRESAS SEM SESI
    # --------------------------------------------------------

    st.subheader(
        "Empresas sem SESI"
    )

    empresas_sem_sesi = df_view[
        ~df_view["POSSUI_SESI"]
    ].copy()

    colunas = selecionar_colunas_existentes(
        empresas_sem_sesi,
        [
            "cnpj",
            "razao_social",
            "Municipio",
            "Porte",
            "CNAE PRIMARIO",
            "POSSUI_SENAI",
            "STATUS_SEBRAE"
        ]
    )

    tabela_sesi = (
        empresas_sem_sesi[colunas]
        .copy()
    )

    if "POSSUI_SENAI" in tabela_sesi.columns:

        tabela_sesi["Possui SENAI"] = (
            tabela_sesi["POSSUI_SENAI"]
            .map(
                {
                    True: "SIM",
                    False: "NÃO"
                }
            )
        )

        tabela_sesi = tabela_sesi.drop(
            columns=["POSSUI_SENAI"]
        )

    st.dataframe(
        tabela_sesi.head(3000),
        use_container_width=True,
        height=500
    )


# ============================================================
# SENAI
# ============================================================

elif pagina == "🟠 SENAI":

    st.header("🟠 Visão SENAI")

    st.caption(
        "Cobertura, penetração e gap comercial do SENAI."
    )

    sem_senai = (
        ~df_view["POSSUI_SENAI"]
    ).sum()

    penet = (
        senai / mercado * 100
        if mercado
        else 0
    )

    c1, c2, c3 = st.columns(3)


    with c1:

        kpi(
            "Possui SENAI",
            numero(senai),
            "empresas"
        )


    with c2:

        kpi(
            "Penetração",
            percentual(penet)
        )


    with c3:

        kpi(
            "Sem SENAI",
            numero(sem_senai),
            "gap de cobertura"
        )


    st.divider()


    # --------------------------------------------------------
    # PENETRAÇÃO POR MUNICÍPIO
    # --------------------------------------------------------

    st.subheader(
        "Penetração SENAI por município"
    )

    if mercado:

        municipio_senai = (
            df_view
            .groupby("Municipio")
            .agg(
                Mercado=("cnpj", "count"),
                SENAI=("POSSUI_SENAI", "sum")
            )
            .reset_index()
        )

        municipio_senai["Penetração"] = (
            municipio_senai["SENAI"]
            /
            municipio_senai["Mercado"]
            *
            100
        )

        municipio_senai = (
            municipio_senai
            .sort_values(
                "Penetração",
                ascending=False
            )
        )

        st.dataframe(
            municipio_senai,
            use_container_width=True,
            height=500
        )


    # --------------------------------------------------------
    # EMPRESAS SEM SENAI
    # --------------------------------------------------------

    st.subheader(
        "Empresas sem SENAI"
    )

    empresas_sem_senai = df_view[
        ~df_view["POSSUI_SENAI"]
    ].copy()

    colunas = selecionar_colunas_existentes(
        empresas_sem_senai,
        [
            "cnpj",
            "razao_social",
            "Municipio",
            "Porte",
            "CNAE PRIMARIO",
            "POSSUI_SESI",
            "STATUS_SEBRAE"
        ]
    )

    tabela_senai = (
        empresas_sem_senai[colunas]
        .copy()
    )

    if "POSSUI_SESI" in tabela_senai.columns:

        tabela_senai["Possui SESI"] = (
            tabela_senai["POSSUI_SESI"]
            .map(
                {
                    True: "SIM",
                    False: "NÃO"
                }
            )
        )

        tabela_senai = tabela_senai.drop(
            columns=["POSSUI_SESI"]
        )

    st.dataframe(
        tabela_senai.head(3000),
        use_container_width=True,
        height=500
    )


# ============================================================
# SEBRAE
# ============================================================

elif pagina == "🟢 SEBRAE":

    st.header("🟢 Visão SEBRAE")

    st.caption(
        "Inteligência de mercado do SEBRAE dentro "
        "do universo industrial de Alagoas."
    )

    if "STATUS_SEBRAE" not in df_view.columns:

        st.error(
            "A informação do SEBRAE não está disponível "
            "na Base Mestre."
        )

        st.stop()


    # --------------------------------------------------------
    # DISTRIBUIÇÃO
    # --------------------------------------------------------

    distribuicao = (
        df_view["STATUS_SEBRAE"]
        .value_counts()
    )

    nao_atendida = distribuicao.get(
        "NÃO ATENDIDA",
        0
    )

    fora_escopo = distribuicao.get(
        "FORA DO ESCOPO SEBRAE",
        0
    )

    sem_info = distribuicao.get(
        "SEM INFORMAÇÃO",
        0
    )

    outros = (
        mercado
        -
        nao_atendida
        -
        fora_escopo
        -
        sem_info
    )


    # --------------------------------------------------------
    # KPIs
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)


    with c1:

        kpi(
            "Mercado",
            numero(mercado),
            "empresas"
        )


    with c2:

        kpi(
            "Não atendidas",
            numero(nao_atendida),
            "oportunidade SEBRAE"
        )


    with c3:

        kpi(
            "Fora do escopo",
            numero(fora_escopo),
            "não elegíveis"
        )


    with c4:

        percentual_no_escopo = (
            (
                nao_atendida
                /
                mercado
            )
            *
            100
            if mercado
            else 0
        )

        kpi(
            "Não atendidas",
            percentual(
                percentual_no_escopo
            ),
            "do mercado"
        )


    st.divider()


    # --------------------------------------------------------
    # DISTRIBUIÇÃO
    # --------------------------------------------------------

    st.subheader(
        "Situação SEBRAE"
    )

    grafico_sebrae = pd.DataFrame(
        {
            "Situação": [
                "Não atendida",
                "Fora do escopo",
                "Sem informação"
            ],

            "Empresas": [
                nao_atendida,
                fora_escopo,
                sem_info
            ]
        }
    )

    if outros > 0:

        grafico_sebrae.loc[
            len(grafico_sebrae)
        ] = [
            "Outros",
            outros
        ]

    st.bar_chart(
        grafico_sebrae.set_index(
            "Situação"
        )
    )


    # --------------------------------------------------------
    # MUNICÍPIO
    # --------------------------------------------------------

    st.subheader(
        "Oportunidade SEBRAE por município"
    )

    df_oportunidade = df_view[
        df_view["STATUS_SEBRAE"]
        .eq("NÃO ATENDIDA")
    ].copy()

    if not df_oportunidade.empty:

        oportunidade_municipio = (
            df_oportunidade["Municipio"]
            .value_counts()
            .head(30)
            .rename_axis("Município")
            .to_frame(
                "Empresas não atendidas"
            )
        )

        st.bar_chart(
            oportunidade_municipio
        )

    else:

        st.info(
            "Não há empresas NÃO ATENDIDAS "
            "no contexto atual dos filtros."
        )


    # --------------------------------------------------------
    # PORTE
    # --------------------------------------------------------

    st.subheader(
        "Oportunidade SEBRAE por porte"
    )

    if not df_oportunidade.empty:

        oportunidade_porte = (
            df_oportunidade["Porte"]
            .value_counts()
            .rename_axis("Porte")
            .to_frame("Empresas")
        )

        st.bar_chart(
            oportunidade_porte
        )


    # --------------------------------------------------------
    # CNAE
    # --------------------------------------------------------

    st.subheader(
        "Oportunidade SEBRAE por atividade"
    )

    if not df_oportunidade.empty:

        oportunidade_cnae = (
            df_oportunidade["CNAE PRIMARIO"]
            .fillna("NÃO INFORMADO")
            .value_counts()
            .head(30)
            .rename_axis("CNAE")
            .to_frame("Empresas")
        )

        st.dataframe(
            oportunidade_cnae,
            use_container_width=True
        )


    # --------------------------------------------------------
    # EMPRESAS NÃO ATENDIDAS
    # --------------------------------------------------------

    st.subheader(
        "Empresas classificadas como NÃO ATENDIDA"
    )

    colunas = selecionar_colunas_existentes(
        df_oportunidade,
        [
            "cnpj",
            "razao_social",
            "Municipio",
            "Porte",
            "CNAE PRIMARIO",
            "STATUS_SEBRAE",
            "POSSUI_SESI",
            "POSSUI_SENAI"
        ]
    )

    tabela_sebrae = (
        df_oportunidade[colunas]
        .copy()
    )

    if "POSSUI_SESI" in tabela_sebrae.columns:

        tabela_sebrae["Possui SESI"] = (
            tabela_sebrae["POSSUI_SESI"]
            .map(
                {
                    True: "SIM",
                    False: "NÃO"
                }
            )
        )

        tabela_sebrae = tabela_sebrae.drop(
            columns=["POSSUI_SESI"]
        )

    if "POSSUI_SENAI" in tabela_sebrae.columns:

        tabela_sebrae["Possui SENAI"] = (
            tabela_sebrae["POSSUI_SENAI"]
            .map(
                {
                    True: "SIM",
                    False: "NÃO"
                }
            )
        )

        tabela_sebrae = tabela_sebrae.drop(
            columns=["POSSUI_SENAI"]
        )

    st.dataframe(
        tabela_sebrae.head(3000),
        use_container_width=True,
        height=500
    )


# ============================================================
# VISÃO INTEGRADA
# ============================================================

elif pagina == "🔥 Visão Integrada":

    st.header("🔥 Visão Integrada")

    st.caption(
        "Uma mesma empresa observada pelas três perspectivas: "
        "SESI, SENAI e SEBRAE."
    )

    dados = df_view.copy()


    # --------------------------------------------------------
    # KPIs
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)


    with c1:

        kpi(
            "SESI",
            numero(
                dados["POSSUI_SESI"].sum()
            )
        )


    with c2:

        kpi(
            "SENAI",
            numero(
                dados["POSSUI_SENAI"].sum()
            )
        )


    with c3:

        kpi(
            "SESI + SENAI",
            numero(
                dados["POSSUI_SESI_SENAI"].sum()
            )
        )


    with c4:

        sem_cobertura = (
            ~(
                dados["POSSUI_SESI"]
                |
                dados["POSSUI_SENAI"]
            )
        ).sum()

        kpi(
            "Sem SESI/SENAI",
            numero(sem_cobertura)
        )


    st.divider()


    # --------------------------------------------------------
    # COBERTURA
    # --------------------------------------------------------

    st.subheader(
        "Cobertura SESI/SENAI"
    )

    cobertura = (
        dados["STATUS_RELACIONAMENTO_REAL"]
        .value_counts()
        .rename_axis("Cobertura")
        .to_frame("Empresas")
    )

    st.bar_chart(cobertura)


    st.divider()


    # --------------------------------------------------------
    # SESI/SENAI × SEBRAE
    # --------------------------------------------------------

    st.subheader(
        "SESI/SENAI × SEBRAE"
    )

    cruzamento = pd.crosstab(
        dados["STATUS_RELACIONAMENTO_REAL"],
        dados["STATUS_SEBRAE"]
    )

    st.dataframe(
        cruzamento,
        use_container_width=True
    )


    st.divider()


    # --------------------------------------------------------
    # OPORTUNIDADE INTEGRADA
    # --------------------------------------------------------

    st.subheader(
        "Sem SESI/SENAI e não atendidas pelo SEBRAE"
    )

    oportunidade_integrada = dados[
        (
            dados["STATUS_RELACIONAMENTO_REAL"]
            == "Sem relacionamento"
        )
        &
        (
            dados["STATUS_SEBRAE"]
            == "NÃO ATENDIDA"
        )
    ].copy()

    st.metric(
        "Empresas nesse grupo",
        numero(
            len(oportunidade_integrada)
        )
    )

    colunas = selecionar_colunas_existentes(
        oportunidade_integrada,
        [
            "cnpj",
            "razao_social",
            "Municipio",
            "Porte",
            "CNAE PRIMARIO",
            "STATUS_RELACIONAMENTO_REAL",
            "STATUS_SEBRAE"
        ]
    )

    st.dataframe(
        oportunidade_integrada[colunas]
        .head(3000),
        use_container_width=True,
        height=500
    )

    st.caption(
        "Importante: este grupo representa uma lacuna "
        "de cobertura institucional. Não significa, por si só, "
        "propensão de compra."
    )


# ============================================================
# CROSS-SELL
# ============================================================

elif pagina == "🔄 Cross-sell":

    st.header("🔄 Cross-sell")

    st.caption(
        "Oportunidades estruturais entre SESI e SENAI."
    )


    # --------------------------------------------------------
    # SESI → SENAI
    # --------------------------------------------------------

    sesi_senai_df = df_view[
        df_view["POSSUI_SESI"]
        &
        ~df_view["POSSUI_SENAI"]
    ].copy()


    # --------------------------------------------------------
    # SENAI → SESI
    # --------------------------------------------------------

    senai_sesi_df = df_view[
        df_view["POSSUI_SENAI"]
        &
        ~df_view["POSSUI_SESI"]
    ].copy()


    sesi_senai = len(
        sesi_senai_df
    )

    senai_sesi = len(
        senai_sesi_df
    )

    total_cross = (
        sesi_senai
        +
        senai_sesi
    )


    # --------------------------------------------------------
    # KPIs
    # --------------------------------------------------------

    c1, c2, c3 = st.columns(3)


    with c1:

        kpi(
            "Cross-sell total",
            numero(total_cross)
        )


    with c2:

        kpi(
            "SESI → SENAI",
            numero(sesi_senai),
            "possui SESI / não possui SENAI"
        )


    with c3:

        kpi(
            "SENAI → SESI",
            numero(senai_sesi),
            "possui SENAI / não possui SESI"
        )


    st.divider()


    # --------------------------------------------------------
    # GRÁFICO
    # --------------------------------------------------------

    grafico_cross = pd.DataFrame(
        {
            "Direção": [
                "SESI → SENAI",
                "SENAI → SESI"
            ],

            "Empresas": [
                sesi_senai,
                senai_sesi
            ]
        }
    )

    st.subheader(
        "Oportunidades por direção"
    )

    st.bar_chart(
        grafico_cross.set_index(
            "Direção"
        )
    )


    st.divider()


    # --------------------------------------------------------
    # SESI → SENAI
    # --------------------------------------------------------

    st.subheader(
        "Empresas com SESI e sem SENAI"
    )

    colunas = selecionar_colunas_existentes(
        sesi_senai_df,
        [
            "cnpj",
            "razao_social",
            "Municipio",
            "Porte",
            "CNAE PRIMARIO",
            "STATUS_SEBRAE"
        ]
    )

    st.dataframe(
        sesi_senai_df[colunas]
        .head(3000),
        use_container_width=True,
        height=400
    )


    st.divider()


    # --------------------------------------------------------
    # SENAI → SESI
    # --------------------------------------------------------

    st.subheader(
        "Empresas com SENAI e sem SESI"
    )

    colunas = selecionar_colunas_existentes(
        senai_sesi_df,
        [
            "cnpj",
            "razao_social",
            "Municipio",
            "Porte",
            "CNAE PRIMARIO",
            "STATUS_SEBRAE"
        ]
    )

    st.dataframe(
        senai_sesi_df[colunas]
        .head(3000),
        use_container_width=True,
        height=400
    )

    st.caption(
        "Cross-sell representa uma oportunidade "
        "estrutural de cobertura. Não é uma previsão de compra."
    )


# ============================================================
# EMPRESAS
# ============================================================

elif pagina == "🔎 Empresas":

    st.header(
        "🔎 Explorador de Empresas"
    )

    st.caption(
        f"{numero(len(df_view))} empresas "
        "no contexto atual."
    )


    # --------------------------------------------------------
    # BUSCA
    # --------------------------------------------------------

    busca = st.text_input(
        "Pesquisar por CNPJ ou razão social",
        placeholder=(
            "Digite parte do CNPJ ou nome da empresa"
        )
    )

    resultado = df_view.copy()


    if busca:

        busca = busca.strip()

        mascara = pd.Series(
            False,
            index=resultado.index
        )


        if "cnpj" in resultado.columns:

            mascara = (
                mascara
                |
                resultado["cnpj"]
                .astype(str)
                .str.contains(
                    busca,
                    case=False,
                    na=False,
                    regex=False
                )
            )


        if "razao_social" in resultado.columns:

            mascara = (
                mascara
                |
                resultado["razao_social"]
                .astype(str)
                .str.contains(
                    busca,
                    case=False,
                    na=False,
                    regex=False
                )
            )


        resultado = resultado[
            mascara
        ]


    # --------------------------------------------------------
    # MÉTRICA
    # --------------------------------------------------------

    st.metric(
        "Empresas encontradas",
        numero(len(resultado))
    )


    # --------------------------------------------------------
    # TABELA
    # --------------------------------------------------------

    tabela = resultado.copy()

    tabela["Possui SESI"] = (
        tabela["POSSUI_SESI"]
        .map(
            {
                True: "SIM",
                False: "NÃO"
            }
        )
    )

    tabela["Possui SENAI"] = (
        tabela["POSSUI_SENAI"]
        .map(
            {
                True: "SIM",
                False: "NÃO"
            }
        )
    )

    tabela["Possui SESI + SENAI"] = (
        tabela["POSSUI_SESI_SENAI"]
        .map(
            {
                True: "SIM",
                False: "NÃO"
            }
        )
    )

    tabela["Status Relacionamento"] = (
        tabela["STATUS_RELACIONAMENTO_REAL"]
    )

    tabela["Status SEBRAE"] = (
        tabela["STATUS_SEBRAE"]
    )


    colunas = selecionar_colunas_existentes(
        tabela,
        [
            "cnpj",
            "razao_social",
            "Municipio",
            "Porte",
            "CNAE PRIMARIO",
            "Possui SESI",
            "Possui SENAI",
            "Possui SESI + SENAI",
            "Status Relacionamento",
            "Status SEBRAE"
        ]
    )

    tabela_final = tabela[
        colunas
    ]


    st.dataframe(
        tabela_final,
        use_container_width=True,
        height=600
    )


    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    st.download_button(
        "⬇️ Baixar resultado",

        data=tabela_final.to_csv(
            index=False,
            encoding="utf-8-sig"
        ),

        file_name="empresas_filtradas.csv",

        mime="text/csv"
    )


# ============================================================
# AUDITORIA DE COBERTURA
# ============================================================

elif pagina == "✅ Auditoria de Cobertura":

    st.header("✅ Auditoria de Cobertura SESI/SENAI")

    st.caption(
        "Por que o número de clientes SESI/SENAI no dashboard "
        "não é igual ao total bruto do cadastro de relacionamento — "
        "e por que agora dá para confiar nele."
    )

    resultado_auditoria = carregar_auditoria_cobertura()

    if resultado_auditoria is None:

        st.info(
            "Auditoria ainda não foi gerada para esta base."
        )

        st.stop()

    auditoria, correcao = resultado_auditoria

    total_bruto = len(auditoria)
    total_confirmado = (
        auditoria["MOTIVO"]
        .eq("Confirmada e incluída no universo")
        .sum()
    )

    st.markdown(
        "O cadastro de relacionamento do SESI/SENAI aponta um total "
        "de empresas maior do que o que aparece no mercado industrial "
        "de Alagoas. Auditamos **cada uma** dessas empresas direto na "
        "Receita Federal para separar o que é exclusão correta do que "
        "é lacuna real de cobertura."
    )

    st.divider()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi(
            "Empresas auditadas",
            numero(total_bruto),
            "cadastradas como indústria, fora do mercado"
        )

    with c2:
        kpi(
            "Fora de Alagoas / baixadas",
            numero(
                auditoria["MOTIVO"]
                .isin([
                    "Ativa, mas fora de Alagoas",
                    "Baixada / inapta / suspensa"
                ])
                .sum()
            ),
            "exclusão correta, confirmada"
        )

    with c3:
        kpi(
            "Mudou de atividade",
            numero(
                auditoria["MOTIVO"]
                .eq("Ativa em AL, mudou de atividade")
                .sum()
            ),
            "não é mais indústria hoje"
        )

    with c4:
        kpi(
            "Gap real confirmado",
            numero(total_confirmado),
            "recuperadas para o universo"
        )

    st.divider()

    # --------------------------------------------------------
    # DISTRIBUIÇÃO DOS MOTIVOS
    # --------------------------------------------------------

    st.subheader("Como se explica a diferença")

    distribuicao_motivo = (
        auditoria["MOTIVO"]
        .value_counts()
        .rename_axis("Motivo")
        .to_frame("Empresas")
    )

    st.bar_chart(distribuicao_motivo)

    st.caption(
        "Cada empresa foi checada individualmente na Receita Federal: "
        "situação cadastral, município/UF de registro e CNAE em vigor."
    )

    st.divider()

    # --------------------------------------------------------
    # POR COBERTURA (SESI / SENAI)
    # --------------------------------------------------------

    st.subheader("Impacto por carteira")

    impacto = (
        auditoria
        .groupby(["COBERTURA", "MOTIVO"])
        .size()
        .unstack(fill_value=0)
    )

    st.dataframe(
        impacto,
        use_container_width=True
    )

    st.divider()

    # --------------------------------------------------------
    # EMPRESAS RECUPERADAS
    # --------------------------------------------------------

    st.subheader(
        "Empresas recuperadas para o seu radar comercial"
    )

    st.caption(
        "Já são clientes SESI e/ou SENAI, estão ativas em Alagoas com "
        "CNAE de indústria — agora aparecem nas demais páginas do "
        "dashboard."
    )

    if correcao is not None and not correcao.empty:

        tabela_recuperadas = correcao[
            [
                "razao_social",
                "Municipio",
                "Porte",
                "CNAE PRIMARIO"
            ]
        ].rename(
            columns={
                "razao_social": "Empresa",
                "Municipio": "Município",
                "CNAE PRIMARIO": "Atividade"
            }
        )

        st.dataframe(
            tabela_recuperadas,
            use_container_width=True,
            height=350
        )

    else:

        st.info(
            "Nenhuma empresa recuperada nesta versão da base."
        )

    st.caption(
        "Metodologia: cruzamento de CNPJ contra consulta pública de "
        "dados da Receita Federal (situação cadastral, município/UF e "
        "CNAE fiscal principal). Considerado indústria de transformação "
        "quando o CNAE em vigor está nas divisões 10 a 33."
    )


# ============================================================
# RODAPÉ
# ============================================================

st.divider()

st.caption(
    "SESI + SENAI + SEBRAE Alagoas | "
    "Inteligência Comercial | V1 | "
    "Dados, validação e visualização"
)