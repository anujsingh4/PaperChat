// frontend/src/api.js
// Single place where API base URL lives
// When we deploy, we only change this one line
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

export const uploadFile = async (file) => {
  const formData = new FormData()
  formData.append("file", file)
  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData
  })
  if (!res.ok) throw new Error(await res.text())
  const data = await res.json()
  console.log("DEBUG upload API response:", data) // add this
  return data
}

export const fetchDocuments = async () => {
  const res = await fetch(`${API_BASE}/documents`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const deleteDocument = async (docId) => {
  const res = await fetch(`${API_BASE}/document/${docId}`, { method: "DELETE" })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const streamChat = (question, docIds, onToken, onSources, onDone) => {
  fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, doc_ids: docIds })
  }).then(async res => {
    const reader = res.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) { onDone(); break }

      const text = decoder.decode(value, { stream: true })

      // each SSE line looks like: data: {"token": "hello"}
      for (const line of text.split("\n")) {
        const trimmed = line.trim()
        if (!trimmed.startsWith("data:")) continue
        const raw = trimmed.slice(5).trim()  // remove "data:" prefix
        if (raw === "[DONE]") { onDone(); return }
        try {
          const parsed = JSON.parse(raw)
          if (parsed.token) onToken(parsed.token)
          if (parsed.sources) onSources(parsed.sources)
        } catch {}
      }
    }
  })
}