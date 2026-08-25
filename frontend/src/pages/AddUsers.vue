<template>
	<header
		class="sticky flex items-center justify-between top-0 z-10 border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="breadcrumbs" />
	</header>

	<div class="p-5 pb-10">
		<div class="w-full md:w-3/4 xl:w-1/2">
			<div class="text-lg text-ink-gray-9 font-semibold mb-1">
				{{ __('Add users') }}
			</div>
			<div class="text-sm text-ink-gray-5 mb-6">
				{{
					__(
						'Creates an account for each address and grants it the role you pick. Everyone gets an email with a link to set their own password.'
					)
				}}
			</div>

			<div
				v-if="readOnlyMode"
				class="flex items-center space-x-2 text-sm text-ink-gray-7 bg-surface-gray-1 px-3 py-2 rounded-md mb-6"
			>
				<CircleAlert class="size-4 stroke-1.5 shrink-0" />
				<span>
					{{ __('You cannot add users in read-only mode.') }}
				</span>
			</div>

			<div v-else class="flex flex-col gap-5">
				<div>
					<FormControl
						type="select"
						:label="__('Role')"
						v-model="role"
						:options="roleOptions"
					/>
					<div class="mt-1.5 text-xs text-ink-gray-5">
						{{ __(roleHint) }}
					</div>
				</div>

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
					<FormControl
						type="text"
						:label="__('Full name (optional)')"
						v-model="fullName"
						:disabled="emailCount > 1"
						:placeholder="__('Anna Smith')"
					/>
					<div class="mt-1.5 text-xs text-ink-gray-5">
						<span v-if="emailCount > 1">
							{{
								__(
									'Only used when adding one address at a time. Names are taken from the address for the rest, and everyone can correct their own.'
								)
							}}
						</span>
						<span v-else>
							{{
								__(
									'The last word is taken as the surname. Leave it blank to use a placeholder from the address.'
								)
							}}
						</span>
					</div>
				</div>

				<div>
					<Button
						variant="solid"
						:loading="submitting"
						@click="submit()"
					>
						<template #prefix>
							<UserRoundPlus class="h-4 w-4 stroke-1.5" />
						</template>
						{{ addLabel }}
					</Button>
				</div>
			</div>

			<div
				v-if="result"
				class="mt-8 rounded-md border divide-y divide-outline-gray-1"
			>
				<div
					v-for="line in resultLines"
					:key="line.label"
					class="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3 px-4 py-2.5 text-sm"
				>
					<span class="text-ink-gray-5 sm:w-2/5 shrink-0">
						{{ line.label }}
					</span>
					<span class="text-ink-gray-8 break-all">{{ line.value }}</span>
				</div>
				<div
					v-if="result.full_name_ignored"
					class="px-4 py-2.5 text-sm text-ink-gray-5"
				>
					{{
						__(
							'The name was not used, because more than one address was added at once.'
						)
					}}
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
	Breadcrumbs,
	Button,
	FormControl,
	call,
	toast,
	usePageMeta,
} from 'frappe-ui'
import { CircleAlert, UserRoundPlus } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'

const { brand } = sessionStore()
const readOnlyMode = window.read_only_mode

const emails = ref('')
const fullName = ref('')
const role = ref('Student')
const result = ref(null)
const submitting = ref(false)

// Kept in step with `ASSIGNABLE_ROLES` in placid_drip/api/user_admin.py, which
// validates against the same closed list - this select is a convenience, not the
// permission check. "Facilitator" is the Batch Evaluator role under the name the
// rest of the app shows it by.
const roleOptions = [
	{ label: __('Student'), value: 'Student' },
	{ label: __('Facilitator'), value: 'Facilitator' },
	{ label: __('Course Creator'), value: 'Course Creator' },
]

const roleHints = {
	Student: 'Can enrol in batches and work through courses.',
	Facilitator:
		'Runs batches: evaluates students, marks assignments and invites people into their own batches.',
	'Course Creator': 'Can create and edit courses.',
}

const roleHint = computed(() => roleHints[role.value] || '')

// Counted here only to decide whether the name field applies. The server parses
// the blob properly - this just needs to know "one address, or several".
const emailCount = computed(
	() =>
		emails.value
			.split(/[\s,;]+/)
			.filter((part) => part.includes('@')).length
)

const addLabel = computed(() =>
	emailCount.value > 1
		? __('Add {0} users').format(emailCount.value)
		: __('Add user')
)

const resultLines = computed(() => {
	if (!result.value) return []

	const r = result.value
	const lines = []
	const add = (label, list) => {
		if (list?.length) lines.push({ label, value: list.join(', ') })
	}

	add(__('Added as {0}').format(__(r.role)), r.created)
	add(__('Already had an account, given the role'), r.role_granted)
	add(__('Already had the role'), r.already_had_role)
	add(__('Could not be added'), r.failed)
	add(__('Not a valid address'), r.invalid)

	return lines
})

const submit = () => {
	if (!emails.value.trim()) {
		toast.error(__('Enter at least one email address.'))
		return
	}
	if (submitting.value) return

	submitting.value = true

	call('placid_drip.api.user_admin.create_users', {
		emails: emails.value,
		role: role.value,
		full_name: fullName.value,
	})
		.then((data) => {
			result.value = data

			const added = (data.created?.length || 0) + (data.role_granted?.length || 0)
			if (added) {
				toast.success(__('{0} user(s) added').format(added))
				// Cleared only on success, so a failed submit keeps the list for a
				// retry rather than making the admin paste it again.
				emails.value = ''
				fullName.value = ''
			}
			if (data.failed?.length) {
				toast.warning(
					__('{0} address(es) could not be added').format(data.failed.length)
				)
			}
		})
		.catch((err) => {
			toast.error(err.messages?.[0] || err.message || String(err))
		})
		.finally(() => {
			submitting.value = false
		})
}

const breadcrumbs = computed(() => [
	{ label: __('Add users'), route: { name: 'AddUsers' } },
])

usePageMeta(() => ({
	title: __('Add users'),
	icon: brand.favicon,
}))
</script>
