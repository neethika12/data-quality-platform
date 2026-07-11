import { AlertCircle } from 'lucide-react'

export default function ErrorDisplay({ message, retry }) {
  return (
    <div className="alert-critical">
      <div className="flex items-start gap-3">
        <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
        <div className="flex-1">
          <p className="font-semibold text-red-800 dark:text-red-300">Error</p>
          <p className="text-red-700 dark:text-red-400 text-sm mt-1">{message}</p>
          {retry && (
            <button
              onClick={retry}
              className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
