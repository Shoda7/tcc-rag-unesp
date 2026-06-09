import {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, Header, TableOfContents, PageBreak, LevelFormat,
  VerticalAlign
} from "docx";
import { writeFileSync } from "fs";

// Medidas ABNT (DXA: 1440 = 1 polegada = 2,54 cm)
// A4: 11906 x 16838 DXA
// Margens: sup 3cm, inf 2cm, esq 3cm, dir 2cm
const A4_W = 11906;
const A4_H = 16838;
const M_TOP = 1701;    // 3cm
const M_BOT = 1134;    // 2cm
const M_LEFT = 1701;   // 3cm
const M_RIGHT = 1134;  // 2cm
const CONTENT_W = A4_W - M_LEFT - M_RIGHT; // ~9071 DXA

const FONT = "Times New Roman";
const SIZE = 24; // 12pt em half-points
const SIZE_SM = 20; // 10pt

// Helpers
const br = () => new Paragraph({ children: [] });

const titulo = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  alignment: AlignmentType.CENTER,
  spacing: { before: 0, after: 280 },
  children: [new TextRun({ text: text.toUpperCase(), font: FONT, size: SIZE, bold: true })]
});

const subtitulo = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 280, after: 140 },
  children: [new TextRun({ text, font: FONT, size: SIZE, bold: true })]
});

const subtitulo3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 280, after: 140 },
  children: [new TextRun({ text, font: FONT, size: SIZE, bold: true })]
});

const p = (text, opts = {}) => new Paragraph({
  alignment: AlignmentType.JUSTIFIED,
  indent: { firstLine: 709 }, // 1,25cm
  spacing: { line: 360, lineRule: "auto" }, // 1,5
  children: [new TextRun({ text, font: FONT, size: SIZE, ...opts })]
});

const pSemRecuo = (text, opts = {}) => new Paragraph({
  alignment: AlignmentType.JUSTIFIED,
  spacing: { line: 360, lineRule: "auto" },
  children: [new TextRun({ text, font: FONT, size: SIZE, ...opts })]
});

const pCentro = (text, opts = {}) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { line: 360, lineRule: "auto" },
  children: [new TextRun({ text, font: FONT, size: SIZE, ...opts })]
});

const pDireita = (text, opts = {}) => new Paragraph({
  alignment: AlignmentType.RIGHT,
  spacing: { line: 360, lineRule: "auto" },
  children: [new TextRun({ text, font: FONT, size: SIZE, ...opts })]
});

const alínea = (letter, text) => new Paragraph({
  alignment: AlignmentType.JUSTIFIED,
  indent: { left: 709, firstLine: 0 },
  spacing: { line: 360, lineRule: "auto" },
  children: [new TextRun({ text: `${letter}) ${text}`, font: FONT, size: SIZE })]
});

const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

// Tabela de cronograma
const meses = ["Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
const atividades = [
  { nome: "Levantamento bibliográfico",  meses: [1,1,0,0,0,0,0,0,0] },
  { nome: "Estudo das tecnologias",       meses: [1,1,1,0,0,0,0,0,0] },
  { nome: "Coleta e pré-processamento",   meses: [0,1,1,0,0,0,0,0,0] },
  { nome: "Escrita TCC I",               meses: [0,1,1,1,1,0,0,0,0] },
  { nome: "Pipeline de indexação",        meses: [0,0,1,1,0,0,0,0,0] },
  { nome: "Banco vetorial (pgvector)",    meses: [0,0,1,1,0,0,0,0,0] },
  { nome: "Pipeline de consulta RAG",     meses: [0,0,0,1,1,0,0,0,0] },
  { nome: "Baseline Full-Text Search",    meses: [0,0,0,1,1,0,0,0,0] },
  { nome: "Experimentos e avaliação",     meses: [0,0,0,0,1,1,0,0,0] },
  { nome: "Análise dos resultados",       meses: [0,0,0,0,0,1,1,0,0] },
  { nome: "Escrita TCC II",              meses: [0,0,0,0,0,1,1,1,0] },
  { nome: "Banca final",                 meses: [0,0,0,0,0,0,0,0,1] },
];

const cellW = Math.floor((CONTENT_W - 3000) / 9);
const colWidths = [3000, ...Array(9).fill(cellW)];

const border = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
const borders = { top: border, bottom: border, left: border, right: border };

const mkCell = (text, isHeader = false, fill = "FFFFFF") => new TableCell({
  borders,
  width: { size: isHeader ? 3000 : cellW, type: WidthType.DXA },
  shading: { fill, type: ShadingType.CLEAR },
  margins: { top: 40, bottom: 40, left: 80, right: 80 },
  verticalAlign: VerticalAlign.CENTER,
  children: [new Paragraph({
    alignment: isHeader ? AlignmentType.LEFT : AlignmentType.CENTER,
    children: [new TextRun({ text, font: FONT, size: SIZE_SM, bold: isHeader })]
  })]
});

const headerRow = new TableRow({
  tableHeader: true,
  children: [
    mkCell("Atividade", true, "D9E2F3"),
    ...meses.map(m => mkCell(m, true, "D9E2F3"))
  ]
});

const dataRows = atividades.map(a => new TableRow({
  children: [
    mkCell(a.nome, false, "F5F5F5"),
    ...a.meses.map(v => mkCell(v ? "X" : "", false, v ? "BDD7EE" : "FFFFFF"))
  ]
}));

const cronogramaTable = new Table({
  width: { size: CONTENT_W, type: WidthType.DXA },
  columnWidths: colWidths,
  rows: [headerRow, ...dataRows]
});

// Seção pré-textual (sem numeração visível)
const preTextual = {
  properties: {
    page: {
      size: { width: A4_W, height: A4_H },
      margin: { top: M_TOP, bottom: M_BOT, left: M_LEFT, right: M_RIGHT }
    }
  },
  children: [
    // CAPA
    br(), br(),
    pCentro("UNIVERSIDADE ESTADUAL PAULISTA \"JÚLIO DE MESQUITA FILHO\"", { bold: true }),
    pCentro("FACULDADE DE CIÊNCIAS — CÂMPUS DE BAURU", { bold: true }),
    pCentro("BACHARELADO EM SISTEMAS DE INFORMAÇÃO", { bold: true }),
    br(), br(), br(),
    pCentro("MATHEUS SHODA LIMA"),
    pCentro("RAFAEL PANHOZZI RUBIO"),
    br(), br(), br(),
    pCentro("IMPLEMENTAÇÃO E AVALIAÇÃO DE UM SISTEMA DE RECUPERAÇÃO AUMENTADA POR GERAÇÃO (RAG) PARA CONSULTA DE DOCUMENTOS REGULATÓRIOS DA UNESP BAURU", { bold: true }),
    br(), br(), br(),
    pCentro("Bauru"),
    pCentro("2026"),

    pageBreak(),

    // FOLHA DE ROSTO
    br(), br(),
    pCentro("MATHEUS SHODA LIMA"),
    pCentro("RAFAEL PANHOZZI RUBIO"),
    br(), br(),
    pCentro("IMPLEMENTAÇÃO E AVALIAÇÃO DE UM SISTEMA DE RECUPERAÇÃO AUMENTADA POR GERAÇÃO (RAG) PARA CONSULTA DE DOCUMENTOS REGULATÓRIOS DA UNESP BAURU", { bold: true }),
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
    br(), br(),
    pCentro("Bauru"),
    pCentro("2026"),

    pageBreak(),

    // RESUMO
    titulo("Resumo"),
    p("Este trabalho apresenta a implementação e avaliação de um sistema de Recuperação Aumentada por Geração (RAG, do inglês Retrieval-Augmented Generation) voltado à consulta em linguagem natural de documentos regulatórios da Universidade Estadual Paulista (UNESP) Bauru. O problema central abordado é a dificuldade enfrentada por estudantes e servidores para localizar informações específicas em um extenso corpus de resoluções, portarias e regulamentos institucionais. A solução proposta combina modelos de linguagem de grande porte (LLMs) com recuperação de documentos, reduzindo o fenômeno de alucinação por meio do aterramento das respostas nas fontes originais. O sistema implementa dois mecanismos de busca — vetorial (embeddings densos) e textual (BM25/Full-Text Search) — cujo desempenho é avaliado comparativamente com métricas de recuperação de informação (Precision@K, Recall@K e Mean Reciprocal Rank). O corpus utilizado compreende resoluções e portarias da UNESP referentes ao período de 2016 a 2026, além de documentos curriculares e regulamentares dos cursos de Bacharelado em Sistemas de Informação e Ciência da Computação da Faculdade de Ciências de Bauru. Os resultados preliminares indicam a viabilidade técnica da abordagem, com o protótipo respondendo corretamente a perguntas sobre estrutura curricular, requisitos de estágio e atividades complementares."),
    br(),
    pSemRecuo("Palavras-chave: Recuperação Aumentada por Geração. RAG. Modelos de Linguagem. Busca Vetorial. Documentos Regulatórios. UNESP."),

    pageBreak(),

    // ABSTRACT
    titulo("Abstract"),
    p("This paper presents the implementation and evaluation of a Retrieval-Augmented Generation (RAG) system for natural language querying of regulatory documents from the Universidade Estadual Paulista (UNESP) Bauru. The central problem addressed is the difficulty faced by students and staff in locating specific information within an extensive corpus of institutional resolutions, ordinances, and regulations. The proposed solution combines large language models (LLMs) with document retrieval, mitigating hallucination by grounding responses in original sources. The system implements two retrieval mechanisms — dense vector search (embeddings) and sparse text search (BM25/Full-Text Search) — whose performance is comparatively evaluated using information retrieval metrics (Precision@K, Recall@K, and Mean Reciprocal Rank). The corpus comprises UNESP resolutions and ordinances from 2016 to 2026, along with curricular and regulatory documents from the Bachelor's programs in Information Systems and Computer Science at the Faculdade de Ciências de Bauru. Preliminary results indicate the technical feasibility of the approach, with the prototype correctly answering questions about curriculum structure, internship requirements, and extracurricular activities."),
    br(),
    pSemRecuo("Keywords: Retrieval-Augmented Generation. RAG. Language Models. Vector Search. Regulatory Documents. UNESP."),

    pageBreak(),

    // SUMÁRIO
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

// Seção textual (com numeração de páginas)
const textual = {
  properties: {
    page: {
      size: { width: A4_W, height: A4_H },
      margin: { top: M_TOP, bottom: M_BOT, left: M_LEFT, right: M_RIGHT }
    }
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
    // CAP 1 - INTRODUÇÃO
    titulo("1 Introdução"),
    p("As instituições de ensino superior brasileiras produzem e mantêm um expressivo volume de documentos regulatórios — resoluções, portarias, regulamentos de curso, normas de atividades complementares e regimentos gerais — que regem os direitos e deveres de estudantes, docentes e servidores. Na Universidade Estadual Paulista \"Júlio de Mesquita Filho\" (UNESP), esses documentos estão dispersos em diferentes portais e sistemas institucionais, tornando a busca por informações específicas uma tarefa onerosa para o usuário final."),
    p("O advento dos Modelos de Linguagem de Grande Porte (LLMs, do inglês Large Language Models) introduziu novas possibilidades para sistemas de resposta a perguntas em linguagem natural. Contudo, modelos como GPT-4 e LLaMA 3 apresentam uma limitação crítica: a tendência a gerar respostas factualmente incorretas, fenômeno conhecido como alucinação (JI et al., 2023). Quando aplicados a domínios institucionais específicos, nos quais precisão e rastreabilidade das fontes são requisitos fundamentais, essa limitação torna-se especialmente problemática."),
    p("A Recuperação Aumentada por Geração (RAG, do inglês Retrieval-Augmented Generation), proposta por Lewis et al. (2020), surge como solução ao combinar a capacidade generativa dos LLMs com a recuperação de trechos relevantes de uma base de conhecimento. Em vez de depender exclusivamente do conhecimento paramétrico do modelo, o sistema RAG recupera documentos pertinentes à consulta do usuário e os fornece como contexto ao LLM, restringindo a geração às informações presentes nas fontes."),

    subtitulo("1.1 Problema de Pesquisa"),
    p("Dada a dificuldade de acesso eficiente à legislação institucional da UNESP Bauru, o presente trabalho formula a seguinte questão de pesquisa: em que medida um sistema RAG, baseado em busca vetorial por similaridade semântica, supera uma abordagem de busca textual tradicional (BM25/Full-Text Search) na recuperação de informações regulatórias institucionais em língua portuguesa?"),

    subtitulo("1.2 Objetivos"),
    subtitulo3("1.2.1 Objetivo Geral"),
    p("Implementar e avaliar um sistema de Recuperação Aumentada por Geração (RAG) para consulta em linguagem natural de documentos regulatórios da UNESP Bauru, comparando seu desempenho com um baseline de busca textual tradicional."),

    subtitulo3("1.2.2 Objetivos Específicos"),
    alínea("a", "Coletar, pré-processar e organizar o corpus de documentos regulatórios da UNESP Bauru;"),
    alínea("b", "Implementar o pipeline de indexação composto por segmentação em chunks, geração de embeddings e armazenamento em banco de dados vetorial (pgvector);"),
    alínea("c", "Implementar o pipeline de consulta RAG integrando recuperação vetorial e modelo de linguagem para geração de respostas fundamentadas nas fontes;"),
    alínea("d", "Implementar o baseline de busca textual utilizando BM25/Full-Text Search sobre o mesmo corpus;"),
    alínea("e", "Avaliar e comparar os dois sistemas utilizando métricas de recuperação de informação: Precision@K, Recall@K e Mean Reciprocal Rank (MRR)."),

    subtitulo("1.3 Justificativa"),
    p("A adoção de sistemas de resposta a perguntas baseados em RAG para documentos institucionais representa uma contribuição tanto prática quanto científica. Do ponto de vista prático, reduz a carga administrativa ao automatizar respostas a dúvidas recorrentes de estudantes — sobre requisitos de estágio, atividades complementares, grades curriculares e prazos regulamentares —, liberando servidores para demandas mais complexas. Do ponto de vista científico, a avaliação comparativa entre busca vetorial e busca textual em um corpus institucional em língua portuguesa contribui para a literatura sobre sistemas RAG em domínios especializados, ainda escassa para o português."),

    pageBreak(),

    // CAP 2 - REFERENCIAL TEÓRICO
    titulo("2 Referencial Teórico"),
    subtitulo("2.1 Modelos de Linguagem de Grande Porte e o Problema das Alucinações"),
    p("Os Modelos de Linguagem de Grande Porte (LLMs) são redes neurais treinadas em vastos corpora textuais com o objetivo de modelar a distribuição probabilística de sequências de tokens. Modelos como a família GPT (OpenAI), LLaMA (Meta) e Claude (Anthropic) demonstraram capacidade notável de geração de texto coerente, tradução, sumarização e resposta a perguntas em linguagem natural."),
    p("Entretanto, Ji et al. (2023) identificam e sistematizam o problema das alucinações em modelos de linguagem natural: a geração de conteúdo factualmente incorreto, porém fluente e aparentemente plausível. Os autores categorizam as alucinações em intrínsecas (contradição com o contexto fornecido) e extrínsecas (informações não verificáveis ou falsas). Em aplicações de alta precisão, como consulta a documentos regulatórios, essa característica representa um risco crítico, pois respostas incorretas sobre prazos, requisitos ou normas podem prejudicar diretamente os usuários."),

    subtitulo("2.2 Recuperação Aumentada por Geração (RAG)"),
    p("Lewis et al. (2020) introduziram o paradigma de Recuperação Aumentada por Geração (RAG) como solução para o problema do conhecimento estático nos LLMs. A arquitetura RAG combina um componente de recuperação (retriever), responsável por selecionar documentos relevantes de uma base de conhecimento externa, com um componente gerador (LLM), que produz respostas condicionadas tanto à pergunta do usuário quanto aos documentos recuperados."),
    p("Gao et al. (2023) apresentam uma revisão abrangente das variantes de RAG, categorizando-as em: RAG Naive (recuperação simples seguida de geração), RAG Avançado (com pré e pós-processamento da recuperação) e RAG Modular (com componentes especializados e intercambiáveis). Os autores destacam que a qualidade do componente de recuperação é determinante para o desempenho do sistema, sendo a escolha entre busca vetorial e busca esparsa um dos principais fatores de diferenciação."),

    subtitulo("2.3 Busca Vetorial e Modelos de Embedding"),
    p("A busca vetorial por similaridade semântica baseia-se na representação de textos como vetores densos em espaços de alta dimensão, nos quais textos semanticamente similares ocupam regiões próximas. Modelos de embedding como o multilingual-e5-large (Wang et al., 2022) e o paraphrase-multilingual-MiniLM-L12-v2 (Reimers; Gurevych, 2019) são treinados para produzir representações que capturam similaridade semântica entre sentenças em múltiplos idiomas, incluindo o português."),
    p("O armazenamento e a recuperação eficiente de vetores em larga escala são viabilizados por bancos de dados vetoriais. O pgvector (2021) é uma extensão open-source para PostgreSQL que adiciona suporte a tipos de dados vetoriais e operações de busca por vizinhos mais próximos aproximados (ANN), utilizando índices HNSW (Hierarchical Navigable Small World) ou IVFFlat. Sua integração ao PostgreSQL permite combinar busca vetorial e busca textual no mesmo sistema gerenciador de banco de dados, simplificando a arquitetura de sistemas RAG."),

    subtitulo("2.4 Busca Textual Esparsa: BM25 e Full-Text Search"),
    p("O BM25 (Best Match 25), formalizado por Robertson e Zaragoza (2009) como parte do Probabilistic Relevance Framework, é uma função de ranqueamento baseada em frequência de termos (TF) e frequência inversa de documentos (IDF), com normalização pelo comprimento do documento. Amplamente adotado como baseline em sistemas de recuperação de informação, o BM25 demonstra desempenho competitivo mesmo frente a métodos neurais em domínios com vocabulário técnico e especializado."),
    p("O PostgreSQL implementa busca de texto completo (Full-Text Search) nativa por meio do tipo tsvector e do índice GIN (Generalized Inverted Index), com suporte a ranqueamento ts_rank compatível com BM25. Essa funcionalidade permite utilizar o mesmo banco de dados tanto para busca vetorial (via pgvector) quanto para busca textual, viabilizando a comparação experimental proposta neste trabalho."),

    pageBreak(),

    // CAP 3 - METODOLOGIA
    titulo("3 Metodologia"),
    p("O trabalho está organizado em quatro fases sequenciais, descritas a seguir."),

    subtitulo("3.1 Fase 1: Coleta e Pré-processamento do Corpus"),
    p("O corpus documental é composto por duas fontes complementares:"),
    alínea("a", "Resoluções e portarias oficiais da UNESP, coletadas do sistema de legislação institucional (sistemas.unesp.br/legislacao-web), compreendendo o período de 2016 a 2026 e totalizando aproximadamente 937 documentos em formato HTML;"),
    alínea("b", "Documentos curriculares e regulamentares dos cursos de Bacharelado em Sistemas de Informação (BSI) e Bacharelado em Ciência da Computação (BCC) da Faculdade de Ciências de Bauru, obtidos nos portais dos respectivos cursos e compostos por 17 arquivos em formato PDF, cobrindo grades curriculares, regulamentos de estágio, normas de atividades complementares (AACC) e projetos político-pedagógicos."),
    p("A coleta foi realizada por meio de scripts de web scraping desenvolvidos em Python, utilizando as bibliotecas requests e BeautifulSoup para extração de conteúdo HTML, e pdfplumber para extração de texto de PDFs. Os textos extraídos passaram por etapas de limpeza (remoção de cabeçalhos e rodapés repetidos, normalização de codificação UTF-8 e eliminação de caracteres de controle) e foram armazenados em arquivos de texto plano com metadados de origem (documento, seção, data)."),

    subtitulo("3.2 Fase 2: Indexação — Chunking, Embeddings e pgvector"),
    p("Os textos pré-processados são segmentados em chunks pelo método de janela deslizante (sliding window), com tamanho de 350 palavras e sobreposição de 60 palavras. Esse parâmetro foi definido com base nas recomendações de Gao et al. (2023) para balancear granularidade e contexto preservado."),
    p("Os embeddings são gerados pelo modelo multilingual-e5-large (dimensão 1024), executado localmente via biblioteca sentence-transformers, sem custo de API. Os vetores resultantes são armazenados na tabela chunks do PostgreSQL com a extensão pgvector, com índice HNSW para busca eficiente por similaridade cosseno. A mesma tabela mantém uma coluna tsvector indexada por GIN para suporte ao baseline de busca textual."),

    subtitulo("3.3 Fase 3: Pipeline de Consulta RAG e Baseline FTS"),
    p("O pipeline de consulta RAG recebe a pergunta do usuário, gera seu embedding, realiza busca por similaridade no pgvector e fornece os K chunks mais similares como contexto a um LLM, que gera a resposta fundamentada nas fontes recuperadas. O baseline de Full-Text Search utiliza o mesmo mecanismo de recuperação, substituindo a busca vetorial pela busca textual nativa do PostgreSQL com ranqueamento BM25."),

    subtitulo("3.4 Fase 4: Avaliação Experimental"),
    p("A avaliação compara os dois sistemas com um conjunto de perguntas-teste elaboradas manualmente, com respostas de referência identificadas no corpus. As métricas utilizadas são:"),
    alínea("a", "Precision@K: proporção de documentos relevantes entre os K recuperados;"),
    alínea("b", "Recall@K: proporção de documentos relevantes recuperados entre todos os relevantes existentes;"),
    alínea("c", "Mean Reciprocal Rank (MRR): média do recíproco da posição do primeiro documento relevante no ranking."),

    pageBreak(),

    // CAP 4 - DESENVOLVIMENTO
    titulo("4 Desenvolvimento"),
    subtitulo("4.1 Arquitetura do Sistema"),
    p("O sistema foi desenvolvido em Python 3.11 e organizado em módulos independentes: coleta (scraper), extração e limpeza de texto (extract), segmentação (chunk), geração de embeddings (embeddings), persistência no banco de dados (db) e orquestração (pipeline). O banco de dados PostgreSQL 16 com a extensão pgvector é executado via Docker, garantindo reprodutibilidade do ambiente."),

    subtitulo("4.2 Coleta do Corpus"),
    p("O corpus de legislação institucional foi coletado do sistema sistemas.unesp.br/legislacao-web, que disponibiliza o texto integral das resoluções e portarias da UNESP. O scraper desenvolvido lê a árvore de documentos disponível no HTML da página inicial, extrai os metadados de cada resolução (número, ano, data) e realiza requisições GET individuais para cada documento, extraindo o texto do elemento div.painelTexto. Um intervalo de 1,2 segundos entre requisições foi adotado para respeitar os recursos do servidor. O processo foi registrado em um arquivo manifest.json para permitir retomada incremental."),
    p("Os documentos curriculares dos cursos de BSI e BCC foram obtidos nos portais dos respectivos departamentos e processados com a biblioteca pymupdf4llm, que converte PDFs para formato Markdown preservando a estrutura de tabelas — especialmente relevante para grades curriculares."),

    subtitulo("4.3 Protótipo Funcional"),
    p("Um protótipo completo do sistema foi implementado em Jupyter Notebooks, permitindo validação end-to-end do fluxo antes da migração para a arquitetura de produção. O protótipo utiliza ChromaDB como banco vetorial, o modelo paraphrase-multilingual-MiniLM-L12-v2 para embeddings e o LLaMA 3 (executado localmente via Ollama) como modelo gerador. A busca híbrida combina BM25 e busca vetorial utilizando Reciprocal Rank Fusion (RRF) para fusão dos rankings, com filtragem automática por curso (BSI ou BCC) quando identificado na pergunta do usuário."),
    p("Testes qualitativos com o protótipo demonstraram respostas corretas a perguntas como \"Quais são as disciplinas optativas do BSI?\", \"Qual é a carga horária mínima de estágio?\" e \"Como funciona o aproveitamento de atividades complementares?\", com as fontes devidamente citadas na resposta."),

    pageBreak(),

    // CRONOGRAMA
    titulo("Cronograma"),
    pSemRecuo("Tabela 1 — Cronograma de atividades", { bold: true }),
    br(),
    cronogramaTable,

    pageBreak(),

    // REFERÊNCIAS
    titulo("Referências"),
    pSemRecuo("GAO, Yunfan et al. Retrieval-augmented generation for large language models: a survey. arXiv:2312.10997, 2023. Disponível em: https://arxiv.org/abs/2312.10997. Acesso em: 2 jun. 2026."),
    br(),
    pSemRecuo("JI, Ziwei et al. Survey of hallucination in natural language generation. ACM Computing Surveys, v. 55, n. 12, p. 1–38, mar. 2023."),
    br(),
    pSemRecuo("LEWIS, Patrick et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. In: ADVANCES IN NEURAL INFORMATION PROCESSING SYSTEMS, 33., 2020. Anais [...]. [S. l.]: NeurIPS, 2020. p. 9459–9474."),
    br(),
    pSemRecuo("PGVECTOR. Open-source vector similarity search for PostgreSQL. Disponível em: https://github.com/pgvector/pgvector. Acesso em: 2 jun. 2026."),
    br(),
    pSemRecuo("REIMERS, Nils; GUREVYCH, Iryna. Sentence-BERT: sentence embeddings using siamese BERT-networks. In: CONFERENCE ON EMPIRICAL METHODS IN NATURAL LANGUAGE PROCESSING, 2019. Anais [...]. [S. l.]: ACL, 2019. p. 3982–3992."),
    br(),
    pSemRecuo("ROBERTSON, Stephen; ZARAGOZA, Hugo. The probabilistic relevance framework: BM25 and beyond. Foundations and Trends in Information Retrieval, v. 3, n. 4, p. 333–389, 2009."),
    br(),
    pSemRecuo("WANG, Liang et al. Text embeddings by weakly-supervised contrastive pre-training. arXiv:2212.03533, 2022. Disponível em: https://arxiv.org/abs/2212.03533. Acesso em: 2 jun. 2026."),
  ]
};

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT, size: SIZE } }
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: SIZE, bold: true, font: FONT },
        paragraph: { spacing: { before: 280, after: 280 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: SIZE, bold: true, font: FONT },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 }
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: SIZE, bold: true, font: FONT },
        paragraph: { spacing: { before: 140, after: 140 }, outlineLevel: 2 }
      },
    ]
  },
  sections: [preTextual, textual]
});

const outPath = "C:/Users/matheuslima/Downloads/TCC1_Matheus_Rafael_preliminar.docx";
Packer.toBuffer(doc).then(buf => {
  writeFileSync(outPath, buf);
  console.log("OK:", outPath);
}).catch(e => { console.error("ERRO:", e.message); process.exit(1); });
