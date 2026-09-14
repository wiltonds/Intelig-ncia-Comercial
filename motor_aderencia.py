# ============================================================
# MOTOR DE ADERÊNCIA DE PORTFÓLIO
# SESI + SENAI | ALAGOAS
# ============================================================

import pandas as pd
import re

# ============================================================
# MAPEAMENTO INTELIGENTE: DESCRICAO / PALAVRAS-CHAVE -> CÓDIGO CNAE
# ============================================================

MAPEAMENTO_PALAVRAS_CHAVE = {
    "CONSTRUCAO": "4120400",
    "EDIFICIO": "4120400",
    "OBRA": "4120400",
    "ALIMENTO": "1099699",
    "PANIFICACAO": "1091102",
    "BEBIDA": "1113002",
    "REFRIGERANTE": "1122401",
    "TEXTIL": "1311100",
    "CONFEC": "1412600",
    "VESTUARIO": "1412600",
    "CALCADO": "1531900",
    "COURO": "1510600",
    "MADEIRA": "1610003",
    "MOVEL": "3101200",
    "MOVEIS": "3101200",
    "PAPEL": "1710900",
    "GRAFICA": "1811302",
    "QUIMIC": "2099199",
    "FARMACEUT": "2110600",
    "PLASTICO": "2229399",
    "BORRACHA": "2212900",
    "CERAMICA": "2349400",
    "VIDRO": "2311700",
    "CIMENTO": "2320600",
    "CONCRETO": "2330301",
    "METAL": "2599399",
    "METALURG": "2410000",
    "USINAGEM": "2539001",
    "MECANIC": "2869100",
    "MAQUINA": "2869100",
    "EQUIPAMENTO": "2869100",
    "ELETRIC": "2710401",
    "ELETRONIC": "2610000",
    "AUTOMOTIV": "2910701",
    "VEICULO": "2910701",
    "MANUTENCAO": "3314799",
    "REPARO": "3314799",
    "INSTALACAO": "3321000",
    "ENERGIA": "3511501",
    "AGUA": "3600600",
    "ESGOTO": "3701100",
    "RESIDUO": "3811400",
    "LOGISTICA": "5211799",
    "TRANSPORTE": "4930202",
    "TI": "6201501",
    "SOFTWARE": "6201501",
    "TELECOM": "6110801",
    "PESQUISA": "7210000",
    "LABORATORIO": "7120100"
}


def extrair_codigo_cnae(cnae_input):
    """
    Normaliza o input de CNAE:
    1. Se contiver 4 ou mais dígitos numéricos, extrai e retorna os números.
    2. Se for texto/descrição, mapeia via palavras-chave.
    3. Se não encontrar, retorna uma chave genérica de indústria/serviço.
    """
    if pd.isna(cnae_input) or not str(cnae_input).strip():
        return "4120400"  # Padrão seguro

    texto = str(cnae_input).strip().upper()
    
    # 1. Tenta extrair dígitos numéricos
    numeros = "".join(filter(str.isdigit, texto))
    if len(numeros) >= 4:
        return numeros

    # 2. Busca por palavra-chave na descrição
    for palavra, codigo in MAPEAMENTO_PALAVRAS_CHAVE.items():
        if palavra in texto:
            return codigo

    # 3. Fallback genérico para a indústria
    return "4120400"


# ============================================================
# MATRIZ DE ADERÊNCIA E PESOS POR SETOR / CANAL
# ============================================================

def obter_matriz_setorial(cnae_code):
    """
    Retorna o ranqueamento de aderência das áreas do SESI e SENAI com base no código do CNAE.
    """
    codigo = str(cnae_code)
    
    # Construção Civil e Obras
    if codigo.startswith(("41", "42", "43")):
        return [
            {"Área": "SST & Saúde Ocupacional (NR-18, PCMSO, PGR)", "Instituição": "SESI", "Relevância": "Altíssima", "Score": 95},
            {"Área": "Formação Técnica em Edificações e Segurança", "Instituição": "SENAI", "Relevância": "Alta", "Score": 88},
            {"Área": "Eficiência Operacional & Processos", "Instituição": "SENAI", "Relevância": "Média/Alta", "Score": 78},
            {"Área": "Gestão de Absenteísmo e Prom. Saúde", "Instituição": "SESI", "Relevância": "Média", "Score": 70},
            {"Área": "Consultoria em Inovação e Sustentabilidade", "Instituição": "SENAI", "Relevância": "Média", "Score": 62}
        ]
    
    # Indústria de Alimentos, Bebidas e Química
    elif codigo.startswith(("10", "11", "20", "21", "22")):
        return [
            {"Área": "SST & Ergonomia de Processos (NR-12, NR-36)", "Instituição": "SESI", "Relevância": "Altíssima", "Score": 92},
            {"Área": "Automação, Mecânica e Manutenção Industrial", "Instituição": "SENAI", "Relevância": "Altíssima", "Score": 90},
            {"Área": "Controle de Qualidade & Laboratórios", "Instituição": "SENAI", "Relevância": "Alta", "Score": 85},
            {"Área": "Programas de Vacinação e Nutrição", "Instituição": "SESI", "Relevância": "Média/Alta", "Score": 75},
            {"Área": "Consultoria em Processos Limpos", "Instituição": "SENAI", "Relevância": "Média", "Score": 65}
        ]

    # Metalmecânica, Vestuário, Calçados e Demais Transformações
    elif codigo.startswith(("13", "14", "15", "24", "25", "28", "29", "30", "31", "33")):
        return [
            {"Área": "Capacitação Operacional & Solda/Usinagem", "Instituição": "SENAI", "Relevância": "Altíssima", "Score": 94},
            {"Área": "Segurança no Trabalho & Proteção de Máquinas (NR-12)", "Instituição": "SESI", "Relevância": "Altíssima", "Score": 91},
            {"Área": "Lean Manufacturing & Produtividade", "Instituição": "SENAI", "Relevância": "Alta", "Score": 84},
            {"Área": "Exames Complementares & Consultas Ocupacionais", "Instituição": "SESI", "Relevância": "Média/Alta", "Score": 78},
            {"Área": "Energia Renovável & Eficiência Energética", "Instituição": "SENAI", "Relevância": "Média", "Score": 60}
        ]

    # Serviços Industriais, Tecnologia, Logística e Outros
    else:
        return [
            {"Área": "Gestão de NR's e Laudos Técnicos Ocupacionais", "Instituição": "SESI", "Relevância": "Alta", "Score": 85},
            {"Área": "Cursos de Formação Profissional & Aperfeiçoamento", "Instituição": "SENAI", "Relevância": "Alta", "Score": 82},
            {"Área": "Programas de Bem-Estar e Saúde Mental", "Instituição": "SESI", "Relevância": "Média/Alta", "Score": 75},
            {"Área": "Consultoria em Digitalização e TI", "Instituição": "SENAI", "Relevância": "Média", "Score": 68},
            {"Área": "Ginástica Laboral & Atividades Físicas", "Instituição": "SESI", "Relevância": "Média", "Score": 60}
        ]


# ============================================================
# FUNÇÃO PRINCIPAL DE DIAGNÓSTICO
# ============================================================

def diagnosticar(cnae_code, porte, ja_sesi, ja_senai):
    """
    Executa o diagnóstico completo calculando estratégia recomendada,
    aderência máxima, potencial de cross-sell e ranqueamento de portfólio.
    """
    # 1. Normalização do Código CNAE
    codigo_cnae = extrair_codigo_cnae(cnae_code)

    # 2. Obtenção do Ranqueamento do Portfólio
    matriz_areas = obter_matriz_setorial(codigo_cnae)
    df_areas = pd.DataFrame(matriz_areas)

    # 3. Cálculo da Aderência Máxima
    aderencia_maxima = df_areas["Score"].max() if not df_areas.empty else 75
    principal_area = df_areas.iloc[0]["Área"] if not df_areas.empty else "SST & Saúde Ocupacional"

    # 4. Definição da Rota Comercial / Estratégia Recomendada
    # (rótulo curto pro card + detalhe completo pro tooltip)
    if ja_sesi and ja_senai:
        rota_comercial = "Fidelização"
        rota_detalhe = "Cliente SESI + SENAI: manter contrato e ampliar escopo de venda recorrente."
        cross_sell = "Manter & Ampliar"
        cross_sell_detalhe = "Manter contratos atuais e ampliar o escopo de atendimento."
    elif ja_sesi and not ja_senai:
        rota_comercial = "Cross-Sell SENAI"
        rota_detalhe = "Já é cliente SESI: oferecer cursos/consultoria SENAI."
        cross_sell = "Oportunidade SENAI"
        cross_sell_detalhe = "Alta oportunidade de venda cruzada para o SENAI."
    elif ja_senai and not ja_sesi:
        rota_comercial = "Cross-Sell SESI"
        rota_detalhe = "Já é cliente SENAI: oferecer SST/Saúde Ocupacional SESI."
        cross_sell = "Oportunidade SESI"
        cross_sell_detalhe = "Alta oportunidade de venda cruzada para o SESI."
    else:
        # Não possui relacionamento (Prospect)
        porte_upper = str(porte).upper()
        if "GRANDE" in porte_upper or "MEDIO" in porte_upper or "MÉDIO" in porte_upper:
            rota_comercial = "Aquisição Prioritária"
            rota_detalhe = "Prospect de porte médio/grande: tratar como conta-chave SESI + SENAI."
            cross_sell = "Oferta Conjunta"
            cross_sell_detalhe = "Apresentar pacote integrado SESI + SENAI."
        else:
            rota_comercial = "Prospecção Padrão"
            rota_detalhe = "Prospect de micro/pequeno porte: entrada por SST ou cursos."
            cross_sell = "Soluções Básicas"
            cross_sell_detalhe = "Apresentar soluções básicas de entrada (SST ou cursos)."

    # 5. Formatação do DataFrame para Retorno Visual
    df_areas_formatado = df_areas.copy()
    df_areas_formatado["Aderência"] = df_areas_formatado["Score"].astype(str) + "%"
    df_areas_display = df_areas_formatado[["Área", "Instituição", "Relevância", "Aderência"]]

    return {
        "rota_comercial": rota_comercial,
        "rota_detalhe": rota_detalhe,
        "aderencia_maxima": int(aderencia_maxima),
        "principal_area": principal_area,
        "cross_sell": cross_sell,
        "cross_sell_detalhe": cross_sell_detalhe,
        "areas_ranqueadas": df_areas_display
    }