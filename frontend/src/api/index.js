import { config } from '../config.js'
import { mockApi } from './mockApi.js'
import { realApi } from './realApi.js'

// One import site for the rest of the app. Which adapter is live is decided by
// VITE_USE_MOCK — both implement the identical interface, so nothing downstream
// changes when you flip to the real backend.
export const api = config.useMock ? mockApi : realApi

export { ApiError } from './httpClient.js'
