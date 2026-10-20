import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

const API = 'http://localhost:8000'

function SourceCard({ source }) {
  const [open, setOpen] = useState(false)
  const name = source.source
    .replace('resolucao_', 'Resolução ')
    .replace('.txt', '')
    .replace(/_/g, '/')
  return (
    <div className="source-card" onClick={() => setOpen(!open)}>
      <div className="source-header">
        <span className="source-name">{name}</span>
        <span className="source-score">score: {source.score.toFixed(4)}</span>
        <span className="toggle">{open ? '▲' : '▼'}</span>
      </div>
      {open && <p className="source-content">{source.content}</p>}
    </div>
  )
}

function Message({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="msg msg-user">
        <div className="bubble bubble-user">{msg.content}</div>
      </div>
    )
  }
  if (msg.loading) {
    return (
      <div className="msg msg-bot">
        <div className="avatar">U</div>
        <div className="bubble bubble-bot loading">Consultando documentos...</div>
      </div>
    )
  }
  return (
    <div className="msg msg-bot">
      <div className="avatar">U</div>
      <div className="bubble-wrapper">
        <div className="bubble bubble-bot">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
        </div>
        {msg.sources?.length > 0 && (
          <div className="sources">
            <p className="sources-title">Fontes consultadas ({msg.sources.length})</p>
            {msg.sources.map((s, i) => <SourceCard key={i} source={s} />)}
          </div>
        )}
        {msg.latency && (
          <p className="latency">Tempo de resposta: {msg.latency} ms</p>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: 'bot',
      content: 'Olá! Sou o assistente de documentos regulatórios da UNESP Bauru. Faça uma pergunta sobre resoluções, regimentos ou normas institucionais.',
      sources: [],
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [method, setMethod] = useState('hybrid')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send() {
    const query = input.trim()
    if (!query || loading) return
    setInput('')
    setLoading(true)

    setMessages(prev => [
      ...prev,
      { role: 'user', content: query },
      { role: 'bot', loading: true },
    ])

    try {
      const res = await fetch(`${API}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, k: 5, method }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Erro desconhecido')
      }
      const data = await res.json()
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'bot', content: data.answer, sources: data.sources, latency: data.latency_ms },
      ])
    } catch (e) {
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'bot', content: `Erro ao conectar ao servidor: ${e.message}`, sources: [] },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <h1>UNESP Bauru — Consulta de Regulamentos</h1>
          <p>Perguntas sobre resoluções, regimentos e normas institucionais</p>
        </div>
      </header>

      <main className="chat">
        {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        <div ref={bottomRef} />
      </main>

      <footer className="input-area">
        <div className="input-row">
          <select
            className="method-select"
            value={method}
            onChange={e => setMethod(e.target.value)}
            title="Método de busca"
          >
            <option value="hybrid">Híbrido (RRF)</option>
            <option value="vector">Vetorial</option>
            <option value="bm25">BM25</option>
            <option value="fts">FTS (PostgreSQL)</option>
          </select>
          <textarea
            className="input-box"
            rows={2}
            placeholder="Digite sua dúvida sobre regulamentos da UNESP..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
          />
          <button className="send-btn" onClick={send} disabled={loading || !input.trim()}>
            {loading ? '...' : 'Enviar'}
          </button>
        </div>
        <p className="hint">Enter para enviar · Shift+Enter para nova linha</p>
      </footer>
    </div>
  )
}
