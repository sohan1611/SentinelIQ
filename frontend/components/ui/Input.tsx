import * as React from "react"

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", label, error, hint, id, ...props }, ref) => {
    const inputId = id ?? props.name
    const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined

    return (
      <div className="flex flex-col w-full">
        {label && (
          <label htmlFor={inputId} className="font-sans text-sm font-semibold text-text-primary mb-[6px]">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={describedBy}
          className={`h-[44px] px-3 font-sans text-base text-text-primary placeholder:text-text-muted bg-surface border rounded-btn outline-none transition-colors duration-fast ease-out disabled:bg-canvas disabled:text-text-muted ${
            error ? "border-risk-high" : "border-border focus:border-navy"
          } ${className}`}
          {...props}
        />
        {error ? (
          <span id={`${inputId}-error`} className="font-sans text-sm text-risk-high mt-[4px]">
            {error}
          </span>
        ) : hint ? (
          <span id={`${inputId}-hint`} className="font-sans text-sm text-text-secondary mt-[4px]">
            {hint}
          </span>
        ) : null}
      </div>
    )
  }
)
Input.displayName = "Input"

export { Input }
