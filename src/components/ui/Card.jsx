import './Card.css'

export default function Card({
  children,
  variant = 'default',
  padding = 'md',
  className = '',
  ...props
}) {
  const classes = [
    'card',
    `card-${variant}`,
    `card-padding-${padding}`,
    className
  ].filter(Boolean).join(' ')

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  )
}

export function CardHeader({ children, className = '' }) {
  return (
    <div className={`card-header ${className}`}>
      {children}
    </div>
  )
}

export function CardTitle({ children, className = '' }) {
  return (
    <h3 className={`card-title ${className}`}>
      {children}
    </h3>
  )
}

export function CardDescription({ children, className = '' }) {
  return (
    <p className={`card-description ${className}`}>
      {children}
    </p>
  )
}

export function CardContent({ children, className = '' }) {
  return (
    <div className={`card-content ${className}`}>
      {children}
    </div>
  )
}

export function CardFooter({ children, className = '' }) {
  return (
    <div className={`card-footer ${className}`}>
      {children}
    </div>
  )
}
