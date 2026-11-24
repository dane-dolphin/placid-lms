<template>
	<div>
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs class="h-7" :items="breadcrumbs" />
			<router-link
				v-if="page.data?.can_manage"
				:to="{ name: 'CourseDetail', params: { courseName } }"
			>
				<Button>
					<template #prefix>
						<ExternalLink class="h-4 w-4 stroke-1.5" />
					</template>
					{{ __('Open course page') }}
				</Button>
			</router-link>
		</header>

		<div v-if="page.data" class="mx-auto max-w-4xl px-5 pb-16 pt-6">
			<!-- The one thing this page is for: what the course is, and the button
			     that starts (or resumes) it. Everything else sits below. -->
			<section class="batch-course-hero rounded-lg border p-6 sm:p-8">
				<div class="text-sm font-medium text-ink-gray-6">
					<span v-if="page.data.course_count > 1">
						{{
							__('Course {0} of {1}').format(
								page.data.position,
								page.data.course_count,
							)
						}}
						<span class="mx-1.5">&middot;</span>
					</span>
					<router-link
						class="underline-offset-2 hover:underline"
						:to="{ name: 'Batch', params: { batchName }, hash: '#courses' }"
					>
						{{ page.data.batch.title }}
					</router-link>
				</div>

				<h1
					class="mt-2 text-3xl font-semibold leading-tight text-ink-gray-9 sm:text-4xl"
				>
					{{ page.data.course.title }}
				</h1>
				<p
					v-if="page.data.course.short_introduction"
					class="mt-3 max-w-2xl text-p-base leading-6 text-ink-gray-7"
				>
					{{ page.data.course.short_introduction }}
				</p>

				<div class="mt-7">
					<template v-if="resume && !resume.locked">
						<router-link :to="lessonRoute" class="inline-block w-full sm:w-auto">
							<button type="button" class="batch-course-launch">
								<Play class="h-5 w-5 fill-current" />
								<span>{{ launchLabel }}</span>
							</button>
						</router-link>
						<div class="mt-2.5 text-sm text-ink-gray-6">
							{{ resume.started ? __('Next up:') : __('Starts with:') }}
							<span class="text-ink-gray-8">{{ resume.title }}</span>
						</div>
					</template>

					<template v-else-if="resume">
						<button type="button" class="batch-course-launch" disabled>
							<Lock class="h-5 w-5" />
							<span>{{ lockedLabel }}</span>
						</button>
						<div class="mt-2.5 text-sm text-ink-gray-6">
							{{
								__(
									'Your facilitator opens classes on a schedule. This one is not open yet.',
								)
							}}
						</div>
					</template>

					<div v-else class="text-sm italic text-ink-gray-6">
						{{ __('Classes have not been added to this course yet.') }}
					</div>
				</div>

				<div
					v-if="page.data.progress !== null"
					class="mt-7 flex items-center gap-3"
				>
					<div class="h-2 flex-1 overflow-hidden rounded-full bg-surface-gray-3">
						<div
							class="h-2 rounded-full bg-surface-gray-7 transition-all duration-500"
							:style="{ width: `${page.data.progress}%` }"
						></div>
					</div>
					<div class="w-24 text-right text-sm text-ink-gray-7">
						{{ __('{0}% complete').format(page.data.progress) }}
					</div>
				</div>
			</section>

			<!-- Numbers scoped to this batch. The site-wide enrolment count that the
			     public course page shows is deliberately absent. -->
			<dl
				class="mt-5 grid grid-cols-1 divide-y rounded-lg border sm:grid-cols-3 sm:divide-x sm:divide-y-0"
			>
				<div class="flex items-center gap-3 px-5 py-4">
					<Users class="h-5 w-5 stroke-1.5 text-ink-gray-6" />
					<div v-if="page.data.classmates">
						<dd class="text-lg font-semibold text-ink-gray-9">
							{{ page.data.classmates }}
						</dd>
						<dt class="text-sm text-ink-gray-6">
							{{ studentsLabel }}
						</dt>
					</div>
					<!-- An empty batch reads as a state, not as a count of zero. -->
					<div v-else>
						<dd class="text-base font-medium text-ink-gray-9">
							{{ __('No students yet') }}
						</dd>
						<dt class="text-sm text-ink-gray-6">
							{{ __('in this batch') }}
						</dt>
					</div>
				</div>
				<div class="flex items-center gap-3 px-5 py-4">
					<BookOpen class="h-5 w-5 stroke-1.5 text-ink-gray-6" />
					<div>
						<dd class="text-lg font-semibold text-ink-gray-9">
							{{ page.data.course.lessons || 0 }}
						</dd>
						<dt class="text-sm text-ink-gray-6">
							{{ page.data.course.lessons == 1 ? __('class') : __('classes') }}
						</dt>
					</div>
				</div>
				<div class="flex items-center gap-3 px-5 py-4">
					<span
						v-if="page.data.course.instructors?.length"
						class="h-6"
						:class="{
							'avatar-group overlap': page.data.course.instructors.length > 1,
						}"
					>
						<UserAvatar
							v-for="instructor in page.data.course.instructors"
							:user="instructor"
						/>
					</span>
					<div class="min-w-0">
						<dd class="truncate text-base font-medium text-ink-gray-9">
							<CourseInstructors
								v-if="page.data.course.instructors?.length"
								:instructors="page.data.course.instructors"
							/>
							<span v-else>&mdash;</span>
						</dd>
						<dt class="text-sm text-ink-gray-6">{{ __('teaching') }}</dt>
					</div>
				</div>
			</dl>

			<div class="mt-10">
				<CourseOutline
					:title="__('Classes in this course')"
					:courseName="courseName"
					:showOutline="true"
					:getProgress="page.data.progress !== null"
				/>
			</div>

			<div v-if="hasDescription" class="mt-10">
				<div class="mb-4 px-2 text-lg font-semibold leading-5 text-ink-gray-9">
					{{ __('About this course') }}
				</div>
				<div class="rounded-md border-2">
					<div
						v-html="page.data.course.description"
						class="ProseMirror prose prose-sm max-w-none !whitespace-normal px-3 py-3 prose-table:table-fixed prose-td:relative prose-td:border prose-td:border-outline-gray-2 prose-td:p-2 prose-th:relative prose-th:border prose-th:border-outline-gray-2 prose-th:bg-surface-gray-2 prose-th:p-2"
					/>
				</div>
			</div>

			<router-link
				v-if="page.data.next_course"
				:to="{
					name: 'BatchCourse',
					params: { batchName, courseName: page.data.next_course.name },
				}"
				class="mt-10 flex items-center justify-between rounded-lg border px-5 py-4 hover:bg-surface-gray-1"
			>
				<div>
					<div class="text-sm text-ink-gray-6">
						{{ __('Next course in this batch') }}
					</div>
					<div class="mt-0.5 font-medium text-ink-gray-9">
						{{ page.data.next_course.title }}
					</div>
				</div>
				<ArrowRight class="h-5 w-5 stroke-1.5 text-ink-gray-6" />
			</router-link>
		</div>

		<div
			v-else-if="page.error"
			class="mx-auto my-24 max-w-md rounded-md border px-5 py-4 text-base"
		>
			<div class="font-medium text-ink-gray-9">
				{{ __('This course is not available') }}
			</div>
			<p class="mt-2 leading-6 text-ink-gray-7">
				{{
					__(
						'It is not part of this batch, or you are not a member of the batch.',
					)
				}}
			</p>
			<router-link :to="{ name: 'Batches' }">
				<Button class="mt-4" variant="solid">{{ __('Go to my batches') }}</Button>
			</router-link>
		</div>
	</div>
</template>
<script setup>
import { Breadcrumbs, Button, createResource, usePageMeta } from 'frappe-ui'
import { computed, watch } from 'vue'
import {
	ArrowRight,
	BookOpen,
	ExternalLink,
	Lock,
	Play,
	Users,
} from 'lucide-vue-next'
import dayjs from 'dayjs/esm'
import { sessionStore } from '@/stores/session'
import CourseOutline from '@/components/CourseOutline.vue'
import CourseInstructors from '@/components/CourseInstructors.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const { brand } = sessionStore()

const props = defineProps({
	batchName: {
		type: String,
		required: true,
	},
	courseName: {
		type: String,
		required: true,
	},
})

/* A course as one batch sees it: the head-count is the batch's own, and `resume`
   is where this student's next class is (with its drip lock, if any). */
const page = createResource({
	url: 'placid_drip.api.batch_course.get_batch_course',
	makeParams() {
		return { batch: props.batchName, course: props.courseName }
	},
	auto: true,
})

watch(
	() => [props.batchName, props.courseName],
	() => page.reload(),
)

const resume = computed(() => page.data?.resume)

const lessonRoute = computed(() => ({
	name: 'Lesson',
	params: {
		courseName: props.courseName,
		chapterNumber: resume.value?.chapter || 1,
		lessonNumber: resume.value?.lesson || 1,
	},
}))

const launchLabel = computed(() => {
	if (page.data?.progress >= 100) return __('Review the course')
	return resume.value?.started
		? __('Continue learning')
		: __('Start the first class')
})

const lockedLabel = computed(() => {
	if (resume.value?.opens_at) {
		return __('Opens {0}').format(
			dayjs(resume.value.opens_at).format('D MMM YYYY, h:mm A'),
		)
	}
	return __('Not open yet')
})

// "Your batch" only makes sense to someone in it; whoever runs the batch, or an
// admin looking in, is told about "this batch" instead.
const studentsLabel = computed(() => {
	const one = page.data?.classmates == 1
	if (page.data?.is_student) {
		return one ? __('student in your batch') : __('students in your batch')
	}
	return one ? __('student in this batch') : __('students in this batch')
})

const hasDescription = computed(() => {
	const text = (page.data?.course?.description || '').replace(/<[^>]*>/g, '')
	return text.trim().length > 0
})

const breadcrumbs = computed(() => [
	{ label: __('Batches'), route: { name: 'Batches' } },
	{
		label: page.data?.batch?.title || props.batchName,
		route: {
			name: 'Batch',
			params: { batchName: props.batchName },
			hash: '#courses',
		},
	},
	{
		label: page.data?.course?.title || '',
		route: {
			name: 'BatchCourse',
			params: { batchName: props.batchName, courseName: props.courseName },
		},
	},
])

usePageMeta(() => {
	return {
		title: page.data?.course?.title,
		icon: brand.favicon,
	}
})
</script>
<style scoped>
.batch-course-hero {
	background: var(--pa-wash);
	border-color: var(--pa-hairline);
}

/* Deliberately larger than any frappe-ui Button size: this is the page's single
   primary action and should be findable from across the room on a projector. */
.batch-course-launch {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 0.75rem;
	width: 100%;
	min-height: 3.5rem;
	padding: 0 2rem;
	border-radius: 0.625rem;
	background: var(--surface-gray-7);
	color: var(--ink-white, #fff);
	font-size: 1.125rem;
	font-weight: 600;
	transition: transform var(--pa-fast, 160ms) var(--pa-ease, ease),
		box-shadow var(--pa-fast, 160ms) var(--pa-ease, ease);
}

@media (min-width: 640px) {
	.batch-course-launch {
		width: auto;
		min-width: 18rem;
	}
}

.batch-course-launch:hover:not(:disabled) {
	transform: translateY(-1px);
	box-shadow: 0 6px 18px -8px var(--surface-gray-7);
}

.batch-course-launch:focus-visible {
	outline: 2px solid var(--surface-gray-7);
	outline-offset: 3px;
}

.batch-course-launch:disabled {
	background: var(--surface-gray-3);
	color: var(--ink-gray-6);
	cursor: not-allowed;
}
</style>
