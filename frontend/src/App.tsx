import { FormEvent, useEffect, useRef, useState } from 'react'
import { ask, Conversation, createConversation, documentDownloadUrl, documentPreviewUrl, getMessages, listConversations, Message, Source } from './api'

const examples = ['Who has strong Python and PostgreSQL experience?', 'Compare the machine learning candidates.', 'Which candidates speak French?']

export function App() {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isHome, setIsHome] = useState(true)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [preview, setPreview] = useState<Source | null>(null)
  const input = useRef<HTMLTextAreaElement>(null)
  const pendingRequest = useRef<AbortController | null>(null)

  useEffect(() => {
    async function initialize() {
      try {
        const history = await listConversations()
        setConversations(history.conversations)
      } catch (e) { setError(e instanceof Error ? e.message : 'Unable to connect') }
    }
    initialize()
  }, [])

  useEffect(() => () => pendingRequest.current?.abort(), [])

  async function submit(event?: FormEvent, suggested?: string) {
    event?.preventDefault()
    const text = (suggested ?? question).trim()
    if (!text || busy) return
    setQuestion(''); setError(''); setBusy(true)
    const controller = new AbortController()
    pendingRequest.current = controller
    try {
      const activeId = conversationId ?? (await createConversation()).id
      const now = new Date().toISOString()
      setIsHome(false)
      setConversationId(activeId)
      setConversations(current => current.some(chat => chat.id === activeId)
        ? current.map(chat => chat.id === activeId ? { ...chat, title: chat.title === 'New chat' ? text : chat.title, updated_at: now } : chat)
        : [{ id: activeId, title: text, created_at: now, updated_at: now }, ...current])
      setMessages(current => [...current, { role: 'user', content: text, sources: [] }])
      const result = await ask(activeId, text, controller.signal)
      setMessages(current => [...current, { role: 'assistant', content: result.answer, sources: result.sources }])
    } catch (e) {
      if (!controller.signal.aborted) {
        setError(e instanceof Error ? e.message : 'The request failed'); setQuestion(text)
      }
    } finally {
      if (pendingRequest.current === controller) pendingRequest.current = null
      setBusy(false); input.current?.focus()
    }
  }

  function stopThinking() {
    pendingRequest.current?.abort()
  }

  function startNewChat() {
    if (busy) return
    setError(''); setPreview(null)
    setIsHome(false); setConversationId(null); setMessages([]); setQuestion('')
    input.current?.focus()
  }

  function backToHome() {
    if (busy) return
    setIsHome(true); setConversationId(null); setMessages([]); setQuestion(''); setError(''); setPreview(null)
    input.current?.focus()
  }

  async function openConversation(id: string) {
    if (busy || id === conversationId) return
    setError(''); setPreview(null)
    try {
      const saved = await getMessages(id)
      setIsHome(false); setConversationId(id); setMessages(saved.messages); setQuestion('')
      input.current?.focus()
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to open this chat') }
  }

  return <div className="shell">
    <header><div className="mark">CV</div><div><h1>CV Compass</h1><p>Evidence-grounded candidate search</p></div><div className="header-actions"><span className="status">30 fictional profiles</span>{!isHome && <><button className="home-button" onClick={backToHome} disabled={busy}>← Back to home</button><button className="new-chat" onClick={startNewChat} disabled={busy}>＋ New chat</button></>}</div></header>
    <div className="workspace">
    <aside className="history" aria-label="Chat history"><h2>Previous chats</h2><nav>{conversations.map(chat => <button key={chat.id} className={chat.id === conversationId ? 'active' : ''} onClick={() => openConversation(chat.id)} disabled={busy}><span>{chat.title}</span><time>{new Date(chat.updated_at).toLocaleDateString()}</time></button>)}</nav></aside>
    <main>
      {messages.length === 0 ? <section className="welcome"><p className="eyebrow">RECRUITING COPILOT</p><h2>Find the signal in every résumé.</h2><p>Ask factual questions or compare experience. Every answer stays grounded in the indexed CVs and links back to its evidence.</p><div className="examples">{examples.map(item => <button key={item} onClick={() => submit(undefined, item)}>{item}<span>→</span></button>)}</div></section> :
        <section className="messages" aria-live="polite">{messages.map((message, index) => <article key={message.id ?? index} className={`message ${message.role}`}><div className="avatar">{message.role === 'user' ? 'You' : 'AI'}</div><div><p>{message.content}</p>{message.sources.length > 0 && <div className="sources"><strong>Sources</strong>{message.sources.map((source, i) => <details key={`${source.document_id}-${source.page}-${i}`}><summary>{source.candidate_name} · page {source.page}</summary><p>{source.excerpt}</p><button className="preview-button" onClick={() => setPreview(source)}>Preview CV</button></details>)}</div>}</div></article>)}{busy && <div className="thinking"><span>Searching the CV collection…</span><button onClick={stopThinking}>Stop</button></div>}</section>}
    </main>
    </div>
    <footer><form onSubmit={submit}><label htmlFor="question" className="sr-only">Ask about the candidates</label><textarea ref={input} id="question" value={question} maxLength={2000} placeholder="Ask about skills, experience, education, or languages…" onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() } }} /><button disabled={busy || !question.trim()} aria-label="Send question">↑</button></form>{error && <p className="error" role="alert">{error} <button onClick={() => submit()}>Retry</button></p>}<p className="notice">AI-assisted screening can be incomplete. Keep a human in every hiring decision.</p></footer>
    {preview && <div className="preview-backdrop" role="dialog" aria-modal="true" aria-labelledby="preview-title" onMouseDown={e => { if (e.target === e.currentTarget) setPreview(null) }}><section className="preview-modal"><div className="preview-header"><div><h2 id="preview-title">{preview.candidate_name}</h2><p>CV preview · page {preview.page}</p></div><a className="download-button" href={documentDownloadUrl(preview.document_id)}>Download CV</a><button onClick={() => setPreview(null)} aria-label="Close CV preview">×</button></div><iframe title={`${preview.candidate_name} CV`} src={documentPreviewUrl(preview.document_id, preview.page)} /></section></div>}
  </div>
}
