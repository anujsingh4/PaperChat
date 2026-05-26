import { useState, useEffect } from "react";
import FileUpload from "./components/FileUpload";
import DocumentList from "./components/DocumentList";
import MessageList from "./components/MessageList";
import ChatInput from "./components/ChatInput";
import { fetchDocuments, streamChat } from "./api";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [streaming, setStreaming] = useState(false);
  const [activeDocIds, setActiveDocIds] = useState([]);

  const loadDocuments = async () => {
    const data = await fetchDocuments();
    setDocuments(data.documents);
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  // When a new file is uploaded, add its doc_id to activeDocIds
  const handleUploadComplete = (docId) => {
    setActiveDocIds((prev) => {
      if (prev.includes(docId)) return prev; // already tracked
      return [...prev, docId];
    });
    loadDocuments();
  };

  const handleSend = (question) => {
    console.log("DEBUG activeDocIds:", activeDocIds); //debug line
    // Add user message
    setMessages((prev) => [...prev, { role: "user", content: question }]);

    // Add empty assistant message that we'll fill with streamed tokens
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", sources: [] },
    ]);
    setStreaming(true);

    streamChat(
      question,
      activeDocIds, // only search docs uploaded this session

      // onToken — append each token to the last message
      (token) => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].content += token;
          return updated;
        });
      },

      // onSources — attach citations to the last message
      (sources) => {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].sources = sources;
          return updated;
        });
      },

      // onDone — re-enable input
      () => setStreaming(false),
    );
  };

  const handleNewChat = () => {
    (setMessages([]), setActiveDocIds([])); // clear active docs on new conversation
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-72 bg-white border-r border-gray-200 flex flex-col p-4">
        <div className="flex items-center gap-2 mb-4">
          <img
            src="public/logo.png"
            alt="PaperChat"
            className="h-8 w-8 rounded-lg object-cover"
          />
          <h1 className="text-lg font-semibold text-gray-800">PaperChat</h1>
        </div>
        <FileUpload onUploadComplete={handleUploadComplete} />
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Documents
          </span>
          <span className="text-xs text-gray-400">
            {documents.length} indexed
          </span>
        </div>
        <DocumentList
          documents={documents}
          activeDocIds={activeDocIds}
          onDelete={loadDocuments}
        />
        <button
          onClick={handleNewChat}
          className="mt-auto text-sm text-gray-500 hover:text-gray-700 py-2 border border-gray-200 rounded-lg hover:bg-gray-50"
        >
          + New conversation
        </button>
      </div>

      {/* Main chat panel */}
      <div className="flex-1 flex flex-col">
        <MessageList messages={messages} />
        <ChatInput onSend={handleSend} disabled={streaming} />
      </div>
    </div>
  );
}
