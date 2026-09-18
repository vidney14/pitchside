import { useEffect, useState } from "react";

// Poll a fetch function on an interval, sharing one source of truth so
// multiple panels don't each open their own duplicate request.
export function useApiPoll(fetchFn, intervalMs) {
  const [data, setData] = useState(null);

  useEffect(() => {
    let alive = true;
    const load = () => fetchFn().then((d) => alive && setData(d)).catch(() => {});
    load();
    const id = setInterval(load, intervalMs);
    return () => {
      alive = false;
      clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs]);

  return data;
}
