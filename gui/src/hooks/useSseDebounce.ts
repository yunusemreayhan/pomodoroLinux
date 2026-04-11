import { useEffect } from "react";

export function useSseDebounce(event: string, callback: () => void, delay = 500) {
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const handler = () => { clearTimeout(timer); timer = setTimeout(callback, delay); };
    window.addEventListener(event, handler);
    return () => { clearTimeout(timer); window.removeEventListener(event, handler); };
  }, [event, callback, delay]);
}
