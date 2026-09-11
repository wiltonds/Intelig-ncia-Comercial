# ============================================================
# GERAR MATRIZ DE PENETRAÇÃO COMERCIAL
# SENAI / SESI / SEBRAE - ALAGOAS
#
# BASE:
# BASE_MESTRE_COMERCIAL.csv
#
# OBJETIVO:
# - Medir tamanho do mercado
# - Medir penetração SESI
# - Medir penetração SENAI
# - Medir penetração combinada
# - Calcular GAP
# - Analisar Município
# - Analisar Porte
# - Analisar CNAE
# - Identificar oportunidades
# - Identificar Cross-sell
# - Gerar ranking comercial
# ============================================================

from pathlib import Path

import pandas as pd
import numpy as np


# ============================================================
# 1. CONFIGURAÇÃO
# ============================================================

ARQUIVO_ENTRADA = Path(
    r"C:\Users\wilton.costa\Desktop\projeto_comercial\saida\BASE_MESTRE_COMERCIAL.csv"
)

PASTA_SAIDA = Path(
    r"C:\Users\wilton.costa\Desktop\projeto_comercial\saida\matriz_penetracao"
)

PASTA_SAIDA.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 2. FUNÇÕES AUXILIARES
# ============================================================

def titulo(texto):

    print()
    print("=" * 78)
    print(texto)
    print("=" * 78)


def normalizar_texto(serie):

    return (
        serie
        .astype("string")
        .str.strip()
    )


def salvar(df, nome):

    caminho = PASTA_SAIDA / nome

    df.to_csv(
        caminho,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"✓ {nome:<45} "
        f"{len(df):>10,} linhas"
    )

    return caminho


def garantir_coluna(df, coluna):

    if coluna not in df.columns:

        raise ValueError(
            "\n"
            "============================================================\n"
            "ERRO: COLUNA OBRIGATÓRIA NÃO ENCONTRADA\n"
            "============================================================\n"
            f"Coluna ausente: {coluna}\n\n"
            "Colunas disponíveis:\n"
            + "\n".join(
                f" - {c}"
                for c in df.columns
            )
        )


def percentual(numerador, denominador):

    """
    Calcula percentual com segurança.

    Aceita:
    - pandas Series
    - numpy array
    - listas
    - números individuais

    Retorna sempre uma Series.
    """

    # --------------------------------------------------------
    # Numerador
    # --------------------------------------------------------

    if isinstance(
        numerador,
        pd.Series
    ):

        numerador_series = numerador.copy()

    elif isinstance(
        numerador,
        (np.ndarray, list, tuple)
    ):

        numerador_series = pd.Series(
            numerador
        )

    else:

        numerador_series = pd.Series(
            [numerador]
        )


    # --------------------------------------------------------
    # Denominador
    # --------------------------------------------------------

    if isinstance(
        denominador,
        pd.Series
    ):

        denominador_series = denominador.copy()

    elif isinstance(
        denominador,
        (np.ndarray, list, tuple)
    ):

        denominador_series = pd.Series(
            denominador
        )

    else:

        denominador_series = pd.Series(
            [denominador]
        )


    # --------------------------------------------------------
    # Conversão numérica
    # --------------------------------------------------------

    numerador_series = pd.to_numeric(
        numerador_series,
        errors="coerce"
    ).fillna(0)


    denominador_series = pd.to_numeric(
        denominador_series,
        errors="coerce"
    ).fillna(0)


    # --------------------------------------------------------
    # Se denominador tiver apenas 1 valor,
    # repete para todas as linhas
    # --------------------------------------------------------

    if (
        len(denominador_series) == 1
        and len(numerador_series) > 1
    ):

        denominador_series = pd.Series(
            np.repeat(
                denominador_series.iloc[0],
                len(numerador_series)
            ),
            index=numerador_series.index
        )


    # --------------------------------------------------------
    # Cálculo
    # --------------------------------------------------------

    resultado = np.where(
        denominador_series > 0,
        (
            numerador_series
            / denominador_series
        ) * 100,
        0.0
    )


    resultado = pd.Series(
        resultado,
        index=numerador_series.index,
        dtype="float64"
    )


    resultado = resultado.round(4)


    # --------------------------------------------------------
    # Validações
    # --------------------------------------------------------

    if (
        resultado < 0
    ).any():

        raise ValueError(
            "ERRO: foi encontrada penetração negativa."
        )


    if (
        resultado > 100.0001
    ).any():

        raise ValueError(
            "ERRO: foi encontrada penetração superior a 100%."
        )


    return resultado


def adicionar_penetracoes(df):

    """
    Adiciona:
    - Penetração SESI
    - Penetração SENAI
    - Penetração combinada
    - GAP SESI
    - GAP SENAI
    - GAP combinado
    """

    df = df.copy()


    # --------------------------------------------------------
    # Penetração SESI
    # --------------------------------------------------------

    df["PENETRACAO_SESI_%"] = percentual(
        df["QT_SESI"],
        df["MERCADO"]
    ).values


    # --------------------------------------------------------
    # Penetração SENAI
    # --------------------------------------------------------

    df["PENETRACAO_SENAI_%"] = percentual(
        df["QT_SENAI"],
        df["MERCADO"]
    ).values


    # --------------------------------------------------------
    # Penetração combinada
    # --------------------------------------------------------

    df["PENETRACAO_COMBINADA_%"] = percentual(
        df["QT_SESI_OU_SENAI"],
        df["MERCADO"]
    ).values


    # --------------------------------------------------------
    # GAP SESI
    # --------------------------------------------------------

    df["GAP_SESI"] = (
        df["MERCADO"]
        - df["QT_SESI"]
    )


    # --------------------------------------------------------
    # GAP SENAI
    # --------------------------------------------------------

    df["GAP_SENAI"] = (
        df["MERCADO"]
        - df["QT_SENAI"]
    )


    # --------------------------------------------------------
    # GAP combinado
    # --------------------------------------------------------

    df["GAP_COMBINADO"] = (
        df["MERCADO"]
        - df["QT_SESI_OU_SENAI"]
    )


    return df


def validar_penetracoes(
    df,
    nome_matriz
):

    colunas = [
        "PENETRACAO_SESI_%",
        "PENETRACAO_SENAI_%",
        "PENETRACAO_COMBINADA_%"
    ]


    print(
        f"\nValidando penetrações: "
        f"{nome_matriz}"
    )


    for coluna in colunas:

        minimo = pd.to_numeric(
            df[coluna],
            errors="coerce"
        ).min()


        maximo = pd.to_numeric(
            df[coluna],
            errors="coerce"
        ).max()


        print(
            f"  {coluna}: "
            f"mín={minimo:.4f} | "
            f"máx={maximo:.4f}"
        )


        if minimo < 0:

            raise ValueError(
                f"ERRO: {coluna} possui valor negativo."
            )


        if maximo > 100:

            raise ValueError(
                f"ERRO: {coluna} possui valor > 100%."
            )


    print(
        "✓ Penetrações válidas."
    )


# ============================================================
# 3. CARREGANDO BASE MESTRE
# ============================================================

titulo(
    "1. CARREGANDO BASE MESTRE"
)


if not ARQUIVO_ENTRADA.exists():

    raise FileNotFoundError(
        "\n"
        "============================================================\n"
        "ARQUIVO NÃO ENCONTRADO\n"
        "============================================================\n"
        f"{ARQUIVO_ENTRADA}\n\n"
        "Execute primeiro:\n"
        "construir_base_mestre.py"
    )


df = pd.read_csv(
    ARQUIVO_ENTRADA,
    encoding="utf-8-sig",
    low_memory=False
)


print(
    f"Linhas carregadas: "
    f"{len(df):,}"
)


print(
    f"Colunas carregadas: "
    f"{len(df.columns):,}"
)


# ============================================================
# 4. VALIDANDO CAMPOS
# ============================================================

titulo(
    "2. VALIDANDO CAMPOS"
)


colunas_obrigatorias = [

    "CNPJ_NORMALIZADO",

    "Municipio",

    "Porte",

    "CNAE PRIMARIO",

    "TEM_SESI",

    "TEM_SENAI",

    "TEM_SESI_SENAI",

    "STATUS_RELACIONAMENTO",

    "OPORTUNIDADE_SEBRAE"

]


for coluna in colunas_obrigatorias:

    garantir_coluna(
        df,
        coluna
    )


print(
    "✓ Todas as colunas obrigatórias existem."
)


# ============================================================
# 5. NORMALIZAÇÃO
# ============================================================

titulo(
    "3. NORMALIZAÇÃO DOS DADOS"
)


df["Municipio"] = normalizar_texto(
    df["Municipio"]
)


df["Porte"] = normalizar_texto(
    df["Porte"]
)


df["CNAE PRIMARIO"] = normalizar_texto(
    df["CNAE PRIMARIO"]
)


df["STATUS_RELACIONAMENTO"] = normalizar_texto(
    df["STATUS_RELACIONAMENTO"]
)


df["OPORTUNIDADE_SEBRAE"] = normalizar_texto(
    df["OPORTUNIDADE_SEBRAE"]
)


# ============================================================
# 6. PADRONIZAÇÃO DOS FLAGS
# ============================================================

titulo(
    "4. PADRONIZAÇÃO DOS FLAGS"
)


for coluna in [

    "TEM_SESI",
    "TEM_SENAI",
    "TEM_SESI_SENAI"

]:

    df[coluna] = pd.to_numeric(
        df[coluna],
        errors="coerce"
    ).fillna(0).astype(int)


print(
    "✓ Flags padronizados."
)


# ============================================================
# 7. STATUS COMERCIAL
# ============================================================

titulo(
    "5. CRIANDO STATUS COMERCIAL"
)


def definir_status(row):

    sesi = row["TEM_SESI"]
    senai = row["TEM_SENAI"]


    if (
        sesi == 1
        and senai == 1
    ):

        return "SESI + SENAI"


    elif sesi == 1:

        return "SOMENTE SESI"


    elif senai == 1:

        return "SOMENTE SENAI"


    else:

        return "SEM RELACIONAMENTO"


df["STATUS_COMERCIAL"] = df.apply(
    definir_status,
    axis=1
)


print(
    "✓ Status comercial criado."
)


# ============================================================
# 8. RESUMO GERAL
# ============================================================

titulo(
    "6. RESUMO GERAL"
)


mercado_total = (
    df["CNPJ_NORMALIZADO"]
    .nunique()
)


qt_sesi = int(
    df["TEM_SESI"].sum()
)


qt_senai = int(
    df["TEM_SENAI"].sum()
)


qt_sesi_senai = int(
    df["TEM_SESI_SENAI"].sum()
)


qt_sesi_ou_senai = int(
    (
        (df["TEM_SESI"] == 1)
        |
        (df["TEM_SENAI"] == 1)
    ).sum()
)


qt_sem_relacionamento = int(
    (
        (df["TEM_SESI"] == 0)
        &
        (df["TEM_SENAI"] == 0)
    ).sum()
)


qt_oportunidade_sebrae = int(
    (
        df["OPORTUNIDADE_SEBRAE"]
        .fillna("")
        .str.upper()
        .eq("NÃO ATENDIDA")
    ).sum()
)


qt_fora_escopo_sebrae = int(
    (
        df["OPORTUNIDADE_SEBRAE"]
        .fillna("")
        .str.upper()
        .eq("FORA DO ESCOPO SEBRAE")
    ).sum()
)


resumo_geral = pd.DataFrame({

    "INDICADOR": [

        "Mercado Total",

        "SESI",

        "SENAI",

        "SESI + SENAI",

        "SESI ou SENAI",

        "Sem relacionamento",

        "Oportunidade SEBRAE",

        "Fora do escopo SEBRAE"

    ],


    "QUANTIDADE": [

        mercado_total,

        qt_sesi,

        qt_senai,

        qt_sesi_senai,

        qt_sesi_ou_senai,

        qt_sem_relacionamento,

        qt_oportunidade_sebrae,

        qt_fora_escopo_sebrae

    ]

})


# ------------------------------------------------------------
# IMPORTANTE:
# Aqui o denominador é sempre o mercado total.
# ------------------------------------------------------------

resumo_geral["PERCENTUAL_%"] = (

    resumo_geral["QUANTIDADE"]
    .astype(float)
    .div(
        float(mercado_total)
    )
    .mul(100)
    .round(4)

)


salvar(
    resumo_geral,
    "01_RESUMO_GERAL.csv"
)


print()


print(
    resumo_geral.to_string(
        index=False
    )
)


# ============================================================
# 9. FUNÇÃO PARA CRIAR AGRUPAMENTOS
# ============================================================

def criar_matriz(
    df,
    grupos
):

    resultado = (

        df
        .groupby(
            grupos,
            dropna=False
        )
        .agg(

            MERCADO=(
                "CNPJ_NORMALIZADO",
                "nunique"
            ),

            QT_SESI=(
                "TEM_SESI",
                "sum"
            ),

            QT_SENAI=(
                "TEM_SENAI",
                "sum"
            ),

            QT_SESI_SENAI=(
                "TEM_SESI_SENAI",
                "sum"
            )

        )
        .reset_index()

    )


    # --------------------------------------------------------
    # SESI OU SENAI
    # --------------------------------------------------------

    df_temp = df.copy()


    df_temp["TEM_SESI_OU_SENAI"] = (

        (
            df_temp["TEM_SESI"] == 1
        )
        |
        (
            df_temp["TEM_SENAI"] == 1
        )

    ).astype(int)


    cross = (

        df_temp
        .groupby(
            grupos,
            dropna=False
        )
        ["TEM_SESI_OU_SENAI"]
        .sum()
        .reset_index()

    )


    resultado = resultado.merge(

        cross,

        on=grupos,

        how="left"

    )


    resultado = resultado.rename(

        columns={
            "TEM_SESI_OU_SENAI":
                "QT_SESI_OU_SENAI"
        }

    )


    # --------------------------------------------------------
    # SEM RELACIONAMENTO
    # --------------------------------------------------------

    resultado["SEM_RELACIONAMENTO"] = (

        resultado["MERCADO"]
        - resultado["QT_SESI_OU_SENAI"]

    )


    # --------------------------------------------------------
    # PENETRAÇÕES E GAPS
    # --------------------------------------------------------

    resultado = adicionar_penetracoes(
        resultado
    )


    return resultado


# ============================================================
# 10. MUNICÍPIO
# ============================================================

titulo(
    "7. PENETRAÇÃO POR MUNICÍPIO"
)


municipio = criar_matriz(
    df,
    ["Municipio"]
)


municipio = municipio.sort_values(
    "MERCADO",
    ascending=False
)


validar_penetracoes(
    municipio,
    "MUNICÍPIO"
)


salvar(
    municipio,
    "02_PENETRACAO_MUNICIPIO.csv"
)


# ============================================================
# 11. PORTE
# ============================================================

titulo(
    "8. PENETRAÇÃO POR PORTE"
)


porte = criar_matriz(
    df,
    ["Porte"]
)


porte = porte.sort_values(
    "MERCADO",
    ascending=False
)


validar_penetracoes(
    porte,
    "PORTE"
)


salvar(
    porte,
    "03_PENETRACAO_PORTE.csv"
)


# ============================================================
# 12. CNAE
# ============================================================

titulo(
    "9. PENETRAÇÃO POR CNAE"
)


cnae = criar_matriz(
    df,
    ["CNAE PRIMARIO"]
)


cnae = cnae.sort_values(
    "MERCADO",
    ascending=False
)


validar_penetracoes(
    cnae,
    "CNAE"
)


salvar(
    cnae,
    "04_PENETRACAO_CNAE.csv"
)


# ============================================================
# 13. MUNICÍPIO × PORTE
# ============================================================

titulo(
    "10. MUNICÍPIO × PORTE"
)


municipio_porte = criar_matriz(

    df,

    [
        "Municipio",
        "Porte"
    ]

)


salvar(
    municipio_porte,
    "05_MUNICIPIO_PORTE.csv"
)


# ============================================================
# 14. MUNICÍPIO × CNAE
# ============================================================

titulo(
    "11. MUNICÍPIO × CNAE"
)


municipio_cnae = criar_matriz(

    df,

    [
        "Municipio",
        "CNAE PRIMARIO"
    ]

)


salvar(
    municipio_cnae,
    "06_MUNICIPIO_CNAE.csv"
)


# ============================================================
# 15. PORTE × CNAE
# ============================================================

titulo(
    "12. PORTE × CNAE"
)


porte_cnae = criar_matriz(

    df,

    [
        "Porte",
        "CNAE PRIMARIO"
    ]

)


salvar(
    porte_cnae,
    "07_PORTE_CNAE.csv"
)


# ============================================================
# 16. OPORTUNIDADE SEBRAE
# ============================================================

titulo(
    "13. OPORTUNIDADE SEBRAE"
)


oportunidade_sebrae = df[
    df["OPORTUNIDADE_SEBRAE"]
    .fillna("")
    .str.upper()
    .eq("NÃO ATENDIDA")
].copy()


colunas_sebrae = [

    "CNPJ_NORMALIZADO",

    "razao_social",

    "Municipio",

    "Porte",

    "CNAE PRIMARIO",

    "TEM_SESI",

    "TEM_SENAI",

    "STATUS_COMERCIAL",

    "OPORTUNIDADE_SEBRAE"

]


oportunidade_sebrae = oportunidade_sebrae[
    [
        c
        for c in colunas_sebrae
        if c in oportunidade_sebrae.columns
    ]
]


oportunidade_sebrae = oportunidade_sebrae.sort_values(

    [
        "Municipio",
        "razao_social"
    ]

)


salvar(
    oportunidade_sebrae,
    "08_OPORTUNIDADE_SEBRAE.csv"
)


# ============================================================
# 17. GAP SESI
# ============================================================

titulo(
    "14. GAP SESI"
)


oportunidade_sesi = df[
    df["TEM_SESI"] == 0
].copy()


oportunidade_sesi["GAP_SESI"] = 1


colunas_sesi = [

    "CNPJ_NORMALIZADO",

    "razao_social",

    "Municipio",

    "Porte",

    "CNAE PRIMARIO",

    "TEM_SESI",

    "TEM_SENAI",

    "STATUS_COMERCIAL",

    "GAP_SESI"

]


oportunidade_sesi = oportunidade_sesi[
    [
        c
        for c in colunas_sesi
        if c in oportunidade_sesi.columns
    ]
]


oportunidade_sesi = oportunidade_sesi.sort_values(

    [
        "Municipio",
        "Porte",
        "razao_social"
    ]

)


salvar(
    oportunidade_sesi,
    "09_OPORTUNIDADE_SESI.csv"
)


# ============================================================
# 18. GAP SENAI
# ============================================================

titulo(
    "15. GAP SENAI"
)


oportunidade_senai = df[
    df["TEM_SENAI"] == 0
].copy()


oportunidade_senai["GAP_SENAI"] = 1


colunas_senai = [

    "CNPJ_NORMALIZADO",

    "razao_social",

    "Municipio",

    "Porte",

    "CNAE PRIMARIO",

    "TEM_SESI",

    "TEM_SENAI",

    "STATUS_COMERCIAL",

    "GAP_SENAI"

]


oportunidade_senai = oportunidade_senai[
    [
        c
        for c in colunas_senai
        if c in oportunidade_senai.columns
    ]
]


oportunidade_senai = oportunidade_senai.sort_values(

    [
        "Municipio",
        "Porte",
        "razao_social"
    ]

)


salvar(
    oportunidade_senai,
    "10_OPORTUNIDADE_SENAI.csv"
)


# ============================================================
# 19. GAP COMBINADO
# ============================================================

titulo(
    "16. GAP COMBINADO SESI + SENAI"
)


oportunidade_combinada = df[

    (
        df["TEM_SESI"] == 0
    )

    &

    (
        df["TEM_SENAI"] == 0
    )

].copy()


oportunidade_combinada[
    "GAP_COMBINADO"
] = 1


colunas_combinadas = [

    "CNPJ_NORMALIZADO",

    "razao_social",

    "Municipio",

    "Porte",

    "CNAE PRIMARIO",

    "TEM_SESI",

    "TEM_SENAI",

    "STATUS_COMERCIAL",

    "GAP_COMBINADO"

]


oportunidade_combinada = oportunidade_combinada[
    [
        c
        for c in colunas_combinadas
        if c in oportunidade_combinada.columns
    ]
]


oportunidade_combinada = oportunidade_combinada.sort_values(

    [
        "Municipio",
        "Porte",
        "razao_social"
    ]

)


salvar(
    oportunidade_combinada,
    "11_OPORTUNIDADE_COMBINADA.csv"
)


# ============================================================
# 20. CROSS-SELL
# ============================================================

titulo(
    "17. CROSS-SELL"
)


# ------------------------------------------------------------
# SESI → SENAI
# ------------------------------------------------------------

cross_sell_sesi_para_senai = df[

    (
        df["TEM_SESI"] == 1
    )

    &

    (
        df["TEM_SENAI"] == 0
    )

].copy()


cross_sell_sesi_para_senai[
    "OPORTUNIDADE_CROSS_SELL"
] = "SESI → SENAI"


# ------------------------------------------------------------
# SENAI → SESI
# ------------------------------------------------------------

cross_sell_senai_para_sesi = df[

    (
        df["TEM_SENAI"] == 1
    )

    &

    (
        df["TEM_SESI"] == 0
    )

].copy()


cross_sell_senai_para_sesi[
    "OPORTUNIDADE_CROSS_SELL"
] = "SENAI → SESI"


# ------------------------------------------------------------
# União
# ------------------------------------------------------------

cross_sell = pd.concat(

    [
        cross_sell_sesi_para_senai,
        cross_sell_senai_para_sesi
    ],

    ignore_index=True

)


colunas_cross = [

    "CNPJ_NORMALIZADO",

    "razao_social",

    "Municipio",

    "Porte",

    "CNAE PRIMARIO",

    "TEM_SESI",

    "TEM_SENAI",

    "STATUS_COMERCIAL",

    "OPORTUNIDADE_CROSS_SELL"

]


cross_sell = cross_sell[
    [
        c
        for c in colunas_cross
        if c in cross_sell.columns
    ]
]


cross_sell = cross_sell.sort_values(

    [
        "OPORTUNIDADE_CROSS_SELL",
        "Municipio",
        "razao_social"
    ]

)


salvar(
    cross_sell,
    "12_CROSS_SELL.csv"
)


# ============================================================
# 21. RANKING DE OPORTUNIDADES
# ============================================================

titulo(
    "18. RANKING DE OPORTUNIDADES"
)


ranking = municipio.copy()


ranking["OPORTUNIDADE_TOTAL"] = (

    ranking["GAP_COMBINADO"]

)


ranking["SCORE_GAP"] = (

    ranking["GAP_COMBINADO"]
    .div(
        ranking["MERCADO"]
    )
    .mul(100)
    .round(4)

)


ranking = ranking.sort_values(

    [
        "OPORTUNIDADE_TOTAL",
        "MERCADO"
    ],

    ascending=[
        False,
        False
    ]

).reset_index(
    drop=True
)


ranking["RANKING"] = (

    np.arange(
        1,
        len(ranking) + 1
    )

)


colunas_ranking = [

    "RANKING",

    "Municipio",

    "MERCADO",

    "QT_SESI",

    "QT_SENAI",

    "QT_SESI_SENAI",

    "QT_SESI_OU_SENAI",

    "SEM_RELACIONAMENTO",

    "PENETRACAO_SESI_%",

    "PENETRACAO_SENAI_%",

    "PENETRACAO_COMBINADA_%",

    "GAP_SESI",

    "GAP_SENAI",

    "GAP_COMBINADO",

    "OPORTUNIDADE_TOTAL",

    "SCORE_GAP"

]


ranking = ranking[
    [
        c
        for c in colunas_ranking
        if c in ranking.columns
    ]
]


salvar(
    ranking,
    "13_RANKING_OPORTUNIDADES.csv"
)


# ============================================================
# 22. DICIONÁRIO DE CAMPOS
# ============================================================

titulo(
    "19. DICIONÁRIO DE CAMPOS"
)


dicionario = pd.DataFrame({

    "CAMPO": [

        "MERCADO",

        "QT_SESI",

        "QT_SENAI",

        "QT_SESI_SENAI",

        "QT_SESI_OU_SENAI",

        "SEM_RELACIONAMENTO",

        "PENETRACAO_SESI_%",

        "PENETRACAO_SENAI_%",

        "PENETRACAO_COMBINADA_%",

        "GAP_SESI",

        "GAP_SENAI",

        "GAP_COMBINADO",

        "STATUS_COMERCIAL",

        "OPORTUNIDADE_SEBRAE",

        "OPORTUNIDADE_CROSS_SELL"

    ],


    "DESCRICAO": [

        "Quantidade de empresas no universo analisado.",

        "Empresas com relacionamento SESI.",

        "Empresas com relacionamento SENAI.",

        "Empresas com SESI e SENAI simultaneamente.",

        "Empresas com SESI ou SENAI.",

        "Empresas sem relacionamento identificado com SESI ou SENAI.",

        "Percentual do mercado com relacionamento SESI.",

        "Percentual do mercado com relacionamento SENAI.",

        "Percentual do mercado com relacionamento SESI ou SENAI.",

        "Mercado total menos empresas com SESI.",

        "Mercado total menos empresas com SENAI.",

        "Mercado total menos empresas com SESI ou SENAI.",

        "Situação comercial consolidada da empresa.",

        "Classificação de oportunidade relacionada ao SEBRAE.",

        "Possibilidade de venda cruzada entre SESI e SENAI."

    ]

})


salvar(
    dicionario,
    "00_DICIONARIO_CAMPOS.csv"
)


# ============================================================
# 23. VALIDAÇÃO FINAL
# ============================================================

titulo(
    "20. VALIDAÇÃO FINAL"
)


print(
    f"Mercado esperado: "
    f"{mercado_total:,}"
)


# ------------------------------------------------------------
# Município
# ------------------------------------------------------------

soma_municipio = int(
    municipio["MERCADO"].sum()
)


print(
    f"Mercado por município: "
    f"{soma_municipio:,}"
)


if soma_municipio != mercado_total:

    raise ValueError(
        "ERRO: soma dos mercados por município "
        "não corresponde ao mercado total."
    )


print(
    "✓ Município fecha corretamente."
)


# ------------------------------------------------------------
# Porte
# ------------------------------------------------------------

soma_porte = int(
    porte["MERCADO"].sum()
)


print(
    f"Mercado por porte: "
    f"{soma_porte:,}"
)


if soma_porte != mercado_total:

    raise ValueError(
        "ERRO: soma dos mercados por porte "
        "não corresponde ao mercado total."
    )


print(
    "✓ Porte fecha corretamente."
)


# ------------------------------------------------------------
# CNAE
# ------------------------------------------------------------

soma_cnae = int(
    cnae["MERCADO"].sum()
)


print(
    f"Mercado por CNAE: "
    f"{soma_cnae:,}"
)


if soma_cnae != mercado_total:

    raise ValueError(
        "ERRO: soma dos mercados por CNAE "
        "não corresponde ao mercado total."
    )


print(
    "✓ CNAE fecha corretamente."
)


# ------------------------------------------------------------
# Relacionamento
# ------------------------------------------------------------

if (

    qt_sesi_ou_senai
    + qt_sem_relacionamento

) != mercado_total:

    raise ValueError(
        "ERRO: relacionamento + "
        "sem relacionamento não fecha o mercado."
    )


print(
    "✓ Relacionamento fecha corretamente."
)


# ------------------------------------------------------------
# SESI
# ------------------------------------------------------------

if qt_sesi > mercado_total:

    raise ValueError(
        "ERRO: quantidade SESI maior que mercado."
    )


print(
    "✓ SESI válido."
)


# ------------------------------------------------------------
# SENAI
# ------------------------------------------------------------

if qt_senai > mercado_total:

    raise ValueError(
        "ERRO: quantidade SENAI maior que mercado."
    )


print(
    "✓ SENAI válido."
)


# ------------------------------------------------------------
# SESI + SENAI
# ------------------------------------------------------------

if qt_sesi_senai > qt_sesi:

    raise ValueError(
        "ERRO: SESI + SENAI maior que SESI."
    )


if qt_sesi_senai > qt_senai:

    raise ValueError(
        "ERRO: SESI + SENAI maior que SENAI."
    )


print(
    "✓ Sobreposição SESI + SENAI válida."
)


# ------------------------------------------------------------
# GAP
# ------------------------------------------------------------

if (
    oportunidade_combinada.shape[0]
    != qt_sem_relacionamento
):

    raise ValueError(
        "ERRO: GAP combinado não corresponde "
        "às empresas sem relacionamento."
    )


print(
    "✓ GAP combinado validado."
)


# ============================================================
# 24. RESUMO EXECUTIVO
# ============================================================

titulo(
    "21. RESUMO EXECUTIVO"
)


penetracao_sesi = (

    qt_sesi
    / mercado_total
    * 100

)


penetracao_senai = (

    qt_senai
    / mercado_total
    * 100

)


penetracao_combinada = (

    qt_sesi_ou_senai
    / mercado_total
    * 100

)


print(
    f"""
MERCADO INDUSTRIAL
------------------------------------------------------------

Mercado total:                  {mercado_total:>10,}


COBERTURA SESI / SENAI
------------------------------------------------------------

SESI:                            {qt_sesi:>10,}
SENAI:                           {qt_senai:>10,}
SESI + SENAI:                    {qt_sesi_senai:>10,}
SESI ou SENAI:                   {qt_sesi_ou_senai:>10,}
Sem relacionamento:             {qt_sem_relacionamento:>10,}


PENETRAÇÃO
------------------------------------------------------------

SESI:                              {penetracao_sesi:>8.4f}%
SENAI:                             {penetracao_senai:>8.4f}%
SESI ou SENAI:                     {penetracao_combinada:>8.4f}%


GAP
------------------------------------------------------------

GAP SESI:                         {mercado_total - qt_sesi:>10,}
GAP SENAI:                        {mercado_total - qt_senai:>10,}
GAP combinado:                    {mercado_total - qt_sesi_ou_senai:>10,}


SEBRAE
------------------------------------------------------------

Oportunidade SEBRAE:             {qt_oportunidade_sebrae:>10,}
Fora do escopo SEBRAE:           {qt_fora_escopo_sebrae:>10,}


CROSS-SELL
------------------------------------------------------------

SESI → SENAI:                     {len(cross_sell_sesi_para_senai):>10,}
SENAI → SESI:                     {len(cross_sell_senai_para_sesi):>10,}
Total Cross-sell:                 {len(cross_sell):>10,}
"""
)


# ============================================================
# 25. LISTA DE ARQUIVOS GERADOS
# ============================================================

titulo(
    "22. ARQUIVOS GERADOS"
)


arquivos_esperados = [

    "00_DICIONARIO_CAMPOS.csv",

    "01_RESUMO_GERAL.csv",

    "02_PENETRACAO_MUNICIPIO.csv",

    "03_PENETRACAO_PORTE.csv",

    "04_PENETRACAO_CNAE.csv",

    "05_MUNICIPIO_PORTE.csv",

    "06_MUNICIPIO_CNAE.csv",

    "07_PORTE_CNAE.csv",

    "08_OPORTUNIDADE_SEBRAE.csv",

    "09_OPORTUNIDADE_SESI.csv",

    "10_OPORTUNIDADE_SENAI.csv",

    "11_OPORTUNIDADE_COMBINADA.csv",

    "12_CROSS_SELL.csv",

    "13_RANKING_OPORTUNIDADES.csv"

]


for arquivo in arquivos_esperados:

    caminho = PASTA_SAIDA / arquivo

    if caminho.exists():

        print(
            f"✓ {arquivo}"
        )

    else:

        raise FileNotFoundError(
            f"ERRO: arquivo esperado não foi gerado: "
            f"{arquivo}"
        )


# ============================================================
# 26. CONCLUSÃO
# ============================================================

titulo(
    "PROCESSAMENTO CONCLUÍDO COM SUCESSO"
)


print(
    f"""
BASE ANALISADA
------------------------------------------------------------

32.926 empresas industriais


RESULTADOS
------------------------------------------------------------

✓ Mercado total validado
✓ SESI validado
✓ SENAI validado
✓ SESI + SENAI validado
✓ Penetração SESI calculada
✓ Penetração SENAI calculada
✓ Penetração combinada calculada
✓ GAP SESI calculado
✓ GAP SENAI calculado
✓ GAP combinado calculado
✓ Município analisado
✓ Porte analisado
✓ CNAE analisado
✓ Município × Porte
✓ Município × CNAE
✓ Porte × CNAE
✓ Oportunidade SEBRAE
✓ Oportunidade SESI
✓ Oportunidade SENAI
✓ Oportunidade combinada
✓ Cross-sell
✓ Ranking comercial
✓ Dicionário de campos
✓ Validação de integridade


PASTA DE SAÍDA
------------------------------------------------------------

{PASTA_SAIDA}


AUDITORIA CONCLUÍDA.
"""
)