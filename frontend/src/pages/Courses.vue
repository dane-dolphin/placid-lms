<template>
	<header
		class="sticky flex items-center justify-between top-0 z-10 border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="breadcrumbs" />
		<router-link
			v-if="canCreateCourse()"
			:to="{
				name: 'CourseForm',
				params: { courseName: 'new' },
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
			<div class="flex items-center space-x-2">
				<Button
					v-if="!showLevelPicker && levels.length"
					variant="ghost"
					:label="__('Back to levels')"
					@click="clearLevel()"
				>
					<template #icon>
						<ChevronLeft class="h-4 w-4 stroke-1.5" />
					</template>
				</Button>
				<div class="text-lg text-ink-gray-9 font-semibold">
					{{ heading }}
				</div>
			</div>
			<div
				v-if="showCourseGrid"
				class="flex flex-col space-y-3 lg:space-y-0 lg:flex-row lg:items-center lg:space-x-4"
			>
				<TabButtons :buttons="courseTabs" v-model="currentTab" class="w-fit" />

				<div class="grid grid-cols-2 gap-2">
					<FormControl
						v-model="title"
						:placeholder="__('Search by Title')"
						type="text"
						class="w-full lg:min-w-0 lg:w-32 xl:w-40"
						@input="updateCourses()"
					/>
					<div class="w-full lg:min-w-0 lg:w-32 xl:w-40">
						<Select
							v-if="categories.length"
							v-model="currentCategory"
							:options="categories"
							:placeholder="__('Category')"
							@change="updateCourses()"
						/>
					</div>
				</div>

				<!-- <FormControl
					v-model="certification"
					:label="__('Certification')"
					type="checkbox"
					@change="updateCourses()"
				/> -->
			</div>
		</div>
		<template v-if="showLevelPicker">
			<div
				class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-6"
			>
				<div v-for="level in levels" :key="level.name" @click="selectLevel(level.name)">
					<LevelCard :level="level" />
				</div>
			</div>
			<div class="flex justify-center mt-8">
				<Button variant="subtle" @click="selectLevel(ALL_LEVELS)">
					{{ __('Browse all courses') }}
				</Button>
			</div>
		</template>

		<template v-else-if="showCourseGrid">
			<div
				v-if="courses.data?.length"
				class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-8"
			>
				<router-link
					v-for="course in courses.data"
					:to="{ name: 'CourseDetail', params: { courseName: course.name } }"
				>
					<CourseCard :course="course" />
				</router-link>
			</div>
			<EmptyState v-else-if="!courses.list.loading" type="Courses" />
			<div
				v-if="!courses.list.loading && courses.hasNextPage"
				class="flex justify-center mt-5"
			>
				<Button @click="courses.next()">
					{{ __('Load More') }}
				</Button>
			</div>
		</template>
	</div>
</template>
<script setup>
import {
	Breadcrumbs,
	Button,
	call,
	createListResource,
	FormControl,
	Select,
	TabButtons,
	usePageMeta,
} from 'frappe-ui'
import { computed, inject, onMounted, ref, watch } from 'vue'
import { ChevronLeft, Plus } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import { canCreateCourse } from '@/utils'
import CourseCard from '@/components/CourseCard.vue'
import LevelCard from '@/components/LevelCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import router from '../router'

// Sentinel for "skip the level screen and show everything". Distinct from null,
// which means "no choice made yet, show the picker" - without the distinction,
// Browse all courses would bounce straight back to the picker on the next render.
const ALL_LEVELS = '__all__'

const user = inject('$user')
const dayjs = inject('$dayjs')
const start = ref(0)
const pageLength = ref(30)
const categories = ref([])
const currentCategory = ref(null)
const title = ref('')
const certification = ref(false)
const filters = ref({})
const is_student = computed(() => user.data?.is_student)
const is_staff = computed(
  () => user.data?.is_moderator || user.data?.is_instructor || user.data?.is_evaluator
)

const currentTab = ref(is_student.value ? 'Enrolled' : 'Published')
const { brand } = sessionStore()
const courseCount = ref(0)
const levels = ref([])
const currentLevel = ref(null)
const levelsLoaded = ref(false)

onMounted(() => {
	setFiltersFromQuery()
	fetchLevels()
	updateCourses()
	getCourseCount()
	categories.value = [
		{
			label: '',
			value: null,
		},
	]
})

// A site with no Course Level records behaves exactly as before: `levels` stays
// empty, `showLevelPicker` is false, and the flat course grid renders on load.
const fetchLevels = () => {
	call('placid_drip.api.course_levels.get_course_levels')
		.then((data) => {
			levels.value = data || []
		})
		.catch(() => {
			// Older backend, or the patch has not run. Fall back to the flat list
			// rather than leaving the page stuck on an empty picker.
			levels.value = []
		})
		.finally(() => {
			levelsLoaded.value = true
		})
}

const showLevelPicker = computed(
	() => levelsLoaded.value && levels.value.length > 0 && currentLevel.value === null
)

// Holds the flat grid back only while the picker might still replace it, so the
// page does not render a full course list and then yank it away a tick later.
// A deep link that already names a level skips the wait entirely.
const showCourseGrid = computed(
	() =>
		!showLevelPicker.value && (currentLevel.value !== null || levelsLoaded.value)
)

const heading = computed(() => {
	if (showLevelPicker.value) return __('Choose a level')
	if (!currentLevel.value || currentLevel.value === ALL_LEVELS)
		return __('All Courses')

	const level = levels.value.find((l) => l.name === currentLevel.value)
	return level ? level.level_name : currentLevel.value
})

const selectLevel = (levelName) => {
	currentLevel.value = levelName
	updateCourses()
}

const clearLevel = () => {
	currentLevel.value = null
	updateCourses()
}

const setFiltersFromQuery = () => {
	let queries = new URLSearchParams(location.search)
	title.value = queries.get('title') || ''
	currentCategory.value = queries.get('category') || null
	certification.value = queries.get('certification') || false
	currentLevel.value = queries.get('level') || null
}

const courses = createListResource({
	doctype: 'LMS Course',
	url: 'lms.lms.utils.get_courses',
	cache: ['courses', user.data?.name],
	pageLength: pageLength.value,
	start: start.value,
	onSuccess(data) {
		setCategories(data)
	},
})

const setCategories = (data) => {
	let allCategories = data.map((course) => course.category)
	allCategories = allCategories.filter(
		(category, index) => allCategories.indexOf(category) === index && category
	)
	if (categories.value.length <= allCategories.length) {
		updateCategories(data)
	}
}

const isPersonaCaptured = async () => {
	let persona = await call('frappe.client.get_single_value', {
		doctype: 'LMS Settings',
		field: 'persona_captured',
	})
	return persona
}

// const identifyUserPersona = async () => {
// 	if (user.data?.is_system_manager && !user.data?.developer_mode) {
// 		let personaCaptured = await isPersonaCaptured()
// 		if (personaCaptured) return
// 		if (!courseCount.value) {
// 			router.push({
// 				name: 'PersonaForm',
// 			})
// 		}
// 	}
// }

const getCourseCount = () => {
	if (!user.data) return

	call('frappe.client.get_count', {
		doctype: 'LMS Course',
	}).then((data) => {
		courseCount.value = data
		//identifyUserPersona()
	})
}

const updateCourses = () => {
	updateFilters()
	courses.update({
		filters: filters.value,
	})
	courses.reload()
}

const updateFilters = () => {
	updateLevelFilter()
	updateCategoryFilter()
	updateTitleFilter()
	updateCertificationFilter()
	updateTabFilter()
	// updateStudentFilter()
	setQueryParams()
}

const updateLevelFilter = () => {
	// The `__unassigned__` name that get_course_levels emits for the null bucket is
	// passed through untouched - the get_courses override turns it into an
	// "is not set" filter server-side, where the null actually lives.
	if (currentLevel.value && currentLevel.value !== ALL_LEVELS) {
		filters.value['level'] = currentLevel.value
	} else {
		delete filters.value['level']
	}
}

const updateCategoryFilter = () => {
	if (currentCategory.value) {
		filters.value['category'] = currentCategory.value
	} else {
		delete filters.value['category']
	}
}

const updateTitleFilter = () => {
	if (title.value) {
		filters.value['title'] = ['like', `%${title.value}%`]
	} else {
		delete filters.value['title']
	}
}

const updateCertificationFilter = () => {
	if (certification.value) {
		filters.value['certification'] = 1
	} else {
		delete filters.value['certification']
	}
}

const updateTabFilter = () => {
  // remove old concepts
  delete filters.value['live']
  delete filters.value['created']
  delete filters.value['published_on']
  delete filters.value['upcoming']

  // clear relevant filters first
  delete filters.value['enrolled']
  delete filters.value['published']

  if (!user.data) {
    // guests: published only
    filters.value['published'] = 1
    return
  }

  // STUDENTS AND FACILITATORS
  // Keyed on who may see drafts, not on is_student: a facilitator is not a
  // student but now gets the same two tabs, and the old is_student check sent
  // them into the staff branch below, where "Enrolled" matched nothing and
  // silently applied no filter at all.
  if (!can_see_unpublished.value) {
    filters.value['published'] = 1

    if (currentTab.value === 'Enrolled') {
      filters.value['enrolled'] = 1
    }
    return
  }

  // MODERATOR
  if (currentTab.value === 'Published') {
    filters.value['published'] = 1
  } else if (currentTab.value === 'Unpublished') {
    filters.value['published'] = 0
  }
  // "All" = no published filter
}

const updateStudentFilter = () => {
  // Do nothing now — tab logic fully controls it
}

const setQueryParams = () => {
	let queries = new URLSearchParams(location.search)
	let filterKeys = {
		title: title.value,
		category: currentCategory.value,
		certification: certification.value,
		level: currentLevel.value,
	}

	Object.keys(filterKeys).forEach((key) => {
		if (filterKeys[key]) {
			queries.set(key, filterKeys[key])
		} else {
			queries.delete(key)
		}
	})

	let queryString = ''
	if (queries.toString()) {
		queryString = `?${queries.toString()}`
	}

	history.replaceState({}, '', `${location.pathname}${queryString}`)
}

const updateCategories = (data) => {
	data.forEach((course) => {
		if (
			course.category &&
			!categories.value.find((category) => category.value === course.category)
		)
			categories.value.push({
				label: course.category,
				value: course.category,
			})
	})
}

watch(currentTab, () => {
	updateCourses()
})

// Authors and admins may see drafts; facilitators may not. `is_instructor` is
// LMS's flag for the Course Creator role (lms/lms/api.py), not for teaching a
// batch - a Batch Evaluator sets `is_evaluator`, which is intentionally absent
// here. Mirrors DRAFT_VISIBLE_ROLES in the get_courses override, which is what
// actually enforces it; this only stops the UI offering an empty tab.
const can_see_unpublished = computed(
  () => user.data?.is_moderator || user.data?.is_instructor || user.data?.is_system_manager
)

const courseTabs = computed(() => {
  if (!user.data) return [{ label: __('Published') }]

  if (can_see_unpublished.value) {
    return [
      { label: __('All') },
      { label: __('Published') },
      { label: __('Unpublished') },
    ]
  }

  return [{ label: __('Published') }, { label: __('Enrolled') }]
})

const breadcrumbs = computed(() => {
	const crumbs = [
		{
			label: __('Courses'),
			route: { name: 'Courses' },
		},
	]

	if (!showLevelPicker.value && levels.value.length) {
		crumbs.push({
			label: heading.value,
			route: { name: 'Courses', query: { level: currentLevel.value } },
		})
	}

	return crumbs
})

usePageMeta(() => {
	return {
		title: __('Courses'),
		icon: brand.favicon,
	}
})
</script>
