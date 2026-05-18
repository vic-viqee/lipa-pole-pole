import './Progress.css'

export default function Progress({
  value,
  max = 100,
  variant = 'default',
  size = 'md',
  showLabel = false,
  label,
  className = '',
}) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)
  
  const classes = [
    'progress',
    `progress-${variant}`,
    `progress-${size}`,
    className
  ].filter(Boolean).join(' ')

  return (
    <div className={classes}>
      {(showLabel || label) && (
        <div className="progress-label-row">
          {label && <span className="progress-label">{label}</span>}
          {showLabel && <span className="progress-value">{Math.round(percentage)}%</span>}
        </div>
      )}
      <div className="progress-track">
        <div 
          className="progress-fill" 
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  )
}
