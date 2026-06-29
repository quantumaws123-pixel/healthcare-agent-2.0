import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn, getInitials } from "@/lib/utils";

const avatarVariants = cva("relative inline-flex items-center justify-center rounded-full shrink-0 font-semibold select-none overflow-hidden", {
  variants: {
    size: {
      xs:   "w-6  h-6  text-[9px]",
      sm:   "w-8  h-8  text-xs",
      md:   "w-10 h-10 text-sm",
      lg:   "w-12 h-12 text-base",
      xl:   "w-16 h-16 text-lg",
      "2xl":"w-20 h-20 text-xl",
    },
  },
  defaultVariants: { size: "md" },
});

const AVATAR_COLORS = [
  "bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300",
  "bg-success-100 dark:bg-green-900/40 text-success-700 dark:text-green-300",
  "bg-warning-100 dark:bg-yellow-900/40 text-warning-600 dark:text-yellow-300",
  "bg-danger-100 dark:bg-red-900/40 text-danger-600 dark:text-red-300",
  "bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300",
  "bg-pink-100 dark:bg-pink-900/40 text-pink-700 dark:text-pink-300",
  "bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300",
];

function colorFromName(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

const STATUS_COLORS = { online: "bg-success-500", away: "bg-warning-500", busy: "bg-danger-500", offline: "bg-gray-400" };

export interface AvatarProps extends VariantProps<typeof avatarVariants> {
  name?: string; src?: string; alt?: string; className?: string;
  status?: "online" | "away" | "busy" | "offline";
}

export function Avatar({ name = "", src, alt, size, className, status }: AvatarProps) {
  const initials = getInitials(name || "?");
  const color = colorFromName(name);
  return (
    <div className="relative inline-flex shrink-0">
      <div className={cn(avatarVariants({ size, className }), !src && color)}>
        {src ? <img src={src} alt={alt ?? name} className="w-full h-full object-cover" /> : <span aria-label={name}>{initials}</span>}
      </div>
      {status && (
        <span className={cn("absolute bottom-0 right-0 rounded-full border-2 border-white dark:border-gray-900", STATUS_COLORS[status], size === "xs" || size === "sm" ? "w-2 h-2" : "w-3 h-3")} />
      )}
    </div>
  );
}
