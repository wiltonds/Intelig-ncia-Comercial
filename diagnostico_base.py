import os
import pandas as pd

# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA = r"C:\Users\wilton.costa\Desktop\projeto_comercial"

ARQ_BASE = os.path.join(
    PASTA,
    "BASE_DADOS_SESI&SENAI_N_RELACIONAMENTO.xlsx"
)

ARQ_REL = os.path.join(
    PASTA,
    "relacionamento_SESI&SENAI.xlsx"
)

SAIDA = os.path.join(PASTA, "saida")

os.makedirs(SAIDA, exist_ok=True)


# ============================================================
# FUNÇÕES
# ============================================================

def normalizar_cnpj(series):

    s = series.astype("string").str.strip()

    # Remove .0 criado pelo Excel
    s = s.str.replace(r"\.0$", "", regex=True)

    # Mantém somente números
    s = s.str.replace(r"\D", "", regex=True)

    # Garante 14 dígitos
    s = s.str.zfill(14)

    return s


def valores_unicos(series):

    valores = []

    for valor in series.dropna():

        valor = str(valor).strip()

        if valor and valor not in valores:
            valores.append(valor)

    return " | ".join(sorted(valores))


# ============================================================
# 1. CARREGAR BASES
# ============================================================

print("\n" + "=" * 70)
print("CARREGANDO BASES")
print("=" * 70)

df_base = pd.read_excel(ARQ_BASE)
df_rel = pd.read_excel(ARQ_REL)

df_base["CNPJ"] = normalizar_cnpj(df_base["CNPJ"])
df_rel["CNPJ"] = normalizar_cnpj(df_rel["CNPJ"])

print(f"\nBase principal: {len(df_base):,} registros")
print(f"Relacionamento: {len(df_rel):,} registros")


# ============================================================
# 2. ENTENDER A COBERTURA ORIGINAL
# ============================================================

print("\n" + "=" * 70)
print("COBERTURA DA BASE PRINCIPAL")
print("=" * 70)

print(
    df_base["COBERTURA"]
    .value_counts(dropna=False)
)


# ============================================================
# 3. IDENTIFICAR SESI E SENAI POR CNPJ
# ============================================================

df_base["COBERTURA_NORM"] = (
    df_base["COBERTURA"]
    .fillna("")
    .astype(str)
    .str.upper()
    .str.strip()
)

# ============================================================
# CNPJs atendidos por SESI
# ============================================================

cnpjs_sesi = set(
    df_base.loc[
        df_base["COBERTURA_NORM"].str.contains("SESI", na=False),
        "CNPJ"
    ]
)

# ============================================================
# CNPJs atendidos por SENAI
# ============================================================

cnpjs_senai = set(
    df_base.loc[
        df_base["COBERTURA_NORM"].str.contains("SENAI", na=False),
        "CNPJ"
    ]
)


# ============================================================
# 4. RELACIONAMENTO SESI + SENAI COMPROVADO
# ============================================================

cnpjs_sesi_senai = set(df_rel["CNPJ"])


# ============================================================
# 5. CRIAR UNIVERSO DE EMPRESAS ÚNICAS
# ============================================================

print("\n" + "=" * 70)
print("CONSTRUINDO UNIVERSO DE EMPRESAS")
print("=" * 70)

agrupamento = {
    "Razão Social": "first",
    "Categoria": valores_unicos,
    "Porte": valores_unicos,
    "CNAE": valores_unicos,
    "Origem da Cobertura": valores_unicos,
}

df_empresas = (
    df_base
    .groupby("CNPJ", as_index=False)
    .agg(agrupamento)
)


# ============================================================
# 6. FLAGS INDEPENDENTES
# ============================================================

df_empresas["TEM_SESI"] = (
    df_empresas["CNPJ"].isin(cnpjs_sesi)
)

df_empresas["TEM_SENAI"] = (
    df_empresas["CNPJ"].isin(cnpjs_senai)
)

df_empresas["TEM_SESI_SENAI"] = (
    df_empresas["CNPJ"].isin(cnpjs_sesi_senai)
)


# ============================================================
# 7. STATUS EXCLUSIVO
# ============================================================

def classificar_status(row):

    sesi = row["TEM_SESI"]
    senai = row["TEM_SENAI"]

    if sesi and senai:
        return "SESI + SENAI"

    elif sesi:
        return "SOMENTE SESI"

    elif senai:
        return "SOMENTE SENAI"

    else:
        return "SEM RELACIONAMENTO"


df_empresas["STATUS_RELACIONAMENTO"] = (
    df_empresas.apply(classificar_status, axis=1)
)


# ============================================================
# 8. QUANTIDADE DE REGISTROS NA BASE ORIGINAL
# ============================================================

qtd_registros = (
    df_base
    .groupby("CNPJ")
    .size()
    .reset_index(
        name="QTD_REGISTROS_BASE"
    )
)

df_empresas = df_empresas.merge(
    qtd_registros,
    on="CNPJ",
    how="left"
)


# ============================================================
# 9. AUDITORIA MATEMÁTICA
# ============================================================

total_empresas = len(df_empresas)

total_sesi = df_empresas["TEM_SESI"].sum()
total_senai = df_empresas["TEM_SENAI"].sum()
total_duplo = df_empresas["TEM_SESI_SENAI"].sum()

somente_sesi = (
    (df_empresas["TEM_SESI"]) &
    (~df_empresas["TEM_SENAI"])
).sum()

somente_senai = (
    (~df_empresas["TEM_SESI"]) &
    (df_empresas["TEM_SENAI"])
).sum()

sem_relacionamento = (
    (~df_empresas["TEM_SESI"]) &
    (~df_empresas["TEM_SENAI"])
).sum()


print("\n" + "=" * 70)
print("VISÃO DE CARTEIRA")
print("=" * 70)

print(f"\nSESI:             {total_sesi:,}")
print(f"SENAI:            {total_senai:,}")
print(f"SESI + SENAI:     {total_duplo:,}")


print("\n" + "=" * 70)
print("VISÃO DE EMPRESAS ÚNICAS")
print("=" * 70)

print(f"\nTotal empresas:   {total_empresas:,}")
print(f"Somente SESI:     {somente_sesi:,}")
print(f"Somente SENAI:    {somente_senai:,}")
print(f"SESI + SENAI:     {total_duplo:,}")
print(f"Sem relacionamento: {sem_relacionamento:,}")


# ============================================================
# 10. VALIDAÇÃO
# ============================================================

print("\n" + "=" * 70)
print("VALIDAÇÃO")
print("=" * 70)

print(
    f"\nSESI: "
    f"{somente_sesi:,} + {total_duplo:,} "
    f"= {somente_sesi + total_duplo:,}"
)

print(
    f"SENAI: "
    f"{somente_senai:,} + {total_duplo:,} "
    f"= {somente_senai + total_duplo:,}"
)

print(
    f"\nEmpresas únicas: "
    f"{somente_sesi:,} + "
    f"{somente_senai:,} + "
    f"{total_duplo:,} + "
    f"{sem_relacionamento:,} "
    f"= {total_empresas:,}"
)


# ============================================================
# 11. EXPORTAR BASE PRINCIPAL ANALÍTICA
# ============================================================

arquivo_empresas = os.path.join(
    SAIDA,
    "BASE_EMPRESAS_ANALITICA.csv"
)

df_empresas.to_csv(
    arquivo_empresas,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 12. EXPORTAR VISÃO SESI
# ============================================================

df_sesi = df_empresas[
    df_empresas["TEM_SESI"]
].copy()

df_sesi.to_csv(
    os.path.join(
        SAIDA,
        "CARTEIRA_SESI.csv"
    ),
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 13. EXPORTAR VISÃO SENAI
# ============================================================

df_senai = df_empresas[
    df_empresas["TEM_SENAI"]
].copy()

df_senai.to_csv(
    os.path.join(
        SAIDA,
        "CARTEIRA_SENAI.csv"
    ),
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 14. EXPORTAR DUPLO RELACIONAMENTO
# ============================================================

df_duplo = df_empresas[
    df_empresas["TEM_SESI_SENAI"]
].copy()

df_duplo.to_csv(
    os.path.join(
        SAIDA,
        "CARTEIRA_SESI_SENAI.csv"
    ),
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 15. RESUMO POR STATUS
# ============================================================

resumo_status = (
    df_empresas[
        "STATUS_RELACIONAMENTO"
    ]
    .value_counts()
    .reset_index()
)

resumo_status.columns = [
    "STATUS_RELACIONAMENTO",
    "QUANTIDADE"
]

resumo_status.to_csv(
    os.path.join(
        SAIDA,
        "RESUMO_STATUS.csv"
    ),
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 16. RESUMO POR CATEGORIA
# ============================================================

if "Categoria" in df_empresas.columns:

    resumo_categoria = (
        df_empresas
        .groupby(
            [
                "Categoria",
                "STATUS_RELACIONAMENTO"
            ],
            dropna=False
        )
        .size()
        .reset_index(
            name="QUANTIDADE"
        )
    )

    resumo_categoria.to_csv(
        os.path.join(
            SAIDA,
            "RESUMO_CATEGORIA.csv"
        ),
        index=False,
        encoding="utf-8-sig"
    )


# ============================================================
# 17. RESUMO POR PORTE
# ============================================================

if "Porte" in df_empresas.columns:

    resumo_porte = (
        df_empresas
        .groupby(
            [
                "Porte",
                "STATUS_RELACIONAMENTO"
            ],
            dropna=False
        )
        .size()
        .reset_index(
            name="QUANTIDADE"
        )
    )

    resumo_porte.to_csv(
        os.path.join(
            SAIDA,
            "RESUMO_PORTE.csv"
        ),
        index=False,
        encoding="utf-8-sig"
    )


# ============================================================
# 18. RESUMO POR CNAE
# ============================================================

if "CNAE" in df_empresas.columns:

    resumo_cnae = (
        df_empresas
        .groupby(
            [
                "CNAE",
                "STATUS_RELACIONAMENTO"
            ],
            dropna=False
        )
        .size()
        .reset_index(
            name="QUANTIDADE"
        )
        .sort_values(
            "QUANTIDADE",
            ascending=False
        )
    )

    resumo_cnae.to_csv(
        os.path.join(
            SAIDA,
            "RESUMO_CNAE.csv"
        ),
        index=False,
        encoding="utf-8-sig"
    )


# ============================================================
# 19. FINAL
# ============================================================

print("\n" + "=" * 70)
print("ARQUIVOS GERADOS")
print("=" * 70)

print(f"\nPasta: {SAIDA}")

print("\nBASE_EMPRESAS_ANALITICA.csv")
print("CARTEIRA_SESI.csv")
print("CARTEIRA_SENAI.csv")
print("CARTEIRA_SESI_SENAI.csv")
print("RESUMO_STATUS.csv")
print("RESUMO_CATEGORIA.csv")
print("RESUMO_PORTE.csv")
print("RESUMO_CNAE.csv")

print("\n" + "=" * 70)
print("MODELO CORRETO")
print("=" * 70)

print("""
SESI  = carteira SESI
SENAI = carteira SENAI

Os 163 CNPJs duplos pertencem às DUAS carteiras.

Não são duplicatas para eliminar.

Na visão de empresa única:
    SOMENTE SESI
    SOMENTE SENAI
    SESI + SENAI
    SEM RELACIONAMENTO
""")