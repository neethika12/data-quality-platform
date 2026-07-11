export default function Button({ children, onClick, variant = 'primary', disabled = false, className = '' }) {
  const variants = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
  }
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${variants[variant]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
    >
      {children}
    </button>
  )
}
