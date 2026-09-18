import { useEffect, useRef, useState } from "react";

const FLUSH_MS = 500; // throttle chart updates to ~2x/second
const MAX_POINTS = 40;

// Turns the raw (fast, per-message) SSE event array into a rolling
// events-per-tick series for the live chart, without re-rendering the
// chart on every single message -- only on the flush interval.
export function useLiveSeries(events) {
  const [series, setSeries] = useState([]);
  const eventsRef = useRef(events);
  const lastCountRef = useRef(0);
  eventsRef.current = events;

  useEffect(() => {
    const id = setInterval(() => {
      const okCount = eventsRef.current.filter((e) => e.stage === "OK").length;
      const delta = Math.max(0, okCount - lastCountRef.current);
      lastCountRef.current = okCount;
      setSeries((prev) => {
        const next = [...prev, { t: Date.now(), rate: delta, total: okCount }];
        return next.length > MAX_POINTS ? next.slice(next.length - MAX_POINTS) : next;
      });
    }, FLUSH_MS);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (events.length === 0) {
      setSeries([]);
      lastCountRef.current = 0;
    }
  }, [events.length === 0]);

  return series;
}
