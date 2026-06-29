import React from "react";
import { motion } from "framer-motion";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const cardVariants = cva("relative rounded-2xl overflow-hidden transition-all duration-200", {
  variants: {
    variant: {
      default:  "bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-card",
      elevated: "bg-white dark:bg-gray-900 shadow-float",
      glass:    "bg-white/70 dark:bg-gray-900/70 backdrop-blur-xl border border-white/40 dark:border-gray-700/40 shadow-panel",
      flat:     "bg-gray-50 dark:bg-gray-800",
      outline:  "bg-transparent border border-gray-200 dark:border-gray-700",
    },
    hoverable: {
      true:  "cursor-pointer hover:shadow-float hover:-translate-y-0.5 active:translate-y-0",
      false: "",
    },
    padding: {
      none: "",
      sm:   "p-4",
      md:   "p-5",
      lg:   "p-6",
      xl:   "p-8",
    },
  },
  defaultVariants: { variant: "default", hoverable: false, padding: "md" },
});

export interface CardProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof cardVariants> {
  asMotion?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, hoverable, padding, asMotion, children, ...props }, ref) => {
    const classes = cn(cardVariants({ variant, hoverable, padding, className }));
    if (asMotion) {
      return (
        <motion.div ref={ref} className={classes}
          whileHover={hoverable ? { y: -2 } : undefined}
          whileTap={hoverable ? { scale: 0.995 } : undefined}
          transition={{ type: "spring", stiffness: 400, damping: 30 }}
          {...(props as any)}>{children}</motion.div>
      );
    }
    return <div ref={ref} className={classes} {...props}>{children}</div>;
  }
);
Card.displayName = "Card";

export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex items-start justify-between gap-4 mb-4", className)} {...props}>{children}</div>;
}
export function CardTitle({ className, children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-base font-semibold text-gray-900 dark:text-white leading-tight", className)} {...props}>{children}</h3>;
}
export function CardDescription({ className, children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-sm text-gray-500 dark:text-gray-400 mt-0.5", className)} {...props}>{children}</p>;
}
export function CardContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("", className)} {...props}>{children}</div>;
}
export function CardFooter({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex items-center gap-3 mt-4 pt-4 border-t border-gray-100 dark:border-gray-800", className)} {...props}>{children}</div>;
}
