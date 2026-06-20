import { useState, useCallback } from 'react';

interface UseClipboardReturn {
  copied: boolean;
  copyToClipboard: (text: string) => Promise<void>;
}

export function useClipboard(): UseClipboardReturn {
  const [copied, setCopied] = useState<boolean>(false);

  const copyToClipboard = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, []);

  return { copied, copyToClipboard };
}
