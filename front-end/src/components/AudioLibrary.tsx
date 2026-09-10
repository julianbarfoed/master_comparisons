import type { ReactNode } from 'react'

type AudioLibraryProps = {
  children?: ReactNode
}

export default function AudioLibrary({ children }: AudioLibraryProps) {
  return (
    <section aria-labelledby="audio-library-heading" className="panel">
      <span className="eyebrow">LIBRARY</span>
      <h2 id="audio-library-heading">Audio library</h2>
      {children ?? (
        <p className="empty-state" role="status">
          Your library is empty. Audio you add will appear here.
        </p>
      )}
    </section>
  )
}
