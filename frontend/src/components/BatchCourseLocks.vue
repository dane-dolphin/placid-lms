<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div class="text-lg font-semibold text-ink-gray-9">
        {{ __('Course Locks') }}
      </div>

      <div class="flex items-center gap-2">
        <select
          v-model="courseName"
          class="border border-outline-gray-2 bg-surface-white text-ink-gray-9 rounded px-2 py-1 text-sm w-[360px] focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
        >
          <option value="" disabled>{{ __('Select course') }}</option>
          <option
            v-for="c in courseOptions"
            :key="c.value"
            :value="c.value"
          >
            {{ c.label }}
          </option>
        </select>

        <Button
          variant="solid"
          :disabled="!isDirty || saving"
          :loading="saving"
          @click="saveAll"
        >
          {{ saving ? __('Saving...') : __('Save') }}
        </Button>
      </div>
    </div>


    <div v-if="loading" class="text-sm text-ink-gray-6">
      {{ __('Loading...') }}
    </div>

    <div v-else-if="outline.length" class="space-y-6">
      <div v-for="ch in outline" :key="ch.name" class="border rounded">
        <div class="px-4 py-2 border-b font-medium">{{ ch.title }}</div>

        <div v-for="l in (ch.lessons || [])" :key="l.name"
             class="flex items-center gap-4 px-3 py-2 border-b last:border-b-0">

          <div class="min-w-0 flex-1">
            <div class="text-sm text-ink-gray-9 truncate">
              {{ l.number }} — {{ l.title }}
            </div>
          </div>

          <label class="text-sm flex items-center gap-2">
            <input
              type="checkbox"
              :checked="draftByLesson[l.name]?.force_lock === 1"
              @change="(e) => (draftByLesson[l.name].force_lock = e.target.checked ? 1 : 0)"
            />
            {{ __('Force lock') }}
          </label>

          <input
            type="date"
            class="border rounded px-2 py-1 text-sm w-[160px]
                  text-ink-gray-5
                  focus:text-ink-gray-9"
            :class="{
              'text-ink-gray-9': draftByLesson[l.name]?.available_from
            }"
            :value="draftByLesson[l.name]?.available_from || ''"
            @change="(e) => (draftByLesson[l.name].available_from = e.target.value)"
          />
        </div>
      </div>
    </div>

    <div v-else class="text-sm text-ink-gray-6">
      {{ courseName ? __('No lessons found.') : __('Select a course to begin.') }}
    </div>
  </div>
</template>
<script setup>
import { ref, computed, watch } from 'vue'
import { Button, createResource, toast } from 'frappe-ui'

const props = defineProps({
  batch: { type: Object, required: true },
})

const courseName = ref('')
const outline = ref([])
const locksByLesson = ref({})
const saving = ref(false)

const originalByLesson = ref({})
const draftByLesson = ref({})

function toDateValue(v) {
  if (!v) return ''
  return String(v).slice(0, 10)
}

const courseOptions = computed(() => {
  const courses = props.batch?.courses || []
  return courses.map((c) => ({
    value: c.course,                 // your batch.courses has `course`
    label: c.title || c.course,
  }))
})

const lockDetails = createResource({
  url: 'placid_drip.api.batch_lesson_access.get_batch_course_lock_details',
  auto: false,
  makeParams() {
    return {
      batch: props.batch.name,
      course: courseName.value,
    }
  },
  onSuccess(data) {
    // createResource returns `data` as the response message for whitelisted methods
    const msg = data || {}
    outline.value = msg.outline || []
    locksByLesson.value = msg.locks_by_lesson || {}

    const orig = {}
    for (const ch of outline.value) {
      for (const l of ch.lessons || []) {
        const lock = locksByLesson.value[l.name] || {}
        orig[l.name] = {
          available_from: toDateValue(lock.available_from),
          force_lock: Number(lock.force_lock || 0),
        }
      }
    }
    originalByLesson.value = orig
    draftByLesson.value = JSON.parse(JSON.stringify(orig))
  },
})

const saveLocks = createResource({
  url: 'placid_drip.api.batch_lesson_access.bulk_save_batch_lesson_access',
  auto: false,
  makeParams(values) {
    return values
  },
  onSuccess() {
    toast.success(__('Saved'))
    lockDetails.reload()
  },
})


// load when course changes
watch(courseName, (v) => {
  if (!v) return
  lockDetails.reload()
})

const loading = computed(() => lockDetails.loading)

const isDirty = computed(() => {
  const o = originalByLesson.value
  const d = draftByLesson.value
  for (const lesson in d) {
    if ((o[lesson]?.available_from || '') !== (d[lesson]?.available_from || '')) return true
    if (Number(o[lesson]?.force_lock || 0) !== Number(d[lesson]?.force_lock || 0)) return true
  }
  return false
})

async function saveAll() {
  if (!isDirty.value) return

  const o = originalByLesson.value
  const d = draftByLesson.value

  const changes = []
  for (const lesson in d) {
    const oldRow = o[lesson] || { available_from: '', force_lock: 0 }
    const newRow = d[lesson] || { available_from: '', force_lock: 0 }

    if (
      (oldRow.available_from || '') === (newRow.available_from || '') &&
      Number(oldRow.force_lock || 0) === Number(newRow.force_lock || 0)
    ) continue

    changes.push({
      lesson,
      available_from: newRow.available_from || null,
      force_lock: Number(newRow.force_lock || 0),
    })
  }

  saving.value = true
  try {
    await saveLocks.submit({
      batch: props.batch.name,
      course: courseName.value,
      changes,
    })
  } finally {
    saving.value = false
  }
}
</script>