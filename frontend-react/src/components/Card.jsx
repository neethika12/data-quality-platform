export default function Card({ children, className = '', gradient = false, ...rest }) {
  const baseClass = 'rounded-xl shadow-md border border-gray-200 dark:border-gray-800 p-6'
  const gradientClass = gradient ? 'text-white' : 'bg-white dark:bg-gray-900'
  return <div className={`${baseClass} ${gradientClass} ${className}`} {...rest}>{children}</div>
}
