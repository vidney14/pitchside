import { useEffect, useRef } from "react";
import { stageColor } from "../stageStyle";

export default function EventFeed({ events, connected }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [events.length]);

  return (
    <div className="panel feed-panel">
      <div className="panel-header">
        <h2>Live Event Feed</h2>
        <span className={`live-pill small ${connected ? "is-live" : "is-idle"}`}>
          <span className="live-dot" />
          {connected ? "connected" : "disconnected"}
        </span>
      </div>
      <div className="feed-scroll">
        {events.length === 0 && (
          <div className="empty-state">No events yet. Start a run to see the feed.</div>
        )}
        {events.map((ev, i) => (
          <div className="feed-row" key={i}>
            <span className="feed-time">{ev.at}</span>
            <span className="stage-badge" style={{ background: stageColor(ev.stage) }}>
              {ev.stage}
            </span>
            <span className="feed-text">{ev.text}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
