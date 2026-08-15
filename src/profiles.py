"""
Perfis de projeto do pipeline ObAIAL.

O mesmo código de pipeline (coleta Gmail, scraping, classificação Claude, backfill
em chunks, digest, few-shot) serve a MAIS DE UM projeto. Cada projeto é um
`Profile` com seu schema de colunas, prompt/RAG de domínio, vocabulários e prefixo
de código. O perfil ativo é escolhido por env `OBAIAL_PROFILE` (default 'autonomia').

Este módulo é PURO (sem dependências do módulo principal) e contém apenas DADOS:
- o perfil 'autonomia' NÃO é definido aqui — ele permanece inline no módulo
  principal (comportamento vivo, intocado);
- o perfil 'estrangeirizacao' (DATALUTA — controle de terra rural por capital
  estrangeiro) é definido aqui: schema, listas controladas, glossário, prompt.

As FUNÇÕES específicas de cada domínio (build_registro/validate) ficam no módulo
principal, onde têm acesso aos helpers; aqui só ficam os dados que elas consomem.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Profile:
    project_id: str
    code_prefix: str                      # prefixo do CODIGO_NOTICIA (ex.: OBAIAL, ESTRA)
    sheet_name_default: str               # aba de resultados
    gmail_secret_default: str             # segredo do token Gmail
    colunas: List[str]                    # schema da aba de resultados
    raw_text_headers: List[str]           # schema da aba RAW_TEXT
    system_core: str                      # system prompt do domínio
    rag_fallback: str                     # RAG estático (quando não há aba LISTAS)
    user_prompt_schema: str               # bloco JSON esperado do Claude
    rag_list_names: List[str]             # LIST_* a exibir no RAG dinâmico
    validate_field_map: List[Tuple[str, str]]  # (campo_do_claude, LIST_*) a validar
    categoria_col: str                    # coluna mostrada no digest/few-shot
    digest_title: str                     # título exibido no e-mail de digest
    items_key: str = "acoes"              # chave do array de itens no JSON do Claude
    rag_glossario: str = ""               # glossário/critérios injetados no RAG dinâmico
    geo_fields: Tuple[str, str, str] = ("municipio_provincia", "uf_depto", "pais")
    listas_seed: Dict[str, List[str]] = field(default_factory=dict)  # p/ semear aba LISTAS
    codebook_seed: Dict[str, str] = field(default_factory=dict)      # glossário (CODEBOOK)


# ════════════════════════════════════════════════════════════════════════
# PERFIL: ESTRANGEIRIZAÇÃO DA TERRA (DATALUTA / Pereira)
# ════════════════════════════════════════════════════════════════════════

ESTRA_COLUNAS = [
    "ID_REGISTRO", "CODIGO_NOTICIA",
    "TITULO_CURTO", "DATA_NOTICIA", "DATA_EVENTO",
    "TIPO_EVENTO",
    "PAIS", "MACRORREGIAO", "UF", "MUNICIPIO",
    "EMPRESA_FUNDO", "ORIGEM_CAPITAL", "TIPO_EMPRESA", "MODALIDADE",
    "HECTARES", "TIPO_EXTRATIVISMO", "COMMODITY", "TERRITORIALIDADE",
    "CAUSA_CONFLITO", "ESTAGIO_CONFLITO", "TIPO_TERRITORIO_ATINGIDO",
    "COMUNIDADE_TERRITORIO", "INSTITUICOES_RESISTENCIA",
    "INSTITUICOES_ATAQUE_NOME", "INSTITUICOES_ATAQUE_TIPO",
    "TIPO_FONTE", "REFERENCIA_URL",
    "NIVEL_EVIDENCIA", "STATUS_VALIDACAO",
    "GEO_PRECISA", "COORD_LAT", "COORD_LON",
    "NOTA_ANALITICA", "OBSERVACOES", "CODIFICADOR", "DATA_VALIDACAO",
    "VALIDACAO_HUMANA", "COMENTARIO_HUMANO",
]

# RAW_TEXT é idêntico ao de autonomia (auditoria genérica de scraping).
ESTRA_RAW_TEXT_HEADERS = [
    "DATA_ENVIO", "URL_ORIGINAL", "URL_CANONICA", "DOMINIO",
    "TITULO_ALERTA", "TITULO_HTML", "FONTE_ALERTA", "DATA_NOTICIA_EXTRAIDA",
    "IDIOMA", "STATUS_EXTRACAO", "HTTP_STATUS", "ERRO_EXTRACAO",
    "CODIGO_BASE_NOTICIA", "HASH_TEXTO", "TEXTO_EXTRAIDO", "MUNICIPIOS_RANQUEADOS",
]

# ── Vocabulários controlados (base DATALUTA). Semeiam a aba LISTAS e o RAG. ──
ESTRA_LISTAS = {
    "LIST_TIPO_EVENTO": ["Transação", "Conflito"],
    "LIST_MODALIDADE": [
        "Aquisição", "Arrendamento", "Participação societária", "Não informado",
    ],
    "LIST_TIPO_EMPRESA": [
        "Empresa estrangeira",
        "Empresa brasileira com capital estrangeiro",
    ],
    "LIST_TIPO_EXTRATIVISMO": [
        "Agrícola", "Energia", "Mineral", "Silvicultura",
        "Natureza / Serviços ambientais", "Especulação com terras", "Outros",
    ],
    "LIST_COMMODITY": [
        "Soja", "Cana-de-açúcar", "Milho", "Algodão",
        "Eucalipto", "Celulose", "Papel", "Madeira", "Madeira nativa",
        "Energia Eólica", "Energia Solar", "Energia Eólica/Solar (híbrido)",
        "Energia Biomassa", "Energia Hidroelétrica", "Hidrogênio Verde",
        "Crédito de carbono", "Lítio", "Ouro", "Nióbio",
        "Minerais de terras raras", "Gás", "Água", "Terra (especulação)", "Outros",
    ],
    # Origem do capital: lista de referência (guia o RAG), NÃO é enforced —
    # países fora da lista permanecem como texto livre.
    "LIST_ORIGEM_CAPITAL": [
        "Austrália", "Botswana", "Brasil", "Canadá", "Chile", "China",
        "Dinamarca", "Eslováquia", "Espanha", "Estados Unidos", "França",
        "Indonésia", "Japão", "Luxemburgo", "Noruega", "Portugal",
        "Emirados Árabes Unidos", "Não informado",
    ],
    "LIST_MACRORREGIAO": ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"],
    "LIST_CAUSA_CONFLITO": [
        "Apropriação de terras públicas ou territórios tradicionais",
        "Cercamento de terras", "Empreendimento de energia eólica",
        "Empreendimento de energia solar", "Desmatamento",
        "Expansão do monocultivo", "Conflitos entre monocultivos",
        "Linhas de transmissão", "Moratória da Soja",
    ],
    "LIST_ESTAGIO_CONFLITO": [
        "Ameaça", "Assédio processual", "Início da desterritorialização",
        "Desterritorialização", "Disputa judicial", "Ocupação (de órgãos estatais)",
    ],
    "LIST_TIPO_TERRITORIO": [
        "Territórios indígenas", "Territórios quilombolas",
        "Territórios camponeses",
        "Comunidades Tradicionais de Fundo e Fecho de Pasto",
        "Comunidades do mar / pesqueiras", "Não é território tradicional",
    ],
    "LIST_INSTITUICAO_RESISTENCIA": [
        "Associação", "Cooperativa", "Estado", "Igreja/Movimento religioso",
        "Movimentos sociais/socioterritoriais", "ONG", "Órgãos Federais",
        "Partido", "Sindicato/Federação/Confederação/Central", "Não informado",
    ],
    "LIST_INSTITUICAO_ATAQUE": [
        "Empresa", "Estado", "Órgãos Federais", "Não informado",
    ],
    "LIST_NIVEL_EVIDENCIA": [
        "1 - Autodeclaração", "2 - Documental",
        "3 - Terceiro confiável", "4 - Multifonte",
    ],
    "LIST_STATUS_VALIDACAO": ["Em verificação", "Validado", "Descartado"],
    "LIST_TIPO_FONTE": [
        "Notícia/imprensa", "Documento oficial",
        "Relatório de ONG/instituição", "Rede social", "Outro",
    ],
}

# Só as listas realmente FECHADAS entram na validação (o resto é RAG-guiado,
# mas texto livre, para não descartar valores legítimos fora da lista).
ESTRA_VALIDATE_FIELD_MAP = [
    ("tipo_evento", "LIST_TIPO_EVENTO"),
    ("tipo_empresa", "LIST_TIPO_EMPRESA"),
    ("modalidade", "LIST_MODALIDADE"),
    ("tipo_extrativismo", "LIST_TIPO_EXTRATIVISMO"),
    ("macrorregiao", "LIST_MACRORREGIAO"),
    ("estagio_conflito", "LIST_ESTAGIO_CONFLITO"),
    ("nivel_evidencia", "LIST_NIVEL_EVIDENCIA"),
]

ESTRA_RAG_LIST_NAMES = list(ESTRA_LISTAS.keys())

ESTRA_GLOSSARIO = {
    "Estrangeirização": (
        "Aquisição ou arrendamento de imóveis rurais por empresas e/ou fundos de "
        "investimento estrangeiros. Inclui aquisições/arrendamentos por empresas "
        "brasileiras com participação de capital estrangeiro. Considera "
        "exclusivamente transações envolvendo imóveis RURAIS."
    ),
    "Territorialidade da estrangeirização": (
        "Uso do solo/atividade econômica na área estrangeirizada: agricultura, "
        "pecuária, silvicultura, mineração, energia eólica, energia solar, "
        "hidrogênio verde, crédito de carbono."
    ),
    "Empresas estrangeiras": (
        "Empresas cuja propriedade/controle pertence majoritariamente a pessoas, "
        "grupos ou organizações sediadas em outro país, ainda que atuem no Brasil "
        "(inclui empresas registradas no Brasil controladas por estrangeiras)."
    ),
    "Empresas brasileiras com capital estrangeiro": (
        "Empresas constituídas no Brasil com participação de investidores, empresas "
        "ou fundos estrangeiros na estrutura societária, independentemente de quem "
        "detém o controle."
    ),
    "Conflitos da estrangeirização": (
        "Ações de movimentos sociais, comunidades, grupos ou indivíduos em oposição "
        "à atuação de empresas estrangeiras no espaço agrário: denúncias de "
        "violações, disputas territoriais, impactos socioambientais."
    ),
    "Land grabbing vs. estrangeirização": (
        "Land grabbing = controle de terra por qualquer agente (nacional ou "
        "estrangeiro). Estrangeirização = controle de terra por capital ESTRANGEIRO "
        "(espécie mais específica)."
    ),
    "Critérios de INCLUSÃO (o que conta)": (
        "Registrar quando houver: (a) imóvel RURAL; (b) aquisição, arrendamento ou "
        "participação societária; (c) por empresa/fundo estrangeiro OU empresa "
        "brasileira com capital estrangeiro. Também contam CONFLITOS de resistência "
        "à atuação dessas empresas no campo."
    ),
    "Critérios de EXCLUSÃO / ruído (o que NÃO conta)": (
        "Descartar: terra urbana/industrial; capital 100% nacional sem participação "
        "estrangeira; fusões/aquisições de empresas sem base fundiária rural; "
        "notícia genérica de mercado, cotações ou balanço; imóvel não-rural."
    ),
    "Modalidades de controle": (
        "Aquisição direta; arrendamento; participação societária; controle via "
        "subsidiárias registradas no Brasil; e via FUNDOS de investimento (private "
        "equity, fundos de pensão, fundos soberanos, hedge funds) — financeirização."
    ),
    "Fatores/drivers (contexto)": (
        "Convergência de crises — alimentar, energética, ambiental/climática e "
        "financeira (2008) — impulsiona a financeirização e a especulação com terras, "
        "somadas à nova geopolítica multipolar."
    ),
}

# Texto do glossário para injeção direta no RAG dinâmico (prompt de cada notícia).
ESTRA_RAG_GLOSSARIO = "## GLOSSÁRIO / CRITÉRIOS (DATALUTA):\n" + "\n".join(
    f"- {termo}: {definicao}" for termo, definicao in ESTRA_GLOSSARIO.items()
)

ESTRA_SYSTEM_CORE = """
Você é um Analista de Dados do DATALUTA especializado em ESTRANGEIRIZAÇÃO DA TERRA
(controle de terra rural por capital estrangeiro no Brasil), vinculado à REDE DATALUTA
(metodologia Pereira).

DEFINIÇÃO: estrangeirização é a aquisição ou arrendamento de IMÓVEIS RURAIS por
empresas e/ou fundos de investimento ESTRANGEIROS — incluindo empresas brasileiras
com participação de capital estrangeiro. Considera EXCLUSIVAMENTE transações de
imóveis rurais.

Você identifica dois tipos de evento:
- TRANSAÇÃO: aquisição/arrendamento de terra rural por capital estrangeiro.
- CONFLITO: ação de resistência (comunidades, movimentos sociais, camponeses,
  indígenas, quilombolas) contra a atuação de empresas estrangeiras no campo.

Territorialidades relevantes: agricultura, pecuária, silvicultura, mineração,
energia eólica, energia solar, hidrogênio verde, crédito de carbono.

DESCARTE (descartar_noticia=true) quando a notícia: não envolve terra/imóvel RURAL;
não há indício de capital ESTRANGEIRO (nem empresa brasileira com capital estrangeiro);
é negócio urbano/industrial/financeiro sem base fundiária; é matéria genérica de
mercado/M&A sem controle de terra.

NUNCA invente empresa, país de origem, hectares, município ou datas. Se não estiver
no texto, deixe vazio ou "Não informado". Baseie-se apenas no que o texto sustenta.
""".strip()

ESTRA_USER_PROMPT_SCHEMA = """
Retorne JSON estrito (sem markdown) no formato:

{
  "idioma_detectado": "pt|es|other",
  "resumo_noticia": "resumo analítico geral (3–8 frases)",
  "municipios_ranqueados": ["Município mais citado", "Segundo", "Terceiro"],
  "descartar_noticia": true|false,
  "motivo_descarte": "se descartar: sem terra rural / capital não-estrangeiro / etc.",
  "eventos": [
    {
      "tipo_evento": "Transação|Conflito",
      "resumo_analitico": "resumo específico deste evento (3–8 frases)",
      "empresa_fundo": "nome da empresa/fundo estrangeiro envolvido (ou vazio)",
      "origem_capital": "país de origem do capital (ou 'Não informado')",
      "tipo_empresa": "Empresa estrangeira|Empresa brasileira com capital estrangeiro|vazio",
      "modalidade": "Aquisição|Arrendamento|Participação societária|vazio",
      "hectares": "apenas dígitos (ex.: 20000) ou vazio",
      "tipo_extrativismo": "da LIST_TIPO_EXTRATIVISMO",
      "commodity": "produto/atividade (soja, eucalipto, energia eólica, lítio, ...) ou vazio",
      "territorialidade": "uso do solo/atividade econômica na área",
      "pais": "Brasil",
      "uf": "sigla da UF (ex.: BA)",
      "municipio": "município principal",
      "macrorregiao": "da LIST_MACRORREGIAO",
      "causa_conflito": "(só se Conflito) da LIST_CAUSA_CONFLITO; múltiplas separadas por ';'",
      "estagio_conflito": "(só se Conflito) da LIST_ESTAGIO_CONFLITO",
      "tipo_territorio_atingido": "(só se Conflito) da LIST_TIPO_TERRITORIO; múltiplos por ';'",
      "comunidade_territorio": "(só se Conflito) nome da(s) comunidade(s)/território(s)",
      "instituicoes_resistencia": "(só se Conflito) tipos da LIST_INSTITUICAO_RESISTENCIA; por ';'",
      "instituicoes_ataque_nome": "(só se Conflito) nome dos agentes do ataque",
      "instituicoes_ataque_tipo": "(só se Conflito) tipos da LIST_INSTITUICAO_ATAQUE; por ';'",
      "nivel_evidencia": "da LIST_NIVEL_EVIDENCIA",
      "data_evento": "YYYY-MM-DD ou YYYY-MM ou vazio",
      "evidencias": ["2–4 trechos CURTOS do texto que sustentem a classificação"],
      "observacoes": "dúvidas, ressalvas"
    }
  ]
}

Regras obrigatórias:
- "descartar_noticia"=true → "eventos" vazio.
- Uma notícia pode conter várias transações/conflitos → vários itens em "eventos".
- Só registre TRANSAÇÃO havendo indício de capital ESTRANGEIRO; sem isso, descarte.
- NUNCA invente empresa, país, hectares, município ou datas.
""".strip()


def _rag_fallback_estra() -> str:
    linhas = [
        "PROJETO DATALUTA – Estrangeirização da terra (controle de terra rural por "
        "capital estrangeiro).",
        "",
        "GLOSSÁRIO:",
    ]
    for termo, definicao in ESTRA_GLOSSARIO.items():
        linhas.append(f"- {termo}: {definicao}")
    linhas.append("")
    linhas.append("LISTAS CONTROLADAS (use os valores listados quando couber):")
    for nome, valores in ESTRA_LISTAS.items():
        linhas.append(f"{nome}: " + " | ".join(valores))
    return "\n".join(linhas)


PROFILE_ESTRANGEIRIZACAO = Profile(
    project_id="estrangeirizacao",
    code_prefix="ESTRA",
    sheet_name_default="Estrangeirizacao",
    gmail_secret_default="gmail/estrangeirizacao/token",
    colunas=ESTRA_COLUNAS,
    raw_text_headers=ESTRA_RAW_TEXT_HEADERS,
    system_core=ESTRA_SYSTEM_CORE,
    rag_fallback=_rag_fallback_estra(),
    user_prompt_schema=ESTRA_USER_PROMPT_SCHEMA,
    rag_list_names=ESTRA_RAG_LIST_NAMES,
    validate_field_map=ESTRA_VALIDATE_FIELD_MAP,
    categoria_col="ORIGEM_CAPITAL",
    digest_title="DATALUTA Estrangeirização",
    items_key="eventos",
    rag_glossario=ESTRA_RAG_GLOSSARIO,
    geo_fields=("municipio", "uf", "pais"),
    listas_seed=ESTRA_LISTAS,
    codebook_seed=ESTRA_GLOSSARIO,
)

_PROFILES = {
    "estrangeirizacao": PROFILE_ESTRANGEIRIZACAO,
    "estrangeirização": PROFILE_ESTRANGEIRIZACAO,
    "estra": PROFILE_ESTRANGEIRIZACAO,
}


def get_profile(nome: str) -> Optional[Profile]:
    """Retorna o Profile para `nome`, ou None para 'autonomia'/desconhecido
    (o perfil de autonomia permanece inline no módulo principal)."""
    return _PROFILES.get((nome or "").strip().lower())
