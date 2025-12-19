import '@testing-library/jest-dom';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      pathname: '/',
      query: {},
      asPath: '/',
    };
  },
  usePathname() {
    return '/';
  },
  useSearchParams() {
    return new URLSearchParams();
  },
}));

// Mock environment variables if needed
process.env.NODE_ENV = 'test';

// Mock browser APIs
Object.defineProperty(window.navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: jest.fn(),
    enumerateDevices: jest.fn(),
    getDisplayMedia: jest.fn()
  }
});

Object.defineProperty(window.navigator, 'userAgent', {
  writable: true,
  value: 'Test Browser'
});

Object.defineProperty(window.navigator, 'vendor', {
  writable: true,
  value: 'Test Vendor'
});

Object.defineProperty(window.navigator, 'platform', {
  writable: true,
  value: 'Test Platform'
});

// Mock WebRTC APIs
global.RTCPeerConnection = jest.fn() as any;
global.RTCSessionDescription = jest.fn() as any;
global.RTCIceCandidate = jest.fn() as any;
global.MediaStream = jest.fn() as any;

// Suppress console errors in tests unless needed
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});