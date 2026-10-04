const BASE = '/api/method'

// Holds the CSRF token when the page is NOT served by Frappe (e.g. Vite dev).
// Populated by initSession() — never shown or managed by the UI.
let csrfToken = ''

function setCsrfToken(token) {
  if (token) csrfToken = token
}

/**
 * Resolve the CSRF token to send as the `X-Frappe-CSRF-Token` header.
 * 1. `window.frappe.csrf_token` — injected by Frappe when it serves the page.
 * 2. `window.csrf_token` — legacy injection used by some Frappe hosts.
 * 3. The token captured by initSession() for the Vite dev proxy case.
 */
function getCsrfToken() {
  if (window.frappe && window.frappe.csrf_token) {
    return window.frappe.csrf_token
  }
  if (window.csrf_token) {
    return window.csrf_token
  }
  return csrfToken
}

/** Perform a GET against a whitelisted method (safe methods skip CSRF). */
async function get(method) {
  const response = await fetch(`${BASE}/${method}`, {
    method: 'GET',
    credentials: 'include',
    headers: { 'Accept': 'application/json' },
  })
  const json = await response.json().catch(() => null)
  return response.ok ? json?.message : null
}

/**
 * Establish a working connection to the user's existing Frappe session.
 * No login form — just confirms a session and (when not served by Frappe)
 * retrieves its CSRF token so subsequent POSTs are authorised.
 *
 * @returns {Promise<{ authenticated: boolean, user: string }>}
 */
export async function initSession() {
  const user = await get('frappe.auth.get_logged_user')

  if (typeof user !== 'string' || !user || user === 'Guest') {
    return { authenticated: false, user: '' }
  }

  // When served by Frappe the token is already injected; in dev only fetch it.
  if (!getCsrfToken()) {
    setCsrfToken(await get('meeting_intelligence.api.get_csrf_token'))
  }

  return { authenticated: true, user }
}

/** Resolve the CSRF header value for a request. */
function requestCsrfHeader() {
  return getCsrfToken()
}

/**
 * Core request helper.
 * @param {string} method  - Python dotted path (or a special endpoint like "login").
 * @param {object} [body]  - Key-value pairs sent as form-encoded body (POST).
 * @param {boolean} [raw]  - When true, the full parsed JSON body is returned
 *                           instead of just the `message` field.
 * @returns {Promise<any>} - The `message` field, or the full JSON when raw.
 */
async function callMethod(method, body = {}, raw = false) {
  const params = new URLSearchParams()

  for (const [key, value] of Object.entries(body)) {
    // Frappe expects complex objects as JSON strings
    params.append(key, typeof value === 'object' ? JSON.stringify(value) : String(value))
  }

  const response = await fetch(`${BASE}/${method}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-Frappe-CSRF-Token': requestCsrfHeader(),
    },
    body: params.toString(),
    credentials: 'include', // send session cookie
  })

  const json = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(buildErrorMessage(response.status, json))
  }

  return raw ? json : json?.message
}

/**
 * Turn an HTTP failure into a human-friendly, single-line message.
 * - Validation errors keep their original text.
 * - 401/403 (session/permission/auth) get an actionable message instead of a raw code.
 * - Everything else falls back to a readable status description.
 */
function buildErrorMessage(status, json) {
  const message = json?.message || json?.exception

  if (json?.exc_type === 'ValidationError' || message) {
    return extractFrappeMessage(message)
  }

  if (status === 401 || status === 403) {
    return 'Your session is invalid or expired. Please log in again.'
  }

  if (status === 404) {
    return `Sorry, that action is not available right now (${status}).`
  }

  return `Could not reach the server. Please try again (HTTP ${status}).`
}

/**
 * Frappe sometimes returns exc messages like:
 *   "frappe.exceptions.ValidationError: Meeting duration must be at least 15 minutes."
 * Strip the class prefix so we show only the human-readable part.
 */
function extractFrappeMessage(raw) {
  if (typeof raw !== 'string') return String(raw)
  const colonIdx = raw.lastIndexOf(': ')
  return colonIdx !== -1 ? raw.slice(colonIdx + 2) : raw
}

// ---------------------------------------------------------------------------
// Public API functions
// ---------------------------------------------------------------------------

/**
 * Fetch all active Meeting Participants for the attendee dropdown.
 *
 * Frontend   : getActiveParticipants()
 * Frappe API : meeting_intelligence.api.get_active_participants
 * DocType    : Meeting Participant  (filter: is_active = 1)
 * Fields     : name, participant_name, designation, department
 *
 * @returns {Promise<Array<{name: string, participant_name: string, designation: string, department: string}>>}
 */
export async function getActiveParticipants() {
  return callMethod('meeting_intelligence.api.get_active_participants')
}


/**
 * Fetch Meeting Session form options from DocType metadata.
 *
 * Frontend   : getMeetingFormOptions()
 * Frappe API : meeting_intelligence.api.get_meeting_form_options
 * Returns    : active Meeting Type records (name, meeting_type_name, description)
 *              and the Select field options of agenda_followed
 *
 * @returns {Promise<{meeting_types: Array<{name: string, meeting_type_name: string, description: string}>, agenda_followed_options: string[]}>}
 */
export async function getMeetingFormOptions() {
  return callMethod('meeting_intelligence.api.get_meeting_form_options')
}

/**
 * Create a new Meeting Session document.
 *
 * Frontend   : createMeetingSession(payload)
 * Frappe API : meeting_intelligence.api.create_meeting_session
 * DocType    : Meeting Session  (child: Meeting Attendee)
 * Triggers   : MeetingSession.validate() — cost, health score, monologue detection
 *
 * @param {{
 *   meeting_title:    string,
 *   meeting_type:     string,
 *   department:       string,
 *   meeting_date:     string,
 *   duration_minutes: number,
 *   agenda_followed:  string,
 *   agenda?:          string,
 *   notes?:           string,
 *   attendees: Array<{participant: string, talk_percentage: number, attended: boolean}>
 * }} payload
 *
 * @returns {Promise<{name: string, meeting_title: string, health_score: number, health_label: string, meeting_cost: number, status: string}>}
 */
export async function createMeetingSession(payload) {
  return callMethod('meeting_intelligence.api.create_meeting_session', { data: payload })
}
