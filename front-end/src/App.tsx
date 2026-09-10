import './styles.css'
import AudioLibrary from './components/AudioLibrary'

export default function App() {
  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <span className="eyebrow">SOUNDBOARD</span>
          <h1>Your audio shelf</h1>
        </div>
      </header>

      <AudioLibrary />
    </main>
  )
}
