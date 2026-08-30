interface CardProps {
  title?: string
  subtitle?: string
  children: React.ReactNode
  className?: string
}

function Card({ title, subtitle, children, className = '' }: CardProps) {
  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
      {(title || subtitle) && (
        <div className="mb-4">
          {title && <h3 className="text-lg font-semibold text-gray-800">{title}</h3>}
          {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  )
}

export default Card
