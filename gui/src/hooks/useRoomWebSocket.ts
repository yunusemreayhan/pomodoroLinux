import { useEffect, useRef, useCallback } from "react";
import { apiCall } from "../store/api";
import { useStore } from "../store/store";
import type { RoomState } from "../store/api";

export function useRoomWebSocket(roomId: number, onState: (s: RoomState) => void) {
  const onStateRef = useRef(onState);
  onStateRef.current = onState;

  const connect = useCallback(async () => {
    const { serverUrl } = useStore.getState();
    let ws: WebSocket | null = null;
    let attempts = 0;
    let unmounted = false;

    const tryConnect = async () => {
      if (unmounted) return;
      try {
        const resp = await apiCall<{ ticket: string }>("POST", "/api/timer/ticket");
        if (unmounted) return;
        const wsUrl = serverUrl.replace(/^http/, "ws");
        ws = new WebSocket(`${wsUrl}/api/rooms/${roomId}/ws?ticket=${encodeURIComponent(resp.ticket)}`);
        ws.onmessage = (e) => {
          try { onStateRef.current(JSON.parse(e.data)); } catch { /* ignore */ }
        };
        ws.onopen = () => { attempts = 0; };
        ws.onclose = () => {
          if (unmounted) return;
          const delay = Math.min(1000 * Math.pow(2, attempts), 15000);
          attempts++;
          setTimeout(tryConnect, delay);
        };
        ws.onerror = () => ws?.close();
      } catch {
        if (!unmounted) {
          const delay = Math.min(1000 * Math.pow(2, attempts), 15000);
          attempts++;
          setTimeout(tryConnect, delay);
        }
      }
    };

    await tryConnect();
    return () => { unmounted = true; ws?.close(); };
  }, [roomId]);

  useEffect(() => {
    let cleanup: (() => void) | undefined;
    connect().then(c => { cleanup = c; });
    return () => { cleanup?.(); };
  }, [connect]);
}
