import {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, Header, TableOfContents, PageBreak, VerticalAlign
} from "docx";
import { readFileSync, writeFileSync } from "fs";

// Resultados gerados por `python scripts/evaluate.py --json data/resultados_resumo.json`.
// As tabelas e os números do texto vêm daqui, para não haver cópia manual.
const R = JSON.parse(readFileSync("data/resultados_resumo.json", "utf-8"));
const G = R.global;
const T = R.por_tipo;
const METODOS = ["vec", "fts", "bm25", "rrf"];
const NOME = { vec: "Vetorial", fts: "FTS-PG", bm25: "BM25", rrf: "Híbrido RRF" };
const QUALIDADE = ["hit1", "hit3", "hit5", "mrr"];

// número no padrão brasileiro (vírgula decimal)
const fmt = (x, d = 3) => x.toFixed(d).replace(".", ",");
const fmtP = (p) => (p < 0.001 ? "< 0,001" : fmt(p, 3));
const pEq = (p) => (p < 0.001 ? "< 0,001" : "= " + fmt(p, 3)); // para "p = 0,05" / "p < 0,001" no texto
const cmp = (a, b) => R.comparacoes.find(c => c.a === a && c.b === b);
const melhor = (obj, key) => Math.max(...METODOS.map(m => obj[m][key]));
const cmpT = (tipo, a, b) => T[tipo].comparacoes.find(c => c.a === a && c.b === b);
const ms = (x) => fmt(x, 0);

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

const fonte = () => new Paragraph({
  alignment: AlignmentType.LEFT,
  spacing: { before: 60, after: 200 },
  children: [new TextRun({ text: "Fonte: elaborado pelos autores (2026).", font: FONT, size: SIZE_SM })]
});

// ── tabelas genéricas ───────────────────────────────────────────────────────
const border = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
const borders = { top: border, bottom: border, left: border, right: border };

// rows: matriz de strings; células terminadas em " *" saem em negrito (sem o asterisco)
const tabela = (colW, rows) => new Table({
  width: { size: colW.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  columnWidths: colW,
  rows: rows.map((row, ri) =>
    new TableRow({
      tableHeader: ri === 0,
      children: row.map((cell, ci) => {
        const isHeader = ri === 0;
        const destaque = cell.endsWith(" *");
        const fill = isHeader ? "D9E2F3" : ri % 2 === 0 ? "F5F5F5" : "FFFFFF";
        return new TableCell({
          borders,
          width: { size: colW[ci], type: WidthType.DXA },
          shading: { fill, type: ShadingType.CLEAR },
          margins: { top: 60, bottom: 60, left: 100, right: 100 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            alignment: ci === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
            children: [new TextRun({
              text: destaque ? cell.slice(0, -2) : cell,
              font: FONT, size: SIZE_SM, bold: isHeader || destaque
            })]
          })]
        });
      })
    })
  )
});

// ── Tabela 1: métricas globais ──────────────────────────────────────────────
const linhaMetrica = (rotulo, key, obj) => [
  rotulo,
  ...METODOS.map(m => fmt(obj[m][key]) + (obj[m][key] === melhor(obj, key) ? " *" : ""))
];
const resultTable = tabela([2300, 1700, 1700, 1700, 1700], [
  ["Métrica", ...METODOS.map(m => NOME[m])],
  linhaMetrica("Hit@1", "hit1", G),
  linhaMetrica("Hit@3", "hit3", G),
  linhaMetrica("Hit@5", "hit5", G),
  linhaMetrica("MRR", "mrr", G),
  ["IC 95% do MRR", ...METODOS.map(m => `${fmt(G[m].mrr_ci95[0], 2)}–${fmt(G[m].mrr_ci95[1], 2)}`)],
  ["Sem resultado", ...METODOS.map(m => String(G[m].sem_resultado))],
]);

// ── Tabela 2: por tipo de consulta ──────────────────────────────────────────
const ROTULO_TIPO = { lexical: "Lexical", semantic: "Semântica" };
const typeTable = tabela([2200, 1900, 1500, 1500, 1500], [
  ["Tipo de consulta", "Método", "Hit@1", "Hit@5", "MRR"],
  ...Object.keys(T).flatMap(tipo => METODOS.map(m => [
    `${ROTULO_TIPO[tipo] ?? tipo} (${T[tipo].n})`,
    NOME[m],
    ...["hit1", "hit5", "mrr"].map(key => fmt(T[tipo][m][key]) + (T[tipo][m][key] === melhor(T[tipo], key) ? " *" : "")),
  ])),
]);

// ── Tabela 3: comparações pareadas ──────────────────────────────────────────
const sigTable = tabela([2600, 1300, 2000, 1500, 1500], [
  ["Comparação (A × B)", "Δ MRR", "Consultas A melhor / B melhor / empate", "p", "p (Holm)"],
  ...R.comparacoes.map(c => [
    `${NOME[c.a]} × ${NOME[c.b]}`,
    (c.delta_mrr >= 0 ? "+" : "−") + fmt(Math.abs(c.delta_mrr)),
    `${c.vitorias_a} / ${c.vitorias_b} / ${c.empates}`,
    fmtP(c.p_mrr),
    fmtP(c.p_mrr_holm) + (c.p_mrr_holm < 0.05 ? " *" : ""),
  ]),
]);

// ── Tabela 4: latência ──────────────────────────────────────────────────────
const latTable = tabela([3200, 1500, 1500, 1500, 1500], [
  ["Latência por consulta (ms)", ...METODOS.map(m => NOME[m])],
  ["Mediana", ...METODOS.map(m => fmt(G[m].lat_median_ms, 1))],
  ["Percentil 95", ...METODOS.map(m => fmt(G[m].lat_p95_ms, 1))],
]);

// ── cronograma ──────────────────────────────────────────────────────────────
// Calendário reprogramado após a greve: entrega final em fevereiro de 2027.
const MESES = ["Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez", "Jan", "Fev"];
const ATIV = [
  { nome: "Levantamento bibliográfico",          meses: [1,1,0,0,0,0,1,0,0,0,0] },
  { nome: "Estudo das tecnologias",              meses: [1,1,1,0,0,0,0,0,0,0,0] },
  { nome: "Coleta e pré-processamento",          meses: [0,1,1,0,0,0,0,0,0,0,0] },
  { nome: "Indexação e banco vetorial",          meses: [0,0,1,0,0,0,0,0,0,0,0] },
  { nome: "Métodos de recuperação e interface",  meses: [0,0,1,0,0,0,0,0,0,0,0] },
  { nome: "Escrita TCC I",                       meses: [0,1,1,0,0,0,0,0,0,0,0] },
  { nome: "Revisão metodológica da avaliação",   meses: [0,0,0,0,0,0,1,0,0,0,0] },
  { nome: "Ampliação do conjunto de avaliação",  meses: [0,0,0,0,0,0,0,1,0,0,0] },
  { nome: "Avaliação da geração de respostas",   meses: [0,0,0,0,0,0,0,1,1,0,0] },
  { nome: "Escrita TCC II",                      meses: [0,0,0,0,0,0,0,1,1,1,0] },
  { nome: "Revisão final e entrega",             meses: [0,0,0,0,0,0,0,0,0,1,1] },
  { nome: "Banca final",                         meses: [0,0,0,0,0,0,0,0,0,0,1] },
];
const cellW = Math.floor((CONTENT_W - 3000) / MESES.length);
const cronTable = new Table({
  width: { size: CONTENT_W, type: WidthType.DXA },
  columnWidths: [3000, ...Array(MESES.length).fill(cellW)],
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

    // ── FOLHA DE APROVAÇÃO ──────────────────────────────────────────────────
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
    br(), br(),
    pSR("Bauru, ______ / ______ / __________."),
    br(), br(), br(),
    pSR("Componentes da Banca Examinadora:"),
    br(), br(), br(),
    pC("_______________________________________________"),
    pC("Presidente e Orientador: Prof. Dr. Clayton Reginaldo Pereira"),
    pC("Universidade Estadual Paulista — UNESP Bauru"),
    br(), br(), br(),
    pC("_______________________________________________"),
    pC("Membro Titular: [nome e título a definir]"),
    pC("Universidade Estadual Paulista — UNESP Bauru"),
    br(), br(), br(),
    pC("_______________________________________________"),
    pC("Membro Titular: [nome e título a definir]"),
    pC("Universidade Estadual Paulista — UNESP Bauru"),

    pageBreak(),

    // ── RESUMO ─────────────────────────────────────────────────────────────
    titulo("Resumo"),
    p(`Este trabalho apresenta a implementação e a avaliação experimental de um sistema de Recuperação Aumentada por Geração (RAG) para consulta em linguagem natural de documentos regulatórios da Universidade Estadual Paulista (UNESP), voltado ao uso na biblioteca do câmpus de Bauru. O corpus reúne 936 resoluções coletadas do portal sistemas.unesp.br/legislacao-web (2016–2026), segmentadas em 4.229 chunks por janela deslizante (350 palavras, sobreposição de 60) e indexadas em PostgreSQL 16 com a extensão pgvector. Quatro métodos de recuperação são comparados em um conjunto de ${R.meta.n_consultas} consultas anotadas (${T.lexical.n} lexicais e ${T.semantic.n} semânticas): busca vetorial densa (embeddings intfloat/multilingual-e5-small, 384 dimensões), BM25, busca textual nativa do PostgreSQL (ts_rank_cd) e busca híbrida por Reciprocal Rank Fusion (RRF) entre os rankings vetorial e BM25. A busca híbrida obteve os maiores valores globais (MRR = ${fmt(G.rrf.mrr)}; Hit@1 = ${fmt(G.rrf.hit1)}), seguida do BM25 (MRR = ${fmt(G.bm25.mrr)}) e da busca vetorial (MRR = ${fmt(G.vec.mrr)}); com ${R.meta.n_consultas} consultas, porém, as diferenças entre esses três métodos não foram estatisticamente significativas após a correção para comparações múltiplas. Nas consultas semânticas, a busca híbrida superou significativamente os dois métodos individuais (MRR = ${fmt(T.semantic.rrf.mrr)}, contra ${fmt(T.semantic.vec.mrr)} da vetorial e ${fmt(T.semantic.bm25.mrr)} do BM25). O BM25 superou amplamente a busca textual nativa do PostgreSQL (MRR = ${fmt(G.bm25.mrr)} contra ${fmt(G.fts.mrr)}), embora ambos usem o mesmo processamento de texto, o que evidencia o peso da função de ranqueamento. Foi desenvolvida ainda uma interface web (FastAPI + React) com geração de respostas por LLM, voltada ao uso em bibliotecas universitárias; a avaliação da qualidade das respostas geradas constitui a próxima etapa do trabalho.`),
    br(),
    pSR("Palavras-chave: Recuperação Aumentada por Geração. RAG. Modelos de Linguagem. Busca Vetorial. pgvector. Full-Text Search. BM25. Reciprocal Rank Fusion. UNESP."),

    pageBreak(),

    // ── ABSTRACT ───────────────────────────────────────────────────────────
    titulo("Abstract"),
    p(`This work presents the implementation and experimental evaluation of a Retrieval-Augmented Generation (RAG) system for natural-language querying of regulatory documents from São Paulo State University (UNESP), designed for use at the Bauru campus library. The corpus comprises 936 resolutions collected from the sistemas.unesp.br/legislacao-web portal (2016–2026), segmented into 4,229 chunks with a sliding window (350 words, 60-word overlap) and indexed in PostgreSQL 16 with the pgvector extension. Four retrieval methods are compared on a set of ${R.meta.n_consultas} annotated queries (${T.lexical.n} lexical and ${T.semantic.n} semantic): dense vector search (intfloat/multilingual-e5-small embeddings, 384 dimensions), BM25, PostgreSQL native full-text search (ts_rank_cd), and hybrid search via Reciprocal Rank Fusion (RRF) of the vector and BM25 rankings. Hybrid search achieved the highest overall scores (MRR = ${G.rrf.mrr.toFixed(3)}; Hit@1 = ${G.rrf.hit1.toFixed(3)}), followed by BM25 (MRR = ${G.bm25.mrr.toFixed(3)}) and vector search (MRR = ${G.vec.mrr.toFixed(3)}); with ${R.meta.n_consultas} queries, however, the differences among these three methods were not statistically significant after correction for multiple comparisons. On semantic queries, hybrid search significantly outperformed both individual methods (MRR = ${T.semantic.rrf.mrr.toFixed(3)}, versus ${T.semantic.vec.mrr.toFixed(3)} for vector search and ${T.semantic.bm25.mrr.toFixed(3)} for BM25). BM25 clearly outperformed PostgreSQL native full-text search (MRR = ${G.bm25.mrr.toFixed(3)} versus ${G.fts.mrr.toFixed(3)}), although both share the same text processing, which highlights the weight of the ranking function. A web interface (FastAPI + React) with LLM-generated answers was also developed for university library use; evaluating the quality of the generated answers is the next stage of the work.`),
    br(),
    pSR("Keywords: Retrieval-Augmented Generation. RAG. Language Models. Vector Search. pgvector. Full-Text Search. BM25. Reciprocal Rank Fusion. UNESP."),

    pageBreak(),

    // ── SUMÁRIO ─────────────────────────────────────────────────────────────
    titulo("Sumário"),
    new TableOfContents("Sumário", {
      hyperlink: true,
      headingStyleRange: "1-3",
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
    p("Implementar e avaliar comparativamente três mecanismos de recuperação de informação — busca vetorial densa, busca textual esparsa (BM25) e busca híbrida por RRF — integrados a um sistema RAG para consulta em linguagem natural de documentos regulatórios da UNESP aplicáveis ao câmpus de Bauru."),

    h3("1.2.2 Objetivos Específicos"),
    alinea("a", "Coletar, pré-processar e organizar o corpus de 936 resoluções da UNESP publicadas no portal sistemas.unesp.br/legislacao-web;"),
    alinea("b", "Implementar o pipeline de indexação composto por segmentação em chunks (sliding window 350 palavras, sobreposição de 60), geração de embeddings multilinguais (intfloat/multilingual-e5-small, 384 dimensões) e persistência em PostgreSQL 16 com pgvector;"),
    alinea("c", "Implementar os mecanismos de recuperação: vetorial (HNSW + similaridade cosseno), lexical com BM25, busca textual nativa do PostgreSQL (tsvector + GIN + ts_rank_cd), como linha de base adicional, e híbrido (RRF combinando os rankings vetorial e BM25);"),
    alinea("d", "Avaliar os métodos com um conjunto de 50 consultas anotadas manualmente, utilizando as métricas Hit@K (K = 1, 3, 5), MRR e latência, com testes de significância estatística pareados;"),
    alinea("e", "Desenvolver uma interface web (FastAPI + React) para uso em contexto de biblioteca universitária, integrando recuperação e geração de respostas via LLM (Groq/LLaMA 3.3 70B);"),
    alinea("f", "Avaliar a qualidade das respostas geradas quanto à correção, à fidelidade às fontes recuperadas e à citação dos documentos de origem (etapa prevista para o TCC II)."),

    h2("1.3 Justificativa"),
    p("A adoção de sistemas RAG para documentos institucionais representa contribuição tanto prática quanto científica. Do ponto de vista prático, o sistema automatiza respostas a dúvidas recorrentes de estudantes — sobre aproveitamento de estudos, reingresso, transferência, calendário escolar, bolsas e emissão de diplomas — liberando servidores para demandas mais complexas. O contexto de uso em biblioteca universitária (kiosque de consulta) é especialmente adequado, pois integra o serviço ao ambiente físico de orientação acadêmica já existente. Embora o contexto de uso seja o câmpus de Bauru, o corpus reúne as resoluções gerais da UNESP, que regem todas as unidades da universidade, inclusive a Faculdade de Ciências de Bauru; normas específicas de unidade ou de curso não foram incluídas nesta etapa."),
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
    p("A busca vetorial por similaridade semântica representa textos como vetores densos em espaços de alta dimensão, de modo que textos semanticamente similares ocupam regiões próximas. Os modelos da família E5 (WANG et al., 2022) e sua versão multilíngue (WANG et al., 2024), à qual pertence o intfloat/multilingual-e5-small, com 384 dimensões, são treinados por aprendizado contrastivo em pares de textos similares e distintos, produzindo representações que capturam relações semânticas além da coincidência lexical. Neste trabalho, o modelo é executado com a biblioteca sentence-transformers, derivada do Sentence-BERT (REIMERS; GUREVYCH, 2019). O prefixo \"query: \" é inserido antes das consultas e \"passage: \" antes dos documentos, seguindo a especificação do modelo E5."),
    p("O armazenamento e a recuperação eficiente de vetores em larga escala são viabilizados por extensões de banco de dados vetorial. O pgvector (PGVECTOR, 2021) adiciona ao PostgreSQL suporte a vetores de dimensão arbitrária e busca por vizinhos mais próximos aproximados (ANN, do inglês Approximate Nearest Neighbors) via índices IVFFlat ou HNSW (Hierarchical Navigable Small World), um grafo hierárquico de proximidade proposto por Malkov e Yashunin (2020). A integração ao PostgreSQL permite executar busca vetorial e textual no mesmo sistema, simplificando a arquitetura e eliminando a necessidade de serviços externos como Pinecone ou Weaviate."),

    h2("2.4 Busca Textual Esparsa: BM25 e Full-Text Search"),
    p("O BM25 (Best Match 25), formalizado por Robertson e Zaragoza (2009), é uma função de ranqueamento baseada em frequência de termos (TF) e frequência inversa de documentos (IDF), com normalização pelo comprimento do documento. A pontuação de um documento D para uma consulta Q é:"),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 140, after: 140 },
      children: [new TextRun({ text: "BM25(D, Q) = Σ IDF(q) · f(q, D) · (k₁ + 1) / [f(q, D) + k₁ · (1 − b + b · |D| / avgdl)]", font: FONT, size: SIZE, italic: true })]
    }),
    p("em que a soma percorre os termos q da consulta, f(q, D) é a frequência de q em D, |D| é o comprimento do documento, avgdl é o comprimento médio dos documentos da coleção e k₁ e b controlam, respectivamente, a saturação da frequência dos termos e a normalização pelo comprimento (valores usuais: k₁ = 1,2 e b = 0,75). Amplamente adotado como baseline em recuperação de informação, o BM25 demonstra desempenho competitivo frente a métodos neurais em domínios com vocabulário técnico especializado e em consultas lexicais diretas."),
    p("O PostgreSQL implementa busca de texto completo nativa por meio do tipo tsvector e do índice GIN (Generalized Inverted Index), com as funções de ranqueamento ts_rank e ts_rank_cd. Diferentemente do BM25, essas funções não usam estatísticas globais da coleção, como o IDF: ts_rank_cd implementa o ranqueamento por densidade de cobertura (cover density) proposto por Clarke, Cormack e Tudhope (2000), que favorece trechos em que os termos da consulta aparecem próximos entre si. Por isso, a busca textual nativa do PostgreSQL e o BM25 são tratados neste trabalho como métodos distintos. A extensão unaccent remove diacríticos durante a tokenização, essencial para o português, onde variações acentuadas (\"gestao\" vs. \"gestão\") devem ser tratadas como equivalentes. Para uso em colunas geradas (GENERATED ALWAYS AS), é necessário envolver unaccent() em uma função IMMUTABLE, contornando a restrição de volatilidade do PostgreSQL para expressões geradas."),

    h2("2.5 Fusão Híbrida: Reciprocal Rank Fusion (RRF)"),
    p("Cormack et al. (2009) propuseram o Reciprocal Rank Fusion como método para combinar múltiplos rankings de recuperação sem necessidade de calibração ou treinamento adicional. A pontuação de um documento d combinando m listas de ranking é:"),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 140, after: 140 },
      children: [new TextRun({ text: "RRF(d) = Σᵢ 1 / (k + rankᵢ(d))", font: FONT, size: SIZE, italic: true })]
    }),
    p("onde rankᵢ(d) é a posição de d no ranking i e k é um parâmetro de suavização (tipicamente 60). O método demonstrou superar estratégias de fusão por aprendizado e métodos de ranqueamento individuais em benchmarks de recuperação ad hoc. No contexto RAG, o RRF é especialmente atraente por combinar a precisão lexical do BM25 com a compreensão semântica da busca vetorial, compensando as fraquezas de cada método em diferentes tipos de consulta."),

    h2("2.6 Avaliação de Sistemas de Recuperação"),
    p("A avaliação de sistemas de recuperação de informação compara os rankings produzidos com julgamentos de relevância previamente anotados. Quando cada consulta possui um documento relevante conhecido, são adequadas métricas orientadas à posição desse documento: Hit@K, que indica se ele aparece entre os K primeiros resultados, e o Mean Reciprocal Rank (MRR), média do inverso da posição em que ele aparece. Como essas métricas são médias sobre um conjunto finito de consultas, diferenças entre sistemas podem decorrer do acaso. Smucker, Allan e Carterette (2007) compararam testes de significância usados em RI e recomendam o teste de aleatorização pareado (randomization test), que não pressupõe distribuição normal das diferenças. Quando várias comparações são feitas sobre os mesmos dados, os valores-p devem ser ajustados, por exemplo pelo método sequencial de Holm (1979), para controlar a probabilidade de falsos positivos."),

    pageBreak(),

    // ════════════════════════════════════════════════════════════════════════
    // CAP 3 — METODOLOGIA
    // ════════════════════════════════════════════════════════════════════════
    titulo("3 Metodologia"),
    p("O trabalho é organizado em cinco fases sequenciais: coleta do corpus, indexação, implementação dos métodos de recuperação, desenvolvimento da interface web e avaliação experimental."),

    h2("3.1 Fase 1 — Coleta e Pré-processamento do Corpus"),
    p("O corpus é composto por 936 resoluções da UNESP publicadas entre 2016 e 2026, coletadas da base de resoluções do sistema sistemas.unesp.br/legislacao-web por meio de um scraper Python desenvolvido com as bibliotecas requests e BeautifulSoup. Portarias e documentos anteriores a 2016 não foram coletados. O scraper percorre a lista de documentos disponível na página inicial do portal, extrai os metadados (número, ano, data) de cada resolução e realiza requisições GET individuais ao endpoint de texto integral. Foi adotado um intervalo de 1,2 segundo entre requisições, com novas tentativas em caso de falha do servidor. O processo é controlado por um arquivo manifest.json que registra os documentos já coletados, permitindo retomada incremental."),
    p("O texto integral de cada resolução é extraído do elemento HTML div.painelTexto, preservando as quebras de linha e removendo os espaços em branco das extremidades de cada linha; respostas sem documento (texto com menos de 500 caracteres ou correspondente à página padrão do portal) são descartadas. Como os documentos são publicados originalmente em HTML, não apresentam os artefatos típicos da extração de PDF, como cabeçalhos, rodapés e numeração de página, e nenhuma limpeza adicional foi necessária. Os textos foram armazenados em UTF-8 em data/legislacao/, no formato resolucao_AAAA_NNNN.txt. As resoluções somam cerca de 1,15 milhão de palavras, com mediana de 570 palavras por documento (mínimo de 124 e máximo de 74.640)."),

    h2("3.2 Fase 2 — Indexação: Chunking, Embeddings e pgvector"),
    p("Os textos pré-processados são segmentados em chunks pelo método de janela deslizante (sliding window), com tamanho de 350 palavras e sobreposição de 60 palavras. O corpus resultou em 4.229 chunks, com média de 318 palavras por chunk; as 369 resoluções com menos de 350 palavras formam um único chunk cada."),
    p("Os embeddings são gerados pelo modelo intfloat/multilingual-e5-small (384 dimensões), executado localmente via sentence-transformers sem custo de API. As consultas recebem o prefixo \"query: \" e os documentos o prefixo \"passage: \", conforme especificação do modelo. Os vetores são persistidos na coluna embedding (tipo vector(384)) da tabela chunks no PostgreSQL 16 com pgvector. Um índice HNSW com métrica de distância cosseno (ops: vector_cosine_ops) é criado sobre a coluna para busca ANN eficiente."),
    p("Simultaneamente, cada chunk recebe uma coluna content_tsv (tipo tsvector), gerada automaticamente pela expressão to_tsvector('portuguese', unaccent_immutable(content)), onde unaccent_immutable é uma função SQL IMMUTABLE e PARALLEL SAFE que envolve a extensão unaccent. Um índice GIN é criado sobre content_tsv para busca textual eficiente."),

    h2("3.3 Fase 3 — Implementação dos Métodos de Recuperação"),
    h3("3.3.1 Busca Vetorial"),
    p("A busca vetorial calcula o embedding da consulta (com prefixo \"query: \"), realiza a operação de distância cosseno (<=> no pgvector) entre o vetor da consulta e os vetores indexados via HNSW e retorna os K chunks com menor distância. A pontuação final é 1 − distância_cosseno. Como o índice HNSW do pgvector retorna no máximo hnsw.ef_search candidatos (40 por padrão), o parâmetro foi elevado para 200, permitindo recuperar os 50 candidatos usados na fusão híbrida e na avaliação."),

    h3("3.3.2 Busca Lexical com BM25"),
    p("Como o PostgreSQL não oferece BM25 nativamente, o ranqueamento foi implementado em Python sobre um índice invertido construído a partir da própria coluna content_tsv: cada lexema e sua frequência no chunk são obtidos com a função unnest(tsvector), e a consulta é normalizada com to_tsvector('portuguese', unaccent(consulta)). Dessa forma, o BM25 e a busca textual nativa compartilham exatamente a mesma tokenização, radicalização (stemmer Snowball para português), lista de stopwords e remoção de acentos, diferindo apenas na função de ranqueamento. Foram adotados k₁ = 1,2 e b = 0,75 (ROBERTSON; ZARAGOZA, 2009) e o IDF na forma ln(1 + (N − n + 0,5)/(n + 0,5)), em que N é o número de chunks e n o número de chunks que contêm o termo; essa forma evita pesos negativos para termos muito frequentes."),

    h3("3.3.3 Busca Textual Nativa do PostgreSQL (FTS-PG)"),
    p("Como linha de base adicional, a busca textual nativa normaliza a consulta com plainto_tsquery (com unaccent) e combina os termos resultantes pelo operador OU (|), de modo que basta um termo em comum para que o chunk seja candidato; os candidatos são ordenados por ts_rank_cd. Na versão preliminar deste trabalho, os termos eram combinados pelo operador E (&), padrão de plainto_tsquery, o que exigia a presença de todos os termos da consulta no mesmo chunk: com essa configuração, 22 das 50 consultas de avaliação não retornavam nenhum resultado, o que penalizava o método de forma artificial."),

    h3("3.3.4 Busca Híbrida (RRF)"),
    p("A busca híbrida combina os rankings vetorial e BM25 via Reciprocal Rank Fusion com k = 60. Os 50 primeiros resultados de cada método são recuperados; a pontuação RRF de cada chunk é calculada como 1/(60 + rank_vetorial) + 1/(60 + rank_BM25), em que um chunk ausente de um dos rankings não recebe a parcela correspondente. Os chunks são reordenados pela pontuação RRF combinada e os K melhores são retornados."),

    h2("3.4 Fase 4 — Interface Web"),
    p("Uma interface de consulta foi desenvolvida para o contexto de uso em biblioteca universitária. O backend é implementado em FastAPI (Python), expondo os endpoints POST /api/ask (recuperação + geração com LLM), POST /api/search (apenas recuperação) e GET /api/health. O LLM utilizado é o LLaMA 3.3 70B Versatile, acessado via API Groq (tier gratuito, compatível com OpenAI), com temperatura 0,1 e máximo de 800 tokens por resposta. O prompt do sistema instrui o modelo a responder exclusivamente com base nos trechos fornecidos, citando a resolução de origem."),
    p("O frontend é implementado em React + Vite com uma interface de chat: o usuário digita a pergunta em uma caixa de texto, o sistema recupera os chunks mais relevantes pelo método selecionado, o LLM gera uma resposta fundamentada nas fontes e a interface exibe a resposta com cards expansíveis mostrando os trechos de origem e a pontuação de relevância. O método de busca pode ser alternado entre Híbrido (RRF), Vetorial, BM25 e FTS-PG por um seletor no rodapé da tela. O tempo de resposta é exibido ao final de cada mensagem."),

    h2("3.5 Fase 5 — Avaliação Experimental"),
    p("A avaliação utiliza um conjunto de 50 consultas anotadas manualmente pelos autores, cada uma associada a um único documento de referência no corpus. As consultas abrangem 25 resoluções distintas e são distribuídas em dois tipos:"),
    alinea("a", "Lexical (26 consultas): termos do documento-alvo aparecem literalmente na pergunta, favorecendo a busca por palavras-chave;"),
    alinea("b", "Semântica (24 consultas): a intenção é expressa por paráfrases ou sinônimos sem coincidência literal com o documento, favorecendo a busca por similaridade semântica."),
    p("Como os métodos retornam chunks e a relevância é atribuída a documentos, cada ranking é convertido em uma lista de documentos distintos, na ordem de sua primeira ocorrência entre os 50 primeiros chunks; as métricas são calculadas sobre os cinco primeiros documentos distintos. As métricas são Hit@K (K = 1, 3, 5), proporção de consultas em que o documento de referência aparece entre os K primeiros documentos, e o Mean Reciprocal Rank (MRR), média do inverso da posição do documento de referência (zero quando ele não aparece entre os cinco primeiros)."),
    p("Para verificar se as diferenças observadas são estatisticamente significativas, aplica-se o teste de aleatorização pareado sobre o recíproco da posição obtido em cada consulta, com 10.000 permutações (SMUCKER; ALLAN; CARTERETTE, 2007), comparando-se a busca híbrida com a vetorial e com o BM25, a vetorial com o BM25 e o BM25 com a busca textual nativa; os valores-p dessas quatro comparações são ajustados pelo método de Holm (1979). Intervalos de confiança de 95% para o MRR são estimados por bootstrap percentil com 10.000 reamostragens."),
    p("Antes das medições, o modelo de embeddings e o índice BM25 são carregados e cada método é executado uma vez (aquecimento), para que o custo de inicialização não seja atribuído à primeira consulta. A latência de cada método é medida com time.perf_counter() e inclui, nos métodos vetorial e híbrido, o tempo de geração do embedding da consulta; são reportados a mediana e o percentil 95 sobre as 50 consultas."),

    pageBreak(),

    // ════════════════════════════════════════════════════════════════════════
    // CAP 4 — EXPERIMENTOS E RESULTADOS
    // ════════════════════════════════════════════════════════════════════════
    titulo("4 Experimentos e Resultados"),

    h2("4.1 Configuração Experimental"),
    p(`Os experimentos foram executados em um notebook com processador Intel Core i7-1355U (13ª geração) e 32 GB de RAM; o modelo de embeddings foi executado em CPU via sentence-transformers. O PostgreSQL 16 com pgvector 0.8.2 é executado em container Docker. O conjunto de avaliação compreende ${R.meta.n_consultas} consultas (${T.lexical.n} lexicais e ${T.semantic.n} semânticas), cada uma com um único documento de referência. As métricas são calculadas sobre os ${R.meta.k} primeiros documentos distintos, obtidos dos ${R.meta.fetch_por_metodo} primeiros chunks de cada método; o RRF usa k = ${R.meta.rrf_k}, o BM25 usa k₁ = ${fmt(R.meta.bm25_k1, 1)} e b = ${fmt(R.meta.bm25_b, 2)}, e o índice HNSW usa ef_search = ${R.meta.hnsw_ef_search}. O código, o conjunto de avaliação e os resultados por consulta estão disponíveis no repositório do projeto.`),

    h2("4.2 Resultados Globais"),
    caption("Tabela 1 — Métricas de recuperação globais (50 consultas, K = 5). Em negrito, o melhor valor de cada métrica."),
    resultTable,
    fonte(),
    p(`Conforme a Tabela 1, a busca híbrida obteve os maiores valores de Hit@1 (${fmt(G.rrf.hit1)}), Hit@3 (${fmt(G.rrf.hit3)}) e MRR (${fmt(G.rrf.mrr)}) e empatou com a busca vetorial em Hit@5 (${fmt(G.rrf.hit5)}). O BM25 ficou em segundo lugar em MRR (${fmt(G.bm25.mrr)}) e Hit@1 (${fmt(G.bm25.hit1)}), à frente da busca vetorial (MRR = ${fmt(G.vec.mrr)}), e a busca textual nativa do PostgreSQL apresentou o menor desempenho (MRR = ${fmt(G.fts.mrr)}). Com a combinação dos termos por OU, todos os métodos retornaram resultados para todas as consultas. Os intervalos de confiança de 95% do MRR dos três primeiros métodos, contudo, sobrepõem-se amplamente, o que antecipa o resultado dos testes de significância.`),

    h2("4.3 Significância Estatística"),
    caption("Tabela 2 — Comparações pareadas do MRR (teste de aleatorização com 10.000 permutações; valores-p ajustados pelo método de Holm). Em negrito, diferenças significativas a 5%."),
    sigTable,
    fonte(),
    p(`A busca híbrida superou a vetorial em ${cmp("rrf", "vec").vitorias_a} consultas e foi superada em ${cmp("rrf", "vec").vitorias_b}, com empate nas ${cmp("rrf", "vec").empates} restantes. O valor-p bruto dessa comparação (${fmtP(cmp("rrf", "vec").p_mrr)}) indicaria significância a 5%, mas deixa de indicá-la após o ajuste de Holm (${fmtP(cmp("rrf", "vec").p_mrr_holm)}). As diferenças entre a busca híbrida e o BM25 (p ajustado ${pEq(cmp("rrf", "bm25").p_mrr_holm)}) e entre a vetorial e o BM25 (p ajustado ${pEq(cmp("vec", "bm25").p_mrr_holm)}) também não são significativas. A única diferença significativa no conjunto completo é a do BM25 sobre a busca textual nativa do PostgreSQL (p ajustado ${pEq(cmp("bm25", "fts").p_mrr_holm)}). Assim, com ${R.meta.n_consultas} consultas, os dados são compatíveis com uma vantagem da busca híbrida, mas não permitem afirmá-la no conjunto completo.`),

    h2("4.4 Análise por Tipo de Consulta"),
    caption("Tabela 3 — Hit@1, Hit@5 e MRR por tipo de consulta (K = 5). Em negrito, o melhor valor de cada métrica dentro do tipo."),
    typeTable,
    fonte(),
    p(`Nas consultas lexicais (Tabela 3), o BM25 obteve os melhores valores de Hit@1 (${fmt(T.lexical.bm25.hit1)}) e MRR (${fmt(T.lexical.bm25.mrr)}); as buscas vetorial e híbrida tiveram MRR idêntico (${fmt(T.lexical.vec.mrr)}) e ambas alcançaram Hit@5 = ${fmt(T.lexical.rrf.hit5)}. Nenhuma diferença entre BM25, vetorial e híbrida foi significativa nesse subconjunto. Nas consultas semânticas, a busca híbrida obteve MRR de ${fmt(T.semantic.rrf.mrr)}, contra ${fmt(T.semantic.vec.mrr)} da vetorial e ${fmt(T.semantic.bm25.mrr)} do BM25, e Hit@1 de ${fmt(T.semantic.rrf.hit1)}, contra ${fmt(T.semantic.vec.hit1)} e ${fmt(T.semantic.bm25.hit1)}. Nesse subconjunto, a vantagem da busca híbrida foi significativa mesmo após o ajuste de Holm, tanto sobre a vetorial (p ${pEq(cmpT("semantic", "rrf", "vec").p_mrr_holm)}) quanto sobre o BM25 (p ${pEq(cmpT("semantic", "rrf", "bm25").p_mrr_holm)}). Ao contrário do esperado, a busca vetorial não superou o BM25 nas consultas semânticas (MRR de ${fmt(T.semantic.vec.mrr)} contra ${fmt(T.semantic.bm25.mrr)}). Por se tratar de uma análise de subgrupos com ${T.semantic.n} consultas, esses resultados devem ser lidos como indícios, e não como conclusões.`),

    h2("4.5 Análise de Latência"),
    caption("Tabela 4 — Latência de recuperação por consulta, após aquecimento (inclui a geração do embedding nos métodos vetorial e híbrido)."),
    latTable,
    fonte(),
    p(`Após o aquecimento, a geração do embedding da consulta levou, em mediana, ${ms(R.embedding_ms.median)} ms. A busca vetorial completa teve mediana de ${ms(G.vec.lat_median_ms)} ms e a híbrida, de ${ms(G.rrf.lat_median_ms)} ms; o BM25 respondeu em ${ms(G.bm25.lat_median_ms)} ms e a busca nativa do PostgreSQL em ${ms(G.fts.lat_median_ms)} ms, pois a combinação por OU torna candidatos muitos chunks, que precisam ser ranqueados. Na versão preliminar deste trabalho, a latência média reportada para a busca vetorial (cerca de 339 ms) incluía o carregamento do modelo na primeira consulta (12,4 s), o que distorcia a média. Em todos os métodos, a latência de recuperação ficou abaixo de 200 ms no percentil 95, valor adequado ao uso interativo; o tempo de geração da resposta pelo LLM será medido na avaliação da geração.`),

    h2("4.6 Discussão"),
    p(`Os resultados revisados alteram a interpretação apresentada na versão preliminar. Naquela versão, a busca textual parecia falhar nas consultas semânticas (MRR de 0,042), o que sugeria uma vantagem clara da busca vetorial nesse tipo de consulta. A revisão mostrou que o efeito vinha da combinação dos termos por E: com a combinação por OU e o ranqueamento BM25, a busca lexical teve desempenho equivalente ao da vetorial também nas consultas semânticas. Uma explicação plausível é que, mesmo parafraseadas, as consultas compartilham com as resoluções termos institucionais específicos, como "reingresso", "extensão" e "diploma", que o IDF do BM25 valoriza.`),
    p(`A busca híbrida foi a mais robusta entre os tipos de consulta: empatou com a vetorial nas consultas lexicais e foi a melhor nas semânticas. Esse comportamento indica que os erros dos métodos vetorial e BM25 são em parte complementares, como prevê a literatura de fusão de rankings (CORMACK et al., 2009). A vantagem global, porém, não foi estatisticamente significativa com ${R.meta.n_consultas} consultas, e a confirmação depende de um conjunto de avaliação maior.`),
    p(`A comparação entre o BM25 e a busca textual nativa do PostgreSQL, que compartilham exatamente o mesmo processamento de texto, isola o efeito da função de ranqueamento: o ts_rank_cd não considera a raridade dos termos na coleção, de modo que termos frequentes e pouco informativos pesam tanto quanto termos raros. A diferença de ${fmt(cmp("bm25", "fts").delta_mrr)} no MRR mostra que a busca textual nativa do PostgreSQL não deve ser tomada como equivalente ao BM25 em comparações experimentais.`),
    p("Os resultados estão sujeitos a limitações que devem ser consideradas: (i) o conjunto de avaliação é pequeno, com 50 consultas que cobrem apenas 25 das 936 resoluções; (ii) as consultas foram redigidas pelos autores a partir dos títulos das resoluções, o que pode favorecer os métodos lexicais e não representa necessariamente as perguntas de usuários reais; (iii) cada consulta tem um único documento relevante, de modo que outros documentos pertinentes recuperados são contados como erro, o que subestima o desempenho de todos os métodos; (iv) a classificação das consultas em lexicais e semânticas foi feita pelos próprios autores; e (v) foi avaliada apenas a recuperação, e não a qualidade das respostas geradas pelo LLM."),
    p("Como trabalhos futuros, destacam-se: (i) a ampliação do conjunto de avaliação com perguntas reais de estudantes e com julgamentos de relevância múltiplos, obtidos pela combinação (pooling) dos resultados dos quatro métodos; (ii) a avaliação das respostas geradas pelo LLM quanto à correção, à fidelidade às fontes e à citação, comparando-as com as respostas do mesmo modelo sem recuperação; (iii) a avaliação de modelos de embedding de maior dimensão (768 ou 1024); (iv) o reranqueamento dos resultados com um modelo cross-encoder; e (v) o uso de metadados estruturados (número, ano e assunto da resolução) como filtros de busca."),

    pageBreak(),

    // ════════════════════════════════════════════════════════════════════════
    // CAP 5 — CONSIDERAÇÕES FINAIS
    // ════════════════════════════════════════════════════════════════════════
    titulo("5 Considerações Finais"),
    p("Este trabalho implementou um sistema RAG para consulta em linguagem natural das resoluções da UNESP, com coleta automatizada do corpus, indexação em PostgreSQL com pgvector, quatro métodos de recuperação e uma interface web voltada ao uso em biblioteca universitária. A comparação experimental dos métodos foi conduzida com métricas de ranking, medição de latência e testes de significância pareados."),
    p(`Em resposta à questão de pesquisa, a busca híbrida por RRF entre os rankings vetorial e BM25 obteve o melhor desempenho global (MRR = ${fmt(G.rrf.mrr)}) e foi a mais robusta entre os tipos de consulta, com vantagem significativa sobre os métodos individuais nas consultas semânticas. No conjunto completo de ${R.meta.n_consultas} consultas, contudo, sua superioridade sobre a busca vetorial e o BM25 não pôde ser confirmada estatisticamente. A revisão metodológica mostrou ainda que detalhes de implementação, como a forma de combinar os termos da consulta e a função de ranqueamento, alteram substancialmente as conclusões de uma comparação entre busca lexical e vetorial.`),
    p("As próximas etapas, previstas para o TCC II, são a ampliação do conjunto de avaliação, com perguntas reais e julgamentos de relevância múltiplos, e a avaliação da qualidade das respostas geradas pelo LLM, que completará a avaliação do sistema RAG proposto."),

    pageBreak(),

    // ════════════════════════════════════════════════════════════════════════
    // PLANO DE TRABALHO
    // ════════════════════════════════════════════════════════════════════════
    titulo("Plano de Trabalho"),
    caption("Tabela 5 — Cronograma de atividades, de abril de 2026 a fevereiro de 2027 (X = período de execução realizado ou previsto)."),
    cronTable,
    fonte(),
    p("A greve na universidade alterou o calendário acadêmico, e a entrega final do trabalho foi reprogramada para fevereiro de 2027, conforme a Tabela 5. A implementação do sistema e a primeira rodada de avaliação foram concluídas até junho de 2026; em outubro de 2026, a avaliação foi revisada, com a implementação do BM25, a correção da busca textual nativa, a medição da latência após aquecimento e a inclusão de testes de significância. Restam a ampliação do conjunto de avaliação, a avaliação da geração de respostas e a escrita do TCC II."),

    pageBreak(),

    // ════════════════════════════════════════════════════════════════════════
    // REFERÊNCIAS
    // ════════════════════════════════════════════════════════════════════════
    titulo("Referências"),

    pSR("CLARKE, Charles L. A.; CORMACK, Gordon V.; TUDHOPE, Elizabeth A. Relevance ranking for one to three term queries. Information Processing & Management, v. 36, n. 2, p. 291–311, 2000."),
    br(),
    pSR("CORMACK, Gordon V.; CLARKE, Charles L. A.; BUETTCHER, Stefan. Reciprocal rank fusion outperforms condorcet and individual rank learning methods. In: ANNUAL INTERNATIONAL ACM SIGIR CONFERENCE ON RESEARCH AND DEVELOPMENT IN INFORMATION RETRIEVAL, 32., 2009, Boston. Proceedings [...]. New York: ACM, 2009. p. 758–759."),
    br(),
    pSR("GAO, Yunfan et al. Retrieval-augmented generation for large language models: a survey. arXiv:2312.10997, 2023. Disponível em: https://arxiv.org/abs/2312.10997. Acesso em: 5 jun. 2026."),
    br(),
    pSR("HOLM, Sture. A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics, v. 6, n. 2, p. 65–70, 1979."),
    br(),
    pSR("JI, Ziwei et al. Survey of hallucination in natural language generation. ACM Computing Surveys, v. 55, n. 12, p. 1–38, mar. 2023."),
    br(),
    pSR("LEWIS, Patrick et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. In: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS, 33., 2020, [S. l.]. Proceedings [...]. [S. l.]: NeurIPS, 2020. p. 9459–9474."),
    br(),
    pSR("MALKOV, Yu. A.; YASHUNIN, D. A. Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs. IEEE Transactions on Pattern Analysis and Machine Intelligence, v. 42, n. 4, p. 824–836, 2020."),
    br(),
    pSR("PGVECTOR. pgvector: open-source vector similarity search for Postgres. [S. l.], 2021. Disponível em: https://github.com/pgvector/pgvector. Acesso em: 5 jun. 2026."),
    br(),
    pSR("REIMERS, Nils; GUREVYCH, Iryna. Sentence-BERT: sentence embeddings using siamese BERT-networks. In: CONFERENCE ON EMPIRICAL METHODS IN NATURAL LANGUAGE PROCESSING, 2019. Proceedings [...]. [S. l.]: ACL, 2019. p. 3982–3992."),
    br(),
    pSR("ROBERTSON, Stephen; ZARAGOZA, Hugo. The probabilistic relevance framework: BM25 and beyond. Foundations and Trends in Information Retrieval, v. 3, n. 4, p. 333–389, 2009."),
    br(),
    pSR("SMUCKER, Mark D.; ALLAN, James; CARTERETTE, Ben. A comparison of statistical significance tests for information retrieval evaluation. In: ACM CONFERENCE ON INFORMATION AND KNOWLEDGE MANAGEMENT, 16., 2007, Lisboa. Proceedings [...]. New York: ACM, 2007. p. 623–632."),
    br(),
    pSR("WANG, Liang et al. Text embeddings by weakly-supervised contrastive pre-training. arXiv:2212.03533, 2022. Disponível em: https://arxiv.org/abs/2212.03533. Acesso em: 5 jun. 2026."),
    br(),
    pSR("WANG, Liang et al. Multilingual E5 text embeddings: a technical report. arXiv:2402.05672, 2024. Disponível em: https://arxiv.org/abs/2402.05672. Acesso em: 14 out. 2026."),
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
