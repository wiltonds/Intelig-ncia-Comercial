import pandas as pd
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA = Path(r"C:\Users\wilton.costa\Desktop\projeto_comercial")
SAIDA = PASTA / "saida"

ARQ_MESTRE = SAIDA / "BASE_MESTRE_COMERCIAL.csv"
ARQ_RELACIONAMENTO = PASTA / "BASE_DADOS_SESI&SENAI_N_RELACIONAMENTO.xlsx"
ARQ_SEBRAE = PASTA / "industrias_ativas_sebrae.xlsx"
ARQ_BASE_MAE = PASTA / "industrias_ativas.xlsx"


# ============================================================
# FUNÇÕES
# ============================================================

def normalizar_cnpj(valor):
    """
    Normaliza CNPJ para comparação.
    """
    if pd.isna(valor):
        return None

    s = str(valor).strip()

    # Trata valores vindos como float
    if s.endswith(".0"):
        s = s[:-2]

    # Mantém somente números
    s = "".join(c for c in s if c.isdigit())

    if not s:
        return None

    return s.zfill(14)


def carregar_cnpjs_excel(caminho, coluna):
    df = pd.read_excel(caminho)

    if coluna not in df.columns:
        raise ValueError(
            f"Coluna '{coluna}' não encontrada em {caminho.name}.\n"
            f"Colunas disponíveis: {list(df.columns)}"
        )

    df["CNPJ_NORMALIZADO"] = df[coluna].apply(normalizar_cnpj)

    return df


# ============================================================
# INÍCIO
# ============================================================

print("=" * 75)
print("AUDITORIA DE INTEGRIDADE DA BASE MESTRE")
print("=" * 75)


# ============================================================
# 1. BASE-MÃE
# ============================================================

print("\n" + "=" * 75)
print("1. BASE-MÃE")
print("=" * 75)

base_mae = carregar_cnpjs_excel(
    ARQ_BASE_MAE,
    "cnpj"
)

cnpjs_mae = set(
    base_mae["CNPJ_NORMALIZADO"]
    .dropna()
)

print(f"Empresas: {len(base_mae):,}")
print(f"CNPJs únicos: {len(cnpjs_mae):,}")


# ============================================================
# 2. BASE OFICIAL DE RELACIONAMENTO
# ============================================================

print("\n" + "=" * 75)
print("2. RELACIONAMENTO SESI/SENAI")
print("=" * 75)

rel = pd.read_excel(ARQ_RELACIONAMENTO)

rel["CNPJ_NORMALIZADO"] = rel["CNPJ"].apply(normalizar_cnpj)

cnpjs_rel = set(
    rel["CNPJ_NORMALIZADO"]
    .dropna()
)

print(f"Registros: {len(rel):,}")
print(f"CNPJs únicos: {len(cnpjs_rel):,}")


# ============================================================
# 3. RELACIONAMENTO × BASE-MÃE
# ============================================================

print("\n" + "=" * 75)
print("3. RELACIONAMENTO OFICIAL × BASE-MÃE")
print("=" * 75)

rel_encontrados = cnpjs_rel.intersection(cnpjs_mae)
rel_fora = cnpjs_rel - cnpjs_mae

print(f"Relacionamentos encontrados na base-mãe: {len(rel_encontrados):,}")
print(f"Relacionamentos FORA da base-mãe:       {len(rel_fora):,}")

if len(cnpjs_rel) > 0:
    perc = len(rel_encontrados) / len(cnpjs_rel) * 100
else:
    perc = 0

print(f"Percentual encontrado: {perc:.2f}%")
print(f"Percentual fora:       {100-perc:.2f}%")


# ============================================================
# 4. ANALISAR OS CNPJs FORA DA BASE-MÃE
# ============================================================

print("\n" + "=" * 75)
print("4. CNPJs DE RELACIONAMENTO FORA DA BASE-MÃE")
print("=" * 75)

rel_fora_df = rel[
    rel["CNPJ_NORMALIZADO"].isin(rel_fora)
].copy()

print(f"Registros fora da base-mãe: {len(rel_fora_df):,}")

if len(rel_fora_df) > 0:

    print("\nDistribuição por cobertura:")

    print(
        rel_fora_df["COBERTURA"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("\nPrimeiros registros:")

    colunas_exibir = [
        c for c in [
            "CNPJ",
            "Razão Social",
            "Categoria",
            "Porte",
            "CNAE",
            "COBERTURA"
        ]
        if c in rel_fora_df.columns
    ]

    print(
        rel_fora_df[colunas_exibir]
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# 5. COMPARAÇÃO SESI
# ============================================================

print("\n" + "=" * 75)
print("5. AUDITORIA SESI")
print("=" * 75)

cnpjs_sesi = set(
    rel.loc[
        rel["COBERTURA"].astype(str).str.upper().str.contains("SESI"),
        "CNPJ_NORMALIZADO"
    ].dropna()
)

sesi_dentro = cnpjs_sesi.intersection(cnpjs_mae)
sesi_fora = cnpjs_sesi - cnpjs_mae

print(f"SESI oficial:       {len(cnpjs_sesi):,}")
print(f"SESI na base-mãe:   {len(sesi_dentro):,}")
print(f"SESI fora:           {len(sesi_fora):,}")


# ============================================================
# 6. COMPARAÇÃO SENAI
# ============================================================

print("\n" + "=" * 75)
print("6. AUDITORIA SENAI")
print("=" * 75)

cnpjs_senai = set(
    rel.loc[
        rel["COBERTURA"].astype(str).str.upper().str.contains("SENAI"),
        "CNPJ_NORMALIZADO"
    ].dropna()
)

senai_dentro = cnpjs_senai.intersection(cnpjs_mae)
senai_fora = cnpjs_senai - cnpjs_mae

print(f"SENAI oficial:       {len(cnpjs_senai):,}")
print(f"SENAI na base-mãe:   {len(senai_dentro):,}")
print(f"SENAI fora:           {len(senai_fora):,}")


# ============================================================
# 7. BASE SEBRAE
# ============================================================

print("\n" + "=" * 75)
print("7. BASE SEBRAE × BASE-MÃE")
print("=" * 75)

sebrae = carregar_cnpjs_excel(
    ARQ_SEBRAE,
    "cnpj"
)

cnpjs_sebrae = set(
    sebrae["CNPJ_NORMALIZADO"]
    .dropna()
)

print(f"SEBRAE: {len(cnpjs_sebrae):,}")

sebrae_dentro = cnpjs_sebrae.intersection(cnpjs_mae)
sebrae_fora = cnpjs_sebrae - cnpjs_mae
mae_fora_sebrae = cnpjs_mae - cnpjs_sebrae

print(f"SEBRAE encontrados na base-mãe: {len(sebrae_dentro):,}")
print(f"SEBRAE fora da base-mãe:         {len(sebrae_fora):,}")
print(f"Base-mãe não encontrada SEBRAE:  {len(mae_fora_sebrae):,}")

if len(cnpjs_mae) > 0:
    perc_sebrae = len(sebrae_dentro) / len(cnpjs_mae) * 100
else:
    perc_sebrae = 0

print(f"\nCobertura SEBRAE sobre base-mãe: {perc_sebrae:.2f}%")


# ============================================================
# 8. COMPARAÇÃO DIRETA BASE-MÃE × SEBRAE
# ============================================================

print("\n" + "=" * 75)
print("8. OS UNIVERSOS SÃO IGUAIS?")
print("=" * 75)

if cnpjs_mae == cnpjs_sebrae:
    print("✓ SIM")
    print("Os 32.926 CNPJs são exatamente os mesmos.")
else:
    print("✗ NÃO")
    print("Existem diferenças entre os universos.")

    print(
        f"\nSomente na BASE-MÃE: {len(mae_fora_sebrae):,}"
    )

    print(
        f"Somente no SEBRAE:   {len(sebrae_fora):,}"
    )


# ============================================================
# 9. EXPORTAR DIFERENÇAS
# ============================================================

print("\n" + "=" * 75)
print("9. EXPORTANDO AUDITORIA")
print("=" * 75)

SAIDA.mkdir(exist_ok=True)

# Relacionamentos fora da base-mãe
if len(rel_fora_df) > 0:

    arquivo = SAIDA / "AUDITORIA_RELACIONAMENTO_FORA_BASE_MAE.csv"

    rel_fora_df.to_csv(
        arquivo,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Criado: {arquivo}")


# CNPJs da base-mãe não encontrados no SEBRAE
if len(mae_fora_sebrae) > 0:

    arquivo = SAIDA / "AUDITORIA_BASE_MAE_FORA_SEBRAE.csv"

    base_mae[
        base_mae["CNPJ_NORMALIZADO"].isin(mae_fora_sebrae)
    ].to_csv(
        arquivo,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Criado: {arquivo}")


# CNPJs SEBRAE fora da base-mãe
if len(sebrae_fora) > 0:

    arquivo = SAIDA / "AUDITORIA_SEBRAE_FORA_BASE_MAE.csv"

    sebrae[
        sebrae["CNPJ_NORMALIZADO"].isin(sebrae_fora)
    ].to_csv(
        arquivo,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Criado: {arquivo}")


# ============================================================
# 10. RESUMO FINAL
# ============================================================

print("\n" + "=" * 75)
print("RESUMO FINAL DA AUDITORIA")
print("=" * 75)

print(f"""
BASE-MÃE
  Empresas:                         {len(cnpjs_mae):,}

RELACIONAMENTO OFICIAL
  CNPJs únicos:                     {len(cnpjs_rel):,}
  Encontrados na base-mãe:         {len(rel_encontrados):,}
  Fora da base-mãe:                 {len(rel_fora):,}

SESI
  Oficial:                          {len(cnpjs_sesi):,}
  Na base-mãe:                      {len(sesi_dentro):,}
  Fora:                              {len(sesi_fora):,}

SENAI
  Oficial:                          {len(cnpjs_senai):,}
  Na base-mãe:                      {len(senai_dentro):,}
  Fora:                              {len(senai_fora):,}

SEBRAE
  Empresas:                         {len(cnpjs_sebrae):,}
  Encontradas na base-mãe:         {len(sebrae_dentro):,}
  Fora da base-mãe:                 {len(sebrae_fora):,}
  Base-mãe fora do SEBRAE:         {len(mae_fora_sebrae):,}
  Cobertura sobre base-mãe:         {perc_sebrae:.2f}%
""")

print("=" * 75)
print("AUDITORIA CONCLUÍDA")
print("=" * 75)