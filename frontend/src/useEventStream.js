import { useEffect, useRef, useState } from "react";
import { API_BASE } from "./api";

const MAX_EVENTS = 500;

export function useEventStream() {
  const [events, setEvents] = useState([]);
  const [connected, setConnected] = useState(false);
  const esRef = useRef(null);

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/events/stream`);
    esRef.current = es;

    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);
    es.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      setEvents((prev) => {
        const next = [...prev, msg];
        return next.length > MAX_EVENTS ? next.slice(next.length - MAX_EVENTS) : next;
      });
    };

    return () => es.close();
  }, []);

  const clear = () => setEvents([]);

  return { events, connected, clear };
}
