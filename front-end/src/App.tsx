import { type FormEvent, useEffect, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import './styles.css'
import AudioLibrary from './components/AudioLibrary'
import { ApiError, getMe, getTracks } from './lib/api'
import { supabase } from './lib/supabase'

type LibraryState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'ready'; tracks: Awaited<ReturnType<typeof getTracks>> }
  | { kind: 'unavailable' }

function formatDuration(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = Math.floor(totalSeconds % 60)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

export default function App() {
  const [session, setSession] = useState<Session | null | undefined>(undefined)
  const [email, setEmail] = useState('')
  const [authMessage, setAuthMessage] = useState<string | null>(null)
  const [isSendingLink, setIsSendingLink] = useState(false)
  const [library, setLibrary] = useState<LibraryState>({ kind: 'idle' })
  const [userId, setUserId] = useState<string | null>(null)

  useEffect(() => {
    if (!supabase) {
      setSession(null)
      return
    }
    let active = true
    void supabase.auth.getSession().then(({ data, error }) => {
      if (!active) return
      setAuthMessage(error?.message ?? null)
      setSession(data.session)
    })
    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (nextSession) setAuthMessage(null)
      setSession(nextSession)
    })
    return () => {
      active = false
      data.subscription.unsubscribe()
    }
  }, [])

  useEffect(() => {
    const accessToken = session?.access_token
    if (!accessToken) {
      setLibrary({ kind: 'idle' })
      setUserId(null)
      return
    }
    let active = true
    setLibrary({ kind: 'loading' })
    setUserId(null)
    void Promise.all([getMe(accessToken), getTracks(accessToken)])
      .then(([user, tracks]) => {
        if (!active) return
        setUserId(user.id)
        setLibrary({ kind: 'ready', tracks })
      })
      .catch((error: unknown) => {
        if (!active) return
        if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
          setAuthMessage('Your session has expired. Sign in again.')
          setSession(null)
          setLibrary({ kind: 'idle' })
          setUserId(null)
          void supabase?.auth.signOut({ scope: 'local' })
          return
        }
        setLibrary({ kind: 'unavailable' })
      })
    return () => { active = false }
  }, [session?.access_token])

  async function sendSignInLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!supabase) return
    setIsSendingLink(true)
    setAuthMessage(null)
    const { error } = await supabase.auth.signInWithOtp({ email })
    setIsSendingLink(false)
    setAuthMessage(error ? error.message : 'Check your email for your sign-in link.')
  }

  async function signOut() {
    setLibrary({ kind: 'idle' })
    setUserId(null)
    setSession(null)
    setAuthMessage(null)
    if (!supabase) return
    const { error } = await supabase.auth.signOut({ scope: 'local' })
    if (error) setAuthMessage(error.message)
  }

  if (session === undefined) return <main className="shell"><p role="status">Restoring your session…</p></main>

  if (!session) {
    return (
      <main className="shell">
        <header className="topbar"><span className="eyebrow">SOUNDBOARD</span><h1>Your audio shelf</h1></header>
        <section aria-labelledby="sign-in-heading" className="panel sign-in-panel">
          <h2 id="sign-in-heading">Sign in to your library</h2>
          {supabase ? (
            <form onSubmit={sendSignInLink}>
              <label htmlFor="email">Email address</label>
              <input autoComplete="email" id="email" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
              <button disabled={isSendingLink} type="submit">{isSendingLink ? 'Sending link…' : 'Email me a sign-in link'}</button>
            </form>
          ) : <p role="alert">Sign-in is unavailable until Supabase is configured.</p>}
          {authMessage && <p role="status">{authMessage}</p>}
        </section>
      </main>
    )
  }

  return (
    <main className="shell">
      <header className="topbar topbar-signed-in">
        <div><span className="eyebrow">SOUNDBOARD</span><h1>Your audio shelf</h1>{userId && <p>Signed in as {userId}</p>}</div>
        <button className="secondary-button" onClick={signOut} type="button">Sign out</button>
      </header>
      <AudioLibrary>
        {library.kind === 'loading' && <p role="status">Loading your library…</p>}
        {library.kind === 'unavailable' && <p role="alert">Your library is unavailable right now. Please try again later.</p>}
        {library.kind === 'ready' && library.tracks.length === 0 && <p className="empty-state" role="status">Your library is empty. Audio you add will appear here.</p>}
        {library.kind === 'ready' && library.tracks.length > 0 && (
          <ul className="track-list" aria-label="Your tracks">
            {library.tracks.map((track) => <li key={track.id}><span>{track.title}</span><time dateTime={`PT${track.duration_seconds}S`}>{formatDuration(track.duration_seconds)}</time></li>)}
          </ul>
        )}
      </AudioLibrary>
    </main>
  )
}
