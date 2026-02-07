<template>
	<header
		class="sticky flex items-center justify-between top-0 z-10 border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="breadcrumbs" />
		<router-link
			v-if="canCreateBatch"
			:to="{
				name: 'BatchForm',
				params: { batchName: 'new' },
			}"
		>
			<Button variant="solid">
				<template #prefix>
					<Plus class="h-4 w-4 stroke-1.5" />
				</template>
				{{ __('Create') }}
			</Button>
		</router-link>
	</header>
	<div class="p-5 pb-10">
		<div
			class="flex flex-col lg:flex-row space-y-4 lg:space-y-0 lg:items-center justify-between mb-5"
		>
			<div class="text-lg text-ink-gray-9 font-semibold">
				{{ __('All Batches') }}
			</div>
			<div
				class="flex flex-col space-y-3 lg:space-y-0 lg:flex-row lg:items-center lg:space-x-4"
			>
				<TabButtons
					v-if="user.data"
					:buttons="batchTabs"
					v-model="currentTab"
					class="w-fit"
				/>
				<div class="grid grid-cols-2 gap-2">
					<FormControl
						v-model="title"
						:placeholder="__('Search by Title')"
						type="text"
						class="min-w-40 lg:min-w-0 lg:w-32 xl:w-40"
						@input="updateBatches()"
					/>
					<div class="min-w-40 lg:min-w-0 lg:w-32 xl:w-40">
						<Select
							v-if="categories.length"
							v-model="currentCategory"
							:options="categories"
							:placeholder="__('Category')"
							@change="updateBatches()"
						/>
					</div>
				</div>
<!-- 
				<FormControl
					v-model="certification"
					:label="__('Certification')"
					type="checkbox"
					@change="updateBatches()"
				/> -->
			</div>
		</div>
		<div
			v-if="(isEvaluatorOnly ? (evaluatorBatches.data || []).length : (batches.data || []).length)"
			class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5"
			>
			<router-link
				v-for="batch in (isEvaluatorOnly ? (evaluatorBatches.data || []) : (batches.data || []))"
				:key="batch.name"
				:to="{ name: 'BatchDetail', params: { batchName: batch.name } }"
			>
				<BatchCard :batch="batch" />
			</router-link>
		</div>

		<EmptyState
		v-else-if="isEvaluatorOnly ? !evaluatorBatches.loading : !batches.list.loading"
		type="Batches"
		/>

		<div
			v-if="!isEvaluatorOnly && !batches.list.loading && batches.hasNextPage"
			class="flex justify-center mt-5"
			>
			<Button @click="batches.next()">{{ __('Load More') }}</Button>
		</div>
	</div>
</template>
<script setup>
import {
  Breadcrumbs,
  Button,
  createListResource,
  createResource,
  FormControl,
  Select,
  TabButtons,
  usePageMeta,
} from 'frappe-ui'
import { computed, inject, onMounted, ref, watch } from 'vue'
import { Plus } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import BatchCard from '@/components/BatchCard.vue'
import EmptyState from '@/components/EmptyState.vue'

const user = inject('$user')
const dayjs = inject('$dayjs')
const { brand } = sessionStore()

const start = ref(0)
const pageLength = ref(20)
const categories = ref([])
const currentCategory = ref(null)
const title = ref('')
const certification = ref(false)
const filters = ref({})
const orderBy = ref('start_date')
const readOnlyMode = window.read_only_mode

const is_student = computed(() => user.data?.is_student)
const currentTab = ref(is_student.value ? 'Enrolled' : 'All')

const canCreateBatch = computed(() => {
  if (readOnlyMode) return false
  return !!(user.data?.is_moderator || user.data?.is_instructor || user.data?.is_evaluator)
})
/** ✅ 1) computed first */
const isEvaluatorOnly = computed(() => {
  if (!user.data) return false
  const isStaff = user.data.is_moderator || user.data.is_instructor
  return user.data.is_evaluator && !isStaff
})

const batchesUrl = computed(() =>
  isEvaluatorOnly.value
    ? 'placid_drip.api.evaluator_batches.get_my_evaluator_batches'
    : 'lms.lms.utils.get_batches'
)

/** ✅ 2) resources next */
const batches = createListResource({
  doctype: 'LMS Batch',
  url: 'lms.lms.utils.get_batches', // keep stable; we won’t swap this object’s url early
  cache: ['batches', user.data?.name],
  pageLength: pageLength.value,
  start: start.value,
  onSuccess(data) {
    let allCategories = (data || []).map((b) => b.category).filter(Boolean)
    allCategories = allCategories.filter((c, i) => allCategories.indexOf(c) === i)
    if (categories.value.length <= allCategories.length) updateCategories(data || [])
  },
})

const evaluatorBatches = createResource({
  url: 'placid_drip.api.evaluator_batches.get_my_evaluator_batches',
  auto: false,
})

/** ✅ 3) functions */
const setFiltersFromQuery = () => {
  const queries = new URLSearchParams(location.search)
  title.value = queries.get('title') || ''
  currentCategory.value = queries.get('category') || null
  certification.value = queries.get('certification') || false
}

const updateBatches = () => {
  updateFilters()
  // only update list resource when NOT evaluator-only
  if (!isEvaluatorOnly.value) {
    batches.update({ filters: filters.value, orderBy: orderBy.value })
    batches.reload()
  } else {
    evaluatorBatches.reload()
  }
}

const updateFilters = () => {
  if (currentCategory.value) filters.value.category = currentCategory.value
  else delete filters.value.category

  if (title.value) filters.value.title = ['like', `%${title.value}%`]
  else delete filters.value.title

  if (certification.value) filters.value.certification = 1
  else delete filters.value.certification

  // tab logic (your existing logic) – keep as-is:
  orderBy.value = 'start_date'
  if (!user.data) return

  if (currentTab.value == 'Enrolled' && is_student.value) {
    filters.value.enrolled = 1
    delete filters.value.start_date
    delete filters.value.published
    orderBy.value = 'start_date desc'
  } else if (is_student.value) {
    delete filters.value.enrolled
  } else {
    delete filters.value.start_date
    delete filters.value.published
    orderBy.value = 'start_date desc'
    if (currentTab.value == 'Upcoming') {
      filters.value.start_date = ['>=', dayjs().format('YYYY-MM-DD')]
      filters.value.published = 1
      orderBy.value = 'start_date'
    } else if (currentTab.value == 'Archived') {
      filters.value.start_date = ['<=', dayjs().format('YYYY-MM-DD')]
    } else if (currentTab.value == 'Unpublished') {
      filters.value.published = 0
    }
  }

  if (!user.data || (is_student.value && currentTab.value != 'Enrolled')) {
    filters.value.start_date = ['>=', dayjs().format('YYYY-MM-DD')]
    filters.value.published = 1
  }
}

const updateCategories = (data) => {
  data.forEach((batch) => {
    if (batch.category && !categories.value.find((c) => c.value === batch.category)) {
      categories.value.push({ label: batch.category, value: batch.category })
    }
  })
}

/** ✅ 4) watchers last */
watch(currentTab, () => updateBatches())

watch(
  () => user.data,
  (u) => {
    if (!u) return
    // initial load once user is ready
    updateBatches()
  },
  { immediate: true }
)

/** mount */
onMounted(() => {
  setFiltersFromQuery()
  categories.value = [{ label: '', value: null }]
})
</script>
