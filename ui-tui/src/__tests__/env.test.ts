import { afterEach, describe, expect, it, vi } from 'vitest'

async function loadEnv(dashboard: string, fresh: string) {
  vi.resetModules()
  vi.stubEnv('HERMES_TUI_DASHBOARD', dashboard)
  vi.stubEnv('HERMES_TUI_DASHBOARD_FRESH', fresh)

  return import('../config/env.js')
}

afterEach(() => {
  vi.unstubAllEnvs()
  vi.resetModules()
})

describe('dashboard fresh startup env', () => {
  it.each(['1', 'true', 'yes', 'on', ' TRUE '])('accepts dashboard truthy value %j', async value => {
    const env = await loadEnv('1', value)

    expect(env.DASHBOARD_FRESH_START).toBe(true)
  })

  it.each(['', '0', 'false', 'no', 'off', 'unexpected'])('rejects dashboard falsy value %j', async value => {
    const env = await loadEnv('1', value)

    expect(env.DASHBOARD_FRESH_START).toBe(false)
  })

  it('ignores the fresh marker outside dashboard mode', async () => {
    const env = await loadEnv('0', '1')

    expect(env.DASHBOARD_FRESH_START).toBe(false)
  })
})
