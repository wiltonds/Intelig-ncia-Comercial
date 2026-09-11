import pandas as pd
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA = Path(".")

ARQUIVO_N_RELACIONAMENTO = (
    PASTA / "BASE_DADOS_SESI&SENAI_N_RELACIONAMENTO.xlsx"
)

ARQUIVO_RELACIONAMENTO = (
    PASTA / "relacionamento_SESI&SENAI.xlsx"
)

ARQUIVO_SAIDA = (
    PASTA / "BASE_CONSOLIDADA_SESI_SENAI.xlsx"
)


# ============================================================
# FUNÇÃO - PADRONIZAR CNPJ
# ============================================================

def padronizar_cnpj(df):

    df = df.copy()

    df["CNPJ"] = (
        df["CNPJ"]
        .astype(str)
        .str.replace(r"\D", "", regex=True)
        .str.zfill(14)
    )

    return df


# ============================================================
# 1. CARREGAR BASES
# ============================================================

df_n = pd.read_excel(
    ARQUIVO_N_RELACIONAMENTO
)

df_rel = pd.read_excel(
    ARQUIVO_RELACIONAMENTO
)

print("\nBASES CARREGADAS")
print("-" * 60)

print("Sem relacionamento:", len(df_n))
print("Com relacionamento:", len(df_rel))


# ============================================================
# 2. PADRONIZAR CNPJ
# ============================================================

df_n = padronizar_cnpj(df_n)
df_rel = padronizar_cnpj(df_rel)


# ============================================================
# 3. REMOVER DUPLICIDADES
# ============================================================

duplicados_n = df_n["CNPJ"].duplicated().sum()
duplicados_rel = df_rel["CNPJ"].duplicated().sum()

print("\nDUPLICIDADES")
print("-" * 60)

print("Duplicados - sem relacionamento:", duplicados_n)
print("Duplicados - relacionamento:", duplicados_rel)

df_n = df_n.drop_duplicates(
    subset="CNPJ",
    keep="first"
)

df_rel = df_rel.drop_duplicates(
    subset="CNPJ",
    keep="first"
)


# ============================================================
# 4. CRIAR INDICADOR DE RELACIONAMENTO
# ============================================================

cnpjs_relacionamento = set(
    df_rel["CNPJ"]
)

df_n["TEM_RELACIONAMENTO"] = (
    df_n["CNPJ"].isin(cnpjs_relacionamento)
)


# ============================================================
# 5. SEPARAR RELACIONAMENTO SESI E SENAI
# ============================================================

df_rel["TEM_SESI"] = False
df_rel["TEM_SENAI"] = False

# COBERTURA SESI
df_rel.loc[
    df_rel["COBERTURA"]
    .astype(str)
    .str.upper()
    .str.contains("SESI", na=False),
    "TEM_SESI"
] = True

# SENAI preenchido
df_rel.loc[
    df_rel["SENAI"].notna()
    & (df_rel["SENAI"] != 0),
    "TEM_SENAI"
] = True


# ============================================================
# 6. CONSOLIDAR
# ============================================================

# Mantemos a base principal sem relacionamento
# e adicionamos os indicadores encontrados
# na base de relacionamento.

df_consolidado = df_n.merge(
    df_rel[
        [
            "CNPJ",
            "TEM_SESI",
            "TEM_SENAI"
        ]
    ],
    on="CNPJ",
    how="left"
)


# ============================================================
# 7. TRATAR NULOS
# ============================================================

df_consolidado["TEM_SESI"] = (
    df_consolidado["TEM_SESI"]
    .fillna(False)
    .astype(bool)
)

df_consolidado["TEM_SENAI"] = (
    df_consolidado["TEM_SENAI"]
    .fillna(False)
    .astype(bool)
)


# ============================================================
# 8. STATUS DE RELACIONAMENTO
# ============================================================

def classificar_relacionamento(row):

    sesi = row["TEM_SESI"]
    senai = row["TEM_SENAI"]

    if sesi and senai:
        return "SESI + SENAI"

    elif sesi:
        return "SESI"

    elif senai:
        return "SENAI"

    else:
        return "SEM RELACIONAMENTO"


df_consolidado["STATUS_RELACIONAMENTO"] = (
    df_consolidado.apply(
        classificar_relacionamento,
        axis=1
    )
)


# ============================================================
# 9. EXPORTAR
# ============================================================

df_consolidado.to_excel(
    ARQUIVO_SAIDA,
    index=False
)


# ============================================================
# 10. AUDITORIA
# ============================================================

print("\n" + "=" * 60)
print("RESULTADO FINAL")
print("=" * 60)

print(
    "Total de empresas:",
    len(df_consolidado)
)

print(
    "\nStatus de relacionamento:"
)

print(
    df_consolidado[
        "STATUS_RELACIONAMENTO"
    ].value_counts()
)

print(
    "\nSESI:",
    df_consolidado["TEM_SESI"].sum()
)

print(
    "SENAI:",
    df_consolidado["TEM_SENAI"].sum()
)

print(
    "\nArquivo gerado:"
)

print(
    ARQUIVO_SAIDA.resolve()
)
print("\n" + "=" * 60)
print("AUDITORIA DA BASE DE RELACIONAMENTO")
print("=" * 60)

print("\nCOBERTURA:")
print(df_rel["COBERTURA"].value_counts(dropna=False))

print("\nSENAI PREENCHIDO:")
print(df_rel["SENAI"].notna().value_counts(dropna=False))

print("\nSENAI = 0:")
print((df_rel["SENAI"] == 0).value_counts(dropna=False))

print("\nPRIMEIRAS LINHAS:")
print(
    df_rel[
        ["CNPJ", "COBERTURA", "SENAI"]
    ].head(20).to_string(index=False)
)