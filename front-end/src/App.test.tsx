import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import App from './App'

test('renders the library shell without configured external services', () => {
  render(<App />)

  expect(screen.getByRole('main')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Audio library' })).toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent(
    'Your library is empty. Audio you add will appear here.',
  )
})
