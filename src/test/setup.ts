import '@testing-library/jest-dom'

// Mock dla WebSocket (dla Twojego real-time monitoring)
global.WebSocket = class MockWebSocket {
  constructor(url: string) {
    console.log(`Mock WebSocket connection to: ${url}`)
  }

  send() {}
  close() {}
  addEventListener() {}
  removeEventListener() {}
} as any

// Mock dla MediaDevices (dla camera integration)
Object.defineProperty(navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: () => []
    })
  }
})

// Mock dla innych API używanych w projekcie przemysłowym
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))