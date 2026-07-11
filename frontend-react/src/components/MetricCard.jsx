export default function MetricCard({ label, value, icon, gradient = 'gradient-primary', subtitle = '' }) {
  return (
    <div className={`metric-card bg-${gradient}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm opacity-90 font-medium">{label}</p>
          <p className="text-3xl font-bold mt-2">{value}</p>
          {subtitle && <p className="text-xs opacity-75 mt-1">{subtitle}</p>}
        </div>
        {icon && <span className="text-4xl">{icon}</span>}
      </div>
    </div>
  )
}
