import './styles.css'

export default function App() {
  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <span className="eyebrow">SOUNDBOARD</span>
          <h1>Your audio shelf</h1>
        </div>
      </header>

      <section className="panel">
        <span className="eyebrow">LIBRARY</span>
        <h2>Audio library</h2>
        <p>Upload, playback, authentication, and library data will be connected here.</p>
      </section>
    </main>
  )
}
