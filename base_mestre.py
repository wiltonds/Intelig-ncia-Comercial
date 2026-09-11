import pandas as pd
from pathlib import Path

ARQUIVO = Path(
    r"C:\Users\wilton.costa\Desktop\projeto_comercial\saida\BASE_MESTRE_COMERCIAL.csv"
)

df = pd.read_csv(
    ARQUIVO,
    encoding="utf-8-sig",
    low_memory=False
)

print("=" * 80)
print("AUDITORIA FINAL DA BASE MESTRE")
print("=" * 80)

# ============================================================
# 1. SESI
# ============================================================

print("\n1. SESI")

esperado_sesi = df["TEM_SESI"].apply(
    lambda x: "NÃO" if x else "SIM"
)

erro_sesi = df[
    df["OPORTUNIDADE_SESI"] != esperado_sesi
]

print("Esperado:")
print(esperado_sesi.value_counts().to_string())

print("Erros:", len(erro_sesi))


# ============================================================
# 2. SENAI
# ============================================================

print("\n2. SENAI")

esperado_senai = df["TEM_SENAI"].apply(
    lambda x: "NÃO" if x else "SIM"
)

erro_senai = df[
    df["OPORTUNIDADE_SENAI"] != esperado_senai
]

print("Esperado:")
print(esperado_senai.value_counts().to_string())

print("Erros:", len(erro_senai))


# ============================================================
# 3. SESI + SENAI
# ============================================================

print("\n3. SESI + SENAI")

esperado_overlap = (
    (df["TEM_SESI"] == True)
    & (df["TEM_SENAI"] == True)
)

erro_overlap = df[
    df["TEM_SESI_SENAI"] != esperado_overlap
]

print("Erros:", len(erro_overlap))


# ============================================================
# 4. STATUS RELACIONAMENTO
# ============================================================

print("\n4. STATUS RELACIONAMENTO")


def calcular_status(row):

    if row["TEM_SESI"] and row["TEM_SENAI"]:
        return "SESI + SENAI"

    if row["TEM_SESI"]:
        return "SOMENTE SESI"

    if row["TEM_SENAI"]:
        return "SOMENTE SENAI"

    return "SEM RELACIONAMENTO"


status_esperado = df.apply(
    calcular_status,
    axis=1
)

erro_status = df[
    df["STATUS_RELACIONAMENTO"] != status_esperado
]

print("Erros:", len(erro_status))


# ============================================================
# 5. CROSS SELL
# ============================================================

print("\n5. CROSS-SELL")

def calcular_cross_sell(row):

    if row["TEM_SESI"] and not row["TEM_SENAI"]:
        return "SENAI"

    if row["TEM_SENAI"] and not row["TEM_SESI"]:
        return "SESI"

    return "NÃO"


cross_esperado = df.apply(
    calcular_cross_sell,
    axis=1
)

erro_cross = df[
    df["OPORTUNIDADE_CROSS_SELL"] != cross_esperado
]

print("Esperado:")
print(cross_esperado.value_counts().to_string())

print("Erros:", len(erro_cross))


# ============================================================
# 6. OPORTUNIDADE GERAL
# ============================================================

print("\n6. OPORTUNIDADE GERAL")

geral_esperado = (
    (
        (df["TEM_SESI"] == True)
        | (df["TEM_SENAI"] == True)
    )
    .map({
        True: "CLIENTE",
        False: "PROSPECT"
    })
)

erro_geral = df[
    df["OPORTUNIDADE_GERAL"] != geral_esperado
]

print("Esperado:")
print(geral_esperado.value_counts().to_string())

print("Erros:", len(erro_geral))


# ============================================================
# 7. SEBRAE
# ============================================================

print("\n7. SEBRAE")

sebrae_elegivel_esperado = df[
    "SEBRAE_ELEGIVEL"
].map({
    "SIM": "NÃO ATENDIDA",
    "NAO": "FORA DO ESCOPO SEBRAE"
})

erro_sebrae_1 = df[
    df["SEBRAE_OPORTUNIDADE"]
    != sebrae_elegivel_esperado
]

print("Erros SEBRAE_OPORTUNIDADE:", len(erro_sebrae_1))


sebrae_oportunidade_esperada = df[
    "SEBRAE_ELEGIVEL"
].map({
    "SIM": "OPORTUNIDADE",
    "NAO": "FORA DO ESCOPO"
})

erro_sebrae_2 = df[
    df["OPORTUNIDADE_SEBRAE"]
    != sebrae_oportunidade_esperada
]

print(
    "Erros OPORTUNIDADE_SEBRAE:",
    len(erro_sebrae_2)
)


# ============================================================
# 8. FECHAMENTO DO MERCADO
# ============================================================

print("\n8. FECHAMENTO DO MERCADO")

mercado = len(df)

sesi = int(df["TEM_SESI"].sum())
senai = int(df["TEM_SENAI"].sum())
ambos = int(df["TEM_SESI_SENAI"].sum())

somente_sesi = int(
    (
        (df["TEM_SESI"] == True)
        & (df["TEM_SENAI"] == False)
    ).sum()
)

somente_senai = int(
    (
        (df["TEM_SESI"] == False)
        & (df["TEM_SENAI"] == True)
    ).sum()
)

sem_relacionamento = int(
    (
        (df["TEM_SESI"] == False)
        & (df["TEM_SENAI"] == False)
    ).sum()
)

print("Mercado total:", mercado)
print("Somente SESI:", somente_sesi)
print("Somente SENAI:", somente_senai)
print("SESI + SENAI:", ambos)
print("Sem relacionamento:", sem_relacionamento)

print(
    "\nFechamento:",
    somente_sesi
    + somente_senai
    + ambos
    + sem_relacionamento
)


# ============================================================
# 9. CROSS-SELL
# ============================================================

print("\n9. CROSS-SELL")

print(
    "SESI -> SENAI:",
    int(
        (
            (df["TEM_SESI"] == True)
            & (df["TEM_SENAI"] == False)
        ).sum()
    )
)

print(
    "SENAI -> SESI:",
    int(
        (
            (df["TEM_SESI"] == False)
            & (df["TEM_SENAI"] == True)
        ).sum()
    )
)


# ============================================================
# 10. RESULTADO FINAL
# ============================================================

total_erros = (
    len(erro_sesi)
    + len(erro_senai)
    + len(erro_overlap)
    + len(erro_status)
    + len(erro_cross)
    + len(erro_geral)
    + len(erro_sebrae_1)
    + len(erro_sebrae_2)
)

print("\n" + "=" * 80)
print("RESULTADO FINAL")
print("=" * 80)

print("Total de erros:", total_erros)

if total_erros == 0:
    print("OK - BASE LOGICAMENTE CONSISTENTE")
else:
    print("ATENCAO - EXISTEM REGRAS INCONSISTENTES")

print("=" * 80)