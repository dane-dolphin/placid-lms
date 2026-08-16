<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Add a course'),
			size: 'sm',
			actions: [
				{
					label: __('Submit'),
					variant: 'solid',
					onClick: (close) => addCourse(close),
				},
			],
		}"
	>
		<template #body-content>
			<Link
				doctype="LMS Course"
				v-model="course"
				:label="__('Course')"
				:required="true"
				:onCreate="
					(value, close) => {
						close()
						router.push({
							name: 'CourseForm',
							params: {
								courseName: 'new',
							},
						})
					}
				"
			/>
			<!-- A facilitator evaluates the courses in their own batch, so there is
			     nothing to pick. The server assigns them either way; hiding the field
			     stops it offering a choice it is going to overrule. -->
			<Link
				v-if="canPickEvaluator"
				doctype="Course Evaluator"
				v-model="evaluator"
				:label="__('Evaluator')"
				:onCreate="(value, close) => openSettings('Evaluators', close)"
				class="mt-4"
			/>
		</template>
	</Dialog>
</template>
<script setup>
import { Dialog, createResource, toast } from 'frappe-ui'
import { computed, ref, inject } from 'vue'
import Link from '@/components/Controls/Link.vue'
import { useOnboarding } from 'frappe-ui/frappe'
import { openSettings } from '@/utils'
import { useRouter } from 'vue-router'

const show = defineModel()
const course = ref(null)
const evaluator = ref(null)
const user = inject('$user')
const courses = defineModel('courses')
const router = useRouter()
const { updateOnboardingStep } = useOnboarding('learning')

const props = defineProps({
	batch: {
		type: String,
		default: null,
	},
})

const canPickEvaluator = computed(
	() => !!(user.data?.is_moderator || user.data?.is_system_manager)
)

const createBatchCourse = createResource({
	url: 'placid_drip.api.batch_courses.add_batch_course',
	makeParams(values) {
		return {
			batch: props.batch,
			course: course.value,
			// Sent only when the dialog actually offered the choice. The endpoint
			// ignores it for anyone else and records them as the evaluator.
			evaluator: canPickEvaluator.value ? evaluator.value : null,
		}
	},
})

const addCourse = (close) => {
	createBatchCourse.submit(
		{},
		{
			onSuccess() {
				if (user.data?.is_system_manager)
					updateOnboardingStep('add_batch_course')

				close()
				courses.value.reload()
				course.value = null
				evaluator.value = null
			},
			onError(err) {
				toast.error(err.messages?.[0] || err)
			},
		}
	)
}
</script>
