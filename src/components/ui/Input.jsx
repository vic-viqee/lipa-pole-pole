import './Input.css'

export default function Input({
  label,
  error,
  hint,
  type = 'text',
  id,
  className = '',
  ...props
}) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')
  
  return (
    <div className={`field ${className}`}>
      {label && (
        <label htmlFor={inputId} className="field-label">
          {label}
        </label>
      )}
      <input
        id={inputId}
        type={type}
        className={`field-input ${error ? 'field-input-error' : ''}`}
        {...props}
      />
      {hint && !error && <p className="field-hint">{hint}</p>}
      {error && <p className="field-error">{error}</p>}
    </div>
  )
}

export function Textarea({
  label,
  error,
  hint,
  id,
  className = '',
  rows = 4,
  ...props
}) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')
  
  return (
    <div className={`field ${className}`}>
      {label && (
        <label htmlFor={inputId} className="field-label">
          {label}
        </label>
      )}
      <textarea
        id={inputId}
        rows={rows}
        className={`field-input field-textarea ${error ? 'field-input-error' : ''}`}
        {...props}
      />
      {hint && !error && <p className="field-hint">{hint}</p>}
      {error && <p className="field-error">{error}</p>}
    </div>
  )
}
