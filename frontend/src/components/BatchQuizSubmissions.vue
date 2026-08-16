<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { createResource } from 'frappe-ui'
import Autocomplete from '@/components/Controls/Autocomplete.vue'

const props = defineProps({
  batch: { type: Object, required: true },
})

const emit = defineEmits(['open-submission'])

const showModal = ref(false)
const selectedSubmission = ref('')

const detail = createResource({
  url: 'frappe.client.get',
  makeParams() {
    return {
      doctype: 'LMS Quiz Submission',
      name: selectedSubmission.value,
    }
  },
  auto: false,
})

const openSubmissionModal = (submissionName) => {
  selectedSubmission.value = submissionName
  showModal.value = true
  detail.reload()
}

const closeModal = () => {
  showModal.value = false
  selectedSubmission.value = ''
  detail.reset?.()
}

/** 1) Course options (same style as BatchCourseLocks.vue) */
const courseOptions = computed(() => {
  const courses = props.batch?.courses || []
  return courses
    .filter((c) => c?.course)
    .map((c) => ({
      value: c.course,
      label: c.title || c.course_title || c.course,
    }))
})

const courseName = ref('')
const quizName = ref('')
const quizSearch = ref('')
const quizOpen = ref(false)

const formatSubmitted = (v) => {
  if (!v) return '-'

  // Handles strings like "2026-02-06 21:30:25.586091"
  // or Date-ish values returned by frappe-ui
  const s = String(v)

  // if it has microseconds: split off the fractional seconds
  const noMicros = s.includes('.') ? s.split('.')[0] : s

  // keep "YYYY-MM-DD HH:MM:SS" only
  // (also works if it comes as ISO with "T")
  return noMicros.replace('T', ' ').slice(0, 16)
}

/** 2) Load quizzes for selected course */
const quizzes = createResource({
  url: 'placid_drip.api.quiz_reports.get_course_quizzes',
  makeParams() {
    return { course: courseName.value }
  },
  auto: false,
})

/** 3) Load submissions for selected quiz, restricted to batch */
const submissions = createResource({
  url: 'placid_drip.api.quiz_reports.get_batch_quiz_submissions',
  makeParams() {
    return { batch: props.batch.name, quiz: quizName.value }
  },
  auto: false,
})

/** Reset + fetch on course change */
watch(courseName, async (v) => {
  quizName.value = ''
  quizSearch.value = ''
  quizOpen.value = false
  submissions.reset?.()
  quizzes.reset?.()
  if (!v) return
  quizzes.reload()
})

const normalizedQuizzes = computed(() => {
  const list = quizzes.data || []
  return (list || []).map((x) => ({
    name: x.quiz,                    // <-- map quiz -> name
    title: x.quiz_title || x.quiz,   // <-- map quiz_title -> title
    lesson: x.lesson,
    lesson_title: x.lesson_title,
    source: x.source,
  }))
})

/** Filter quizzes for search */
const filteredQuizzes = computed(() => {
  const list = normalizedQuizzes.value
  const q = (quizSearch.value || '').trim().toLowerCase()
  if (!q) return list
  return list.filter((x) => {
    const name = (x.name || '').toLowerCase()
    const title = (x.title || '').toLowerCase()
    return name.includes(q) || title.includes(q)
  })
})

const selectQuiz = (q) => {
  quizName.value = q.name
  quizSearch.value = q.title || q.name
  quizOpen.value = false
  submissions.reload()
}

const clearQuiz = () => {
  quizName.value = ''
  quizSearch.value = ''
  quizOpen.value = false
  submissions.reset?.()
}

/** close dropdown on outside click */
const onDocClick = () => (quizOpen.value = false)
onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div class="text-lg font-semibold text-ink-gray-9">
        {{ __('Quiz Submissions') }}
      </div>
    </div>

    <!-- selectors row -->
    <div class="flex flex-col md:flex-row gap-3 md:items-end">
      <!-- Course selector (exactly your pattern) -->
      <div class="min-h-[74px]">
        <div class="text-xs text-ink-gray-5 mb-1">{{ __('Course') }}</div>
        <Autocomplete
          class="w-[360px]"
          :modelValue="courseName"
          :options="courseOptions"
          :placeholder="__('Select course')"
          @update:modelValue="(opt) => (courseName = opt?.value || '')"
        />
      </div>

      <!-- Quiz searchable dropdown -->
      <div class="w-[420px] min-h-[74px]">
        <div class="text-xs text-ink-gray-5 mb-1">{{ __('Quiz') }}</div>

        <div class="relative" @click.stop>
          <input
            v-model="quizSearch"
            class="border rounded px-2 py-1 text-sm w-full"
            :disabled="!courseName || quizzes.loading"
            :placeholder="!courseName ? __('Select course first') : __('Search quiz...')"
            @focus="quizOpen = true"
          />

          <div
            v-if="quizOpen && courseName"
            class="absolute z-10 mt-1 w-full bg-white border rounded shadow max-h-64 overflow-auto"
          >
            <button
              v-for="q in filteredQuizzes"
              :key="q.name"
              type="button"
              class="w-full text-left px-2 py-2 text-sm hover:bg-surface-gray-1"
              @click="selectQuiz(q)"
            >
              <div class="font-medium text-ink-gray-9">{{ q.title || q.name }}</div>
              <div class="text-xs text-ink-gray-5">{{ q.name }}</div>
            </button>
            <div v-if="!filteredQuizzes.length" class="px-2 py-2 text-sm text-ink-gray-6">
              {{ quizzes.loading ? __('Loading...') : __('No quizzes found') }}
            </div>
          </div>
        </div>

        <div v-if="quizName" class="text-xs text-ink-gray-6 mt-1">
          {{ __('Selected') }}:
          <span class="font-medium">{{ quizSearch }}</span>
          <button class="ml-2 underline" type="button" @click="clearQuiz">
            {{ __('Clear') }}
          </button>
        </div>
      </div>
    </div>

    <!-- loading states -->
    <div v-if="quizzes.loading" class="text-sm text-ink-gray-6">
      {{ __('Loading quizzes...') }}
    </div>
    <div v-else-if="quizName && submissions.loading" class="text-sm text-ink-gray-6">
      {{ __('Loading submissions...') }}
    </div>

    <!-- table -->
    <div v-else-if="quizName" class="border rounded-md overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-surface-gray-2 text-ink-gray-8">
          <tr>
            <th class="text-left px-3 py-2 border-b">{{ __('Student') }}</th>
            <th class="text-left px-3 py-2 border-b">{{ __('Score') }}</th>
            <th class="text-left px-3 py-2 border-b">{{ __('%') }}</th>
            <th class="text-left px-3 py-2 border-b">{{ __('Status') }}</th>
            <th class="text-left px-3 py-2 border-b">{{ __('Submitted') }}</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="r in (submissions.data || [])"
            :key="r.name"
            class="hover:bg-surface-gray-1 cursor-pointer"
            @click="openSubmissionModal(r.name)"
          >
            <td class="px-3 py-2 border-b">{{ r.member_name || r.member }}</td>
            <td class="px-3 py-2 border-b">{{ r.score ?? '-' }}</td>
            <td class="px-3 py-2 border-b">{{ r.percentage ?? '-' }}</td>
            <td class="px-3 py-2 border-b">{{ r.pass ? __('Pass') : __('Fail') }}</td>
            <td class="px-3 py-2 border-b">
              {{ formatSubmitted(r.modified || r.creation) }}
            </td>
          </tr>

          <tr v-if="(submissions.data || []).length === 0">
            <td class="px-3 py-3 text-ink-gray-6" colspan="5">
              {{ __('No submissions yet.') }}
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Submission Detail Modal -->
      <div
        v-if="showModal"
        class="fixed inset-0 z-50 bg-black/30 flex items-center justify-center p-6"
        @click.self="closeModal"
      >
        <div class="bg-white w-full max-w-4xl rounded-lg shadow-lg overflow-hidden">
          <div class="flex items-center justify-between px-4 py-3 border-b">
            <div class="font-semibold text-ink-gray-9">
              {{ __('Quiz Submission') }}: {{ selectedSubmission }}
            </div>
            <button class="text-sm underline" type="button" @click="closeModal">
              {{ __('Close') }}
            </button>
          </div>

          <!-- Scroll container -->
          <div class="p-4 max-h-[75vh] overflow-auto">
            <div v-if="detail.loading" class="text-sm text-ink-gray-6">
              {{ __('Loading...') }}
            </div>

            <div v-else-if="detail.data">
              <!-- Summary -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4 text-sm">
                <div><span class="text-ink-gray-6">{{ __('Student') }}:</span> {{ detail.data.member_name || detail.data.member }}</div>
                <div><span class="text-ink-gray-6">{{ __('Quiz') }}:</span> {{ detail.data.quiz_title || detail.data.quiz }}</div>
                <div><span class="text-ink-gray-6">{{ __('Score') }}:</span> {{ detail.data.score }} / {{ detail.data.score_out_of }}</div>
                <div><span class="text-ink-gray-6">{{ __('Percentage') }}:</span> {{ detail.data.percentage }}%</div>
              </div>

              <!-- Results table -->
              <div class="border rounded-md overflow-hidden">
                <table class="w-full text-sm">
                  <thead class="bg-surface-gray-2 text-ink-gray-8">
                    <tr>
                      <th class="text-left px-3 py-2 border-b">{{ __('Question') }}</th>
                      <th class="text-left px-3 py-2 border-b">{{ __('Answer') }}</th>
                      <th class="text-left px-3 py-2 border-b">{{ __('Marks') }}</th>
                      <th class="text-left px-3 py-2 border-b">{{ __('Correct') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in (detail.data.result || [])" :key="row.name">
                      <td class="px-3 py-2 border-b">{{ row.question }}</td>
                      <td class="px-3 py-2 border-b">{{ row.answer }}</td>
                      <td class="px-3 py-2 border-b">{{ row.marks }} / {{ row.marks_out_of }}</td>
                      <td class="px-3 py-2 border-b">
                        {{ row.is_correct ? __('Yes') : __('No') }}
                      </td>
                    </tr>
                    <tr v-if="!(detail.data.result || []).length">
                      <td class="px-3 py-3 text-ink-gray-6" colspan="4">
                        {{ __('No result rows.') }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Debug (optional) -->
              <!--
              <pre class="text-xs bg-surface-gray-2 rounded p-3 mt-4 overflow-auto">
      {{ JSON.stringify(detail.data, null, 2) }}
              </pre>
              -->
            </div>

            <div v-else class="text-sm text-ink-gray-6">
              {{ __('No data found.') }}
            </div>
          </div>
        </div>
      </div>

    </div>

    <div v-else class="text-sm text-ink-gray-6">
      {{ __('Select a course and quiz to view submissions.') }}
    </div>
  </div>
</template>