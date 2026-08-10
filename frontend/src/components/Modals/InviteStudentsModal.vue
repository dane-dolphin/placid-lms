<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Invite students'),
			size: 'xl',
			actions: [
				{
					label: __('Send invites'),
					variant: 'solid',
					onClick: () => submit(),
				},
			],
		}"
	>
		<template #body-content>
			<div class="flex flex-col gap-5">
				<div>
					<div class="mb-1.5 text-sm text-ink-gray-5">
						{{ __('Email addresses') }}
					</div>
					<textarea
						v-model="emails"
						rows="4"
						:placeholder="'anna@example.com, ben@example.com'"
						class="w-full rounded-md border border-outline-gray-2 bg-surface-gray-2 px-3 py-2 text-base text-ink-gray-9 placeholder-ink-gray-4 focus:border-outline-gray-3 focus:outline-none"
					/>
					<div class="mt-1 text-xs text-ink-gray-5">
						{{
							__(
								'Separate with commas, spaces or new lines. Pasting a column from a spreadsheet works.'
							)
						}}
					</div>
				</div>

				<div>
					<div class="mb-1.5 text-sm text-ink-gray-5">
						{{ __('Add them to') }}
					</div>

					<div
						v-if="batchOptions.length"
						class="max-h-40 overflow-y-auto rounded-md border border-outline-gray-2 divide-y divide-outline-gray-1"
					>
						<label
							v-for="option in batchOptions"
							:key="option.name"
							class="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-surface-gray-2"
						>
							<input
								type="checkbox"
								:value="option.name"
								v-model="selectedBatches"
								class="rounded border-outline-gray-3"
							/>
							<span class="text-sm text-ink-gray-8">
								{{ option.title || option.name }}
							</span>
						</label>
					</div>
					<div v-else class="text-sm italic text-ink-gray-5">
						{{ __('You do not facilitate any batches yet.') }}
					</div>
				</div>

				<div v-if="result" class="rounded-md bg-surface-gray-2 p-3 text-sm">
					<div v-for="line in resultLines" :key="line.label" class="flex gap-2">
						<span class="text-ink-gray-5">{{ line.label }}:</span>
						<span class="text-ink-gray-8">{{ line.value }}</span>
					</div>
				</div>
			</div>
		</template>

	</Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Dialog, call, toast } from 'frappe-ui'

const show = defineModel()

const props = defineProps({
	// When opened from inside a batch, that batch is pre-ticked. The picker is
	// still shown, so the same modal can add the same people to a second batch
	// without making them start again from the Students page.
	batch: {
		type: String,
		default: null,
	},
})

const emit = defineEmits(['invited'])

const emails = ref('')
const selectedBatches = ref([])
const batchOptions = ref([])
const result = ref(null)
const sending = ref(false)

const canSend = computed(
	() => emails.value.trim().length > 0 && selectedBatches.value.length > 0
)

const loadBatches = () => {
	call('placid_drip.api.student_invites.get_invitable_batches')
		.then((data) => {
			batchOptions.value = data || []
			if (props.batch && !selectedBatches.value.includes(props.batch)) {
				selectedBatches.value.push(props.batch)
			}
		})
		.catch(() => {
			batchOptions.value = []
		})
}

// Reload on every open rather than once on mount: a facilitator may have been
// added to a new batch since the modal was last used in this session.
watch(show, (isOpen) => {
	if (isOpen) {
		result.value = null
		loadBatches()
	}
})

const resultLines = computed(() => {
	if (!result.value) return []

	const r = result.value
	const lines = []
	const add = (label, list) => {
		if (list?.length) lines.push({ label, value: list.join(', ') })
	}

	add(__('Account created and enrolled'), r.invited)
	add(__('Enrolled (already had an account)'), r.enrolled)
	add(__('Already enrolled'), r.already_enrolled)
	add(__('Could not create an account for'), r.account_failed)
	add(__('Could not send email to'), r.email_failed)
	add(__('Not a valid address'), r.invalid)

	return lines
})

const submit = () => {
	// The action button lives in Dialog's `options`, which has no disabled state,
	// so the guard has to be here rather than on the button.
	if (!canSend.value) {
		toast.error(__('Enter at least one email address and pick a batch.'))
		return
	}
	if (sending.value) return

	sending.value = true

	call('placid_drip.api.student_invites.send_invites', {
		emails: emails.value,
		batches: selectedBatches.value,
	})
		.then((data) => {
			result.value = data
			emails.value = ''

			const sent = (data.invited?.length || 0) + (data.enrolled?.length || 0)
			if (sent) toast.success(__('{0} student(s) processed').format(sent))
			if (data.email_failed?.length) {
				toast.warning(
					__('{0} invite(s) were created but the email failed to send').format(
						data.email_failed.length
					)
				)
			}

			emit('invited')
		})
		.catch((err) => {
			toast.error(err.messages?.[0] || err.message || String(err))
		})
		.finally(() => {
			sending.value = false
		})
}
</script>
