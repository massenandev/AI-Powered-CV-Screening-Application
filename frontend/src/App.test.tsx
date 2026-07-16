import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, vi, test, expect } from 'vitest'
import { App } from './App'
beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string, init?: RequestInit) => Promise.resolve({
    ok: true,
    json: async () => {
      if (url.endsWith('/conversations') && init?.method !== 'POST') return { conversations: [] }
      if (url.endsWith('/conversations')) return { id: '00000000-0000-0000-0000-000000000001' }
      return { answer: 'Python experience found.', sources: [] }
    },
  })))
})
afterEach(cleanup)
test('shows grounded chat welcome and chat history', async () => {
  render(<App />)
  expect(screen.getByText('Find the signal in every résumé.')).toBeInTheDocument()
  expect(screen.getByLabelText('Ask about the candidates')).toBeInTheDocument()
  expect(screen.getByRole('complementary', { name: 'Chat history' })).toBeInTheDocument()
  expect(screen.queryByText('New chat')).not.toBeInTheDocument()
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1))
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/conversations'), expect.objectContaining({ headers: expect.any(Object) }))
})

test('shows chat navigation only after a chat is started', async () => {
  render(<App />)
  await waitFor(() => expect(fetch).toHaveBeenCalled())
  fireEvent.change(screen.getByLabelText('Ask about the candidates'), { target: { value: 'Who knows Python?' } })
  fireEvent.click(screen.getByLabelText('Send question'))
  expect(await screen.findByRole('button', { name: /New chat/ })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /Back to home/ })).toBeInTheDocument()
})

test('previews a sourced CV immediately and offers a download', async () => {
  vi.mocked(fetch).mockImplementation((url: string | URL | Request, init?: RequestInit) => Promise.resolve({
    ok: true,
    json: async () => {
      const path = url.toString()
      if (path.endsWith('/conversations') && init?.method !== 'POST') return { conversations: [] }
      if (path.endsWith('/conversations')) return { id: '00000000-0000-0000-0000-000000000001' }
      return { answer: 'Candidate found.', sources: [{ document_id: 'doc-1', candidate_name: 'Ada Lovelace', page: 2, excerpt: 'Relevant experience' }] }
    },
  } as Response))
  render(<App />)
  fireEvent.change(screen.getByLabelText('Ask about the candidates'), { target: { value: 'Show Ada' } })
  fireEvent.click(screen.getByLabelText('Send question'))
  fireEvent.click(await screen.findByRole('button', { name: 'Preview CV' }))
  expect(screen.getByTitle('Ada Lovelace CV')).toHaveAttribute('src', expect.stringContaining('/documents/doc-1/file#page=2'))
  expect(screen.getByRole('link', { name: 'Download CV' })).toHaveAttribute('href', expect.stringContaining('/documents/doc-1/file?download=true'))
})
