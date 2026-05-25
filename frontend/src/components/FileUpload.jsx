import { useDropzone } from "react-dropzone"
import { uploadFile } from "../api"
import { useState } from "react"

export default function FileUpload({ onUploadComplete }) {
  const [status, setStatus] = useState("")
  const [loading, setLoading] = useState(false)

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0]
    if (!file) return

    setLoading(true)
    setStatus(`Uploading ${file.name}...`)

    try {
      const result = await uploadFile(file)
      console.log("DEBUG upload result:", result) //debug line
      setStatus(result.skipped
        ? `'${result.filename}' already indexed`
        : `'${result.filename}' indexed — ${result.chunks} chunks`)
      onUploadComplete(result.doc_id) // pass doc_id back to App
    } catch (err) {
      setStatus(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"] },
    maxFiles: 1,
    disabled: loading
  })

  return (
    <div className="mb-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors
          ${isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-blue-400"}
          ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        <input {...getInputProps()} />
        <p className="text-sm text-gray-500">
          {loading ? "Processing..." : isDragActive ? "Drop it here..." : "Drop PDF or DOCX here, or click to select"}
        </p>
      </div>
      {status && (
        <p className="mt-2 text-xs text-gray-600">{status}</p>
      )}
    </div>
  )
}