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
			<div>
				<h1 class="text-2xl text-ink-gray-9 font-semibold">
					{{ __('Batches') }}
				</h1>
				<p class="mt-1 text-base text-ink-gray-7">
					{{
						groups.length > 1 || groups[0]?.parish
							? __('Grouped by parish.')
							: __('Every group of students learning together.')
					}}
				</p>
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
		<div v-if="shownBatches.length" class="space-y-12">
			<section v-for="group in groups" :key="group.key">
				<!-- A parish's batches sit under a banner of its church. Batches with
				     no parish share one plain heading, and a list with no parishes
				     at all has no headings. -->
				<div
					v-if="group.parish"
					class="parish-banner"
					:style="
						group.cover
							? { backgroundImage: `url('${encodeURI(group.cover)}')` }
							: {}
					"
				>
					<div class="parish-banner-shade"></div>
					<div class="relative flex items-center gap-3">
						<div class="parish-banner-avatar">
							<img
								v-if="group.image"
								:src="group.image"
								class="size-full object-cover"
								alt=""
							/>
							<Church v-else class="size-5 stroke-1.5" />
						</div>
						<div class="min-w-0">
							<div class="truncate text-xl font-semibold leading-6">
								{{ group.title }}
							</div>
							<div class="text-sm opacity-85">
								{{
									group.batches.length == 1
										? __('1 batch')
										: __('{0} batches').format(group.batches.length)
								}}
							</div>
						</div>
					</div>
				</div>
				<div
					v-else-if="groups.length > 1"
					class="mb-4 text-lg font-semibold text-ink-gray-9"
				>
					{{ __('Other batches') }}
				</div>

				<div
					class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-8"
				>
					<router-link
						v-for="batch in group.batches"
						:key="batch.name"
						:to="{ name: 'BatchDetail', params: { batchName: batch.name } }"
					>
						<BatchCard :batch="batch" />
					</router-link>
				</div>
			</section>
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
import { Church, Plus } from 'lucide-vue-next'
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

/* What is on screen, and the same list cut into parishes. Order: parishes by
   name, then the batches that have none. */
const shownBatches = computed(() =>
  isEvaluatorOnly.value ? evaluatorBatches.data || [] : batches.data || []
)

const groups = computed(() => {
  const byParish = new Map()
  for (const batch of shownBatches.value) {
    const key = batch.parish || ''
    if (!byParish.has(key)) {
      byParish.set(key, {
        key: key || '__none__',
        parish: batch.parish || null,
        title: batch.parish_name || batch.parish || '',
        image: batch.parish_image,
        cover: batch.parish_cover,
        batches: [],
      })
    }
    byParish.get(key).batches.push(batch)
  }
  return [...byParish.values()].sort((a, b) => {
    if (!a.parish) return 1
    if (!b.parish) return -1
    return a.title.localeCompare(b.title)
  })
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
<style scoped>
.parish-banner {
	position: relative;
	display: flex;
	align-items: flex-end;
	min-height: 9.5rem;
	margin-bottom: 1.25rem;
	padding: 1.1rem 1.25rem;
	overflow: hidden;
	border-radius: 0.875rem;
	color: #fff;
	background-color: #315d54;
	background-image: linear-gradient(135deg, #3d7266 0%, #315d54 45%, #1f4039 100%);
	background-size: cover;
	background-position: center;
}

/* Keeps the parish name readable over any photograph. */
.parish-banner-shade {
	position: absolute;
	inset: 0;
	background: linear-gradient(
		to top,
		rgba(15, 31, 27, 0.82) 0%,
		rgba(15, 31, 27, 0.35) 45%,
		rgba(15, 31, 27, 0.05) 100%
	);
}

.parish-banner-avatar {
	display: grid;
	place-items: center;
	flex: none;
	width: 3rem;
	height: 3rem;
	overflow: hidden;
	border: 2px solid rgba(255, 255, 255, 0.9);
	border-radius: 9999px;
	background: rgba(255, 255, 255, 0.16);
}
</style>
