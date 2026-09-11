export type VerifiedUser = { id: string }

export type Track = {
  id: string
  title: string
  duration_seconds: number
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message = `Request failed with status ${status}`,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

const apiUrl = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

async function request<T>(path: string, accessToken: string): Promise<T> {
  const response = await fetch(`${apiUrl}${path}`, {
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
  })
  if (!response.ok) throw new ApiError(response.status)
  return response.json() as Promise<T>
}

export function getMe(accessToken: string) {
  return request<VerifiedUser>('/me', accessToken)
}

export function getTracks(accessToken: string) {
  return request<Track[]>('/tracks', accessToken)
}
