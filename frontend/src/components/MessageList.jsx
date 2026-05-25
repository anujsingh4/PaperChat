import ReactMarkdown from "react-markdown"
import { useEffect, useRef } from "react"

export default function MessageList({ messages }) {
  const bottomRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
        Upload a document and ask a question
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-4">
      {messages.map((msg, i) => (
        <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
          <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
            msg.role === "user"
              ? "bg-blue-600 text-white"
              : "bg-white border border-gray-200 text-gray-800"
          }`}>
            {/* Message content */}
            <div className="text-sm prose prose-sm max-w-none">
            <ReactMarkdown>
              {msg.content || "..."}
            </ReactMarkdown>
            </div>

            {/* Citations */}
            {msg.sources && msg.sources.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-100 flex flex-wrap gap-1">
                {msg.sources.map((s, j) => (
                  <span key={j} className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">
                    {s.filename} · p.{s.page}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}