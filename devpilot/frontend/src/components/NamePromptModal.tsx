import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

interface Props {
  open: boolean;
  title: string;
  placeholder?: string;
  initialValue?: string;
  confirmLabel?: string;
  onCancel: () => void;
  onConfirm: (value: string) => void;
}

export default function NamePromptModal({
  open,
  title,
  placeholder,
  initialValue = "",
  confirmLabel = "Create",
  onCancel,
  onConfirm,
}: Props) {
  const [value, setValue] = useState(initialValue);

  useEffect(() => {
    if (open) setValue(initialValue);
  }, [open, initialValue]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-32 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onCancel}
        >
          <motion.form
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.12 }}
            onClick={(e) => e.stopPropagation()}
            onSubmit={(e) => {
              e.preventDefault();
              if (value.trim()) onConfirm(value.trim());
            }}
            className="w-full max-w-sm rounded-lg border border-ink-700 bg-ink-900 p-4 shadow-2xl"
          >
            <p className="mb-2 text-xs font-medium text-ink-300">{title}</p>
            <input
              autoFocus
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={placeholder}
              className="w-full rounded-md border border-ink-600 bg-ink-850 px-3 py-2 font-mono text-sm text-ink-100 placeholder:text-ink-500 focus:border-amber-500 focus:outline-none"
            />
            <div className="mt-3 flex justify-end gap-2">
              <button
                type="button"
                onClick={onCancel}
                className="rounded-md px-3 py-1.5 text-xs font-medium text-ink-400 hover:bg-ink-800 hover:text-ink-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="rounded-md bg-amber-500 px-3 py-1.5 text-xs font-medium text-ink-950 hover:bg-amber-400"
              >
                {confirmLabel}
              </button>
            </div>
          </motion.form>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
