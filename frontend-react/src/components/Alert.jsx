import { AlertCircle, AlertTriangle, Info, CheckCircle } from 'lucide-react'

export default function Alert({ type = 'info', title, message, onDismiss }) {
  const icons = {
    critical: <AlertCircle className="text-red-600" size={20} />,
    warning: <AlertTriangle className="text-yellow-600" size={20} />,
    info: <Info className="text-blue-600" size={20} />,
    success: <CheckCircle className="text-green-600" size={20} />,
  }

  const classes = {
    critical: 'alert-critical',
    warning: 'alert-warning',
    info: 'alert-info',
    success: 'bg-green-50 dark:bg-green-900/20 border-l-4 border-green-600 p-4 rounded',
  }

  return (
    <div className={classes[type]}>
      <div className="flex items-start gap-3">
        {icons[type]}
        <div className="flex-1">
          {title && <p className="font-semibold">{title}</p>}
          <p className="text-sm mt-1">{message}</p>
        </div>
        {onDismiss && (
          <button onClick={onDismiss} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        )}
      </div>
    </div>
  )
}
