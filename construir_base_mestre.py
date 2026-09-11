import os
import pandas as pd

# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA = r"C:\Users\wilton.costa\Desktop\projeto_comercial"
SAIDA = os.path.join(PASTA, "saida")

ARQ_MERCADO = os.path.join(
    PASTA,
    "industrias_ativas.xlsx"
)

ARQ_RELACIONAMENTO = os.path.join(
    PASTA,
    "BASE_DADOS_SESI&SENAI_N_RELACIONAMENTO.xlsx"
)

ARQ_RELACIONAMENTO_DUPLO = os.path.join(
    PASTA,
    "relacionamento_SESI&SENAI.xlsx"
)

ARQ_SEBRAE = os.path.join(
    PASTA,
    "industrias_ativas_sebrae.xlsx"
)

ARQ_CORRECAO_UNIVERSO = os.path.join(
    PASTA,
    "CORRECAO_UNIVERSO_CONFIRMADA.csv"
)

os.makedirs(SAIDA, exist_ok=True)


# ============================================================
# FUNÇÕES
# ============================================================

def normalizar_cnpj(series):

    s = series.astype("string").str.strip()

    s = s.str.replace(
        r"\.0$",
        "",
        regex=True
    )

    s = s.str.replace(
        r"\D",
        "",
        regex=True
    )

    s = s.str.zfill(14)

    return s


def encontrar_coluna(df, nome_exato=None, contem=None):

    if nome_exato:

        for coluna in df.columns:

            if str(coluna).strip().lower() == nome_exato.lower():

                return coluna

    if contem:

        for coluna in df.columns:

            if contem.lower() in str(coluna).lower():

                return coluna

    return None


def transformar_cnpj_relacionamento(df):

    """
    Cria uma tabela única de relacionamento por CNPJ,
    preservando as duas carteiras.
    """

    coluna_cnpj = encontrar_coluna(
        df,
        nome_exato="CNPJ"
    )

    coluna_cobertura = encontrar_coluna(
        df,
        nome_exato="COBERTURA"
    )

    if coluna_cnpj is None:
        raise ValueError(
            "Coluna CNPJ não encontrada na base de relacionamento."
        )

    if coluna_cobertura is None:
        raise ValueError(
            "Coluna COBERTURA não encontrada."
        )

    temp = df.copy()

    temp["CNPJ_NORMALIZADO"] = normalizar_cnpj(
        temp[coluna_cnpj]
    )

    temp["COBERTURA_NORMALIZADA"] = (
        temp[coluna_cobertura]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # SESI
    # --------------------------------------------------------

    cnpjs_sesi = set(
        temp.loc[
            temp["COBERTURA_NORMALIZADA"] == "SESI",
            "CNPJ_NORMALIZADO"
        ]
    )

    # --------------------------------------------------------
    # SENAI
    # --------------------------------------------------------

    cnpjs_senai = set(
        temp.loc[
            temp["COBERTURA_NORMALIZADA"] == "SENAI",
            "CNPJ_NORMALIZADO"
        ]
    )

    todos = sorted(
        cnpjs_sesi | cnpjs_senai
    )

    relacionamento = pd.DataFrame({
        "CNPJ_NORMALIZADO": todos
    })

    relacionamento["TEM_SESI"] = (
        relacionamento["CNPJ_NORMALIZADO"]
        .isin(cnpjs_sesi)
    )

    relacionamento["TEM_SENAI"] = (
        relacionamento["CNPJ_NORMALIZADO"]
        .isin(cnpjs_senai)
    )

    relacionamento["TEM_SESI_SENAI"] = (
        relacionamento["TEM_SESI"]
        & relacionamento["TEM_SENAI"]
    )

    relacionamento["STATUS_RELACIONAMENTO"] = "SEM RELACIONAMENTO"

    relacionamento.loc[
        relacionamento["TEM_SESI"]
        & ~relacionamento["TEM_SENAI"],
        "STATUS_RELACIONAMENTO"
    ] = "SOMENTE SESI"

    relacionamento.loc[
        ~relacionamento["TEM_SESI"]
        & relacionamento["TEM_SENAI"],
        "STATUS_RELACIONAMENTO"
    ] = "SOMENTE SENAI"

    relacionamento.loc[
        relacionamento["TEM_SESI_SENAI"],
        "STATUS_RELACIONAMENTO"
    ] = "SESI + SENAI"

    return relacionamento


# ============================================================
# INÍCIO
# ============================================================

print("=" * 75)
print("CONSTRUÇÃO DA BASE MESTRE COMERCIAL")
print("=" * 75)


# ============================================================
# 1. CARREGAR MERCADO
# ============================================================

print("\n" + "=" * 75)
print("1. CARREGANDO BASE-MÃE")
print("=" * 75)

mercado = pd.read_excel(
    ARQ_MERCADO,
    engine="openpyxl"
)

print(
    f"\nEmpresas na base-mãe: {len(mercado):,}"
)

mercado["CNPJ_NORMALIZADO"] = normalizar_cnpj(
    mercado["cnpj"]
)

print(
    f"CNPJs únicos: "
    f"{mercado['CNPJ_NORMALIZADO'].nunique():,}"
)


# ------------------------------------------------------------
# CORREÇÃO DE UNIVERSO
#
# Empresas confirmadas via auditoria cruzada com a Receita
# Federal (ATIVA + registrada em Alagoas + CNAE de indústria
# de transformação) que a base-mãe original não capturou.
# Ver saida/AUDITORIA_GAP_REAL_CONFIRMADO.csv para a evidência
# de cada uma.
# ------------------------------------------------------------

if os.path.exists(ARQ_CORRECAO_UNIVERSO):

    correcao_universo = pd.read_csv(
        ARQ_CORRECAO_UNIVERSO,
        encoding="utf-8-sig"
    )

    correcao_universo["CNPJ_NORMALIZADO"] = normalizar_cnpj(
        correcao_universo["cnpj"]
    )

    correcao_universo = correcao_universo[
        ~correcao_universo["CNPJ_NORMALIZADO"].isin(
            mercado["CNPJ_NORMALIZADO"]
        )
    ]

    print(
        f"\nCorreção de universo aplicada: "
        f"{len(correcao_universo):,} empresas "
        f"(auditoria Receita Federal)"
    )

    mercado = pd.concat(
        [mercado, correcao_universo],
        ignore_index=True
    )


# ============================================================
# 2. CARREGAR RELACIONAMENTO SESI/SENAI
# ============================================================

print("\n" + "=" * 75)
print("2. CARREGANDO RELACIONAMENTO SESI/SENAI")
print("=" * 75)

relacionamento_original = pd.read_excel(
    ARQ_RELACIONAMENTO,
    engine="openpyxl"
)

print(
    f"\nRegistros da base: "
    f"{len(relacionamento_original):,}"
)

relacionamento = transformar_cnpj_relacionamento(
    relacionamento_original
)

print(
    f"CNPJs únicos de relacionamento: "
    f"{len(relacionamento):,}"
)

print(
    f"SESI: "
    f"{relacionamento['TEM_SESI'].sum():,}"
)

print(
    f"SENAI: "
    f"{relacionamento['TEM_SENAI'].sum():,}"
)

print(
    f"SESI + SENAI: "
    f"{relacionamento['TEM_SESI_SENAI'].sum():,}"
)


# ============================================================
# 3. CRUZAR MERCADO × RELACIONAMENTO
# ============================================================

print("\n" + "=" * 75)
print("3. CRUZANDO MERCADO × RELACIONAMENTO")
print("=" * 75)

base = mercado.merge(
    relacionamento,
    on="CNPJ_NORMALIZADO",
    how="left"
)

base["TEM_SESI"] = (
    base["TEM_SESI"]
    .fillna(False)
    .astype(bool)
)

base["TEM_SENAI"] = (
    base["TEM_SENAI"]
    .fillna(False)
    .astype(bool)
)

base["TEM_SESI_SENAI"] = (
    base["TEM_SESI_SENAI"]
    .fillna(False)
    .astype(bool)
)

base["STATUS_RELACIONAMENTO"] = (
    base["STATUS_RELACIONAMENTO"]
    .fillna("SEM RELACIONAMENTO")
)


# ============================================================
# 4. CARREGAR SEBRAE
# ============================================================

print("\n" + "=" * 75)
print("4. CARREGANDO BASE SEBRAE")
print("=" * 75)

sebrae = pd.read_excel(
    ARQ_SEBRAE,
    engine="openpyxl"
)

print(
    f"\nEmpresas SEBRAE: "
    f"{len(sebrae):,}"
)

coluna_cnpj_sebrae = encontrar_coluna(
    sebrae,
    nome_exato="cnpj"
)

if coluna_cnpj_sebrae is None:

    coluna_cnpj_sebrae = encontrar_coluna(
        sebrae,
        contem="cnpj"
    )

if coluna_cnpj_sebrae is None:

    raise ValueError(
        "CNPJ não encontrado na base SEBRAE."
    )

sebrae["CNPJ_NORMALIZADO"] = normalizar_cnpj(
    sebrae[coluna_cnpj_sebrae]
)


# ============================================================
# 5. VERIFICAR DUPLICIDADE SEBRAE
# ============================================================

print("\n" + "=" * 75)
print("5. AUDITORIA SEBRAE")
print("=" * 75)

duplicados_sebrae = (
    sebrae["CNPJ_NORMALIZADO"]
    .duplicated()
    .sum()
)

print(
    f"\nRegistros duplicados por CNPJ: "
    f"{duplicados_sebrae:,}"
)

if duplicados_sebrae > 0:

    print(
        "\nExistem CNPJs duplicados na base SEBRAE."
    )

    print(
        "Será mantido o primeiro registro por CNPJ."
    )

    sebrae = (
        sebrae
        .drop_duplicates(
            subset="CNPJ_NORMALIZADO",
            keep="first"
        )
    )


# ============================================================
# 6. PREPARAR COLUNAS SEBRAE
# ============================================================

print("\n" + "=" * 75)
print("6. PREPARANDO DADOS SEBRAE")
print("=" * 75)

colunas_sebrae = []

for coluna in sebrae.columns:

    if coluna == "CNPJ_NORMALIZADO":

        continue

    novo_nome = f"SEBRAE_{coluna}"

    sebrae = sebrae.rename(
        columns={
            coluna: novo_nome
        }
    )

    colunas_sebrae.append(
        novo_nome
    )


# ============================================================
# 7. CRUZAR BASE-MÃE × SEBRAE
# ============================================================

print("\n" + "=" * 75)
print("7. CRUZANDO BASE-MÃE × SEBRAE")
print("=" * 75)

base = base.merge(
    sebrae,
    on="CNPJ_NORMALIZADO",
    how="left"
)

# ------------------------------------------------------------
# Indicador de presença no SEBRAE
# ------------------------------------------------------------

coluna_razao_sebrae = None

for coluna in base.columns:

    if coluna == "SEBRAE_CNPJ_NORMALIZADO":

        continue

    if coluna.startswith("SEBRAE_"):

        if coluna.replace(
            "SEBRAE_",
            ""
        ).lower() == "razao_social":

            coluna_razao_sebrae = coluna

            break

if coluna_razao_sebrae:

    base["ENCONTRADO_SEBRAE"] = (
        base[coluna_razao_sebrae]
        .notna()
    )

else:

    # fallback: qualquer coluna SEBRAE preenchida
    colunas_verificacao = [
        c for c in base.columns
        if c.startswith("SEBRAE_")
    ]

    if colunas_verificacao:

        base["ENCONTRADO_SEBRAE"] = (
            base[colunas_verificacao]
            .notna()
            .any(axis=1)
        )

    else:

        base["ENCONTRADO_SEBRAE"] = False


# ============================================================
# 8. NORMALIZAR CAMPOS SEBRAE
# ============================================================

print("\n" + "=" * 75)
print("8. CAMPOS DE OPORTUNIDADE SEBRAE")
print("=" * 75)

coluna_elegibilidade = None
coluna_oportunidade = None

for coluna in base.columns:

    nome = coluna.lower()

    if (
        "elegivel" in nome
        or "elegível" in nome
    ):

        coluna_elegibilidade = coluna

    if "oportunidade_comercial" in nome:

        coluna_oportunidade = coluna


# ------------------------------------------------------------
# SEBRAE_ELEGIVEL
# ------------------------------------------------------------

if coluna_elegibilidade:

    base["SEBRAE_ELEGIVEL"] = (
        base[coluna_elegibilidade]
        .astype("string")
        .str.strip()
        .str.upper()
    )

else:

    base["SEBRAE_ELEGIVEL"] = pd.NA


# ------------------------------------------------------------
# SEBRAE_OPORTUNIDADE
# ------------------------------------------------------------

if coluna_oportunidade:

    base["SEBRAE_OPORTUNIDADE"] = (
        base[coluna_oportunidade]
        .astype("string")
        .str.strip()
        .str.upper()
    )

else:

    base["SEBRAE_OPORTUNIDADE"] = pd.NA


# ============================================================
# 9. CRIAR CLASSIFICAÇÕES COMERCIAIS
# ============================================================

print("\n" + "=" * 75)
print("9. CRIANDO CLASSIFICAÇÕES COMERCIAIS")
print("=" * 75)


# ------------------------------------------------------------
# OPORTUNIDADE SEBRAE
# ------------------------------------------------------------

base["OPORTUNIDADE_SEBRAE"] = "NÃO AVALIADA"

base.loc[
    (
        base["SEBRAE_ELEGIVEL"] == "SIM"
    )
    &
    (
        base["SEBRAE_OPORTUNIDADE"] == "NÃO ATENDIDA"
    ),
    "OPORTUNIDADE_SEBRAE"
] = "OPORTUNIDADE"


base.loc[
    (
        base["SEBRAE_ELEGIVEL"] == "NAO"
    )
    |
    (
        base["SEBRAE_ELEGIVEL"] == "NÃO"
    ),
    "OPORTUNIDADE_SEBRAE"
] = "FORA DO ESCOPO"


# ------------------------------------------------------------
# OPORTUNIDADE SESI
# ------------------------------------------------------------

base["OPORTUNIDADE_SESI"] = "NÃO"

base.loc[
    ~base["TEM_SESI"],
    "OPORTUNIDADE_SESI"
] = "SIM"


# ------------------------------------------------------------
# OPORTUNIDADE SENAI
# ------------------------------------------------------------

base["OPORTUNIDADE_SENAI"] = "NÃO"

base.loc[
    ~base["TEM_SENAI"],
    "OPORTUNIDADE_SENAI"
] = "SIM"


# ------------------------------------------------------------
# OPORTUNIDADE GERAL
# ------------------------------------------------------------

base["OPORTUNIDADE_GERAL"] = "SEM RELACIONAMENTO"

base.loc[
    (
        base["TEM_SESI"]
        | base["TEM_SENAI"]
    ),
    "OPORTUNIDADE_GERAL"
] = "CLIENTE"


base.loc[
    (
        ~base["TEM_SESI"]
        &
        ~base["TEM_SENAI"]
    ),
    "OPORTUNIDADE_GERAL"
] = "PROSPECT"


# ------------------------------------------------------------
# CROSS-SELL
# ------------------------------------------------------------

base["OPORTUNIDADE_CROSS_SELL"] = "NÃO"

base.loc[
    (
        base["TEM_SESI"]
        &
        ~base["TEM_SENAI"]
    ),
    "OPORTUNIDADE_CROSS_SELL"
] = "SENAI"


base.loc[
    (
        base["TEM_SENAI"]
        &
        ~base["TEM_SESI"]
    ),
    "OPORTUNIDADE_CROSS_SELL"
] = "SESI"


# ============================================================
# 10. RESUMO
# ============================================================

print("\n" + "=" * 75)
print("10. RESUMO COMERCIAL")
print("=" * 75)

print("\nUNIVERSO")

print(
    f"Empresas: "
    f"{len(base):,}"
)

print("\nRELACIONAMENTO")

print(
    f"SESI: "
    f"{base['TEM_SESI'].sum():,}"
)

print(
    f"SENAI: "
    f"{base['TEM_SENAI'].sum():,}"
)

print(
    f"SESI + SENAI: "
    f"{base['TEM_SESI_SENAI'].sum():,}"
)

print(
    f"Sem relacionamento: "
    f"{(
        ~base['TEM_SESI']
        &
        ~base['TEM_SENAI']
    ).sum():,}"
)


print("\nSTATUS RELACIONAMENTO")

print(
    base["STATUS_RELACIONAMENTO"]
    .value_counts()
    .to_string()
)


print("\nSEBRAE")

print(
    base["ENCONTRADO_SEBRAE"]
    .value_counts()
    .rename({
        True: "ENCONTRADA",
        False: "NÃO ENCONTRADA"
    })
    .to_string()
)


print("\nOPORTUNIDADE SEBRAE")

print(
    base["OPORTUNIDADE_SEBRAE"]
    .value_counts()
    .to_string()
)


print("\nOPORTUNIDADE CROSS-SELL")

print(
    base["OPORTUNIDADE_CROSS_SELL"]
    .value_counts()
    .to_string()
)


# ============================================================
# 11. MATRIZES COMERCIAIS
# ============================================================

print("\n" + "=" * 75)
print("11. MATRIZES COMERCIAIS")
print("=" * 75)


print("\nSEBRAE × RELACIONAMENTO")

print(
    pd.crosstab(
        base["STATUS_RELACIONAMENTO"],
        base["ENCONTRADO_SEBRAE"]
    )
)


print("\nSEBRAE × OPORTUNIDADE")

print(
    pd.crosstab(
        base["OPORTUNIDADE_SEBRAE"],
        base["STATUS_RELACIONAMENTO"]
    )
)


print("\nPORTE × RELACIONAMENTO")

print(
    pd.crosstab(
        base["Porte"],
        base["STATUS_RELACIONAMENTO"]
    )
)


print("\nSETOR × RELACIONAMENTO")

print(
    pd.crosstab(
        base["SETOR"],
        base["STATUS_RELACIONAMENTO"]
    )
)


# ============================================================
# 12. EXPORTAR BASE MESTRE
# ============================================================

print("\n" + "=" * 75)
print("12. EXPORTANDO BASE MESTRE")
print("=" * 75)

arquivo_saida = os.path.join(
    SAIDA,
    "BASE_MESTRE_COMERCIAL.csv"
)

base.to_csv(
    arquivo_saida,
    index=False,
    encoding="utf-8-sig"
)

print("\nArquivo criado:")

print(arquivo_saida)

print(
    f"\nLinhas exportadas: "
    f"{len(base):,}"
)

print(
    f"Colunas exportadas: "
    f"{len(base.columns):,}"
)


# ============================================================
# 13. EXPORTAR RESUMOS
# ============================================================

print("\n" + "=" * 75)
print("13. EXPORTANDO RESUMOS")
print("=" * 75)


# Status
resumo_status = (
    base["STATUS_RELACIONAMENTO"]
    .value_counts()
    .rename_axis("STATUS_RELACIONAMENTO")
    .reset_index(name="EMPRESAS")
)

resumo_status.to_csv(
    os.path.join(
        SAIDA,
        "MESTRE_RESUMO_RELACIONAMENTO.csv"
    ),
    index=False,
    encoding="utf-8-sig"
)


# SEBRAE
resumo_sebrae = (
    base["OPORTUNIDADE_SEBRAE"]
    .value_counts()
    .rename_axis("OPORTUNIDADE_SEBRAE")
    .reset_index(name="EMPRESAS")
)

resumo_sebrae.to_csv(
    os.path.join(
        SAIDA,
        "MESTRE_RESUMO_SEBRAE.csv"
    ),
    index=False,
    encoding="utf-8-sig"
)


# Município
resumo_municipio = (
    base.groupby(
        "Municipio",
        dropna=False
    )
    .agg(
        EMPRESAS=("CNPJ_NORMALIZADO", "nunique"),
        CLIENTES_SESI=(
            "TEM_SESI",
            "sum"
        ),
        CLIENTES_SENAI=(
            "TEM_SENAI",
            "sum"
        ),
        SEM_RELACIONAMENTO=(
            "STATUS_RELACIONAMENTO",
            lambda x: (
                x == "SEM RELACIONAMENTO"
            ).sum()
        ),
        OPORTUNIDADE_SEBRAE=(
            "OPORTUNIDADE_SEBRAE",
            lambda x: (
                x == "OPORTUNIDADE"
            ).sum()
        )
    )
    .reset_index()
    .sort_values(
        "EMPRESAS",
        ascending=False
    )
)

resumo_municipio.to_csv(
    os.path.join(
        SAIDA,
        "MESTRE_RESUMO_MUNICIPIO.csv"
    ),
    index=False,
    encoding="utf-8-sig"
)


# Porte
resumo_porte = (
    base.groupby(
        "Porte",
        dropna=False
    )
    .agg(
        EMPRESAS=("CNPJ_NORMALIZADO", "nunique"),
        SESI=("TEM_SESI", "sum"),
        SENAI=("TEM_SENAI", "sum"),
        SEM_RELACIONAMENTO=(
            "STATUS_RELACIONAMENTO",
            lambda x: (
                x == "SEM RELACIONAMENTO"
            ).sum()
        ),
        OPORTUNIDADE_SEBRAE=(
            "OPORTUNIDADE_SEBRAE",
            lambda x: (
                x == "OPORTUNIDADE"
            ).sum()
        )
    )
    .reset_index()
    .sort_values(
        "EMPRESAS",
        ascending=False
    )
)

resumo_porte.to_csv(
    os.path.join(
        SAIDA,
        "MESTRE_RESUMO_PORTE.csv"
    ),
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 14. VALIDAÇÃO FINAL
# ============================================================

print("\n" + "=" * 75)
print("14. VALIDAÇÃO FINAL")
print("=" * 75)

print(
    f"\nBase-mãe original: "
    f"{len(mercado):,}"
)

print(
    f"Base mestre:       "
    f"{len(base):,}"
)

print(
    f"CNPJs únicos mestre: "
    f"{base['CNPJ_NORMALIZADO'].nunique():,}"
)

if (
    len(base) == len(mercado)
    and
    base["CNPJ_NORMALIZADO"].nunique()
    == len(mercado)
):

    print(
        "\n✓ VALIDAÇÃO OK"
    )

    print(
        "A BASE MESTRE mantém 1 linha por CNPJ."
    )

else:

    print(
        "\n⚠ ATENÇÃO"
    )

    print(
        "A quantidade de linhas/CNPJs mudou."
    )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 75)
print("BASE MESTRE COMERCIAL CONCLUÍDA")
print("=" * 75)

print("""
Próxima etapa:

1. Auditar a BASE_MESTRE_COMERCIAL
2. Medir penetração SESI/SENAI
3. Mapear oportunidades SEBRAE
4. Mapear mercado sem relacionamento
5. Criar visão por:
   - Município
   - Porte
   - CNAE
   - Setor
6. Depois construir o dashboard comercial

Ainda NÃO vamos trabalhar com portfólio,
upsell, cross-sell avançado ou IA.

Primeiro vamos entender o mercado.
""")

print("=" * 75)