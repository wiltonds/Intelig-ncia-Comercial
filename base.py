import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA = Path(".")

ARQUIVO_BASE = (
    PASTA / "BASE_DADOS_SESI&SENAI_N_RELACIONAMENTO.xlsx"
)

ARQUIVO_RELACIONAMENTO = (
    PASTA / "relacionamento_SESI&SENAI.xlsx"
)

ARQUIVO_SAIDA = (
    PASTA / "BASE_CONSOLIDADA_SESI_SENAI.xlsx"
)


# ============================================================
# FUNÇÃO — PADRONIZAR CNPJ
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

df_base = pd.read_excel(
    ARQUIVO_BASE
)

df_rel = pd.read_excel(
    ARQUIVO_RELACIONAMENTO
)


# ============================================================
# 2. PADRONIZAR CNPJ
# ============================================================

df_base = padronizar_cnpj(df_base)
df_rel = padronizar_cnpj(df_rel)


# ============================================================
# 3. AUDITORIA
# ============================================================

print("\n" + "=" * 70)
print("AUDITORIA INICIAL")
print("=" * 70)

print(f"Base geral: {len(df_base):,}")
print(f"Relacionamento SESI: {len(df_rel):,}")


# ============================================================
# 4. VERIFICAR DUPLICIDADES
# ============================================================

duplicados_base = df_base["CNPJ"].duplicated().sum()
duplicados_rel = df_rel["CNPJ"].duplicated().sum()

print("\nDUPLICIDADES")
print("-" * 70)

print(f"Base geral: {duplicados_base}")
print(f"Relacionamento: {duplicados_rel}")


# ============================================================
# 5. VALIDAR RELACIONAMENTO
# ============================================================

cnpjs_sesi = set(
    df_rel["CNPJ"]
)


df_base["TEM_RELACIONAMENTO_SESI"] = (
    df_base["CNPJ"].isin(cnpjs_sesi)
)


# ============================================================
# 6. CLASSIFICAR STATUS
# ============================================================

df_base["STATUS_RELACIONAMENTO"] = "SEM RELACIONAMENTO"

df_base.loc[
    df_base["TEM_RELACIONAMENTO_SESI"],
    "STATUS_RELACIONAMENTO"
] = "SESI"


# ============================================================
# 7. VALIDAR CRUZAMENTO
# ============================================================

total_sesi = (
    df_base["TEM_RELACIONAMENTO_SESI"].sum()
)

total_sem_relacionamento = (
    (~df_base["TEM_RELACIONAMENTO_SESI"]).sum()
)


# ============================================================
# 8. EXPORTAR
# ============================================================

df_base.to_excel(
    ARQUIVO_SAIDA,
    index=False
)


# ============================================================
# 9. RESULTADO
# ============================================================

print("\n" + "=" * 70)
print("RESULTADO FINAL")
print("=" * 70)

print(
    f"Total de empresas: {len(df_base):,}"
)

print(
    f"Com relacionamento SESI: {total_sesi:,}"
)

print(
    f"Sem relacionamento SESI: {total_sem_relacionamento:,}"
)

print("\nSTATUS:")

print(
    df_base["STATUS_RELACIONAMENTO"]
    .value_counts()
)

print("\nArquivo gerado:")

print(
    ARQUIVO_SAIDA.resolve()
)