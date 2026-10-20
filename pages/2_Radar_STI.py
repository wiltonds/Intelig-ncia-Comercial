from __future__ import annotations

import pandas as pd
import streamlit as st

from sti_pipeline import (
    BASE_MESTRE_PATH,
    RSS_QUERIES,
    build_pipeline,
    fetch_public_signals,
    load_catalog,
    load_crm,
    load_master,
    load_seed_signals,
)

st.set_page_config(page_title="Radar Comercial STI | SENAI-AL", page_icon="🎯", layout="wide")
st.title("Radar de Inteligência Comercial — STI")
st.caption("Sinais públicos de mercado → empresa/estabelecimento → catálogo STI 2026 → priorização → validação comercial.")

with st.sidebar:
    st.header("Configuração do pipeline")
    st.markdown("**1. Base de empresas / relacionamento**")
    master_upload = st.file_uploader(
        "Envie a base de empresas/CRM (CSV ou XLSX)",
        type=["csv", "xlsx", "xls"],
        key="sti_master",
        help="Pode ser uma exportação do CRM ou a BASE_MESTRE_COMERCIAL. O painel não grava alterações no CRM.",
    )
    st.caption(f"Base local procurada: {BASE_MESTRE_PATH.relative_to(BASE_MESTRE_PATH.parent.parent) if BASE_MESTRE_PATH.exists() else 'saida/BASE_MESTRE_COMERCIAL.csv'}")
    st.divider()
    st.markdown("**2. Catálogo oficial STI 2026**")
    catalog_upload = st.file_uploader(
        "Envie Produtos STI 2026.xlsx ou CSV",
        type=["xlsx", "xls", "csv"],
        key="sti_catalog",
        help="O matching usa os nomes literais desta planilha. Sem catálogo, o painel não inventa nomes de produtos.",
    )
    st.divider()
    st.markdown("**3. Exportação do Moskit**")
    crm_upload = st.file_uploader(
        "Envie a exportação do Moskit (CSV ou XLSX)",
        type=["csv", "xlsx", "xls"],
        key="sti_crm",
        help="Use uma exportação autorizada com nome da empresa, CNPJ quando disponível, status, responsável e oportunidade. O arquivo é usado somente nesta sessão; o painel não altera o CRM.",
    )
    st.divider()
    st.markdown("**4. Coleta de sinais públicos**")
    max_results = st.slider("Máximo de notícias coletadas", min_value=10, max_value=100, value=50, step=10)
    st.caption("A busca por notícias descobre pistas. Ela não confirma demanda, cadastro ativo nem intenção de compra.")

try:
    master = load_master(master_upload)
except Exception as exc:
    master = pd.DataFrame()
    st.sidebar.error(f"Falha ao ler a base: {exc}")

try:
    crm = load_crm(crm_upload) if crm_upload is not None else pd.DataFrame()
    if crm_upload is not None:
        st.sidebar.success(f"Exportação CRM carregada: {len(crm):,} registros.")
except Exception as exc:
    crm = pd.DataFrame()
    st.sidebar.error(f"Falha ao ler exportação CRM: {exc}")

try:
    catalog = load_catalog(catalog_upload) if catalog_upload is not None else pd.DataFrame(columns=["produto_sti"])
    if catalog_upload is not None:
        st.sidebar.success(f"Catálogo carregado: {len(catalog)} nomes de produtos.")
except Exception as exc:
    catalog = pd.DataFrame(columns=["produto_sti"])
    st.sidebar.error(f"Falha ao ler catálogo: {exc}")

if "sti_signals" not in st.session_state:
    st.session_state["sti_signals"] = load_seed_signals()

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    if st.button("Buscar sinais públicos agora", type="primary", use_container_width=True):
        with st.spinner("Consultando feeds públicos de notícias..."):
            found = fetch_public_signals(limit=max_results)
        if found.empty:
            st.warning("A coleta RSS não retornou resultados. Mantive os sinais iniciais; tente novamente mais tarde.")
        else:
            st.session_state["sti_signals"] = found
            st.success(f"{len(found)} sinais coletados. Revise fonte, data e conteúdo antes de encaminhar.")
with col_b:
    if st.button("Recarregar sinais iniciais", use_container_width=True):
        st.session_state["sti_signals"] = load_seed_signals()
with col_c:
    st.info("Fontes-semente incluem Sudene, SEFAZ-AL, ANP e notícia setorial. Novos sinais coletados via RSS devem ser confirmados na publicação original.")

signals = st.session_state["sti_signals"].copy()
pipeline = build_pipeline(signals, master, catalog, crm)

# KPIs
total = len(pipeline)
high = int((pipeline.get("prioridade", pd.Series(dtype=str)) == "Alta").sum())
identified = int(pipeline.get("cnpj", pd.Series(dtype=str)).fillna("").astype(str).str.len().eq(14).sum())
unvalidated = int(pipeline.get("validacao_demanda", pd.Series(dtype=str)).str.startswith("Não validada").sum())
k1, k2, k3, k4 = st.columns(4)
k1.metric("Sinais no radar", total)
k2.metric("Prioridade alta", high)
k3.metric("CNPJ identificado na base", identified)
k4.metric("Demanda ainda não validada", unvalidated)

st.subheader("1. Filtros de priorização")
f1, f2, f3 = st.columns(3)
with f1:
    priorities = sorted(pipeline["prioridade"].dropna().unique().tolist()) if "prioridade" in pipeline else []
    selected_priority = st.multiselect("Prioridade", priorities, default=priorities)
with f2:
    themes = sorted(pipeline["tema_sti"].dropna().unique().tolist()) if "tema_sti" in pipeline else []
    selected_theme = st.multiselect("Tema STI inferido", themes, default=themes)
with f3:
    match_statuses = sorted(pipeline["match_empresa"].dropna().unique().tolist()) if "match_empresa" in pipeline else []
    selected_match = st.multiselect("Identificação da empresa", match_statuses, default=match_statuses)

filtered = pipeline.copy()
if selected_priority and "prioridade" in filtered:
    filtered = filtered[filtered["prioridade"].isin(selected_priority)]
if selected_theme and "tema_sti" in filtered:
    filtered = filtered[filtered["tema_sti"].isin(selected_theme)]
if selected_match and "match_empresa" in filtered:
    filtered = filtered[filtered["match_empresa"].isin(selected_match)]

st.subheader("2. Oportunidades candidatas para validação")
display_cols = [
    "prioridade", "score_prioridade", "titulo_sinal", "data_publicacao", "fonte",
    "empresa_encontrada_base", "cnpj", "municipio", "cnae", "porte",
    "relacionamento_sesi", "relacionamento_senai", "crm_encontrado", "crm_empresa", "crm_cnpj", "crm_status", "crm_responsavel", "crm_oportunidade", "crm_metodo_match", "produtos_sti_sugeridos",
    "confianca_matching_produto", "validacao_demanda", "proximo_passo", "url_fonte",
]
display_cols = [c for c in display_cols if c in filtered.columns]
if filtered.empty:
    st.warning("Nenhum registro corresponde aos filtros.")
else:
    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "url_fonte": st.column_config.LinkColumn("Fonte original", display_text="Abrir notícia"),
            "score_prioridade": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
        },
    )
    st.download_button(
        "Baixar oportunidades filtradas (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name="radar_oportunidades_sti_al.csv",
        mime="text/csv",
    )

with st.expander("Como a priorização funciona e o que ainda precisa ser validado"):
    st.markdown(
        """
        - **Sinal de mercado:** evidência pública localizada em notícia ou fonte oficial.
        - **Aderência STI:** sugestão baseada em palavras-chave e nos nomes do catálogo carregado; não substitui parecer técnico.
        - **Identificação da empresa:** correspondência automática com a base enviada/local. CNPJ em branco significa que não foi confirmado.
        - **Relacionamento SESI/SENAI:** flags vêm exclusivamente da base mestre carregada.
        - **CRM/Moskit:** cruzamento local da exportação enviada, priorizando CNPJ exato e depois nome exato; correspondência aproximada só é sugerida quando única e requer confirmação. O painel não acessa nem altera o Moskit.
        - **Privacidade:** a exportação é processada em memória durante a sessão e não é incorporada à base mestre nem enviada de volta ao CRM.
        - **Demanda validada:** permanece como não validada até que comercial/técnico confirme necessidade, prazo, orçamento e responsável.
        - **Score:** indicador heurístico para triagem, não probabilidade estatística nem previsão de receita.
        """
    )

with st.expander("Consultas usadas na descoberta de sinais"):
    for query in RSS_QUERIES:
        st.write(f"• {query}")


st.subheader("3. Fontes públicas prioritárias de Alagoas")
st.markdown(
    """
    - [Radar de Investimentos — SEFAZ-AL](https://data.amerigeoss.org/dataset/radar-de-investimentos-alagoas): investimentos, benefícios fiscais e contexto econômico.
    - [Portal da Transparência — API](https://www.transparencia.al.gov.br/portal/api): consultas estruturadas em JSON; endpoints específicos devem ser mapeados antes da ingestão automática.
    - [IMA-AL — Licenciamento ambiental](https://www2.ima.al.gov.br/licenciamento/): licenças, autorizações e processos ambientais disponíveis publicamente.
    - [Receita Federal — Dados abertos CNPJ](https://www.gov.br/receitafederal/dados): cadastro oficial para enriquecimento em lote; os arquivos são volumosos e exigem rotina de atualização.
    - [Sudene — projeto NE 4.0 em Alagoas](https://www.gov.br/sudene/pt-br/assuntos/imprensa/ne-4-0-entrega-primeiro-projeto-de-transformacao-digital-para-industria-de-alagoas): sinal oficial de transformação digital na Cooperativa Pindorama.
    """
)
st.caption("Nesta versão, a coleta automatizada implementada é a descoberta via RSS. As fontes estruturadas acima estão catalogadas para integração incremental; ainda não são todas ingeridas automaticamente.")
\nst.caption("MVP STI — valide o sinal na fonte original, confirme matriz/filial e CNPJ, confira relacionamento no CRM e registre o resultado da validação comercial.")
