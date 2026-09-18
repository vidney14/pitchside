export default function Header({ running }) {
  return (
    <header className="hero">
      <h1 className="hero-title">Pitchside</h1>
      <p className="hero-tagline">
        A soccer pipeline that breaks on purpose — and an AI agent that fixes it.
      </p>
      <div className={`live-pill ${running ? "is-live" : "is-idle"}`}>
        <span className="live-dot" />
        {running ? "LIVE" : "IDLE"}
      </div>
    </header>
  );
}
