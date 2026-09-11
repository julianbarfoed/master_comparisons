import { afterEach, expect, test, vi } from 'vitest'
import { ApiError, getMe, getTracks } from './api'

afterEach(() => vi.unstubAllGlobals())

test('sends the current bearer token to both private endpoints', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({ id: 'subject-1' }), { status: 200 }))
    .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }))
  vi.stubGlobal('fetch', fetchMock)

  await expect(getMe('token-123')).resolves.toEqual({ id: 'subject-1' })
  await expect(getTracks('token-123')).resolves.toEqual([])
  expect(fetchMock).toHaveBeenNthCalledWith(1, '/me', expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer token-123' }) }))
  expect(fetchMock).toHaveBeenNthCalledWith(2, '/tracks', expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer token-123' }) }))
})

test('exposes an API error status for authentication handling', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 401 })))
  await expect(getMe('expired-token')).rejects.toEqual(expect.objectContaining({ status: 401 }))
  await expect(getMe('expired-token')).rejects.toBeInstanceOf(ApiError)
})
