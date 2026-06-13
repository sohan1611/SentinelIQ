import * as React from "react"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "link" | "destructive";
  isLoading?: boolean;
  loadingText?: string;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "primary", isLoading, loadingText, children, disabled, ...props }, ref) => {
    // using custom transition duration utilities from tailwind config
    const baseStyles = "inline-flex items-center justify-center text-[14px] font-sans transition-colors duration-fast ease-out active:duration-instant disabled:pointer-events-none min-h-[44px] md:min-h-0";
    
    const shapeStyles = variant === "link" ? "" : "rounded-btn px-[16px] py-[12px] md:px-[20px] md:py-[10px] font-semibold";
    
    const variants = {
      primary: "bg-navy text-white hover:bg-[#142848] active:bg-[#0E1E38] disabled:bg-[#C8C5BF] disabled:text-white",
      secondary: "border border-navy text-navy bg-transparent hover:bg-[#F0EDE8] active:bg-[#F0EDE8] disabled:border-[#C8C5BF] disabled:text-[#C8C5BF]",
      link: "text-navy hover:underline active:underline disabled:text-[#C8C5BF] disabled:no-underline duration-instant",
      destructive: "bg-[#FAE8E8] text-[#B03028] hover:bg-[#F5D5D5] active:bg-[#F5D5D5] disabled:bg-[#C8C5BF] disabled:text-white",
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${shapeStyles} ${variants[variant]} ${className} ${isLoading ? 'opacity-75' : ''}`}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (loadingText ?? "...") : children}
      </button>
    )
  }
)
Button.displayName = "Button"

export { Button }
