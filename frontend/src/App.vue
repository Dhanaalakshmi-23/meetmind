<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getActiveParticipants, getMeetingFormOptions, createMeetingSession, initSession } from './api.js'

// Meeting Types — sourced from the centralized Meeting Type DocType
const meetingTypes = ref([])           // [{ name, meeting_type_name }]
const typesLoading = ref(false)
const typesError = ref('')

// Agenda options — sourced from Meeting Session DocType metadata via the backend
const agendaFollowedOptions = ref([])
const optionsLoading = ref(false)
const optionsError = ref('')

// Participants — fetched from Meeting Participant DocType on mount
const participantOptions = ref([])     // [{ name, participant_name, designation, department }]
const participantsLoading = ref(false)
const participantsError = ref('')

onMounted(async () => {
  await initSession()
  loadFormOptions()
  loadParticipants()
})

async function loadFormOptions() {
  optionsLoading.value = true
  optionsError.value = ''
  typesLoading.value = true
  typesError.value = ''
  try {
    // get_meeting_form_options() returns both the active Meeting Type records
    // and the Meeting Session agenda_followed options in a single call.
    const options = (await getMeetingFormOptions()) || {}
    meetingTypes.value = options.meeting_types || []
    agendaFollowedOptions.value = options.agenda_followed_options || []
  } catch (err) {
    const message = err.message || 'Could not load meeting options. Please refresh.'
    optionsError.value = message
    typesError.value = message
  } finally {
    optionsLoading.value = false
    typesLoading.value = false
  }
}

async function loadParticipants() {
  participantsLoading.value = true
  participantsError.value = ''
  try {
    participantOptions.value = (await getActiveParticipants()) || []
  } catch (err) {
    participantsError.value = err.message || 'Could not load participants. Please refresh.'
  } finally {
    participantsLoading.value = false
  }
}

const wizardSteps = [
  { label: 'Meeting', title: 'Meeting Details' },
  { label: 'Attendees', title: 'Attendees' },
  { label: 'Meeting Context', title: 'Meeting Context' },
]
const totalSteps = wizardSteps.length
const currentStep = ref(1)

const progressPercent = computed(() => Math.round((currentStep.value / totalSteps) * 100))
const activeStepTitle = computed(() => wizardSteps[currentStep.value - 1].title)

const form = reactive({
  meetingTitle: '',
  meetingType: '',
  department: '',
  meetingDate: new Date().toISOString().slice(0, 10),
  durationMinutes: 60,
  agendaFollowed: '',
  agenda: '',
  notes: '',
})

const attendees = ref([
  {
    participant: '',
    talk_percentage: 0,
    attended: true,
  },
])

const errors = reactive({
  meetingTitle: '',
  meetingType: '',
  department: '',
  meetingDate: '',
  durationMinutes: '',
  agendaFollowed: '',
})

const attendeesErrors = ref([])

const validated = ref(false)

function clearError(field) {
  errors[field] = ''
}

function clearAttendeesErrors() {
  attendeesErrors.value = []
}

function addAttendee() {
  attendees.value.push({
    participant: '',
    talk_percentage: 0,
    attended: true,
  })
  clearAttendeesErrors()
}

function removeAttendee(index) {
  attendees.value.splice(index, 1)
  clearAttendeesErrors()
}

function validateAttendees() {
  const messages = []

  if (attendees.value.length === 0) {
    messages.push('Add at least one attendee.')
    return messages
  }

  if (attendees.value.some((attendee) => !attendee.participant)) {
    messages.push('Every attendee must have a Participant selected.')
  }

  if (
    attendees.value.some(
      (attendee) => attendee.talk_percentage < 0 || attendee.talk_percentage > 100
    )
  ) {
    messages.push('Talk Percentage must be between 0 and 100.')
  }

  const total = attendees.value.reduce(
    (sum, attendee) => sum + (Number(attendee.talk_percentage) || 0),
    0
  )

  if (total !== 100) {
    messages.push(`Talk Percentages must total 100%. Current total: ${total}%.`)
  }

  return messages
}

function validateStep(step) {
  if (step === 1) {
    errors.meetingTitle = form.meetingTitle.trim() ? '' : 'Meeting Title is required.'
    errors.meetingType = form.meetingType ? '' : 'Meeting Type is required.'
    errors.department = form.department.trim() ? '' : 'Department is required.'
    errors.meetingDate = form.meetingDate ? '' : 'Meeting Date is required.'
    errors.durationMinutes = String(form.durationMinutes).trim() ? '' : 'Duration is required.'

    return (
      !errors.meetingTitle &&
      !errors.meetingType &&
      !errors.department &&
      !errors.meetingDate &&
      !errors.durationMinutes
    )
  }

  if (step === 2) {
    attendeesErrors.value = validateAttendees()
    return attendeesErrors.value.length === 0
  }

  errors.agendaFollowed = form.agendaFollowed ? '' : 'Agenda Followed is required.'
  return !errors.agendaFollowed
}

function validateForm() {
  const step1Valid = validateStep(1)
  const step2Valid = validateStep(2)
  const step3Valid = validateStep(3)

  return step1Valid && step2Valid && step3Valid
}

function goToStep(step) {
  if (step >= 1 && step <= totalSteps) {
    currentStep.value = step
  }
}

function goNext() {
  if (currentStep.value < totalSteps && validateStep(currentStep.value)) {
    goToStep(currentStep.value + 1)
  }
}

function goPrevious() {
  goToStep(currentStep.value - 1)
}

// Submit state
const submitting = ref(false)
const submitError = ref('')
const submitResult = ref(null)  // holds { name, health_score, health_label, meeting_cost } on success

async function handleSubmit() {
  validated.value = validateForm()

  if (!validated.value) {
    const step1HasErrors =
      errors.meetingTitle ||
      errors.meetingType ||
      errors.department ||
      errors.meetingDate ||
      errors.durationMinutes

    if (step1HasErrors) {
      goToStep(1)
    } else if (attendeesErrors.value.length > 0) {
      goToStep(2)
    } else {
      goToStep(3)
    }
    return
  }

  submitting.value = true
  submitError.value = ''
  submitResult.value = null

  try {
    const payload = {
      meeting_title: form.meetingTitle,
      meeting_type: form.meetingType,
      department: form.department,
      meeting_date: form.meetingDate,
      duration_minutes: form.durationMinutes,
      agenda_followed: form.agendaFollowed,
      agenda: form.agenda,
      notes: form.notes,
      attendees: attendees.value.map((a) => ({
        participant: a.participant,
        talk_percentage: a.talk_percentage,
        attended: a.attended,
      })),
    }

    const result = await createMeetingSession(payload)
    submitResult.value = result
  } catch (err) {
    submitError.value = err.message || 'Submission failed. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="container">
      <header class="app-header">
        <div class="brand-row">
          <div class="brand">
            <div class="logo-mark" aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <rect x="1" y="6" width="2.6" height="6" rx="1.3" fill="#ffffff" />
                <rect x="5.2" y="3" width="2.6" height="12" rx="1.3" fill="#ffffff" />
                <rect x="9.4" y="5" width="2.6" height="8" rx="1.3" fill="#ffffff" />
                <rect x="13.6" y="7" width="2.6" height="4" rx="1.3" fill="#ffffff" />
              </svg>
            </div>
            <span class="brand-name">MeetMind</span>
          </div>
          <span class="header-badge">Meeting Summary</span>
        </div>
        <h1 class="app-title">Meeting Intelligence</h1>
        <p class="app-tagline">Capture the important outcomes of every meeting.</p>
      </header>

      <div class="progress-card">
        <div class="progress-meta">
          <span class="progress-step-text">
            Step {{ currentStep }} of {{ totalSteps }} — {{ activeStepTitle }}
          </span>
          <span class="progress-pct">{{ progressPercent }}%</span>
        </div>
        <div class="progress-track" aria-hidden="true">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <div class="steps">
          <template v-for="(step, index) in wizardSteps" :key="step.label">
            <div
              class="step"
              :class="{ active: currentStep === index + 1, completed: currentStep > index + 1 }"
            >
              <span class="step-dot">{{ currentStep > index + 1 ? '✓' : index + 1 }}</span>
              <span class="step-label">{{ step.label }}</span>
            </div>
            <div
              v-if="index < wizardSteps.length - 1"
              class="step-connector"
              aria-hidden="true"
            ></div>
          </template>
        </div>
      </div>

      <form class="card" novalidate @submit.prevent="handleSubmit">
        <div v-show="currentStep === 1" class="step-panel">
          <section class="form-section">
            <h2 class="section-title">Basic Information</h2>
            <p class="section-desc">Tell us a little about the meeting.</p>

            <div class="field">
              <label for="meeting-title">Meeting Title <span class="required">*</span></label>
              <input
                id="meeting-title"
                v-model="form.meetingTitle"
                type="text"
                placeholder="e.g. Q3 Product Planning"
                :class="{ invalid: errors.meetingTitle }"
                @input="clearError('meetingTitle')"
              />
              <p v-if="errors.meetingTitle" class="error-text">{{ errors.meetingTitle }}</p>
            </div>

            <div class="grid-2">
              <div class="field">
                <label for="meeting-type">Meeting Type <span class="required">*</span></label>
                <select
                  id="meeting-type"
                  v-model="form.meetingType"
                  :disabled="typesLoading"
                  :class="{ invalid: errors.meetingType }"
                  @change="clearError('meetingType')"
                >
                  <option value="" disabled>
                    {{ typesLoading ? 'Loading meeting types…' : 'Select meeting type' }}
                  </option>
                  <option v-for="type in meetingTypes" :key="type.name" :value="type.name">
                    {{ type.meeting_type_name }}
                  </option>
                </select>
                <p v-if="errors.meetingType" class="error-text">{{ errors.meetingType }}</p>
                <p v-if="typesError" class="error-text">{{ typesError }}</p>
                <p
                  v-if="!typesLoading && !typesError && meetingTypes.length === 0"
                  class="error-text"
                >
                  No active meeting types found. Add them in MeetMind before capturing meetings.
                </p>
              </div>

              <div class="field">
                <label for="department">Department <span class="required">*</span></label>
                <input
                  id="department"
                  v-model="form.department"
                  type="text"
                  placeholder="e.g. Engineering"
                  :class="{ invalid: errors.department }"
                  @input="clearError('department')"
                />
                <p v-if="errors.department" class="error-text">{{ errors.department }}</p>
              </div>
            </div>
          </section>

          <section class="form-section">
            <h2 class="section-title">Meeting Timing</h2>
            <p class="section-desc">When did the meeting happen and how long did it run?</p>

            <div class="grid-2">
              <div class="field">
                <label for="meeting-date">Meeting Date <span class="required">*</span></label>
                <input
                  id="meeting-date"
                  v-model="form.meetingDate"
                  type="date"
                  :class="{ invalid: errors.meetingDate }"
                  @input="clearError('meetingDate')"
                />
                <p v-if="errors.meetingDate" class="error-text">{{ errors.meetingDate }}</p>
              </div>

              <div class="field">
                <label for="duration-minutes">Duration <span class="required">*</span></label>
                <div class="input-group">
                  <input
                    id="duration-minutes"
                    v-model="form.durationMinutes"
                    type="number"
                    min="0"
                    :class="{ invalid: errors.durationMinutes }"
                    @input="clearError('durationMinutes')"
                  />
                  <span class="input-suffix">minutes</span>
                </div>
                <p v-if="errors.durationMinutes" class="error-text">{{ errors.durationMinutes }}</p>
              </div>
            </div>
          </section>
        </div>

        <div v-show="currentStep === 2" class="step-panel">
          <section class="form-section">
            <h2 class="section-title">Meeting Attendees <span class="required">*</span></h2>
            <p class="section-desc">Who was in the room and how much did each person speak?</p>

            <div
              v-for="(attendee, index) in attendees"
              :key="index"
              class="attendee-row"
            >
              <div class="attendee-field participant-field">
                <label :for="`participant-${index}`">
                  Participant <span class="required">*</span>
                </label>
                <select
                  :id="`participant-${index}`"
                  v-model="attendee.participant"
                  :disabled="participantsLoading"
                  @change="clearAttendeesErrors"
                >
                  <option value="" disabled>
                    {{ participantsLoading ? 'Loading participants…' : 'Select participant' }}
                  </option>
                  <option
                    v-for="option in participantOptions"
                    :key="option.name"
                    :value="option.name"
                  >
                    {{ option.participant_name }}
                    <template v-if="option.designation"> — {{ option.designation }}</template>
                  </option>
                </select>
              </div>

              <div class="attendee-field">
                <label :for="`talk-percentage-${index}`">Talk Percentage</label>
                <input
                  :id="`talk-percentage-${index}`"
                  v-model.number="attendee.talk_percentage"
                  type="number"
                  min="0"
                  max="100"
                  @input="clearAttendeesErrors"
                />
              </div>

              <div class="attendee-field attendee-check">
                <label :for="`attended-${index}`">Attended</label>
                <input
                  :id="`attended-${index}`"
                  v-model="attendee.attended"
                  type="checkbox"
                  @change="clearAttendeesErrors"
                />
              </div>

              <button
                type="button"
                class="remove-btn"
                @click="removeAttendee(index)"
              >
                Remove
              </button>
            </div>

            <button type="button" class="add-btn" @click="addAttendee">+ Add Attendee</button>

            <!-- Participants fetch error -->
            <p v-if="participantsError" class="error-text attendee-error">{{ participantsError }}</p>

            <!-- Participants empty state -->
            <p
              v-if="!participantsLoading && !participantsError && participantOptions.length === 0"
              class="error-text attendee-error"
            >
              No active participants found. Add participants in MeetMind before capturing meetings.
            </p>

            <p
              v-for="(message, index) in attendeesErrors"
              :key="index"
              class="error-text attendee-error"
            >
              {{ message }}
            </p>
          </section>
        </div>

        <div v-show="currentStep === 3" class="step-panel">
          <section class="form-section">
            <h2 class="section-title">Meeting Context</h2>
            <p class="section-desc">Capture how the meeting actually went.</p>

            <div class="field">
              <label for="agenda-followed">Agenda Followed <span class="required">*</span></label>
              <select
                id="agenda-followed"
                v-model="form.agendaFollowed"
                :disabled="optionsLoading"
                :class="{ invalid: errors.agendaFollowed }"
                @change="clearError('agendaFollowed')"
              >
                <option value="" disabled>
                  {{ optionsLoading ? 'Loading options…' : 'Select an option' }}
                </option>
                <option v-for="option in agendaFollowedOptions" :key="option" :value="option">
                  {{ option }}
                </option>
              </select>
              <p v-if="errors.agendaFollowed" class="error-text">{{ errors.agendaFollowed }}</p>
            </div>

            <div class="field">
              <label for="agenda">Agenda</label>
              <textarea
                id="agenda"
                v-model="form.agenda"
                maxlength="1000"
                placeholder="What topics were discussed?"
              ></textarea>
              <p class="char-counter">{{ form.agenda.length }} / 1000</p>
            </div>

            <div class="field">
              <label for="notes">Notes</label>
              <textarea
                id="notes"
                v-model="form.notes"
                maxlength="1000"
                placeholder="Add any important context or observations..."
              ></textarea>
              <p class="char-counter">{{ form.notes.length }} / 1000</p>
            </div>
          </section>
        </div>

        <div class="wizard-actions">
          <button
            v-if="currentStep > 1"
            type="button"
            class="back-btn"
            @click="goPrevious"
          >
            ← Previous
          </button>
          <button
            v-if="currentStep < totalSteps"
            type="button"
            class="continue-btn"
            @click="goNext"
          >
            {{ currentStep === 1 ? 'Continue to Attendees →' : 'Continue to Meeting Context →' }}
          </button>
          <button
            v-else
            type="submit"
            class="continue-btn"
            :disabled="submitting"
          >
            {{ submitting ? 'Saving…' : 'Submit Meeting' }}
          </button>
        </div>

        <!-- API submit error -->
        <div v-if="submitError" class="error-banner" role="alert">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <circle cx="8" cy="8" r="7" fill="#d93025" />
            <path d="M8 4.5V8.5" stroke="#fff" stroke-width="1.6" stroke-linecap="round" />
            <circle cx="8" cy="11" r="0.8" fill="#fff" />
          </svg>
          <span>{{ submitError }}</span>
        </div>

        <!-- Success card after create -->
        <div v-if="submitResult" class="success-card" role="status">
          <div class="success-card-header">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
              <circle cx="9" cy="9" r="8" fill="#188038" />
              <path d="M5.4 9.2L7.9 11.7L12.6 6.3" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <span>Meeting saved — {{ submitResult.name }}</span>
          </div>
          <div class="success-metrics">
            <div class="metric-chip">
              <span class="metric-label">Health</span>
              <span class="metric-value">{{ submitResult.health_label }} ({{ submitResult.health_score }}/100)</span>
            </div>
            <div class="metric-chip">
              <span class="metric-label">Meeting Cost</span>
              <span class="metric-value">{{ submitResult.meeting_cost.toFixed(2) }}</span>
            </div>
            <div class="metric-chip">
              <span class="metric-label">Status</span>
              <span class="metric-value">{{ submitResult.status }}</span>
            </div>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.page {
  --primary: #673ab7;
  --primary-dark: #56309b;
  --primary-soft: #f0eafc;
  --bg: #f5f3fb;
  --card: #ffffff;
  --border: #e6e2f0;
  --text: #221d35;
  --muted: #6f6a80;
  --error: #d93025;
  --success: #188038;

  min-height: 100vh;
  background: var(--bg);
  padding: 32px 24px 72px;
  font-family: 'Segoe UI', Roboto, Arial, sans-serif;
  color: var(--text);
  box-sizing: border-box;
}

.container {
  max-width: 760px;
  margin: 0 auto;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.app-header {
  background: linear-gradient(135deg, #ffffff 0%, #f0eafc 100%);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 26px 28px;
  margin-bottom: 16px;
  animation: rise 0.35s ease both;
}

.brand-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, #673ab7, #8e5ce6);
  box-shadow: 0 2px 6px rgba(103, 58, 183, 0.3);
}

.brand-name {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.header-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
  background: #efe9fb;
  border: 1px solid #e0d5f5;
  border-radius: 999px;
}

.header-badge::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary);
}

.app-title {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.app-tagline {
  margin: 0;
  font-size: 14px;
  color: var(--muted);
}

.progress-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 16px;
  animation: rise 0.35s ease 0.06s both;
}

.progress-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.progress-step-text {
  font-size: 13px;
  font-weight: 600;
}

.progress-pct {
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
}

.progress-track {
  height: 6px;
  background: #ece8f5;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 18px;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #673ab7, #8e5ce6);
  transition: width 0.3s ease;
}

.steps {
  display: flex;
  align-items: center;
  gap: 10px;
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.step-dot {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  color: #9a94ad;
  background: #ffffff;
  border: 2px solid #d5d0e2;
  flex-shrink: 0;
}

.step-label {
  font-size: 13px;
  color: var(--muted);
}

.step.active .step-dot {
  color: #ffffff;
  background: var(--primary);
  border-color: var(--primary);
  box-shadow: 0 2px 6px rgba(103, 58, 183, 0.35);
}

.step.active .step-label {
  font-weight: 600;
  color: var(--text);
}

.step.completed .step-dot {
  color: #ffffff;
  background: var(--primary);
  border-color: var(--primary);
}

.step.completed .step-label {
  color: var(--text);
}

.step-connector {
  flex: 1;
  min-width: 12px;
  height: 2px;
  border-radius: 1px;
  background: #e6e2f0;
}

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 1px 3px rgba(34, 29, 53, 0.05), 0 10px 28px rgba(34, 29, 53, 0.06);
  animation: rise 0.35s ease 0.12s both;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 6px rgba(34, 29, 53, 0.06), 0 16px 36px rgba(34, 29, 53, 0.09);
}

.step-panel {
  animation: fade-slide-in 0.25s ease;
}

@keyframes fade-slide-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.form-section {
  padding-bottom: 26px;
  margin-bottom: 26px;
  border-bottom: 1px solid #efecf7;
}

.step-panel .form-section:last-child {
  padding-bottom: 0;
  margin-bottom: 0;
  border-bottom: none;
}

.section-title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
}

.section-desc {
  margin: 0 0 18px;
  font-size: 13px;
  color: var(--muted);
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.field {
  margin-bottom: 18px;
}

.grid-2 .field {
  margin-bottom: 0;
}

.field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 7px;
}

.required {
  color: var(--error);
}


input,
select,
textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  min-height: 48px;
  font-size: 14px;
  font-family: inherit;
  color: var(--text);
  background: #ffffff;
  border: 1px solid #d5d0e2;
  border-radius: 10px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

input::placeholder,
textarea::placeholder {
  color: #a5a0b5;
}

input:focus,
select:focus,
textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(103, 58, 183, 0.12);
}

textarea {
  min-height: 120px;
  padding: 12px 14px;
  resize: vertical;
  line-height: 1.55;
}

select {
  appearance: none;
  padding-right: 40px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5L6 6.5L11 1.5' stroke='%236f6a80' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
}

.invalid {
  border-color: var(--error);
}

.invalid:focus {
  border-color: var(--error);
  box-shadow: 0 0 0 4px rgba(217, 48, 37, 0.1);
}

.input-group {
  position: relative;
}

.input-group input {
  padding-right: 78px;
}

.input-suffix {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 13px;
  color: var(--muted);
  pointer-events: none;
}

.char-counter {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--muted);
  text-align: right;
}

@keyframes fade-slide {
  from {
    opacity: 0;
    transform: translateY(-2px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.error-text {
  margin: 7px 0 0;
  font-size: 12px;
  color: var(--error);
  animation: fade-slide 0.18s ease;
}

.success-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 16px;
  font-size: 14px;
  font-weight: 500;
  color: var(--success);
  background: #e6f4ea;
  border: 1px solid #ceead6;
  border-radius: 10px;
  margin-top: 14px;
  animation: fade-slide 0.2s ease;
}

.success-banner svg {
  flex-shrink: 0;
}

/* API submit error */
.error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 16px;
  font-size: 14px;
  font-weight: 500;
  color: var(--error);
  background: #fdecea;
  border: 1px solid #f5c6c3;
  border-radius: 10px;
  margin-top: 14px;
  animation: fade-slide 0.2s ease;
}

.error-banner svg {
  flex-shrink: 0;
}

/* Success card with computed metrics */
.success-card {
  margin-top: 16px;
  padding: 18px 20px;
  background: linear-gradient(135deg, #e6f4ea 0%, #f0fbf2 100%);
  border: 1px solid #a8d5b5;
  border-radius: 14px;
  animation: fade-slide 0.25s ease;
}

.success-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  font-weight: 600;
  color: var(--success);
  margin-bottom: 14px;
}

.success-card-header svg {
  flex-shrink: 0;
}

.success-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.metric-chip {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 14px;
  background: #ffffff;
  border: 1px solid #c3e6cb;
  border-radius: 10px;
  min-width: 120px;
}

.metric-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-value {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
}

.attendee-row {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: end;
  padding: 16px;
  background: #faf9fd;
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 12px;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.attendee-row:hover {
  transform: translateY(-1px);
  border-color: #d5c8f0;
  box-shadow: 0 4px 12px rgba(103, 58, 183, 0.08);
}

.attendee-field label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--muted);
}

.attendee-check input[type='checkbox'] {
  width: 18px;
  height: 18px;
  min-height: 18px;
  margin: 0 0 13px;
  accent-color: var(--primary);
  cursor: pointer;
}

.remove-btn {
  padding: 12px 8px;
  font-size: 13px;
  font-weight: 600;
  font-family: inherit;
  color: var(--error);
  background: none;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.remove-btn:hover {
  background: #fdecea;
}

.add-btn {
  padding: 11px 18px;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  color: var(--primary);
  background: #ffffff;
  border: 1px dashed #c9b8ec;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.add-btn:hover {
  background: var(--primary-soft);
  border-color: var(--primary);
}

.attendee-error {
  margin-top: 8px;
}

.wizard-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.continue-btn {
  flex: 1;
  padding: 14px 24px;
  font-size: 15px;
  font-weight: 600;
  font-family: inherit;
  color: #ffffff;
  background: var(--primary);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(103, 58, 183, 0.25);
  transition: background 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}

.continue-btn:hover {
  background: var(--primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(103, 58, 183, 0.3);
}

.continue-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(103, 58, 183, 0.25);
}

.back-btn {
  padding: 14px 22px;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  color: var(--muted);
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.back-btn:hover {
  background: var(--primary-soft);
  border-color: var(--primary);
  color: var(--primary);
}

.back-btn:active {
  transform: translateY(1px);
}

/* Session notice */
.auth-card {
  animation: rise 0.35s ease both;
}

.auth-message {
  text-align: center;
  color: var(--muted);
  font-size: 14px;
}

@media (max-width: 720px) {
  .page {
    padding: 16px 12px 48px;
  }

  .app-header {
    padding: 20px 18px;
  }

  .app-title {
    font-size: 22px;
  }

  .brand-name {
    font-size: 12px;
    letter-spacing: 1.5px;
  }

  .progress-card {
    padding: 16px;
  }

  .step:not(.active) .step-label {
    display: none;
  }

  .card {
    padding: 20px 16px;
  }

  .grid-2 {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .grid-2 .field {
    margin-bottom: 18px;
  }

  .attendee-row {
    grid-template-columns: 1fr 1fr auto;
  }

  .participant-field {
    grid-column: 1 / -1;
  }

  .add-btn {
    width: 100%;
  }

  .back-btn {
    padding: 14px 18px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-header,
  .progress-card,
  .card,
  .step-panel,
  .error-text,
  .success-banner {
    animation: none;
  }

  .progress-fill {
    transition: none;
  }

  .card:hover,
  .attendee-row:hover,
  .continue-btn:hover,
  .back-btn:active {
    transform: none;
  }
}
</style>
