import os
import re
from pathlib import Path

import pandas as pd

# ============================================================
# FUNÇÕES DE HIGIENIZAÇÃO E REGRA DE NEGÓCIO
# ============================================================

# Lista expandida de termos da Indústria de Transformação (CNAEs 10 a 33)
TERMOS_INDUSTRIA = [
    # Verbos e Termos Gerais
    "FABRICACAO", "FABRICACAO DE", "INDUSTRIA", "INDUSTRIAL", "PRODUCAO", 
    "PROCESSAMENTO", "MONTAGEM", "USINA", "REFINO", "REFINARIA", "REPARACAO", 
    "MANUTENCAO E REPARACAO", "INSTALACAO DE MAQUINAS", "REFORMACAO",
    
    # Alimentos, Bebidas e Fumo (Divisões 10, 11, 12)
    "ABATE", "ABATIMENTO", "TORREFACTAO", "MOAGEM", "PANIFICACAO", "LATICINIOS", 
    "CONSERVAS", "DESOSSAMENTO", "FRIGORIFICO", "PREPARACAO DE LEITE", 
    "PREPARACAO DE CARNE", "CERVEJAS", "BEBIDAS", "DESTILACAO", "FUMO",
    
    # Têxtil, Vestuário, Couro e Calçados (Divisões 13, 14, 15)
    "FIACAO", "TECELAGEM", "ACABAMENTO DE FIOS", "CONFECCAO", "COSTURA", 
    "STAMPARIA", "CURTUME", "ALPARGATAS", "CALCADOS", "ARTEFATOS DE COURO",
    
    # Madeira, Papel e Gráfica (Divisões 16, 17, 18)
    "DESDOBRAMENTO DE MADEIRA", "SERRARIA", "SULFATACAO", "CELULOSE", 
    "EMBALAGENS DE PAPEL", "IMPRESSAO", "GRAFICA", "ENCADERNACAO", "MARCENARIA",
    
    # Química, Farmacêutica, Borracha e Plástico (Divisões 19, 20, 21, 22)
    "COQUERIAS", "PETROQUIMICA", "BIODIESEL", "ADUBOS", "FERTILIZANTES", 
    "TINTAS", "COSMETICOS", "PERFUMARIA", "FARMACEUTICOS", "MEDICAMENTOS", 
    "VULCANIZACAO", "PNEUMATICOS", "ARTEFATOS DE PLASTICO", "LAMINAÇÃO DE PLASTICO",
    
    # Minerais Não-Metálicos, Metalurgia e Produtos de Metal (Divisões 23, 24, 25)
    "CERAMICA", "VIDROS", "CIMENTO", "GESSO", "CONCRETO", "OLARIA", 
    "SIDERURGIA", "FUNDICAO", "METALURGIA", "LAMINACAO", "TREFILACAO", 
    "ESQUANQUADRIAS", "CALDEIRARIA", "USINAGEM", "SERRALHERIA", "ESTAMPARIA",
    
    # Equipamentos, Máquinas e Veículos (Divisões 26 a 33)
    "INFORMATICA", "ELETRONICOS", "COMPONENTES ELETRONICOS", "MOTORES", 
    "TRANSFORMADORES", "GERADORES", "COMPRESSORES", "MAQUINAS", "EQUIPAMENTOS", 
    "CARROCERIAS", "REBOQUES", "NAVAL", "AERONAUTICA", "MOVEIS", "BIJUTERIAS"
]


def extrair_apenas_numeros(val):
    """Extrai estritamente os dígitos numéricos de qualquer valor."""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).split('.')[0].strip()
    return re.sub(r"\D", "", s)


def identificar_industria(val):
    """
    Identifica se a empresa pertence à indústria por:
    1. Código CNAE (Divisões 10 a 33).
    2. Busca abrangente por vocabulário industrial na descrição.

    ATENÇÃO — regra não usada para decidir EH_INDUSTRIA (ver abaixo,
    onde EH_INDUSTRIA confia na coluna SETOR já pronta). Esta função só
    alimenta CNAE_DIVISAO, um campo diagnóstico secundário e já
    documentado como não confiável (AI-Commercial-Intelligence/docs/
    dicionario_dados.md). Foi testada e descartada como regra oficial
    de indústria: subestimava o universo (17.676 de 32.926 empresas).
    A regra oficial de "o que é indústria" tem duas etapas, em outros
    dois repositórios: BI_Project (tabela DN, CNAE principal) e
    classificacao-industria-al (seção CNAE/IBGE) — ver
    AI-Commercial-Intelligence/docs/arquitetura_dados.md.
    """
    if pd.isna(val):
        return False, 0
    
    texto = str(val).upper().strip()
    numeros = extrair_apenas_numeros(texto)
    
    divisao = 0
    if len(numeros) >= 2:
        div_candidata = int(numeros[:2])
        if 10 <= div_candidata <= 33:
            return True, div_candidata
        divisao = div_candidata

    # Checagem flexível de termos de transformação
    for termo in TERMOS_INDUSTRIA:
        if termo in texto:
            return True, (divisao if divisao > 0 else 10)
            
    return False, divisao


def normalizar_cnpj(series):
    """Padroniza o CNPJ mantendo 14 dígitos (preenchendo zeros à esquerda)."""
    s = series.astype("string").fillna("").str.strip()
    s = s.str.replace(r"\.0$", "", regex=True)
    s = s.str.replace(r"\D", "", regex=True)
    return s.str.zfill(14)


def encontrar_coluna(df, termos):
    """
    Busca dinâmica por nomes de colunas.
    Prioriza correspondência EXATA antes de parcial, pra evitar que uma
    coluna como "Origem da Cobertura" seja confundida com "COBERTURA".
    """
    for termo in termos:
        for col in df.columns:
            if str(col).strip().lower() == termo.lower():
                return col

    for col in df.columns:
        col_clean = str(col).strip().lower()
        for termo in termos:
            if termo.lower() in col_clean:
                return col
    return None


def definir_status_sebrae(row):
    """
    Define o status comercial do SEBRAE.
    A elegibilidade vem da base SEBRAE (CNAE principal na lista de CNAEs
    SEBRAE). Quem é cliente vem do relacionamento desta própria base
    (TEM_SESI/TEM_SENAI) — não da 'oportunidade_comercial' do arquivo
    SEBRAE, que usa uma cópia antiga do relacionamento e divergia do
    STATUS_RELACIONAMENTO em ~150 empresas.
    """
    if not row.get("EH_INDUSTRIA", False):
        return "FORA DO ESCOPO SEBRAE"

    elegivel = str(row.get("SEBRAE_ELEGIVEL", "")).upper()
    if elegivel in ["NAO", "NÃO", "FALSE"]:
        return "FORA DO ESCOPO SEBRAE"
    if elegivel not in ["SIM", "TRUE"]:
        return "SEM INFORMAÇÃO"

    tem_sesi = bool(row.get("TEM_SESI", False))
    tem_senai = bool(row.get("TEM_SENAI", False))
    if tem_sesi and tem_senai:
        return "SESI + SENAI"
    if tem_sesi:
        return "CLIENTE SESI / OPORTUNIDADE SENAI"
    if tem_senai:
        return "CLIENTE SENAI / OPORTUNIDADE SESI"
    return "NÃO ATENDIDA"


def transformar_cnpj_relacionamento(df):
    """Cria tabela única de relacionamento por CNPJ (SESI x SENAI)."""
    coluna_cnpj = encontrar_coluna(df, ["cnpj"])
    coluna_cobertura = encontrar_coluna(df, ["cobertura", "cnae cobertura", "entidade", "casa"])

    if coluna_cnpj is None:
        raise ValueError("Coluna CNPJ não encontrada na base de relacionamento.")

    temp = df.copy()
    temp["CNPJ_NORMALIZADO"] = normalizar_cnpj(temp[coluna_cnpj])
    
    temp = temp[temp["CNPJ_NORMALIZADO"].str.len() == 14]
    temp = temp[temp["CNPJ_NORMALIZADO"] != "00000000000000"]

    if coluna_cobertura:
        cobertura_txt = temp[coluna_cobertura].astype("string").fillna("").str.upper()
        cnpjs_sesi = set(temp.loc[cobertura_txt.str.contains("SESI", regex=False), "CNPJ_NORMALIZADO"])
        cnpjs_senai = set(temp.loc[cobertura_txt.str.contains("SENAI", regex=False), "CNPJ_NORMALIZADO"])
    else:
        cnpjs_sesi = set(temp["CNPJ_NORMALIZADO"])
        cnpjs_senai = set()

    todos = sorted(cnpjs_sesi | cnpjs_senai)

    relacionamento = pd.DataFrame({"CNPJ_NORMALIZADO": todos})
    relacionamento["TEM_SESI"] = relacionamento["CNPJ_NORMALIZADO"].isin(cnpjs_sesi)
    relacionamento["TEM_SENAI"] = relacionamento["CNPJ_NORMALIZADO"].isin(cnpjs_senai)
    relacionamento["TEM_SESI_SENAI"] = relacionamento["TEM_SESI"] & relacionamento["TEM_SENAI"]

    relacionamento["STATUS_RELACIONAMENTO"] = "SEM RELACIONAMENTO"
    relacionamento.loc[relacionamento["TEM_SESI"] & ~relacionamento["TEM_SENAI"], "STATUS_RELACIONAMENTO"] = "SOMENTE SESI"
    relacionamento.loc[~relacionamento["TEM_SESI"] & relacionamento["TEM_SENAI"], "STATUS_RELACIONAMENTO"] = "SOMENTE SENAI"
    relacionamento.loc[relacionamento["TEM_SESI_SENAI"], "STATUS_RELACIONAMENTO"] = "SESI + SENAI"

    return relacionamento


# ============================================================
# CONFIGURAÇÃO DE CAMINHOS
# ============================================================

# Antes era um caminho absoluto fixo (C:\Users\wilton.costa\Desktop\
# projeto_comercial) que não batia com a pasta real deste script
# (…\Desktop\PROJETOS\projeto_comercial) — quebrava assim que alguém
# rodava isto fora daquela máquina/pasta específica.
PASTA = str(Path(__file__).resolve().parent)
SAIDA = os.path.join(PASTA, "saida")

ARQ_MERCADO = os.path.join(PASTA, "industrias_ativas.xlsx")
ARQ_RELACIONAMENTO = os.path.join(PASTA, "BASE_DADOS_SESI&SENAI_N_RELACIONAMENTO.xlsx")
ARQ_SEBRAE = os.path.join(PASTA, "industrias_ativas_sebrae.xlsx")
ARQ_CORRECAO_UNIVERSO = os.path.join(PASTA, "CORRECAO_UNIVERSO_CONFIRMADA.csv")

os.makedirs(SAIDA, exist_ok=True)

print("=" * 75)
print("CONSTRUÇÃO DA BASE MESTRE COMERCIAL")
print("=" * 75)

# ------------------------------------------------------------
# 1. CARREGAR E HIGIENIZAR BASE-MÃE
# ------------------------------------------------------------
print("\n" + "=" * 75)
print("1. CARREGANDO E HIGIENIZANDO BASE-MÃE")
print("=" * 75)

mercado = pd.read_excel(ARQ_MERCADO, engine="openpyxl")
print(f"Empresas na base-mãe: {len(mercado):,}")

col_cnpj_mae = encontrar_coluna(mercado, ["cnpj"])
if not col_cnpj_mae:
    raise ValueError("Coluna de CNPJ não foi encontrada na base-mãe!")
mercado["CNPJ_NORMALIZADO"] = normalizar_cnpj(mercado[col_cnpj_mae])

coluna_cnae = encontrar_coluna(mercado, ["cnae primario", "cnae", "atividade"])

if coluna_cnae:
    print(f"-> Coluna identificada para CNAE: '{coluna_cnae}'")
    res_ind = mercado[coluna_cnae].apply(identificar_industria)
    mercado["CNAE_DIVISAO"] = [r[1] for r in res_ind]
else:
    print("[AVISO] Nenhuma coluna de CNAE foi encontrada na base-mãe!")
    mercado["CNAE_DIVISAO"] = 0

# EH_INDUSTRIA confia na coluna SETOR da própria base-mãe (já validada:
# 100% das empresas de industrias_ativas.xlsx são SETOR = INDÚSTRIA).
# Classificar de novo por palavra-chave no CNAE subestimava o universo
# (17.676 de 32.926), o que inflava incorretamente "FORA DO ESCOPO SEBRAE".
coluna_setor = encontrar_coluna(mercado, ["setor"])
if coluna_setor:
    # Compara com e sem acento (evita falha por problema de encoding
    # em algum arquivo de origem). Verificado: 100% das linhas de
    # industrias_ativas.xlsx têm SETOR = "INDÚSTRIA".
    valores_setor = mercado[coluna_setor].astype(str).str.upper().str.strip()
    mercado["EH_INDUSTRIA"] = valores_setor.isin(["INDÚSTRIA", "INDUSTRIA"])
else:
    mercado["EH_INDUSTRIA"] = [r[0] for r in res_ind] if coluna_cnae else False

print(f"CNPJs únicos: {mercado['CNPJ_NORMALIZADO'].nunique():,}")
print(f"Empresas identificadas no setor industrial: {mercado['EH_INDUSTRIA'].sum():,}")

# Tratamento de correção de universo
if os.path.exists(ARQ_CORRECAO_UNIVERSO):
    correcao_universo = pd.read_csv(ARQ_CORRECAO_UNIVERSO, encoding="utf-8-sig")
    col_cnpj_corr = encontrar_coluna(correcao_universo, ["cnpj"])
    correcao_universo["CNPJ_NORMALIZADO"] = normalizar_cnpj(correcao_universo[col_cnpj_corr])
    
    col_cnae_corr = encontrar_coluna(correcao_universo, ["cnae primario", "cnae", "atividade"])
    if col_cnae_corr:
        res_ind_corr = correcao_universo[col_cnae_corr].apply(identificar_industria)
        correcao_universo["CNAE_DIVISAO"] = [r[1] for r in res_ind_corr]
    else:
        correcao_universo["CNAE_DIVISAO"] = 0

    # Cada linha deste arquivo já passou por auditoria manual contra a
    # Receita Federal (ATIVA + Alagoas + CNAE de indústria confirmado).
    # Não faz sentido reclassificar por palavra-chave (a lista de termos
    # é sem acento e o texto real do CNAE vem acentuado, então falha).
    correcao_universo["EH_INDUSTRIA"] = True

    correcao_universo = correcao_universo[
        ~correcao_universo["CNPJ_NORMALIZADO"].isin(mercado["CNPJ_NORMALIZADO"])
    ]

    print(f"Correção de universo aplicada: {len(correcao_universo):,} empresas.")
    mercado = pd.concat([mercado, correcao_universo], ignore_index=True)


# ------------------------------------------------------------
# 1B. EXCLUSÃO DE OPTANTES MEI
#
# Regra de negócio: empresas optantes pelo MEI não entram no universo
# comercial. Status obtido do arquivo oficial "Simples" da Receita
# Federal (dados abertos), cruzado por CNPJ básico (8 primeiros
# dígitos). Ver saida/SITUACAO_MEI_SIMPLES.csv para o detalhe.
# ------------------------------------------------------------

ARQ_SITUACAO_MEI = os.path.join(SAIDA, "SITUACAO_MEI_SIMPLES.csv")

if os.path.exists(ARQ_SITUACAO_MEI):
    situacao_mei = pd.read_csv(ARQ_SITUACAO_MEI, encoding="utf-8-sig", dtype=str)
    raizes_mei = set(situacao_mei.loc[situacao_mei["opcao_mei"] == "S", "cnpj_basico"])

    mercado["CNPJ_BASICO"] = mercado["CNPJ_NORMALIZADO"].str[:8]
    mercado["OPTANTE_MEI"] = mercado["CNPJ_BASICO"].isin(raizes_mei)

    total_antes = len(mercado)
    total_mei = int(mercado["OPTANTE_MEI"].sum())
    mercado = mercado[~mercado["OPTANTE_MEI"]].drop(columns=["OPTANTE_MEI"])

    print(f"\nExclusão de optantes MEI: {total_mei:,} de {total_antes:,} removidas.")
    print(f"Universo após exclusão MEI: {len(mercado):,}")
else:
    # Falha em vez de avisar: num job agendado ninguém lê o aviso, e a
    # base sairia com os optantes MEI dentro.
    raise FileNotFoundError(
        f"{ARQ_SITUACAO_MEI} não encontrado — sem ele não dá para excluir "
        "os optantes MEI. Gere com BI_Project/gerar_situacao_mei.py "
        "(mesma competência da Receita) e copie para saida/."
    )


# ------------------------------------------------------------
# 2. CARREGAR RELACIONAMENTO SESI/SENAI
# ------------------------------------------------------------
print("\n" + "=" * 75)
print("2. CARREGANDO RELACIONAMENTO SESI/SENAI")
print("=" * 75)

relacionamento_original = pd.read_excel(ARQ_RELACIONAMENTO, engine="openpyxl")
relacionamento = transformar_cnpj_relacionamento(relacionamento_original)
print(f"CNPJs únicos de relacionamento: {len(relacionamento):,}")


# ------------------------------------------------------------
# 3. CRUZANDO MERCADO × RELACIONAMENTO
# ------------------------------------------------------------
print("\n" + "=" * 75)
print("3. CRUZANDO MERCADO × RELACIONAMENTO")
print("=" * 75)

base = mercado.merge(relacionamento, on="CNPJ_NORMALIZADO", how="left")

base["TEM_SESI"] = base["TEM_SESI"].fillna(False).astype("boolean")
base["TEM_SENAI"] = base["TEM_SENAI"].fillna(False).astype("boolean")
base["TEM_SESI_SENAI"] = base["TEM_SESI_SENAI"].fillna(False).astype("boolean")
base["STATUS_RELACIONAMENTO"] = base["STATUS_RELACIONAMENTO"].fillna("SEM RELACIONAMENTO")


# ------------------------------------------------------------
# 4. CARREGAR E AUDITAR SEBRAE
# ------------------------------------------------------------
print("\n" + "=" * 75)
print("4. CARREGANDO E AUDITANDO SEBRAE")
print("=" * 75)

sebrae = pd.read_excel(ARQ_SEBRAE, engine="openpyxl")
coluna_cnpj_sebrae = encontrar_coluna(sebrae, ["cnpj"])

if coluna_cnpj_sebrae is None:
    raise ValueError("CNPJ não encontrado na base SEBRAE.")

sebrae["CNPJ_NORMALIZADO"] = normalizar_cnpj(sebrae[coluna_cnpj_sebrae])

duplicados_sebrae = sebrae["CNPJ_NORMALIZADO"].duplicated().sum()
if duplicados_sebrae > 0:
    sebrae = sebrae.drop_duplicates(subset="CNPJ_NORMALIZADO", keep="first")

for coluna in list(sebrae.columns):
    if coluna != "CNPJ_NORMALIZADO":
        sebrae = sebrae.rename(columns={coluna: f"SEBRAE_{coluna}"})


# ------------------------------------------------------------
# 5. CRUZAR BASE-MÃE × SEBRAE E PROCESSAR STATUS
# ------------------------------------------------------------
print("\n" + "=" * 75)
print("5. CRUZANDO BASE-MÃE × SEBRAE E PROCESSANDO STATUS")
print("=" * 75)

base = base.merge(sebrae, on="CNPJ_NORMALIZADO", how="left")

coluna_razao_sebrae = encontrar_coluna(base, ["sebrae_razao", "sebrae_nome"])
if coluna_razao_sebrae:
    base["ENCONTRADO_SEBRAE"] = base[coluna_razao_sebrae].notna()
else:
    colunas_verificacao = [c for c in base.columns if c.startswith("SEBRAE_")]
    base["ENCONTRADO_SEBRAE"] = base[colunas_verificacao].notna().any(axis=1) if colunas_verificacao else False

coluna_elegibilidade = encontrar_coluna(base, ["sebrae_elegivel", "elegivel"])
base["SEBRAE_ELEGIVEL"] = (
    base[coluna_elegibilidade].astype("string").str.strip().str.upper()
    if coluna_elegibilidade else pd.NA
)

coluna_oportunidade_original = encontrar_coluna(
    base, ["sebrae_oportunidade_comercial", "oportunidade_comercial", "sebrae_oportunidade"]
)
if coluna_oportunidade_original:
    base["SEBRAE_OPORTUNIDADE_ORIGINAL"] = base[coluna_oportunidade_original]
else:
    base["SEBRAE_OPORTUNIDADE_ORIGINAL"] = pd.NA

base["STATUS_SEBRAE"] = base.apply(definir_status_sebrae, axis=1)
base["SEBRAE_OPORTUNIDADE"] = base["STATUS_SEBRAE"]
base["OPORTUNIDADE_SEBRAE"] = base["STATUS_SEBRAE"]


# ------------------------------------------------------------
# 6. CRIAR CLASSIFICAÇÕES COMERCIAIS ADICIONAIS
# ------------------------------------------------------------
print("\n" + "=" * 75)
print("6. CRIANDO CLASSIFICAÇÕES COMERCIAIS")
print("=" * 75)

base["OPORTUNIDADE_SESI"] = "NÃO"
base.loc[~base["TEM_SESI"], "OPORTUNIDADE_SESI"] = "SIM"

base["OPORTUNIDADE_SENAI"] = "NÃO"
base.loc[~base["TEM_SENAI"], "OPORTUNIDADE_SENAI"] = "SIM"

base["OPORTUNIDADE_GERAL"] = "SEM RELACIONAMENTO"
base.loc[(base["TEM_SESI"] | base["TEM_SENAI"]), "OPORTUNIDADE_GERAL"] = "CLIENTE"
base.loc[(~base["TEM_SESI"] & ~base["TEM_SENAI"]), "OPORTUNIDADE_GERAL"] = "PROSPECT"

base["OPORTUNIDADE_CROSS_SELL"] = "NÃO"
base.loc[(base["TEM_SESI"] & ~base["TEM_SENAI"]), "OPORTUNIDADE_CROSS_SELL"] = "SENAI"
base.loc[(base["TEM_SENAI"] & ~base["TEM_SESI"]), "OPORTUNIDADE_CROSS_SELL"] = "SESI"


# ------------------------------------------------------------
# 7. EXPORTAÇÃO DOS RESULTADOS E RESUMOS
# ------------------------------------------------------------
print("\n" + "=" * 75)
print("7. EXPORTANDO BASE MESTRE E RESUMOS")
print("=" * 75)

arquivo_saida = os.path.join(SAIDA, "BASE_MESTRE_COMERCIAL.csv")
base.to_csv(arquivo_saida, index=False, encoding="utf-8-sig")

resumo_status = (
    base["STATUS_RELACIONAMENTO"]
    .value_counts()
    .rename_axis("STATUS_RELACIONAMENTO")
    .reset_index(name="EMPRESAS")
)
resumo_status.to_csv(os.path.join(SAIDA, "MESTRE_RESUMO_RELACIONAMENTO.csv"), index=False, encoding="utf-8-sig")

resumo_sebrae = (
    base["STATUS_SEBRAE"]
    .value_counts()
    .rename_axis("STATUS_SEBRAE")
    .reset_index(name="EMPRESAS")
)
resumo_sebrae.to_csv(os.path.join(SAIDA, "MESTRE_RESUMO_SEBRAE.csv"), index=False, encoding="utf-8-sig")

print(f"\nSucesso! Base mestre atualizada em: {arquivo_saida}")
print(f"Linhas exportadas: {len(base):,}")
print("=" * 75)