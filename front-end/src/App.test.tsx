import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, test, vi } from 'vitest'

const mocks = vi.hoisted(() => {
  class TestApiError extends Error {
    constructor(public status: number) { super(`Request failed with status ${status}`) }
  }
  return {
    ApiError: TestApiError,
    getMe: vi.fn(),
    getSession: vi.fn(),
    getTracks: vi.fn(),
    onAuthStateChange: vi.fn(),
    signInWithOtp: vi.fn(),
    signOut: vi.fn(),
  }
})

vi.mock('./lib/api', () => ({
  ApiError: mocks.ApiError,
  getMe: mocks.getMe,
  getTracks: mocks.getTracks,
}))

vi.mock('./lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: mocks.getSession,
      onAuthStateChange: mocks.onAuthStateChange,
      signInWithOtp: mocks.signInWithOtp,
      signOut: mocks.signOut,
    },
  },
}))

import App from './App'

const session = { access_token: 'access-token' }

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.getSession.mockResolvedValue({ data: { session: null }, error: null })
    mocks.onAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } })
    mocks.signInWithOtp.mockResolvedValue({ error: null })
    mocks.signOut.mockResolvedValue({ error: null })
    mocks.getMe.mockResolvedValue({ id: 'verified-user' })
    mocks.getTracks.mockResolvedValue([])
  })

  test('restores a session and renders populated tracks from the contract', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.getTracks.mockResolvedValue([{ id: 'track-1', title: 'Ocean sounds', duration_seconds: 65 }])

    render(<App />)

    expect(screen.getByRole('status')).toHaveTextContent('Restoring your session')
    expect(await screen.findByText('Ocean sounds')).toBeInTheDocument()
    expect(screen.getByText('1:05')).toBeInTheDocument()
    expect(screen.getByText('Signed in as verified-user')).toBeInTheDocument()
    expect(mocks.getMe).toHaveBeenCalledWith('access-token')
    expect(mocks.getTracks).toHaveBeenCalledWith('access-token')
  })

  test('sends an email OTP from the signed-out screen', async () => {
    render(<App />)

    fireEvent.change(await screen.findByLabelText('Email address'), { target: { value: 'me@example.com' } })
    fireEvent.click(screen.getByRole('button', { name: 'Email me a sign-in link' }))

    await waitFor(() => expect(mocks.signInWithOtp).toHaveBeenCalledWith({ email: 'me@example.com' }))
    expect(screen.getByRole('status')).toHaveTextContent('Check your email for your sign-in link.')
  })

  test('renders an empty library for a verified session with no tracks', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    render(<App />)
    expect(await screen.findByText('Your library is empty. Audio you add will appear here.')).toBeInTheDocument()
  })

  test('shows a loading state while the private library is being fetched', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.getTracks.mockReturnValue(new Promise(() => undefined))
    render(<App />)
    expect(await screen.findByText('Loading your library…')).toBeInTheDocument()
  })

  test('shows an unavailable state for a non-auth API failure', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.getTracks.mockRejectedValue(new Error('network unavailable'))
    render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Your library is unavailable right now')
  })

  test('clears private data and avoids retrying after an expired session', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.getMe.mockRejectedValue(new mocks.ApiError(401))
    render(<App />)

    expect(await screen.findByText('Sign in to your library')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Your session has expired')
    expect(mocks.signOut).toHaveBeenCalledWith({ scope: 'local' })
    expect(mocks.getMe).toHaveBeenCalledTimes(1)
    expect(mocks.getTracks).toHaveBeenCalledTimes(1)
  })

  test('clears the library immediately when signing out', async () => {
    mocks.getSession.mockResolvedValue({ data: { session }, error: null })
    mocks.getTracks.mockResolvedValue([{ id: 'track-1', title: 'Ocean sounds', duration_seconds: 65 }])
    render(<App />)
    await screen.findByText('Ocean sounds')

    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))

    expect(await screen.findByText('Sign in to your library')).toBeInTheDocument()
    expect(screen.queryByText('Ocean sounds')).not.toBeInTheDocument()
    expect(mocks.signOut).toHaveBeenCalledWith({ scope: 'local' })
  })
})
