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
				class="flex flex-col gap-2 border-b last:border-b-0 p-4 sm:flex-row sm:items-center sm:justify-between"
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

					<template v-if="invite.status === 'Pending'">
						<Button
							variant="subtle"
							:label="__('Copy link')"
							@click="copyLink(invite)"
						/>
						<Button
							variant="ghost"
							:label="__('Resend')"
							@click="resend(invite)"
						/>
						<Button
							variant="ghost"
							:label="__('Cancel')"
							@click="revoke(invite)"
						/>
					</template>
				</div>
			</div>
		</div>

		<div v-else class="text-sm italic text-ink-gray-5">
			{{ __('No invites yet.') }}
		</div>
	</div>

	<InviteStudentsModal v-model="showInviteModal" @invited="invites.reload()" />
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
import { Plus } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import InviteStudentsModal from '@/components/Modals/InviteStudentsModal.vue'

const { brand } = sessionStore()
const showInviteModal = ref(false)
const currentStatus = ref('Pending')

const statusTabs = [
	{ label: 'Pending' },
	{ label: 'Accepted' },
	{ label: 'Cancelled' },
]

const invites = createResource({
	url: 'placid_drip.api.student_invites.get_invites',
	makeParams() {
		return { status: currentStatus.value }
	},
	auto: true,
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
			if (data.sent) toast.success(__('Invite resent'))
			else toast.warning(__('Email could not be sent. Copy the link instead.'))
		})
		.catch((err) => toast.error(err.messages?.[0] || err.message || String(err)))
}

const revoke = (invite) => {
	call('placid_drip.api.student_invites.revoke_invite', { name: invite.name })
		.then(() => {
			toast.success(__('Invite cancelled'))
			invites.reload()
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
