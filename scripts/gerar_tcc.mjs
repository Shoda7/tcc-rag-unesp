import {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, Header, TableOfContents, PageBreak, VerticalAlign
} from "docx";
import { writeFileSync } from "fs";

// A4 + margens ABNT (DXA: 1 polegada = 1440 DXA = 2,54 cm)
const A4_W = 11906, A4_H = 16838;
const M_TOP = 1701, M_BOT = 1134, M_LEFT = 1701, M_RIGHT = 1134;
const CONTENT_W = A4_W - M_LEFT - M_RIGHT; // ~9071 DXA

const FONT = "Times New Roman";
const SIZE = 24;   // 12 pt (half-points)
const SIZE_SM = 20; // 10 pt

// ── helpers ────────────────────────────────────────────────────────────────
const br = () => new Paragraph({ children: [] });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

const titulo = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  alignment: AlignmentType.CENTER,
  spacing: { before: 0, after: 280 },
  children: [new TextRun({ text: text.toUpperCase(), font: FONT, size: SIZE, bold: true })]
});

const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 280, after: 140 },
  children: [new TextRun({ text, font: FONT, size: SIZE, bold: true })]
});

const h3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 200, after: 100 },
  children: [new TextRun({ text, font: FONT, size: SIZE, bold: true })]
});

const p = (text, opts = {}) => new Paragraph({
  alignment: AlignmentType.JUSTIFIED,
  indent: { firstLine: 709 }, // 1,25 cm
  spacing: { line: 360, lineRule: "auto" }, // 1,5
  children: [new TextRun({ text, font: FONT, size: SIZE, ...opts })]
});

const pSR = (text, opts = {}) => new Paragraph({ // sem recuo
  alignment: AlignmentType.JUSTIFIED,
  spacing: { line: 360, lineRule: "auto" },
  children: [new TextRun({ text, font: FONT, size: SIZE, ...opts })]
});

const pC = (text, opts = {}) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { line: 360, lineRule: "auto" },
  children: [new TextRun({ text, font: FONT, size: SIZE, ...opts })]
});

const alinea = (letter, text) => new Paragraph({
  alignment: AlignmentType.JUSTIFIED,
  indent: { left: 709, firstLine: 0 },
  spacing: { line: 360, lineRule: "auto" },
  children: [new TextRun({ text: `${letter}) ${text}`, font: FONT, size: SIZE })]
});

const caption = (text) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 80, after: 80, line: 300, lineRule: "auto" },
  children: [new TextRun({ text, font: FONT, size: SIZE_SM, bold: true })]
});

// ── tabela de resultados (métricas) ─────────────────────────────────────────
const border = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
const borders = { top: border, bottom: border, left: border, right: border };

const RESULT_COL_W = [2400, 1600, 1800, 1900];
const resultRows = [
  ["Métrica",         "Vetorial", "FTS (BM25)", "Híbrido RRF"],
  ["Hit@1",           "0,520",    "0,400",      "0,560 *"],
  ["Hit@3",           "0,740",    "0,520",      "0,840 *"],
  ["Hit@5",           "0,840",    "0,520",      "0,900 *"],
  ["MRR",             "0,642",    "0,457",      "0,697 *"],
  ["Latência (ms)",   "~339",     "~4",         "~348"],
];
const resultTable = new Table({
  width: { size: RESULT_COL_W.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  columnWidths: RESULT_COL_W,
  rows: resultRows.map((row, ri) =>
    new TableRow({
      tableHeader: ri === 0,
      children: row.map((cell, ci) => {
        const isHeader = ri === 0;
        const isFirst = ci === 0;
        const fill = isHeader ? "D9E2F3" : ri % 2 === 0 ? "F5F5F5" : "FFFFFF";
        return new TableCell({
          borders,
          shading: { fill, type: ShadingType.CLEAR },
          margins: { top: 60, bottom: 60, left: 100, right: 100 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            alignment: isFirst ? AlignmentType.LEFT : AlignmentType.CENTER,
            children: [new TextRun({ text: cell, font: FONT, size: SIZE_SM, bold: isHeader || cell.includes("*") })]
          })]
        });
      })
    })
  )
});

// ── tabela por tipo de consulta ─────────────────────────────────────────────
const TYPE_COL_W = [2400, 1600, 1700, 1100];
const typeRows = [
  ["Tipo de consulta", "Método",  "Hit@1",   "MRR"],
  ["Lexical (26)",     "FTS",     "0,731",   "0,840 *"],
  ["Lexical (26)",     "Vetorial","0,654",   "0,758"],
  ["Semântica (24)",   "Vetorial","0,375 *", "0,517 *"],
  ["Semântica (24)",   "FTS",     "0,042",   "0,042"],
];
const typeTable = new Table({
  width: { size: TYPE_COL_W.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  columnWidths: TYPE_COL_W,
  rows: typeRows.map((row, ri) =>
    new TableRow({
      tableHeader: ri === 0,
      children: row.map((cell, ci) => {
        const isHeader = ri === 0;
        const fill = isHeader ? "D9E2F3" : ri <= 2 ? "F0F4FB" : "FFFFFF";
        return new TableCell({
          borders,
          shading: { fill, type: ShadingType.CLEAR },
          margins: { top: 60, bottom: 60, left: 100, right: 100 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: cell, font: FONT, size: SIZE_SM, bold: isHeader || cell.includes("*") })]
          })]
        });
      })
    })
  )
});

// ── cronograma ──────────────────────────────────────────────────────────────
const MESES = ["Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
const ATIV = [
  { nome: "Levantamento bibliográfico",   meses: [1,1,0,0,0,0,0,0,0] },
  { nome: "Estudo das tecnologias",        meses: [1,1,1,0,0,0,0,0,0] },
  { nome: "Coleta e pré-processamento",    meses: [0,1,1,0,0,0,0,0,0] },
  { nome: "Escrita TCC I",                meses: [0,1,1,1,1,0,0,0,0] },
  { nome: "Pipeline de indexação",         meses: [0,0,1,1,0,0,0,0,0] },
  { nome: "Banco vetorial (pgvector)",     meses: [0,0,1,1,0,0,0,0,0] },
  { nome: "Pipeline de consulta RAG",      meses: [0,0,0,1,1,0,0,0,0] },
  { nome: "Baseline Full-Text Search",     meses: [0,0,0,1,1,0,0,0,0] },
  { nome: "Interface web (FastAPI+React)", meses: [0,0,0,0,1,1,0,0,0] },
  { nome: "Experimentos e avaliação",      meses: [0,0,0,0,1,1,0,0,0] },
  { nome: "Análise dos resultados",        meses: [0,0,0,0,0,1,1,0,0] },
  { nome: "Escrita TCC II",               meses: [0,0,0,0,0,1,1,1,0] },
  { nome: "Banca final",                  meses: [0,0,0,0,0,0,0,0,1] },
];
const cellW = Math.floor((CONTENT_W - 3000) / 9);
const cronTable = new Table({
  width: { size: CONTENT_W, type: WidthType.DXA },
  columnWidths: [3000, ...Array(9).fill(cellW)],
  rows: [
    new TableRow({
      tableHeader: true,
      children: [
        new TableCell({
          borders, shading: { fill: "D9E2F3", type: ShadingType.CLEAR },
          margins: { top: 40, bottom: 40, left: 80, right: 80 }, verticalAlign: VerticalAlign.CENTER,
          width: { size: 3000, type: WidthType.DXA },
          children: [new Paragraph({ alignment: AlignmentType.LEFT,
            children: [new TextRun({ text: "Atividade", font: FONT, size: SIZE_SM, bold: true })] })]
        }),
        ...MESES.map(m => new TableCell({
          borders, shading: { fill: "D9E2F3", type: ShadingType.CLEAR },
          margins: { top: 40, bottom: 40, left: 60, right: 60 }, verticalAlign: VerticalAlign.CENTER,
          width: { size: cellW, type: WidthType.DXA },
          children: [new Paragraph({ alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: m, font: FONT, size: SIZE_SM, bold: true })] })]
        }))
      ]
    }),
    ...ATIV.map(a => new TableRow({
      children: [
        new TableCell({
          borders, shading: { fill: "F5F5F5", type: ShadingType.CLEAR },
          margins: { top: 40, bottom: 40, left: 80, right: 80 }, verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({ children: [new TextRun({ text: a.nome, font: FONT, size: SIZE_SM })] })]
        }),
        ...a.meses.map(v => new TableCell({
          borders, shading: { fill: v ? "BDD7EE" : "FFFFFF", type: ShadingType.CLEAR },
          margins: { top: 40, bottom: 40, left: 60, right: 60 }, verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({ alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: v ? "X" : "", font: FONT, size: SIZE_SM })] })]
        }))
      ]
    }))
  ]
});

// ══════════════════════════════════════════════════════════════════════════════
// SEÇÃO PRÉ-TEXTUAL
// ══════════════════════════════════════════════════════════════════════════════
const preTextual = {
  properties: {
    page: { size: { width: A4_W, height: A4_H }, margin: { top: M_TOP, bottom: M_BOT, left: M_LEFT, right: M_RIGHT } }
  },
  children: [
    // ── CAPA ──────────────────────────────────────────────────────────────
    br(), br(),
    pC("UNIVERSIDADE ESTADUAL PAULISTA \"JÚLIO DE MESQUITA FILHO\"", { bold: true }),
    pC("FACULDADE DE CIÊNCIAS — CÂMPUS DE BAURU", { bold: true }),
    pC("BACHARELADO EM SISTEMAS DE INFORMAÇÃO", { bold: true }),
    br(), br(), br(),
    pC("MATHEUS SHODA LIMA"),
    pC("RAFAEL PANHOZZI RUBIO"),
    br(), br(), br(),
    pC("IMPLEMENTAÇÃO E AVALIAÇÃO DE UM SISTEMA DE RECUPERAÇÃO AUMENTADA POR GERAÇÃO (RAG) PARA CONSULTA DE DOCUMENTOS REGULATÓRIOS DA UNESP BAURU", { bold: true }),
    br(), br(), br(), br(),
    pC("Bauru"),
    pC("2026"),

    pageBreak(),

    // ── FOLHA DE ROSTO ─────────────────────────────────────────────────────
    br(), br(),
    pC("MATHEUS SHODA LIMA"),
    pC("RAFAEL PANHOZZI RUBIO"),
    br(), br(),
    pC("IMPLEMENTAÇÃO E AVALIAÇÃO DE UM SISTEMA DE RECUPERAÇÃO AUMENTADA POR GERAÇÃO (RAG) PARA CONSULTA DE DOCUMENTOS REGULATÓRIOS DA UNESP BAURU", { bold: true }),
    br(), br(),
    new Paragraph({
      alignment: AlignmentType.RIGHT,
      indent: { left: Math.floor(CONTENT_W / 2) },
      spacing: { line: 300, lineRule: "auto" },
      children: [new TextRun({
        text: "Trabalho de Conclusão de Curso apresentado ao Curso de Sistemas de Informação da Faculdade de Ciências — Câmpus de Bauru, Universidade Estadual Paulista \"Júlio de Mesquita Filho\", como parte dos requisitos para obtenção do grau de Bacharel em Sistemas de Informação.",
        font: FONT, size: SIZE_SM
      })]
    }),
    br(),
    new Paragraph({
      alignment: AlignmentType.RIGHT,
      indent: { left: Math.floor(CONTENT_W / 2) },
      spacing: { line: 300, lineRule: "auto" },
      children: [new TextRun({ text: "Orientador: Prof. Dr. Clayton Reginaldo Pereira", font: FONT, size: SIZE_SM })]
    }),
    br(), br(), br(),
    pC("Bauru"),
    pC("2026"),

    pageBreak(),

    // ── RESUMO ─────────────────────────────────────────────────────────────
    titulo("Resumo"),
    p("Este trabalho apresenta a implementação e avaliação experimental de um sistema de Recuperação Aumentada por Geração (RAG) voltado à consulta em linguagem natural de documentos regulatórios da Universidade Estadual Paulista (UNESP) Bauru. O corpus é composto por 936 resoluções e portarias institucionais coletadas do portal sistemas.unesp.br/legislacao-web (período 2016–2026), segmentadas em 4.229 chunks por janela deslizante (350 palavras, sobreposição de 60) e indexadas em PostgreSQL 16 com a extensão pgvector. Três métodos de recuperação são implementados e avaliados em um conjunto de 50 consultas anotadas (26 lexicais e 24 semânticas): busca vetorial densa por similaridade cosseno (embeddings intfloat/multilingual-e5-small, 384 dimensões), busca por texto completo com ranqueamento BM25 nativo do PostgreSQL e busca híbrida por Reciprocal Rank Fusion (RRF). Os resultados mostram que a busca híbrida supera os demais métodos nas métricas globais (Hit@1 = 0,560; MRR = 0,697; Hit@5 = 0,900), enquanto a busca vetorial é superior em consultas semânticas (Hit@1 = 0,375 vs. 0,042 do FTS) e o FTS lidera em consultas lexicais (MRR = 0,840 vs. 0,758 do vetorial). Uma interface web (FastAPI + React) voltada ao uso em bibliotecas universitárias foi desenvolvida como produto adicional."),
    br(),
    pSR("Palavras-chave: Recuperação Aumentada por Geração. RAG. Modelos de Linguagem. Busca Vetorial. pgvector. Full-Text Search. BM25. Reciprocal Rank Fusion. UNESP."),

    pageBreak(),

    // ── ABSTRACT ───────────────────────────────────────────────────────────
    titulo("Abstract"),
    p("This paper presents the implementation and experimental evaluation of a Retrieval-Augmented Generation (RAG) system for natural-language querying of regulatory documents from UNESP Bauru. The corpus consists of 936 institutional resolutions and ordinances collected from the sistemas.unesp.br/legislacao-web portal (2016–2026), segmented into 4,229 chunks via sliding-window chunking (350 words, 60-word overlap) and indexed in PostgreSQL 16 with the pgvector extension. Three retrieval methods are implemented and evaluated on a set of 50 annotated queries (26 lexical and 24 semantic): dense vector search by cosine similarity (intfloat/multilingual-e5-small embeddings, 384 dimensions), full-text search with PostgreSQL-native BM25 ranking, and hybrid search via Reciprocal Rank Fusion (RRF). Results show that hybrid search outperforms the other methods overall (Hit@1 = 0.560, MRR = 0.697, Hit@5 = 0.900), while vector search is superior for semantic queries (Hit@1 = 0.375 vs. 0.042 for FTS) and FTS leads on lexical queries (MRR = 0.840 vs. 0.758 for vector). A web interface (FastAPI + React) designed for university library kiosk use was also developed."),
    br(),
    pSR("Keywords: Retrieval-Augmented Generation. RAG. Language Models. Vector Search. pgvector. Full-Text Search. BM25. Reciprocal Rank Fusion. UNESP."),

    pageBreak(),

    // ── SUMÁRIO ─────────────────────────────────────────────────────────────
    titulo("Sumário"),
    new TableOfContents("Sumário", {
      hyperlink: true,
      headingStyleRange: "1-3",
      stylesWithLevels: [
        { styleId: "Heading1", level: 1 },
        { styleId: "Heading2", level: 2 },
        { styleId: "Heading3", level: 3 },
      ]
    }),
  ]
};

// ══════════════════════════════════════════════════════════════════════════════
// SEÇÃO TEXTUAL
// ══════════════════════════════════════════════════════════════════════════════
const textual = {
  properties: {
    page: { size: { width: A4_W, height: A4_H }, margin: { top: M_TOP, bottom: M_BOT, left: M_LEFT, right: M_RIGHT } }
  },
  headers: {
    default: new Header({
      children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: SIZE })]
      })]
    })
  },
  children: [

    // ════════════════════════════════════════════════════════════════════════
    // CAP 1 — INTRODUÇÃO
    // ════════════════════════════════════════════════════════════════════════
    titulo("1 Introdução"),
    p("As instituições de ensino superior brasileiras produzem e mantêm um expressivo volume de documentos regulatórios — resoluções, portarias, regulamentos de curso e regimentos gerais — que regem os direitos e deveres de estudantes, docentes e servidores. Na Universidade Estadual Paulista \"Júlio de Mesquita Filho\" (UNESP), esses documentos estão dispersos em diferentes portais e sistemas institucionais, tornando a localização de informações específicas uma tarefa onerosa, especialmente para estudantes ingressantes e usuários ocasionais."),
    p("O advento dos Modelos de Linguagem de Grande Porte (LLMs, do inglês Large Language Models) introduziu novas possibilidades para sistemas de resposta a perguntas em linguagem natural. Contudo, modelos como GPT-4 e LLaMA 3 apresentam uma limitação crítica: a tendência a gerar respostas factualmente incorretas, fenômeno conhecido como alucinação (JI et al., 2023). Quando aplicados a domínios institucionais específicos, nos quais precisão e rastreabilidade das fontes são requisitos fundamentais, essa limitação torna-se especialmente problemática."),
    p("A Recuperação Aumentada por Geração (RAG, do inglês Retrieval-Augmented Generation), proposta por Lewis et al. (2020), surge como solução ao combinar a capacidade generativa dos LLMs com a recuperação de trechos relevantes de uma base de conhecimento externa. Em vez de depender exclusivamente do conhecimento paramétrico do modelo, o sistema RAG recupera documentos pertinentes à consulta do usuário e os fornece como contexto ao LLM, restringindo a geração às informações presentes nas fontes originais."),

    h2("1.1 Problema de Pesquisa"),
    p("Dada a dificuldade de acesso eficiente à legislação institucional da UNESP Bauru, o presente trabalho formula a seguinte questão de pesquisa: em que medida um sistema RAG baseado em busca vetorial por similaridade semântica, busca textual BM25 e sua fusão por Reciprocal Rank Fusion (RRF) se diferenciam na recuperação de documentos regulatórios institucionais em língua portuguesa, e qual combinação oferece o melhor desempenho?"),

    h2("1.2 Objetivos"),
    h3("1.2.1 Objetivo Geral"),
    p("Implementar e avaliar comparativamente três mecanismos de recuperação de informação — busca vetorial densa, busca textual esparsa (BM25) e busca híbrida por RRF — integrados a um sistema RAG para consulta em linguagem natural de documentos regulatórios da UNESP Bauru."),

    h3("1.2.2 Objetivos Específicos"),
    alinea("a", "Coletar, pré-processar e organizar o corpus de 936 documentos regulatórios da UNESP do portal sistemas.unesp.br/legislacao-web;"),
    alinea("b", "Implementar o pipeline de indexação composto por segmentação em chunks (sliding window 350 palavras, sobreposição de 60), geração de embeddings multilinguais (intfloat/multilingual-e5-small, 384 dimensões) e persistência em PostgreSQL 16 com pgvector;"),
    alinea("c", "Implementar os três mecanismos de recuperação: vetorial (HNSW + similaridade cosseno), textual (tsvector + GIN + BM25) e híbrido (RRF combinando os dois rankings anteriores);"),
    alinea("d", "Avaliar os três métodos com um conjunto de 50 consultas anotadas manualmente, utilizando as métricas Hit@K (K = 1, 3, 5) e MRR;"),
    alinea("e", "Desenvolver uma interface web (FastAPI + React) para uso em contexto de biblioteca universitária, integrando recuperação e geração de respostas via LLM (Groq/LLaMA 3.3 70B)."),

    h2("1.3 Justificativa"),
    p("A adoção de sistemas RAG para documentos institucionais representa contribuição tanto prática quanto científica. Do ponto de vista prático, o sistema automatiza respostas a dúvidas recorrentes de estudantes — sobre requisitos de estágio, atividades complementares, grades curriculares e prazos — liberando servidores para demandas mais complexas. O contexto de uso em biblioteca universitária (kiosque de consulta) é especialmente adequado, pois integra o serviço ao ambiente físico de orientação acadêmica já existente."),
    p("Do ponto de vista científico, a avaliação comparativa entre busca vetorial, BM25 e RRF em um corpus institucional em língua portuguesa contribui para a literatura sobre sistemas RAG em domínios especializados. A maioria dos estudos de avaliação RAG concentra-se no inglês e em domínios como medicina ou legislação federal; corpora institucionais universitários em português ainda são pouco explorados. A disponibilização pública do conjunto de avaliação anotado (50 consultas com ground truth) constitui contribuição adicional para trabalhos futuros."),

    pageBreak(),

    // ════════════════════════════════════════════════════════════════════════
    // CAP 2 — REFERENCIAL TEÓRICO
    // ════════════════════════════════════════════════════════════════════════
    titulo("2 Referencial Teórico"),

    h2("2.1 Modelos de Linguagem de Grande Porte e Alucinações"),
    p("Os Modelos de Linguagem de Grande Porte (LLMs) são redes neurais autoregressivas treinadas em grandes corpora textuais com o objetivo de modelar a distribuição probabilística de sequências de tokens. Modelos como GPT-4 (OpenAI), LLaMA 3 (Meta) e Claude (Anthropic) demonstraram capacidade notável em tarefas de geração de texto, sumarização, tradução e resposta a perguntas em linguagem natural."),
    p("Contudo, Ji et al. (2023) sistematizam o problema das alucinações em modelos de geração de linguagem natural: a produção de conteúdo factualmente incorreto, porém fluente e aparentemente plausível. Os autores distinguem alucinações intrínsecas (contradição com informação fornecida no prompt) de extrínsecas (informação não verificável ou falsa introduzida pelo modelo). Em aplicações institucionais — consulta de normas, prazos e requisitos regulamentares — respostas alucinadas podem causar prejuízo direto ao usuário que as toma como verdadeiras."),

    h2("2.2 Recuperação Aumentada por Geração (RAG)"),
    p("Lewis et al. (2020) introduziram o paradigma RAG como solução ao conhecimento estático dos LLMs. A arquitetura combina um retriever, que seleciona documentos relevantes de uma base de conhecimento externa, com um gerador (LLM), que produz respostas condicionadas tanto à pergunta do usuário quanto aos documentos recuperados. As respostas ficam assim ancoradas em fontes verificáveis, reduzindo alucinações e permitindo a citação das origens."),
    p("Gao et al. (2023) revisam as variantes de RAG, distinguindo RAG Naive (recuperação simples seguida de geração), RAG Avançado (com reranking, query rewriting e pós-processamento) e RAG Modular (com componentes especializados e intercambiáveis). Os autores identificam que a qualidade do componente retriever é o principal fator de variação no desempenho do sistema, sendo a escolha entre busca densa e esparsa determinante para consultas com diferentes características linguísticas."),

    h2("2.3 Busca Vetorial e Modelos de Embedding"),
    p("A busca vetorial por similaridade semântica representa textos como vetores densos em espaços de alta dimensão, de modo que textos semanticamente similares ocupam regiões próximas. Modelos de embedding como o intfloat/multilingual-e5-small (Wang et al., 2022) — com 384 dimensões — são treinados por contrastive learning em pares de textos similares e distintos, produzindo representações que capturam relações semânticas além da coincidência lexical. O prefixo \"query: \" é inserido antes das consultas e \"passage: \" antes dos documentos, seguindo a especificação do modelo E5."),
    p("O armazenamento e a recuperação eficiente de vetores em larga escala são viabilizados por extensões de banco de dados vetorial. O pgvector (2021) adiciona ao PostgreSQL suporte a vetores de dimensão arbitrária e busca por vizinhos mais próximos aproximados (ANN) via índices HNSW (Hierarchical Navigable Small World) ou IVFFlat. A integração ao PostgreSQL permite executar busca vetorial e textual no mesmo sistema, simplificando a arquitetura e eliminando a necessidade de serviços externos como Pinecone ou Weaviate."),

    h2("2.4 Busca Textual Esparsa: BM25 e Full-Text Search"),
    p("O BM25 (Best Match 25), formalizado por Robertson e Zaragoza (2009), é uma função de ranqueamento baseada em frequência de termos (TF) e frequência inversa de documentos (IDF), com normalização pelo comprimento do documento. Amplamente adotado como baseline em recuperação de informação, o BM25 demonstra desempenho competitivo frente a métodos neurais em domínios com vocabulário técnico especializado e em consultas lexicais diretas."),
    p("O PostgreSQL implementa busca de texto completo nativa por meio do tipo tsvector e do índice GIN (Generalized Inverted Index), com ranqueamento ts_rank_cd compatível com BM25. A extensão unaccent remove diacríticos durante a tokenização, essencial para o português, onde variações acentuadas (\"gestao\" vs. \"gestão\") devem ser tratadas como equivalentes. Para uso em colunas geradas (GENERATED ALWAYS AS), é necessário envolver unaccent() em uma função IMMUTABLE, contornando a restrição de volatilidade do PostgreSQL para expressões geradas."),

    h2("2.5 Fusão Híbrida: Reciprocal Rank Fusion (RRF)"),
    p("Cormack et al. (2009) propuseram o Reciprocal Rank Fusion como método para combinar múltiplos rankings de recuperação sem necessidade de calibração ou treinamento adicional. A pontuação de um documento d combinando m listas de ranking é:"),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 140, after: 140 },
      children: [new TextRun({ text: "RRF(d) = Σᵢ 1 / (k + rankᵢ(d))", font: FONT, size: SIZE, italic: true })]
    }),
    p("onde rankᵢ(d) é a posição de d no ranking i e k é um parâmetro de suavização (tipicamente 60). O método demonstrou superar estratégias de fusão por aprendizado e métodos de ranqueamento individuais em benchmarks de recuperação ad hoc. No contexto RAG, o RRF é especialmente atraente por combinar a precisão lexical do BM25 com a compreensão semântica da busca vetorial, compensando as fraquezas de cada método em diferentes tipos de consulta."),

    pageBreak(),

    // ════════════════════════════════════════════════════════════════════════
    // CAP 3 — METODOLOGIA
    // ════════════════════════════════════════════════════════════════════════
    titulo("3 Metodologia"),
    p("O trabalho é organizado em cinco fases sequenciais: coleta do corpus, indexação, implementação dos três métodos de recuperação, desenvolvimento da interface web e avaliação experimental."),

    h2("3.1 Fase 1 — Coleta e Pré-processamento do Corpus"),
    p("O corpus é composto por 936 resoluções e portarias da UNESP, coletadas do sistema sistemas.unesp.br/legislacao-web por meio de um scraper Python desenvolvido com as bibliotecas requests e BeautifulSoup. O scraper percorre a lista de documentos disponível na página inicial do portal, extrai os metadados (número, ano, data) de cada resolução e realiza requisições GET individuais ao endpoint de texto integral, extraindo o conteúdo do elemento HTML div.painelTexto. Um intervalo de 1,2 segundos entre requisições foi adotado. O processo é controlado por um arquivo manifest.json que registra os documentos já coletados, permitindo retomada incremental."),
    p("Os textos resultantes passaram por limpeza: remoção de cabeçalhos e rodapés repetidos, normalização de codificação UTF-8 e eliminação de caracteres de controle. Os arquivos limpos foram armazenados em data/legislacao/ com nomenclatura padronizada no formato resolucao_AAAA_NNNN.txt."),

    h2("3.2 Fase 2 — Indexação: Chunking, Embeddings e pgvector"),
    p("Os textos pré-processados são segmentados em chunks pelo método de janela deslizante (sliding window), com tamanho de 350 palavras e sobreposição de 60 palavras. O corpus resultou em 4.229 chunks com média de aproximadamente 285 palavras por chunk."),
    p("Os embeddings são gerados pelo modelo intfloat/multilingual-e5-small (384 dimensões), executado localmente via sentence-transformers sem custo de API. As consultas recebem o prefixo \"query: \" e os documentos o prefixo \"passage: \", conforme especificação do modelo. Os vetores são persistidos na coluna embedding (tipo vector(384)) da tabela chunks no PostgreSQL 16 com pgvector. Um índice HNSW com métrica de distância cosseno (ops: vector_cosine_ops) é criado sobre a coluna para busca ANN eficiente."),
    p("Simultaneamente, cada chunk recebe uma coluna content_tsv (tipo tsvector), gerada automaticamente pela expressão to_tsvector('portuguese', unaccent_immutable(content)), onde unaccent_immutable é uma função SQL IMMUTABLE e PARALLEL SAFE que envolve a extensão unaccent. Um índice GIN é criado sobre content_tsv para busca textual eficiente."),

    h2("3.3 Fase 3 — Implementação dos Três Métodos de Recuperação"),
    h3("3.3.1 Busca Vetorial"),
    p("A busca vetorial calcula o embedding da consulta (com prefixo \"query: \"), realiza a operação de distância cosseno (<=> no pgvector) entre o vetor da consulta e os vetores indexados via HNSW e retorna os K chunks com menor distância. A pontuação final é 1 − distância_cosseno, resultando em valores em [0, 1]."),

    h3("3.3.2 Busca Textual (FTS / BM25)"),
    p("A busca textual converte a consulta em uma query tsvector via websearch_to_tsquery (com unaccent para remoção de diacríticos) e recupera os chunks com maior ts_rank_cd em relação ao índice GIN. websearch_to_tsquery suporta consultas em linguagem natural sem necessidade de operadores booleanos explícitos, adequado ao perfil de usuário do sistema."),

    h3("3.3.3 Busca Híbrida (RRF)"),
    p("A busca híbrida combina os rankings dos dois métodos anteriores via Reciprocal Rank Fusion com k = 60. Os top-50 resultados de cada método são recuperados; a pontuação RRF de cada chunk é calculada como 1/(60 + rank_vetorial) + 1/(60 + rank_fts), onde um rank inexistente implica ausência do termo no somatório. Os chunks são reordenados pela pontuação RRF combinada e os K melhores são retornados."),

    h2("3.4 Fase 4 — Interface Web"),
    p("Uma interface de consulta foi desenvolvida para o contexto de uso em biblioteca universitária. O backend é implementado em FastAPI (Python), expondo os endpoints POST /api/ask (recuperação + geração com LLM), POST /api/search (apenas recuperação) e GET /api/health. O LLM utilizado é o LLaMA 3.3 70B Versatile, acessado via API Groq (tier gratuito, compatível com OpenAI), com temperatura 0,1 e máximo de 800 tokens por resposta. O prompt do sistema instrui o modelo a responder exclusivamente com base nos trechos fornecidos, citando a resolução de origem."),
    p("O frontend é implementado em React + Vite com uma interface de chat: o usuário digita a pergunta em uma caixa de texto, o sistema recupera os chunks mais relevantes pelo método selecionado, o LLM gera uma resposta fundamentada nas fontes e a interface exibe a resposta com cards expansíveis mostrando os trechos de origem e a pontuação de relevância. O método de busca pode ser alternado entre Híbrido (RRF), Vetorial e FTS por um seletor no rodapé da tela. O tempo de resposta é exibido ao final de cada mensagem."),

    h2("3.5 Fase 5 — Avaliação Experimental"),
    p("A avaliação utiliza um conjunto de 50 consultas anotadas manualmente, cada uma associada a um documento de referência identificado no corpus (ground truth de source único por consulta). As consultas são distribuídas em dois tipos:"),
    alinea("a", "Lexical (26 consultas): termos do documento-alvo aparecem literalmente na pergunta, favorecendo a busca por palavras-chave;"),
    alinea("b", "Semântica (24 consultas): a intenção é expressa por paráfrases ou sinônimos sem coincidência literal com o documento, favorecendo a busca por similaridade semântica."),
    p("As métricas calculadas para cada método são: Hit@K (K = 1, 3, 5) — proporção de consultas em que o documento de referência aparece nos K primeiros resultados — e Mean Reciprocal Rank (MRR) — média do recíproco da posição do documento de referência no ranking (max K = 5), penalizando rankings onde o documento correto aparece em posições inferiores."),
    p("A latência de cada componente (geração do embedding, busca vetorial, busca FTS, cálculo RRF) é medida em milissegundos via time.perf_counter(), reportando a média sobre as 50 consultas."),

    pageBreak(),

    // ════════════════════════════════════════════════════════════════════════
    // CAP 4 — EXPERIMENTOS E RESULTADOS
    // ════════════════════════════════════════════════════════════════════════
    titulo("4 Experimentos e Resultados"),

    h2("4.1 Configuração Experimental"),
    p("Todos os experimentos foram executados em máquina local com processador Intel Core, 16 GB de RAM e sem GPU dedicada. O banco de dados PostgreSQL 16 com pgvector é executado em container Docker. O modelo de embedding intfloat/multilingual-e5-small é executado em CPU via sentence-transformers. O conjunto de avaliação compreende 50 consultas (26 lexicais, 24 semânticas) com ground truth de documento único. O parâmetro K = 5 é utilizado em todos os experimentos; o RRF usa k = 60 e busca os top-50 de cada método antes da fusão."),

    h2("4.2 Resultados Globais"),
    caption("Tabela 1 — Métricas de recuperação globais (50 consultas, K = 5). * = melhor valor por métrica."),
    br(),
    resultTable,
    br(),
    p("Os resultados globais, apresentados na Tabela 1, mostram que a busca híbrida por RRF obtém os melhores valores em todas as métricas de qualidade: Hit@1 = 0,560; Hit@3 = 0,840; Hit@5 = 0,900; MRR = 0,697. A busca vetorial ocupa a segunda posição global (MRR = 0,642) e o FTS apresenta o menor desempenho global (MRR = 0,457). Quanto à latência, o FTS é substancialmente mais rápido (~4 ms) do que os métodos que envolvem geração de embedding (~339–348 ms)."),

    h2("4.3 Análise por Tipo de Consulta"),
    caption("Tabela 2 — Hit@1 e MRR por tipo de consulta (K = 5). * = melhor valor por combinação tipo/métrica."),
    br(),
    typeTable,
    br(),
    p("A análise por tipo de consulta, exibida na Tabela 2, revela comportamentos complementares. Para consultas lexicais — em que termos do documento-alvo aparecem literalmente na pergunta —, o FTS supera os demais com MRR = 0,840, confirmando a eficácia do BM25 em correspondência exata de termos técnicos presentes nas resoluções. Para consultas semânticas — formuladas por paráfrases ou sinônimos —, a busca vetorial é amplamente superior (Hit@1 = 0,375; MRR = 0,517) frente ao colapso do FTS (Hit@1 = 0,042; MRR = 0,042). A busca híbrida RRF não apresenta valor extremo em nenhuma categoria, mas garante robustez em ambos os tipos."),

    h2("4.4 Análise de Latência"),
    p("A latência média de geração do embedding é de aproximadamente 325 ms por consulta, dominando o tempo total de resposta dos métodos vetorial (~339 ms) e híbrido (~348 ms). O FTS, por não requerer embedding, responde em ~4 ms, sendo adequado para interfaces com requisitos de resposta imediata. Em cenários de produção com GPU ou serviço de embedding por API, esse gargalo seria reduzido para dezenas de milissegundos, tornando a latência do RRF comparável ao FTS."),

    h2("4.5 Discussão"),
    p("Os resultados confirmam a hipótese principal: a busca híbrida por RRF é o método mais robusto para um corpus regulatório institucional que contém tanto consultas técnicas lexicais (números de resolução, termos específicos como \"AACC\", \"estágio obrigatório\") quanto consultas conceituais semânticas. O ganho do RRF sobre o melhor método individual (MRR 0,697 vs. 0,642) é modesto mas consistente, alinhado com a literatura de fusão de rankings (CORMACK et al., 2009)."),
    p("A disparidade do FTS em consultas semânticas (MRR = 0,042) evidencia a limitação crítica da busca por palavras-chave quando o usuário parafraseia a consulta sem usar a terminologia exata do documento — cenário frequente em usuários não familiarizados com a nomenclatura regulatória. Esse padrão reforça o valor da dimensão semântica fornecida pelos embeddings. Inversamente, a superioridade do FTS em consultas lexicais indica que embeddings compactos (384 dims) perdem precisão quando a correspondência exata de termos técnicos é suficiente."),
    p("Como trabalhos futuros, destacam-se: (i) melhoria na qualidade do pré-processamento para documentos com tabelas complexas; (ii) inclusão de metadados estruturados (número, ano, categoria da resolução) como filtros de busca; (iii) avaliação com modelos de embedding de maior dimensão (768 ou 1024 dims) para verificar impacto no desempenho semântico; (iv) reranking neural dos resultados RRF com cross-encoder; e (v) expansão do corpus com atas de reuniões do Conselho Universitário."),

    pageBreak(),

    // ════════════════════════════════════════════════════════════════════════
    // PLANO DE TRABALHO
    // ════════════════════════════════════════════════════════════════════════
    titulo("Plano de Trabalho"),
    caption("Tabela 3 — Cronograma de atividades (X = período de execução previsto/realizado)."),
    br(),
    cronTable,
    br(),
    p("O cronograma distingue as atividades concluídas até a submissão do TCC I — levantamento bibliográfico, coleta do corpus, implementação do pipeline completo (indexação, três métodos de busca, interface web) e avaliação experimental — das previstas para o TCC II: análise aprofundada dos resultados, incorporação de trabalhos futuros e escrita da monografia final com banca de apresentação prevista para dezembro de 2026."),

    pageBreak(),

    // ════════════════════════════════════════════════════════════════════════
    // REFERÊNCIAS
    // ════════════════════════════════════════════════════════════════════════
    titulo("Referências"),

    pSR("CORMACK, Gordon V.; CLARKE, Charles L. A.; BUETTCHER, Stefan. Reciprocal rank fusion outperforms condorcet and individual rank learning methods. In: ANNUAL INTERNATIONAL ACM SIGIR CONFERENCE ON RESEARCH AND DEVELOPMENT IN INFORMATION RETRIEVAL, 32., 2009, Boston. Proceedings [...]. New York: ACM, 2009. p. 758–759."),
    br(),
    pSR("GAO, Yunfan et al. Retrieval-augmented generation for large language models: a survey. arXiv:2312.10997, 2023. Disponível em: https://arxiv.org/abs/2312.10997. Acesso em: 5 jun. 2026."),
    br(),
    pSR("JI, Ziwei et al. Survey of hallucination in natural language generation. ACM Computing Surveys, v. 55, n. 12, p. 1–38, mar. 2023."),
    br(),
    pSR("LEWIS, Patrick et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. In: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS, 33., 2020, [S. l.]. Proceedings [...]. [S. l.]: NeurIPS, 2020. p. 9459–9474."),
    br(),
    pSR("PGVECTOR. Open-source vector similarity search for PostgreSQL. Disponível em: https://github.com/pgvector/pgvector. Acesso em: 5 jun. 2026."),
    br(),
    pSR("REIMERS, Nils; GUREVYCH, Iryna. Sentence-BERT: sentence embeddings using siamese BERT-networks. In: CONFERENCE ON EMPIRICAL METHODS IN NATURAL LANGUAGE PROCESSING, 2019. Proceedings [...]. [S. l.]: ACL, 2019. p. 3982–3992."),
    br(),
    pSR("ROBERTSON, Stephen; ZARAGOZA, Hugo. The probabilistic relevance framework: BM25 and beyond. Foundations and Trends in Information Retrieval, v. 3, n. 4, p. 333–389, 2009."),
    br(),
    pSR("WANG, Liang et al. Text embeddings by weakly-supervised contrastive pre-training. arXiv:2212.03533, 2022. Disponível em: https://arxiv.org/abs/2212.03533. Acesso em: 5 jun. 2026."),
  ]
};

// ══════════════════════════════════════════════════════════════════════════════
// DOCUMENT
// ══════════════════════════════════════════════════════════════════════════════
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT, size: SIZE } }
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: SIZE, bold: true, font: FONT, color: "000000" },
        paragraph: { spacing: { before: 280, after: 280 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: SIZE, bold: true, font: FONT, color: "000000" },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 }
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: SIZE, bold: true, font: FONT, color: "000000" },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 }
      },
    ]
  },
  sections: [preTextual, textual]
});

const outPath = "DOCUMENTO-ENVIO/TCC_RAG_UNESP_Bauru.docx";
Packer.toBuffer(doc).then(buf => {
  writeFileSync(outPath, buf);
  console.log("OK:", outPath);
}).catch(e => { console.error("ERRO:", e.message); process.exit(1); });
