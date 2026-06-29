/**
 * Framer Motion animation presets — Spatial UI / VisionOS inspired.
 * Import these wherever you need consistent motion behaviour.
 */

import type { Variants, Transition } from "framer-motion";

/* ─── Transitions ──────────────────────────────────────────────────────── */

export const springSnappy: Transition = {
  type: "spring",
  stiffness: 500,
  damping: 35,
  mass: 0.8,
};

export const springGentle: Transition = {
  type: "spring",
  stiffness: 300,
  damping: 30,
  mass: 1,
};

export const springBouncy: Transition = {
  type: "spring",
  stiffness: 400,
  damping: 20,
  mass: 0.7,
};

export const easeOut: Transition = {
  type: "tween",
  ease: [0.16, 1, 0.3, 1],
  duration: 0.35,
};

export const easeOutFast: Transition = {
  type: "tween",
  ease: [0.16, 1, 0.3, 1],
  duration: 0.2,
};

export const easeSpatial: Transition = {
  type: "tween",
  ease: [0.4, 0, 0.2, 1],
  duration: 0.4,
};

/* ─── Fade variants ────────────────────────────────────────────────────── */

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: easeOut },
  exit: { opacity: 0, transition: easeOutFast },
};

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: easeOut },
  exit: { opacity: 0, y: 8, transition: easeOutFast },
};

export const fadeInDown: Variants = {
  hidden: { opacity: 0, y: -12 },
  visible: { opacity: 1, y: 0, transition: easeOut },
  exit: { opacity: 0, y: -8, transition: easeOutFast },
};

export const fadeInScale: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1, transition: springSnappy },
  exit: { opacity: 0, scale: 0.97, transition: easeOutFast },
};

/* ─── Panel / floating layer variants ─────────────────────────────────── */

export const floatIn: Variants = {
  hidden: { opacity: 0, y: 24, scale: 0.96 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { ...springGentle, delay: 0.05 },
  },
  exit: { opacity: 0, y: 12, scale: 0.98, transition: easeOutFast },
};

export const slideInRight: Variants = {
  hidden: { opacity: 0, x: "100%" },
  visible: { opacity: 1, x: 0, transition: easeSpatial },
  exit: { opacity: 0, x: "100%", transition: easeSpatial },
};

export const slideInLeft: Variants = {
  hidden: { opacity: 0, x: "-100%" },
  visible: { opacity: 1, x: 0, transition: easeSpatial },
  exit: { opacity: 0, x: "-100%", transition: easeSpatial },
};

/* ─── Stagger container ────────────────────────────────────────────────── */

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
      delayChildren: 0.05,
    },
  },
};

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: easeOut },
};

/* ─── List item ────────────────────────────────────────────────────────── */

export const listItem: Variants = {
  hidden: { opacity: 0, x: -8 },
  visible: { opacity: 1, x: 0, transition: easeOut },
  exit: { opacity: 0, x: 8, transition: easeOutFast },
};

/* ─── Overlay backdrop ─────────────────────────────────────────────────── */

export const overlayBackdrop: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.2, ease: "easeOut" } },
  exit: { opacity: 0, transition: { duration: 0.15, ease: "easeIn" } },
};

/* ─── Hover / tap micro-interactions ──────────────────────────────────── */

export const tapScale = {
  whileTap: { scale: 0.97 },
  transition: springSnappy,
};

export const hoverLift = {
  whileHover: { y: -2, transition: springSnappy },
};

export const hoverScale = {
  whileHover: { scale: 1.02, transition: springSnappy },
};

/* ─── Progress / counter ───────────────────────────────────────────────── */

export const progressBar: Variants = {
  hidden: { scaleX: 0, originX: 0 },
  visible: {
    scaleX: 1,
    transition: { ...easeOut, duration: 0.7, delay: 0.1 },
  },
};
