<template>
	<aside class="lesson-sidebar pa-scroll">
		<!-- Where you are: the course, and how much of it is behind you. -->
		<div class="lesson-sidebar-head">
			<div class="text-xs font-semibold uppercase tracking-widest text-ink-gray-5">
				{{ __('Course') }}
			</div>
			<div class="mt-1.5 text-lg font-semibold leading-6 text-ink-gray-9">
				{{ title }}
			</div>

			<div v-if="showProgress" class="mt-4">
				<div class="flex items-baseline justify-between text-sm">
					<span class="text-ink-gray-7">
						{{
							__('{0} of {1} classes done').format(doneCount, lessonCount)
						}}
					</span>
					<span class="font-semibold text-ink-gray-9">
						{{ Math.ceil(progress) }}%
					</span>
				</div>
				<div class="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-gray-3">
					<div
						class="h-1.5 rounded-full bg-surface-gray-7 transition-all duration-500"
						:style="{ width: `${Math.min(Math.ceil(progress), 100)}%` }"
					></div>
				</div>
			</div>
		</div>

		<div class="space-y-3 p-3">
			<section
				v-for="chapter in outline.data"
				:key="chapter.name"
				class="lesson-sidebar-chapter"
			>
				<button
					type="button"
					class="flex w-full items-center gap-3 px-3 py-3 text-left"
					:aria-expanded="isOpen(chapter)"
					@click="toggle(chapter)"
				>
					<span class="lesson-sidebar-number">{{ chapter.idx }}</span>
					<span class="min-w-0 flex-1">
						<span
							class="block truncate text-base font-medium leading-5 text-ink-gray-9"
						>
							{{ chapter.title }}
						</span>
						<span
							v-if="!chapter.is_scorm_package"
							class="mt-0.5 block text-xs text-ink-gray-5"
						>
							{{ chapterSummary(chapter) }}
						</span>
					</span>
					<ChevronDown
						v-if="!chapter.is_scorm_package"
						class="h-4 w-4 shrink-0 stroke-1.5 text-ink-gray-5 transition-transform duration-200"
						:class="{ 'rotate-180': isOpen(chapter) }"
					/>
					<ArrowRight
						v-else
						class="h-4 w-4 shrink-0 stroke-1.5 text-ink-gray-5"
					/>
				</button>

				<ol
					v-if="!chapter.is_scorm_package && isOpen(chapter)"
					class="pb-2"
				>
					<li v-for="lesson in chapter.lessons" :key="lesson.name">
						<!-- Locked by the batch schedule: shown, but not a link. -->
						<div
							v-if="lesson.is_locked"
							class="lesson-sidebar-row cursor-not-allowed"
							:title="lesson.lock_reason || __('Locked')"
						>
							<span class="lesson-sidebar-mark is-locked">
								<Lock class="h-3 w-3 stroke-2" />
							</span>
							<span class="min-w-0 flex-1">
								<span class="block text-sm leading-5 text-ink-gray-5">
									{{ lesson.title }}
								</span>
								<span class="block text-xs text-ink-gray-5">
									{{
										lesson.opens_at
											? __('Opens {0}').format(formatOpens(lesson.opens_at))
											: __('Not open yet')
									}}
								</span>
							</span>
						</div>

						<router-link
							v-else
							:to="lessonRoute(lesson)"
							class="lesson-sidebar-row"
							:class="{ 'is-current': isCurrent(lesson) }"
							:aria-current="isCurrent(lesson) ? 'page' : undefined"
						>
							<span
								class="lesson-sidebar-mark"
								:class="{
									'is-done': lesson.is_complete && showProgress,
									'is-current': isCurrent(lesson),
								}"
							>
								<Check
									v-if="lesson.is_complete && showProgress"
									class="h-3 w-3 stroke-[3]"
								/>
							</span>
							<span class="min-w-0 flex-1">
								<span
									class="block text-sm leading-5"
									:class="
										isCurrent(lesson)
											? 'font-semibold text-ink-gray-9'
											: 'text-ink-gray-8'
									"
								>
									{{ lesson.title }}
								</span>
								<span class="flex items-center gap-1 text-xs text-ink-gray-5">
									<component :is="kind(lesson).icon" class="h-3 w-3 stroke-1.5" />
									{{ kind(lesson).label }}
								</span>
							</span>
						</router-link>
					</li>
				</ol>
			</section>
		</div>
	</aside>
</template>
<script setup>
import { createResource } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import {
	ArrowRight,
	Check,
	ChevronDown,
	FileText,
	HelpCircle,
	Lock,
	MonitorPlay,
} from 'lucide-vue-next'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs/esm'
import { showsCourseProgress } from '@/utils'

/* The lesson page's side panel: the course outline as a reading list, with the
   class you are on marked and the ones you have finished ticked. A leaner
   sibling of CourseOutline, which also has to serve the course editor. */
const props = defineProps({
	courseName: {
		type: String,
		required: true,
	},
	title: {
		type: String,
		default: '',
	},
	// Whether the viewer is enrolled, i.e. has progress worth showing.
	enrolled: {
		type: Boolean,
		default: false,
	},
	progress: {
		type: Number,
		default: 0,
	},
})

const route = useRoute()
const router = useRouter()

const showProgress = computed(() => props.enrolled && showsCourseProgress())

const outline = createResource({
	url: 'lms.lms.utils.get_course_outline',
	makeParams() {
		return { course: props.courseName, progress: props.enrolled }
	},
	auto: true,
})

watch(
	() => [props.courseName, props.progress, props.enrolled],
	() => outline.reload(),
)

const lessons = computed(() =>
	(outline.data || []).flatMap((chapter) => chapter.lessons || []),
)
const lessonCount = computed(() => lessons.value.length)
const doneCount = computed(
	() => lessons.value.filter((lesson) => lesson.is_complete).length,
)

// Chapters the reader has opened or closed by hand; the rest follow the route.
const toggled = ref({})

const isOpen = (chapter) => {
	if (chapter.name in toggled.value) return toggled.value[chapter.name]
	return chapter.idx == route.params.chapterNumber
}

const toggle = (chapter) => {
	if (chapter.is_scorm_package) {
		router.push({
			name: 'SCORMChapter',
			params: { courseName: props.courseName, chapterName: chapter.name },
		})
		return
	}
	toggled.value = { ...toggled.value, [chapter.name]: !isOpen(chapter) }
}

const chapterSummary = (chapter) => {
	const total = chapter.lessons?.length || 0
	if (!showProgress.value) {
		return total == 1 ? __('1 class') : __('{0} classes').format(total)
	}
	const done = chapter.lessons.filter((lesson) => lesson.is_complete).length
	return __('{0} of {1} done').format(done, total)
}

const isCurrent = (lesson) => {
	const [chapterNumber, lessonNumber] = lesson.number.split('.')
	return (
		route.params.chapterNumber == chapterNumber &&
		route.params.lessonNumber == lessonNumber
	)
}

const lessonRoute = (lesson) => {
	const [chapterNumber, lessonNumber] = lesson.number.split('.')
	return {
		name: 'Lesson',
		params: { courseName: props.courseName, chapterNumber, lessonNumber },
	}
}

const kind = (lesson) => {
	if (lesson.icon === 'icon-youtube')
		return { icon: MonitorPlay, label: __('Video') }
	if (lesson.icon === 'icon-quiz') return { icon: HelpCircle, label: __('Quiz') }
	return { icon: FileText, label: __('Lesson') }
}

const formatOpens = (value) => dayjs(value).format('D MMM, h:mm A')
</script>
<style scoped>
.lesson-sidebar {
	position: sticky;
	top: 3.2rem;
	height: calc(100vh - 3.2rem);
	overflow-y: auto;
	background: var(--pa-wash);
}

.lesson-sidebar-head {
	padding: 1.25rem 1.25rem 1.1rem;
	background: var(--surface-white);
	border-bottom: 1px solid var(--pa-hairline);
}

.lesson-sidebar-chapter {
	overflow: hidden;
	border: 1px solid var(--pa-hairline);
	border-radius: 0.75rem;
	background: var(--surface-white);
}

.lesson-sidebar-number {
	display: grid;
	place-items: center;
	flex: none;
	width: 1.75rem;
	height: 1.75rem;
	border-radius: 0.5rem;
	background: var(--pa-wash);
	color: var(--ink-gray-8);
	font-size: 0.8125rem;
	font-weight: 600;
}

.lesson-sidebar-row {
	position: relative;
	display: flex;
	align-items: flex-start;
	gap: 0.75rem;
	margin: 0 0.5rem;
	padding: 0.5rem 0.625rem;
	border-radius: 0.5rem;
	transition: background-color var(--pa-fast, 160ms) var(--pa-ease, ease);
}

a.lesson-sidebar-row:hover {
	background: var(--pa-wash);
}

a.lesson-sidebar-row:focus-visible {
	outline: 2px solid var(--surface-gray-7);
	outline-offset: -2px;
}

.lesson-sidebar-row.is-current {
	background: var(--pa-wash);
}

/* The status mark: empty ring to do, filled ring for the class you are on,
   solid tick when done, padlock when the schedule has not opened it. */
.lesson-sidebar-mark {
	display: grid;
	place-items: center;
	flex: none;
	width: 1.125rem;
	height: 1.125rem;
	margin-top: 0.0625rem;
	border: 1.5px solid var(--outline-gray-3, #c7c7c7);
	border-radius: 9999px;
	color: var(--ink-white, #fff);
}

.lesson-sidebar-mark.is-current {
	border-color: var(--surface-gray-7);
	box-shadow: inset 0 0 0 3px var(--surface-white),
		inset 0 0 0 9px var(--surface-gray-7);
}

.lesson-sidebar-mark.is-done {
	border-color: var(--surface-gray-7);
	background: var(--surface-gray-7);
	box-shadow: none;
}

.lesson-sidebar-mark.is-locked {
	border-color: transparent;
	color: var(--ink-gray-5);
}
</style>
