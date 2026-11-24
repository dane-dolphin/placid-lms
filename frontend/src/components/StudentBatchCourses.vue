<template>
	<div>
		<div v-if="batches.data?.length" class="space-y-12">
			<section v-for="batch in batches.data" :key="batch.name">
				<div class="mb-4 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
					<router-link
						:to="{ name: 'Batch', params: { batchName: batch.name } }"
						class="text-lg font-semibold text-ink-gray-9 underline-offset-2 hover:underline"
					>
						{{ batch.title }}
					</router-link>
					<span class="text-sm text-ink-gray-6">
						{{
							batch.courses.length == 1
								? __('1 course')
								: __('{0} courses').format(batch.courses.length)
						}}
					</span>
				</div>
				<div
					v-if="batch.courses.length"
					class="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4"
				>
					<router-link
						v-for="course in batch.courses"
						:key="course.name"
						:to="{
							name: 'BatchCourse',
							params: { batchName: batch.name, courseName: course.name },
						}"
					>
						<CourseCard :course="course" />
					</router-link>
				</div>
				<div v-else class="text-sm italic text-ink-gray-5">
					{{ __('Your facilitator has not added courses to this batch yet.') }}
				</div>
			</section>
		</div>

		<div
			v-else-if="batches.data"
			class="mx-auto mt-24 max-w-md text-center"
		>
			<GraduationCap class="mx-auto size-10 stroke-1 text-ink-gray-5" />
			<div class="mt-3 text-lg font-semibold text-ink-gray-8">
				{{ __('You are not in a batch yet') }}
			</div>
			<p class="mt-2 text-base leading-6 text-ink-gray-7">
				{{
					__(
						'Your courses appear here once you join a batch. Ask your facilitator for the join link.',
					)
				}}
			</p>
		</div>
	</div>
</template>
<script setup>
import { createResource } from 'frappe-ui'
import { GraduationCap } from 'lucide-vue-next'
import CourseCard from '@/components/CourseCard.vue'

/* A student's whole catalogue: the courses of the batches they belong to, each
   opening the batch's own page for that course rather than the public one. */
const batches = createResource({
	url: 'placid_drip.api.batch_course.get_my_batch_courses',
	auto: true,
})
</script>
