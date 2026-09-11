import os
import pandas as pd

# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA = r"C:\Users\wilton.costa\Desktop\projeto_comercial"

ARQ_EMPRESAS = os.path.join(
    PASTA,
    "saida",
    "BASE_EMPRESAS_ANALITICA.csv"
)

ARQ_SEBRAE = os.path.join(
    PASTA,
    "industrias_ativas_sebrae.xlsx"
)

SAIDA = os.path.join(
    PASTA,
    "saida"
)

os.makedirs(SAIDA, exist_ok=True)


# ============================================================
# FUNÇÃO CNPJ
# ============================================================

def normalizar_cnpj(series):

    s = series.astype("string").str.strip()

    # Remove .0 caso tenha vindo do Excel
    s = s.str.replace(r"\.0$", "", regex=True)

    # Remove caracteres não numéricos
    s = s.str.replace(r"\D", "", regex=True)

    # Completa para 14 posições
    s = s.str.zfill(14)

    return s


# ============================================================
# CARREGAR BASES
# ============================================================

print("\n" + "=" * 70)
print("CARREGANDO BASES")
print("=" * 70)

df_empresas = pd.read_csv(
    ARQ_EMPRESAS,
    dtype={"CNPJ": "string"}
)

df_sebrae = pd.read_excel(
    ARQ_SEBRAE,
    dtype={"cnpj": "string"}
)

print(f"\nEmpresas SESI/SENAI: {len(df_empresas):,}")
print(f"Empresas SEBRAE:     {len(df_sebrae):,}")


# ============================================================
# NORMALIZAR CNPJ
# ============================================================

df_empresas["CNPJ"] = normalizar_cnpj(
    df_empresas["CNPJ"]
)

df_sebrae["cnpj"] = normalizar_cnpj(
    df_sebrae["cnpj"]
)


# ============================================================
# AUDITORIA DOS CNPJs
# ============================================================

print("\n" + "=" * 70)
print("AUDITORIA CNPJ")
print("=" * 70)

print(
    f"\nCNPJs únicos nossa base: "
    f"{df_empresas['CNPJ'].nunique():,}"
)

print(
    f"CNPJs únicos SEBRAE: "
    f"{df_sebrae['cnpj'].nunique():,}"
)


# ============================================================
# VERIFICAR DUPLICIDADES SEBRAE
# ============================================================

duplicados_sebrae = (
    df_sebrae["cnpj"]
    .duplicated(keep=False)
)

print(
    f"\nRegistros SEBRAE pertencentes "
    f"a CNPJs duplicados: "
    f"{duplicados_sebrae.sum():,}"
)

print(
    f"CNPJs SEBRAE duplicados: "
    f"{df_sebrae.loc[duplicados_sebrae, 'cnpj'].nunique():,}"
)


# ============================================================
# PREPARAR BASE SEBRAE
# ============================================================

# Vamos verificar se existe mais de um registro por CNPJ.
# Por enquanto, mantemos o primeiro registro para o cruzamento.

df_sebrae_unico = (
    df_sebrae
    .drop_duplicates(
        subset="cnpj",
        keep="first"
    )
    .copy()
)


# ============================================================
# RENOMEAR CNPJ SEBRAE
# ============================================================

df_sebrae_unico = df_sebrae_unico.rename(
    columns={
        "cnpj": "CNPJ"
    }
)


# ============================================================
# EVITAR COLISÃO DE NOMES
# ============================================================

colunas_sebrae = [
    "CNPJ",
    "situacao_atual",
    "razao_social",
    "SETOR",
    "CNAE PRIMARIO",
    "Porte",
    "Municipio",
    "SESI",
    "SENAI",
    "cnae_codigo_recuperado",
    "cnae_norm",
    "cnae_divisao",
    "secao",
    "setor",
    "subsetor",
    "e_industria",
    "auditoria",
    "elegivel_sebrae",
    "oportunidade_comercial"
]

# Manter somente as colunas existentes
colunas_sebrae = [
    c for c in colunas_sebrae
    if c in df_sebrae_unico.columns
]

df_sebrae_unico = df_sebrae_unico[
    colunas_sebrae
]


# ============================================================
# PREFIXAR COLUNAS SEBRAE
# ============================================================

colunas_para_prefixar = [
    c for c in df_sebrae_unico.columns
    if c != "CNPJ"
]

df_sebrae_unico = df_sebrae_unico.rename(
    columns={
        c: f"SEBRAE_{c}"
        for c in colunas_para_prefixar
    }
)


# ============================================================
# CRUZAMENTO
# ============================================================

print("\n" + "=" * 70)
print("CRUZANDO CNPJs")
print("=" * 70)

df_final = df_empresas.merge(
    df_sebrae_unico,
    on="CNPJ",
    how="left",
    indicator=True
)


# ============================================================
# CLASSIFICAR PRESENÇA NO SEBRAE
# ============================================================

df_final["ENCONTRADO_SEBRAE"] = (
    df_final["_merge"] == "both"
)


df_final = df_final.drop(
    columns=["_merge"]
)


# ============================================================
# RESULTADOS DO CRUZAMENTO
# ============================================================

total = len(df_final)

encontrados = (
    df_final["ENCONTRADO_SEBRAE"].sum()
)

nao_encontrados = total - encontrados


print(f"\nEmpresas analisadas: {total:,}")
print(f"Encontradas SEBRAE:  {encontrados:,}")
print(f"Não encontradas:     {nao_encontrados:,}")


# ============================================================
# PERCENTUAL
# ============================================================

percentual = (
    encontrados / total * 100
    if total > 0
    else 0
)

print(
    f"\nCobertura SEBRAE sobre nossa base: "
    f"{percentual:.2f}%"
)


# ============================================================
# CRUZAR COM RELACIONAMENTO
# ============================================================

print("\n" + "=" * 70)
print("SEBRAE × RELACIONAMENTO")
print("=" * 70)

if "STATUS_RELACIONAMENTO" in df_final.columns:

    tabela = pd.crosstab(
        df_final["STATUS_RELACIONAMENTO"],
        df_final["ENCONTRADO_SEBRAE"]
    )

    print("\n")
    print(tabela)


# ============================================================
# SEBRAE × SESI
# ============================================================

print("\n" + "=" * 70)
print("SEBRAE × SESI")
print("=" * 70)

if "TEM_SESI" in df_final.columns:

    tabela_sesi = pd.crosstab(
        df_final["TEM_SESI"],
        df_final["ENCONTRADO_SEBRAE"]
    )

    print(tabela_sesi)


# ============================================================
# SEBRAE × SENAI
# ============================================================

print("\n" + "=" * 70)
print("SEBRAE × SENAI")
print("=" * 70)

if "TEM_SENAI" in df_final.columns:

    tabela_senai = pd.crosstab(
        df_final["TEM_SENAI"],
        df_final["ENCONTRADO_SEBRAE"]
    )

    print(tabela_senai)


# ============================================================
# ELEGIBILIDADE SEBRAE
# ============================================================

coluna_elegivel = "SEBRAE_elegivel_sebrae"

if coluna_elegivel in df_final.columns:

    print("\n" + "=" * 70)
    print("ELEGIBILIDADE SEBRAE")
    print("=" * 70)

    print(
        df_final[
            coluna_elegivel
        ]
        .value_counts(
            dropna=False
        )
    )


# ============================================================
# OPORTUNIDADE COMERCIAL
# ============================================================

coluna_oportunidade = (
    "SEBRAE_oportunidade_comercial"
)

if coluna_oportunidade in df_final.columns:

    print("\n" + "=" * 70)
    print("OPORTUNIDADE COMERCIAL SEBRAE")
    print("=" * 70)

    print(
        df_final[
            coluna_oportunidade
        ]
        .value_counts(
            dropna=False
        )
    )


# ============================================================
# EXPORTAR
# ============================================================

arquivo_final = os.path.join(
    SAIDA,
    "BASE_ANALITICA_SESI_SENAI_SEBRAE.csv"
)

df_final.to_csv(
    arquivo_final,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# EXPORTAR EMPRESAS NÃO ENCONTRADAS
# ============================================================

df_nao_sebrae = df_final[
    ~df_final["ENCONTRADO_SEBRAE"]
].copy()

df_nao_sebrae.to_csv(
    os.path.join(
        SAIDA,
        "EMPRESAS_NAO_ENCONTRADAS_SEBRAE.csv"
    ),
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# EXPORTAR EMPRESAS ENCONTRADAS
# ============================================================

df_com_sebrae = df_final[
    df_final["ENCONTRADO_SEBRAE"]
].copy()

df_com_sebrae.to_csv(
    os.path.join(
        SAIDA,
        "EMPRESAS_ENCONTRADAS_SEBRAE.csv"
    ),
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("CONCLUÍDO")
print("=" * 70)

print(f"\nArquivo principal:")
print(arquivo_final)

print("\nArquivos adicionais:")
print("EMPRESAS_NAO_ENCONTRADAS_SEBRAE.csv")
print("EMPRESAS_ENCONTRADAS_SEBRAE.csv")