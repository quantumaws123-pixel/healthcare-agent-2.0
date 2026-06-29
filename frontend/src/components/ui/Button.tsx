import React from "react";
import { motion } from "framer-motion";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-xl font-medium text-sm transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-40 select-none cursor-pointer",
  {
    variants: {
      variant: {
        primary:   "bg-primary-500 text-white hover:bg-primary-600 shadow-sm hover:shadow-md",
        secondary: "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 shadow-sm",
        ghost:     "bg-transparent text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white",
        danger:    "bg-danger-500 text-white hover:bg-danger-600 shadow-sm",
        success:   "bg-success-500 text-white hover:bg-success-600 shadow-sm",
        glass:     "bg-white/60 dark:bg-white/10 backdrop-blur-md border border-white/40 dark:border-white/10 text-gray-700 dark:text-white hover:bg-white/80 shadow-sm",
      },
      size: {
        xs:       "h-7 px-3 text-xs rounded-lg",
        sm:       "h-8 px-3.5 text-xs",
        md:       "h-9 px-4",
        lg:       "h-11 px-6 text-base",
        xl:       "h-12 px-8 text-base rounded-2xl",
        icon:     "h-9 w-9 p-0",
        "icon-sm":"h-8 w-8 p-0 rounded-lg",
        "icon-lg":"h-11 w-11 p-0 rounded-xl",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  }
);

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, leftIcon, rightIcon, children, disabled, ...props }, ref) => (
    <motion.button
      ref={ref}
      whileTap={{ scale: 0.97 }}
      transition={{ type: "spring", stiffness: 500, damping: 35 }}
      className={cn(buttonVariants({ variant, size, className }))}
      disabled={disabled || loading}
      {...(props as any)}
    >
      {loading ? <Loader2 size={15} className="animate-spin" aria-hidden /> : leftIcon}
      {children}
      {!loading && rightIcon}
    </motion.button>
  )
);
Button.displayName = "Button";
