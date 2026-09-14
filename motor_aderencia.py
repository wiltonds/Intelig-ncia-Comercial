"""
Motor de aderência Portfólio × CNPJ — SESI/SENAI Alagoas
Adaptado às colunas da BASE_MESTRE_COMERCIAL.csv.

Usa: cnae_fiscal_codigo (ou 'CNAE PRIMARIO' code), Porte,
     STATUS_RELACIONAMENTO_REAL, POSSUI_SESI, POSSUI_SENAI.
Arquivos de apoio: de_para_cnae_area.csv, portfolio_compact.json
"""
import json, re, pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
UNIVERSAIS = {'1 - Gestão': 1.0, '27 - Segurança do trabalho': 1.0,
              '32 - Meio ambiente': 0.8, '48 - Logística': 0.7}

def _carregar(depara_csv=None, portfolio_json=None):
    depara_csv = depara_csv or (BASE_DIR / 'de_para_cnae_area.csv')
    portfolio_json = portfolio_json or (BASE_DIR / 'portfolio_compact.json')
    dp = pd.read_csv(depara_csv, dtype={'divisao_cnae': str})
    depara = {}
    for _, r in dp.iterrows():
        depara.setdefault(str(r['divisao_cnae']).zfill(2), []).append(
            (r['area_senai'], float(r['peso_afinidade'])))
    tree = json.load(open(portfolio_json, encoding='utf-8'))['trees']['SENAI']
    contagem = {}
    def _f(n):
        if not n.get('ch') and n.get('a'):
            contagem[n['a']] = contagem.get(n['a'], 0) + 1
        for c in n.get('ch', []): _f(c)
    _f(tree)
    return depara, contagem

_DEPARA, _CONTAGEM = None, None
def _ensure():
    global _DEPARA, _CONTAGEM
    if _DEPARA is None:
        _DEPARA, _CONTAGEM = _carregar()

def _divisao(cnae_code):
    d = re.sub(r'\D', '', str(cnae_code))
    return d.zfill(7)[:2] if d else '00'

def _gate(porte):
    p = (porte or '').upper()
    if 'MICRO' in p:  return 0.6, 0.4, 'SEBRAE-first'
    if 'PEQUEN' in p: return 0.85, 0.7, 'SENAI/SEBRAE'
    return 1.0, 1.0, 'SENAI/SESI'

def diagnosticar(cnae_code, porte, ja_sesi=False, ja_senai=False):
    """Retorna o diagnóstico de aderência de um CNPJ ao portfólio."""
    _ensure()
    div = _divisao(cnae_code)
    g_set, g_uni, rota = _gate(porte)
    res = {}
    for area, peso in _DEPARA.get(div, []):
        res[area] = max(res.get(area, 0), peso * g_set)
    tem_setorial = len(res) > 0
    for area, base in UNIVERSAIS.items():
        res[area] = max(res.get(area, 0), base * g_uni)
    areas = sorted(
        ({'area': a, 'score': round(s, 3), 'n_produtos': _CONTAGEM.get(a, 0),
          'tipo': 'universal' if a in UNIVERSAIS else 'setorial'} for a, s in res.items()),
        key=lambda x: -x['score'])
    # cross-sell: já é cliente de um, oferecer o outro
    if ja_sesi and not ja_senai:   cross = 'SENAI (já é cliente SESI)'
    elif ja_senai and not ja_sesi: cross = 'SESI (já é cliente SENAI)'
    elif ja_sesi and ja_senai:     cross = 'Aprofundar carteira (já tem os dois)'
    else:                          cross = 'Prospect novo'
    return {'divisao': div, 'rota': rota, 'cross_sell': cross,
            'tem_encaixe_setorial': tem_setorial,
            'score_max': areas[0]['score'] if areas else 0.0, 'areas': areas}

def scorear_base(df, col_cnae='cnae_fiscal_codigo', col_porte='Porte',
                 col_sesi='POSSUI_SESI', col_senai='POSSUI_SENAI'):
    """Aplica a toda a base. Colunas ausentes viram False/0 sem quebrar."""
    _ensure()
    def _linha(r):
        return diagnosticar(r.get(col_cnae), r.get(col_porte),
                            bool(r.get(col_sesi, False)), bool(r.get(col_senai, False)))
    out = df.apply(_linha, axis=1)
    df = df.copy()
    df['ADER_divisao']   = out.map(lambda x: x['divisao'])
    df['ADER_rota']      = out.map(lambda x: x['rota'])
    df['ADER_cross']     = out.map(lambda x: x['cross_sell'])
    df['ADER_score_max'] = out.map(lambda x: x['score_max'])
    df['ADER_top_areas'] = out.map(lambda x: '; '.join(
        f"{a['area']} ({a['score']})" for a in x['areas'][:3]))
    df['_ADER_full']     = out.map(lambda x: x['areas'])
    return df

def fila_prospeccao(df_scored, area_alvo, apenas_sem_relacionamento=True,
                    col_status='STATUS_RELACIONAMENTO_REAL'):
    """Leitura 2: dado um alvo, ordena os CNPJs mais aderentes (fila do SDR)."""
    linhas = []
    for _, r in df_scored.iterrows():
        for a in r['_ADER_full']:
            if a['area'] == area_alvo:
                d = r.drop('_ADER_full').to_dict()
                d['score_area'] = a['score']
                linhas.append(d)
                break
    out = pd.DataFrame(linhas)
    if len(out):
        out = out.sort_values('score_area', ascending=False)
        if apenas_sem_relacionamento and col_status in out.columns:
            out = out[out[col_status].astype(str).str.contains('SEM RELAC', case=False, na=False)]
    return out
