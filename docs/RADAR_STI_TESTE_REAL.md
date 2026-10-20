# Teste real do Radar STI — SENAI-AL

## Objetivo do piloto

Validar o fluxo de sinais públicos → empresa/estabelecimento → catálogo STI 2026 → exportação do Moskit → triagem comercial/técnica. O piloto não grava no CRM nem altera a base mestre.

## Antes de executar

1. **Privacidade primeiro:** confirme que o repositório está privado antes de usar dados empresariais/CRM. A base mestre e outros arquivos empresariais não devem ficar em um repositório público. Tornar privado não remove cópias do histórico; revisar histórico, acessos e eventual necessidade de rotação de credenciais.
2. Instale dependências: `pip install -r requirements.txt`.
3. Execute a partir da raiz do repositório: `streamlit run app.py`.
4. Abra a página **Radar de Inteligência Comercial — STI**.
5. Confirme que `saida/BASE_MESTRE_COMERCIAL.csv` é a base vigente, gerada pelo pipeline oficial. Não gere nem mantenha uma segunda base paralela para o Radar.

## Arquivos usados no piloto

- **Base mestre:** `saida/BASE_MESTRE_COMERCIAL.csv` — fonte de CNPJ, razão social/nome fantasia quando presentes, município, CNAE e flags de relacionamento SESI/SENAI.
- **Catálogo:** `Produtos STI 2026.xlsx` — carregar a versão oficial vigente. O painel deve preservar literalmente os nomes de produto dessa planilha. Se não conseguir identificar a coluna, parar e mapear a coluna correta; não criar rótulos substitutos.
- **Moskit:** exportação autorizada em CSV/XLSX. Carregar na sessão para comparação, sem incorporar à base mestre e sem escrever no Moskit.

## Mapeamento mínimo da exportação Moskit

O painel procura colunas por nomes comuns. Para matching confiável, incluir:

- Nome da empresa/conta;
- CNPJ, se disponível;
- Status/etapa;
- Responsável;
- Nome da oportunidade.

Se o cabeçalho real não for reconhecido, adaptar o mapeamento com base no arquivo de exportação real antes de considerar o resultado validado. Não carregar tokens, senhas ou dados pessoais desnecessários.

## Ordem de validação

1. Confirmar que o catálogo foi lido e contar os produtos únicos; comparar os nomes exibidos com a planilha original.
2. Conferir 5–10 empresas manualmente: razão social, CNPJ completo, município, CNAE e flags SESI/SENAI.
3. Conferir o cruzamento com Moskit por CNPJ exato. Quando houver match por nome, validar manualmente. Múltiplos registros devem ser revisados, nunca deduplicados automaticamente.
4. Abrir cada fonte original do sinal e registrar se o sinal é recente, factual e pertinente à operação em Alagoas.
5. Verificar se o produto sugerido existe literalmente no catálogo. A sugestão automática é triagem, não parecer técnico.
6. Comercial/técnico registra se há demanda validada, prazo, responsável, orçamento e próximo passo. Notícia de investimento sozinha não significa intenção de compra.

## Critérios de aceite

- Nenhum produto sugerido aparece com nome diferente do catálogo oficial.
- CNPJ ausente ou ambíguo fica explícito; não é preenchido por inferência.
- CRM distingue não localizado, localizado e múltiplos registros.
- Cada oportunidade tem link de fonte e data de publicação quando disponíveis.
- Score é identificado como heurístico e não como probabilidade de venda.
- A exportação do radar contém só os campos necessários e é armazenada conforme as regras internas de segurança.
- Comercial e área técnica revisam os primeiros 30–50 sinais antes de usar o painel como rotina operacional.

## Limitações atuais do MVP

- Descoberta automática implementada via RSS; os portais estruturados de AL estão documentados para integrações posteriores, não totalmente ingeridos.
- A identificação automática de empresas é conservadora e baseada em nomes/aliases; é necessário validar matriz, filial e grupo econômico.
- A aderência de produto usa palavras-chave e nomes literais do catálogo; não interpreta requisitos técnicos detalhados nem substitui avaliação de especialista.
- A exportação Moskit é lida localmente na sessão; não há integração direta com a API nem atualização de registros.
