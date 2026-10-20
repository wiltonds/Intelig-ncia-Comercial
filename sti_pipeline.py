"""Pipeline de inteligência comercial STI: ingestão, normalização, matching e priorização."""
from __future__ import annotations

import re
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
BASE_MESTRE_PATH = BASE_DIR / "saida" / "BASE_MESTRE_COMERCIAL.csv"

RSS_QUERIES = [
    '"Alagoas" indústria investimento fábrica expansão 2026',
    '"Alagoas" indústria licença ambiental ampliação 2026',
    '"Alagoas" indústria contrato modernização produção 2026',
    'site:gov.br Alagoas indústria investimento 2026',
    'site:al.gov.br indústria Alagoas investimento 2026',
    'site:fiea.com.br Alagoas indústria investimento',
]

# Temas são apenas pistas para buscar nomes existentes no catálogo carregado.
# Não criamos nomes de produtos: a saída sempre usa o nome literal do catálogo oficial.
THEME_TERMS = {
    "digital_industria40": ["indústria 4.0", "digital", "sensor", "conectividade", "dados", "inteligência artificial", "gêmeo digital", "automação", "iot"],
    "alimentos_qualidade": ["alimentos", "laticínio", "leite", "trigo", "alimento", "agroindústria", "sanitária", "bpf", "appcc", "rotulagem", "qualidade"],
    "metrologia": ["calibração", "calibracao", "instrumento", "pressão", "temperatura", "balança", "medidor", "metrologia"],
    "eficiencia_lean": ["eficiência", "energia", "perdas", "produtividade", "processo", "manutenção", "estoque", "lean", "indicadores"],
    "construcao_materiais": ["construção", "cimento", "obra", "materiais", "pvc", "plástico", "tubos", "conexões"],
    "residuos_ambiental": ["resíduos", "residuos", "emissões", "gases de efeito estufa", "carbono", "ambiental", "licença ambiental"],
    "inovacao": ["inovação", "pesquisa", "desenvolvimento", "financiamento", "finep", "embrapii"],
}

COMPANY_ALIASES = {
    "Cooperativa Agroindustrial Pindorama": ["pindorama", "cooperativa pindorama"],
    "Natville": ["natville", "laticínios santa maria", "laticinios santa maria"],
    "Grupo Maratá": ["maratá", "marata", "jav indústria de alimentos", "jav industria de alimentos"],
    "Origem Energia": ["origem energia"],
    "Krona": ["krona tubos", "krona tubos e conexões", "krona tubos e conexoes"],
}

def normalize_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9]+", " ", value)).strip().lower()

def normalize_cnpj(value) -> str:
    if value is None or pd.isna(value):
        return ""
    digits = re.sub(r"\D", "", str(value).split(".")[0] if str(value).endswith(".0") else str(value))
    return digits.zfill(14) if digits else ""

def fetch_public_signals(queries=None, limit=100) -> pd.DataFrame:
    """Consulta RSS público do Google Notícias. É descoberta de sinais, não validação final."""
    records, seen = [], set()
    for query in (queries or RSS_QUERIES):
        params = urllib.parse.urlencode({"q": query, "hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"})
        url = "https://news.google.com/rss/search?" + params
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; RadarSTI/1.0)"})
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                root = ET.fromstring(response.read())
        except Exception:
            continue
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            summary = re.sub(r"<[^>]+>", " ", item.findtext("description") or "")
            published_raw = item.findtext("pubDate") or ""
            source_node = item.find("source")
            source = (source_node.text or "").strip() if source_node is not None else ""
            if not link or link in seen:
                continue
            seen.add(link)
            try:
                published = parsedate_to_datetime(published_raw).isoformat()
            except Exception:
                published = ""
            records.append({
                "titulo_sinal": title,
                "data_publicacao": published,
                "fonte": source or "Google Notícias RSS (fonte original no link)",
                "url_fonte": link,
                "resumo": re.sub(r"\s+", " ", summary).strip(),
                "consulta_origem": query,
                "data_coleta_utc": datetime.now(timezone.utc).isoformat(),
            })
            if len(records) >= limit:
                break
        if len(records) >= limit:
            break
    return pd.DataFrame(records, columns=[
        "titulo_sinal", "data_publicacao", "fonte", "url_fonte", "resumo",
        "consulta_origem", "data_coleta_utc"
    ])

def load_master(uploaded=None) -> pd.DataFrame:
    if uploaded is not None:
        name = uploaded.name.lower()
        if name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded, dtype=str)
        else:
            df = pd.read_csv(uploaded, dtype=str, encoding="utf-8-sig", low_memory=False)
    elif BASE_MESTRE_PATH.exists():
        df = pd.read_csv(BASE_MESTRE_PATH, dtype=str, encoding="utf-8-sig", low_memory=False)
    else:
        return pd.DataFrame()
    df.columns = [str(c).strip() for c in df.columns]
    cnpj_col = next((c for c in df.columns if normalize_text(c) in {"cnpj", "cnpj completo", "cnpj estabelecimento"}), None)
    if cnpj_col:
        df["_cnpj_norm"] = df[cnpj_col].map(normalize_cnpj)
    else:
        df["_cnpj_norm"] = ""
    return df

def load_catalog(uploaded) -> pd.DataFrame:
    if uploaded is None:
        return pd.DataFrame(columns=["produto_sti"])
    name = uploaded.name.lower()
    if name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded, dtype=str)
    else:
        df = pd.read_csv(uploaded, dtype=str, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    candidate = next((c for c in df.columns if normalize_text(c) in {
        "produto", "produto sti", "nome do produto", "nome produto", "servico", "servico sti", "produto servico"
    }), None)
    if candidate is None:
        # Se a planilha tiver uma única coluna, seu conteúdo é interpretado como lista de produtos.
        if len(df.columns) == 1:
            candidate = df.columns[0]
        else:
            raise ValueError("Não encontrei a coluna de nome do produto. Use uma coluna chamada 'Produto' ou 'Produto STI'.")
    products = df[candidate].dropna().astype(str).str.strip()
    products = products[products.ne("")].drop_duplicates()
    return pd.DataFrame({"produto_sti": products.tolist()})

def classify_theme(text: str) -> tuple[str, list[str]]:
    normalized = normalize_text(text)
    hits = []
    for theme, terms in THEME_TERMS.items():
        count = sum(1 for term in terms if normalize_text(term) in normalized)
        if count:
            hits.append((theme, count))
    hits.sort(key=lambda item: item[1], reverse=True)
    return (hits[0][0], [theme for theme, _ in hits]) if hits else ("revisao_manual", [])

def match_company(text: str, master: pd.DataFrame) -> dict:
    normalized = normalize_text(text)
    if master.empty:
        return {"empresa_encontrada_base": "", "cnpj": "", "municipio": "", "cnae": "", "porte": "", "relacionamento_sesi": "", "relacionamento_senai": "", "match_empresa": "Base interna não carregada"}
    # Procura aliases conhecidos e razão social/nome fantasia no texto da notícia.
    name_columns = [c for c in master.columns if normalize_text(c) in {"razao social", "nome fantasia", "empresa", "nome empresarial"}]
    for alias_company, aliases in COMPANY_ALIASES.items():
        for alias in aliases:
            if normalize_text(alias) in normalized:
                for col in name_columns:
                    mask = master[col].fillna("").map(normalize_text).str.contains(normalize_text(alias), regex=False)
                    matches = master.loc[mask]
                    if not matches.empty:
                        row = matches.iloc[0]
                        return _master_record(row, col, master, "Nome/alias localizado na base")
                # Alias detectado na notícia, mas não localizado na base interna.
                return {"empresa_encontrada_base": alias_company, "cnpj": "", "municipio": "", "cnae": "", "porte": "", "relacionamento_sesi": "", "relacionamento_senai": "", "match_empresa": "Empresa citada no sinal; não localizada automaticamente na base"}
    for col in name_columns:
        vals = master[col].fillna("").astype(str)
        for idx, value in vals.items():
            candidate = normalize_text(value)
            if len(candidate) >= 8 and candidate in normalized:
                return _master_record(master.loc[idx], col, master, "Razão social/nome localizado no texto")
    return {"empresa_encontrada_base": "", "cnpj": "", "municipio": "", "cnae": "", "porte": "", "relacionamento_sesi": "", "relacionamento_senai": "", "match_empresa": "Não identificado automaticamente; revisar"}

def _master_record(row, name_col, master, status):
    def find_col(options):
        for col in master.columns:
            if normalize_text(col) in options:
                return col
        return None
    cnpj_col = find_col({"cnpj", "cnpj completo", "cnpj estabelecimento"})
    city_col = find_col({"municipio", "município", "cidade"})
    cnae_col = find_col({"cnae primario", "cnae principal", "cnae"})
    size_col = find_col({"porte", "porte empresa"})
    sesi_col = find_col({"tem sesi", "possui sesi"})
    senai_col = find_col({"tem senai", "possui senai"})
    def val(col):
        return str(row.get(col, "") or "") if col else ""
    return {
        "empresa_encontrada_base": val(name_col),
        "cnpj": normalize_cnpj(val(cnpj_col)),
        "municipio": val(city_col),
        "cnae": val(cnae_col),
        "porte": val(size_col),
        "relacionamento_sesi": val(sesi_col),
        "relacionamento_senai": val(senai_col),
        "match_empresa": status,
    }

def match_products(text: str, catalog: pd.DataFrame, max_products=3) -> tuple[str, str]:
    if catalog.empty:
        return "Carregue o catálogo oficial STI 2026", "Não avaliado"
    theme, _ = classify_theme(text)
    if theme == "revisao_manual":
        return "Sem correspondência automática", "Baixa"
    terms = THEME_TERMS.get(theme, [])
    scored = []
    for product in catalog["produto_sti"].astype(str):
        pnorm = normalize_text(product)
        hits = [term for term in terms if normalize_text(term) in pnorm]
        if hits:
            scored.append((len(hits), product))
    scored.sort(key=lambda x: (-x[0], x[1]))
    if not scored:
        return "Sem correspondência automática — validação técnica necessária", "Baixa"
    return " | ".join(product for _, product in scored[:max_products]), "Alta" if scored[0][0] >= 2 else "Média"

def score_signal(row: pd.Series) -> dict:
    text = " ".join(str(row.get(c, "")) for c in ["titulo_sinal", "resumo"])
    norm = normalize_text(text)
    evidence = 0
    for term, points in [
        ("investimento", 25), ("expansao", 20), ("nova fabrica", 25),
        ("nova unidade", 20), ("licenca de instalacao", 20), ("contrato", 15),
        ("modernizacao", 15), ("ampliacao", 20), ("inauguracao", 15),
        ("projeto", 8), ("incentivo fiscal", 12),
    ]:
        if normalize_text(term) in norm:
            evidence = min(40, evidence + points)
    theme, _ = classify_theme(text)
    fit = 25 if theme != "revisao_manual" else 5
    recency = 20
    try:
        dt = pd.to_datetime(row.get("data_publicacao"), utc=True, errors="coerce")
        if pd.notna(dt):
            days = (pd.Timestamp.now(tz="UTC") - dt).days
            recency = 20 if days <= 30 else 15 if days <= 90 else 8 if days <= 365 else 3
    except Exception:
        recency = 5
    total = min(100, evidence + fit + recency + 15)
    priority = "Alta" if total >= 70 else "Média" if total >= 45 else "Baixa"
    return {"tema_sti": theme, "score_prioridade": total, "prioridade": priority,
            "validacao_demanda": "Não validada — sinal público não comprova intenção de compra"}

def build_pipeline(signals: pd.DataFrame, master: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    if signals.empty:
        return signals.copy()
    rows = []
    for _, signal in signals.iterrows():
        row = signal.to_dict()
        full_text = " ".join(str(row.get(c, "")) for c in ["titulo_sinal", "resumo", "fonte"])
        company = match_company(full_text, master)
        product, product_confidence = match_products(full_text, catalog)
        scoring = score_signal(pd.Series(row))
        row.update(company)
        row["produtos_sti_sugeridos"] = product
        row["confianca_matching_produto"] = product_confidence
        row.update(scoring)
        row["proximo_passo"] = (
            "Confirmar empresa/CNPJ e relacionamento no CRM; validar aderência com especialista STI; só então abordar."
            if row["prioridade"] in {"Alta", "Média"}
            else "Revisar sinal, confirmar atualidade e identificar empresa antes de encaminhar."
        )
        rows.append(row)
    result = pd.DataFrame(rows)
    if "url_fonte" in result.columns:
        result = result.drop_duplicates(subset=["url_fonte"])
    return result.sort_values(["score_prioridade", "data_publicacao"], ascending=[False, False], na_position="last")

def load_seed_signals() -> pd.DataFrame:
    """Sinais iniciais com fontes públicas verificadas; servem como seed, não como demanda validada."""
    return pd.DataFrame([
        {"titulo_sinal": "NE 4.0: projeto de transformação digital na Cooperativa Pindorama, em Coruripe",
         "data_publicacao": "2026-09-21", "fonte": "Sudene",
         "url_fonte": "https://www.gov.br/sudene/pt-br/assuntos/imprensa/ne-4-0-entrega-primeiro-projeto-de-transformacao-digital-para-industria-de-alagoas",
         "resumo": "Projeto SIOB-Flex propõe IA, sensores e Gêmeo Digital; projeto está em avaliação pela cooperativa.",
         "consulta_origem": "Sinal inicial verificado"},
        {"titulo_sinal": "Governo de Alagoas anuncia fábrica do Grupo Maratá em Pilar com investimento de R$ 400 milhões",
         "data_publicacao": "", "fonte": "SEFAZ Alagoas",
         "url_fonte": "https://www.sefaz.al.gov.br/noticias/item/3819-governo-de-alagoas-anuncia-instalacao-de-fabrica-do-grupo-marata-com-investimento-de-r-400-milhoes",
         "resumo": "Anúncio de instalação de nova fábrica; confirmar cronograma e estabelecimento local.",
         "consulta_origem": "Sinal inicial verificado"},
        {"titulo_sinal": "Natville anuncia plano de investimentos e nova planta de laticínios em Batalha",
         "data_publicacao": "2026-04-06", "fonte": "Notícias Agrícolas",
         "url_fonte": "https://www.noticiasagricolas.com.br/noticias/leite/418445-natville-acelera-investimentos-no-nordeste-e-fortalece-producao-leiteira-no-semiarido.html",
         "resumo": "Plano divulgado de expansão de produção leiteira; validar estágio atual da implantação e necessidade específica.",
         "consulta_origem": "Sinal inicial verificado"},
        {"titulo_sinal": "ANP aprova projeto de estocagem subterrânea de gás natural no campo de Pilar",
         "data_publicacao": "2025-12-19", "fonte": "ANP",
         "url_fonte": "https://www.gov.br/anp/pt-br/canais_atendimento/imprensa/noticias-comunicados/anp-aprova-minuta-de-autorizacao-para-primeiro-projeto-de-estocagem-subterranea-de-gas-do-pais",
         "resumo": "Projeto de estocagem subterrânea de gás desenvolvido pela Origem Energia Alagoas; confirmar status atual e escopo de serviços contratáveis.",
         "consulta_origem": "Sinal inicial verificado"},
    ])
