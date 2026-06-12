import * as React from "react"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "link" | "destructive";
  isLoading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "primary", isLoading, children, disabled, ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center text-[14px] font-sans transition-colors focus-visible:outline-none disabled:pointer-events-none min-h-[44px] md:min-h-0";
    
    const shapeStyles = variant === "link" ? "" : "rounded-btn px-[16px] py-[12px] md:px-[20px] md:py-[10px] font-semibold";
    
    const variants = {
      primary: "bg-navy text-white hover:bg-[#142848] active:bg-[#142848] disabled:bg-[#C8C5BF] disabled:text-white",
      secondary: "border border-navy text-navy bg-transparent hover:bg-[#F0EDE8] active:bg-[#F0EDE8] disabled:border-[#C8C5BF] disabled:text-[#C8C5BF]",
      link: "text-navy hover:underline active:underline disabled:text-[#C8C5BF] disabled:no-underline",
      destructive: "bg-tint-high text-risk-high hover:bg-risk-high hover:text-white active:bg-risk-high active:text-white disabled:bg-[#C8C5BF] disabled:text-white font-semibold",
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${shapeStyles} ${variants[variant]} ${className}`}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? "..." : children}
      </button>
    )
  }
)
Button.displayName = "Button"

export { Button }
