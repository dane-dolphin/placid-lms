<template>
	<header
		class="sticky flex items-center justify-between top-0 z-10 border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="breadcrumbs" />
		<Button variant="solid" @click="showInviteModal = true">
			<template #prefix>
				<Plus class="h-4 w-4 stroke-1.5" />
			</template>
			{{ __('Invite students') }}
		</Button>
	</header>

	<div class="p-5 pb-10">
		<div class="flex items-center justify-between mb-5">
			<div class="text-lg text-ink-gray-9 font-semibold">
				{{ __('Students') }}
			</div>
			<div v-if="students.data?.length" class="text-sm text-ink-gray-5">
				{{ students.data.length }}
				{{ students.data.length === 1 ? __('student') : __('students') }}
			</div>
		</div>

		<div v-if="students.loading" class="text-sm italic text-ink-gray-5">
			{{ __('Loading...') }}
		</div>

		<div
			v-else-if="sortedStudents.length"
			class="pa-enter rounded-md border overflow-x-auto mb-10"
		>
			<table class="w-full text-base">
				<thead>
					<tr class="pa-table-head text-ink-gray-7">
						<th
							v-for="column in studentColumns"
							:key="column.key"
							class="pa-sort text-left font-medium px-4 py-2.5 whitespace-nowrap cursor-pointer select-none hover:text-ink-gray-9"
							@click="sortBy(column.key)"
						>
							<span class="inline-flex items-center gap-1">
								{{ __(column.label) }}
								<ArrowUp
									v-if="sortKey === column.key && sortAsc"
									class="h-3.5 w-3.5 stroke-1.5"
								/>
								<ArrowDown
									v-else-if="sortKey === column.key"
									class="h-3.5 w-3.5 stroke-1.5"
								/>
								<ChevronsUpDown
									v-else
									class="h-3.5 w-3.5 stroke-1.5 text-ink-gray-4"
								/>
							</span>
						</th>
					</tr>
				</thead>
				<tbody>
					<tr
						v-for="student in sortedStudents"
						:key="student.email"
						class="pa-row border-t"
					>
						<td class="px-4 py-2.5 text-ink-gray-9">
							{{ student.full_name || __('Not registered yet') }}
						</td>
						<td class="px-4 py-2.5 text-ink-gray-7">
							{{ student.email }}
						</td>
						<td class="px-4 py-2.5 text-ink-gray-7">
							{{ batchNames(student) || '-' }}
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div v-else class="text-sm italic text-ink-gray-5 mb-10">
			{{ __('No students yet.') }}
		</div>

		<div class="flex items-center justify-between mb-5">
			<div class="text-lg text-ink-gray-9 font-semibold">
				{{ __('Invited students') }}
			</div>
			<TabButtons :buttons="statusTabs" v-model="currentStatus" class="w-fit" />
		</div>

		<div v-if="invites.loading" class="text-sm italic text-ink-gray-5">
			{{ __('Loading...') }}
		</div>

		<div v-else-if="invites.data?.length" class="rounded-md border overflow-hidden">
			<div
				v-for="invite in invites.data"
				:key="invite.name"
				class="pa-row flex flex-col gap-2 border-b last:border-b-0 p-4 sm:flex-row sm:items-center sm:justify-between"
			>
				<div class="min-w-0">
					<div class="text-base text-ink-gray-9 truncate">
						{{ invite.email }}
					</div>
					<div class="mt-0.5 text-sm text-ink-gray-6 truncate">
						{{ batchLabel(invite) }}
					</div>
				</div>

				<div class="flex items-center gap-2 shrink-0">
					<Badge :theme="statusTheme(invite.status)" variant="subtle">
						{{ __(invite.status) }}
					</Badge>

					<!-- Only pending invites carry a link; once the account exists the
					     password-setup email is the useful one, sent via Resend. -->
					<Button
						v-if="invite.invite_url"
						variant="subtle"
						:label="__('Copy link')"
						@click="copyLink(invite)"
					/>
					<Button
						v-if="invite.status !== 'Cancelled'"
						variant="ghost"
						:label="__('Resend')"
						@click="resend(invite)"
					/>
					<Button
						v-if="invite.status === 'Pending'"
						variant="ghost"
						:label="__('Cancel')"
						@click="revoke(invite)"
					/>
				</div>
			</div>
		</div>

		<div v-else class="text-sm italic text-ink-gray-5">
			{{ __('No invites yet.') }}
		</div>
	</div>

	<InviteStudentsModal
		v-model="showInviteModal"
		@invited="
			() => {
				invites.reload()
				students.reload()
			}
		"
	/>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
	Badge,
	Breadcrumbs,
	Button,
	TabButtons,
	call,
	createResource,
	toast,
	usePageMeta,
} from 'frappe-ui'
import { ArrowDown, ArrowUp, ChevronsUpDown, Plus } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import InviteStudentsModal from '@/components/Modals/InviteStudentsModal.vue'

const { brand } = sessionStore()
const showInviteModal = ref(false)
// Accepted by default: an invite now provisions the account immediately, so it
// reaches Accepted within the same request. Pending holds only the ones where
// account creation failed, which is the exception rather than the waiting room.
const currentStatus = ref('Accepted')

const statusTabs = [
	{ label: 'Accepted' },
	{ label: 'Pending' },
	{ label: 'Cancelled' },
]

const invites = createResource({
	url: 'placid_drip.api.student_invites.get_invites',
	makeParams() {
		return { status: currentStatus.value }
	},
	auto: true,
})

// Everyone in a batch this user runs, plus everyone they invited. The endpoint
// merges the two on email, so an invite that has since been accepted appears
// once with its batch rather than twice.
const students = createResource({
	url: 'placid_drip.api.students.get_my_students',
	auto: true,
})

const studentColumns = [
	{ label: 'Name', key: 'full_name' },
	{ label: 'Email', key: 'email' },
	{ label: 'Batch', key: 'batches' },
]

const sortKey = ref('full_name')
const sortAsc = ref(true)

const sortBy = (key) => {
	if (sortKey.value === key) {
		sortAsc.value = !sortAsc.value
	} else {
		sortKey.value = key
		sortAsc.value = true
	}
}

const batchNames = (student) =>
	(student.batches || []).map((b) => b.title || b.name).join(', ')

// Sorted here rather than server-side: the roster is one page of a facilitator's
// own batches, so re-fetching on every header click would cost a round trip to
// reorder a list already in memory.
const sortedStudents = computed(() => {
	const rows = [...(students.data || [])]
	const key = sortKey.value

	const valueOf = (row) =>
		key === 'batches' ? batchNames(row) : row[key] || ''

	rows.sort((a, b) => {
		const result = valueOf(a).localeCompare(valueOf(b), undefined, {
			sensitivity: 'base',
		})
		return sortAsc.value ? result : -result
	})

	return rows
})

watch(currentStatus, () => invites.reload())

const batchLabel = (invite) =>
	(invite.batches || []).map((b) => b.title || b.name).join(', ')

const statusTheme = (status) =>
	({ Pending: 'orange', Accepted: 'green', Cancelled: 'gray' })[status] || 'gray'

const copyLink = async (invite) => {
	if (!invite.invite_url) {
		toast.error(__('This invite has no link.'))
		return
	}

	try {
		await navigator.clipboard.writeText(invite.invite_url)
		toast.success(__('Invite link copied'))
	} catch (e) {
		// clipboard is unavailable over plain http and in some embedded browsers -
		// show the link so it can still be copied by hand rather than failing.
		toast.error(invite.invite_url)
	}
}

const resend = (invite) => {
	call('placid_drip.api.student_invites.resend_invite', { name: invite.name })
		.then((data) => {
			if (!data.sent) {
				toast.warning(__('Email could not be sent.'))
			} else if (data.kind === 'password') {
				toast.success(__('Password setup email resent'))
			} else {
				toast.success(__('Invite resent'))
			}
		})
		.catch((err) => toast.error(err.messages?.[0] || err.message || String(err)))
}

const revoke = (invite) => {
	call('placid_drip.api.student_invites.revoke_invite', { name: invite.name })
		.then(() => {
			toast.success(__('Invite cancelled'))
			invites.reload()
			// A cancelled invite drops out of the roster unless the person is also
			// enrolled in one of the caller's batches.
			students.reload()
		})
		.catch((err) => toast.error(err.messages?.[0] || err.message || String(err)))
}

const breadcrumbs = computed(() => [
	{ label: __('Students'), route: { name: 'Students' } },
])

usePageMeta(() => ({
	title: __('Students'),
	icon: brand.favicon,
}))
</script>
