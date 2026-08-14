"use client";

import { AnimatePresence, motion } from "framer-motion";
import { usePathname } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export function PageTransitionSweep() {
  const pathname = usePathname();
  const [playKey, setPlayKey] = useState(0);
  const isFirstRender = useRef(true);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    setPlayKey((key) => key + 1);
  }, [pathname]);

  return (
    <AnimatePresence>
      {playKey > 0 ? (
        <motion.div
          key={playKey}
          className="pointer-events-none fixed inset-x-0 top-14 z-40 h-28 overflow-hidden"
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 1, 1, 0] }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.75, times: [0, 0.12, 0.75, 1] }}
          aria-hidden="true"
        >
          <div className="absolute inset-0 bg-gradient-to-b from-[color-mix(in_srgb,var(--brand)_10%,transparent)] to-transparent" />
          <motion.div
            className="absolute inset-y-0 flex items-center"
            initial={{ left: "-14%" }}
            animate={{ left: "104%" }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="h-px w-32 bg-gradient-to-r from-transparent via-[var(--brand)] to-[var(--accent)] blur-[0.5px]" />
            <span className="-ml-3 flex h-9 w-9 items-center justify-center rounded-full bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
              <ArrowRight className="h-4 w-4 text-brand-foreground" aria-hidden="true" />
            </span>
            <div className="-ml-6 h-44 w-44 shrink-0 rounded-full bg-gradient-radial-brand opacity-25 blur-3xl" />
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
