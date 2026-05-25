import { deleteDocument } from "../api"

export default function DocumentList({ documents, activeDocIds, onDelete }) {
  const handleDelete = async (docId, filename) => {
    if (!confirm(`Delete '${filename}'?`)) return
    await deleteDocument(docId)
    onDelete()
  }

  if (documents.length === 0) {
    return <p className="text-xs text-gray-400 text-center mt-4">No documents indexed yet</p>
  }

  return (
    <div className="flex flex-col gap-2 overflow-y-auto">
      {documents.map(doc => (
        <div
          key={doc.doc_id}
          className={`flex items-center justify-between rounded-lg px-3 py-2 border
            ${activeDocIds.includes(doc.doc_id)
              ? "bg-blue-50 border-blue-200"
              : "bg-gray-50 border-transparent"}`}
        >
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {/* Green dot = active in this session, gray = old */}
            <div className={`w-2 h-2 rounded-full flex-shrink-0
              ${activeDocIds.includes(doc.doc_id) ? "bg-green-500" : "bg-gray-300"}`}
            />
            <span className="text-xs text-gray-700 truncate">{doc.filename}</span>
          </div>
          <button
            onClick={() => handleDelete(doc.doc_id, doc.filename)}
            className="ml-2 text-red-400 hover:text-red-600 text-xs font-medium flex-shrink-0"
          >
            Delete
          </button>
        </div>
      ))}
    </div>
  )
}