<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Invite to {0}').format(title || batch),
			size: 'lg',
		}"
	>
		<template #body-content>
			<div
				v-if="link.loading && !link.data"
				class="py-12 text-center text-sm text-ink-gray-5"
			>
				{{ __('Preparing your link...') }}
			</div>

			<div v-else-if="link.data?.enabled" class="flex flex-col gap-5">
				<p class="text-sm leading-5 text-ink-gray-7">
					{{
						__(
							'Anyone who opens this link can join the batch. Newcomers create their account on the spot; existing students just log in.',
						)
					}}
				</p>

				<div>
					<div class="mb-1.5 text-sm text-ink-gray-5">{{ __('Link') }}</div>
					<div class="flex items-center gap-2">
						<input
							ref="urlInput"
							readonly
							:value="link.data.url"
							@focus="selectAll"
							class="min-w-0 flex-1 rounded-md border border-outline-gray-2 bg-surface-gray-2 px-3 py-1.5 font-mono text-sm text-ink-gray-9 focus:border-outline-gray-3 focus:outline-none"
						/>
						<Button variant="solid" @click="copyLink">
							<template #prefix>
								<Check v-if="copied" class="h-4 w-4" />
								<Copy v-else class="h-4 w-4" />
							</template>
							{{ copied ? __('Copied') : __('Copy') }}
						</Button>
					</div>
				</div>

				<div
					class="flex flex-col items-center gap-3 rounded-md border border-outline-gray-2 bg-surface-gray-1 px-4 py-5"
				>
					<img
						:src="link.data.qr"
						:alt="__('QR code for the join link')"
						class="h-48 w-48 rounded bg-white"
					/>
					<div class="text-xs text-ink-gray-5">
						{{
							__('Show this on screen or print it. Scanning opens the link.')
						}}
					</div>
					<Button variant="subtle" @click="downloadQr">
						<template #prefix>
							<Download class="h-4 w-4" />
						</template>
						{{ __('Download QR code') }}
					</Button>
				</div>

				<div
					v-if="confirmingReset"
					class="flex flex-wrap items-center justify-between gap-3 rounded-md border border-outline-red-2 bg-surface-red-1 px-3 py-2.5 text-sm text-ink-red-4"
				>
					<span>
						{{
							__('Every copy of the current link will stop working. Reset it?')
						}}
					</span>
					<div class="flex items-center gap-2">
						<Button variant="ghost" @click="confirmingReset = false">
							{{ __('Keep it') }}
						</Button>
						<Button
							variant="solid"
							theme="red"
							:loading="changing"
							@click="resetLink"
						>
							{{ __('Reset link') }}
						</Button>
					</div>
				</div>
			</div>

			<div
				v-else-if="link.data"
				class="flex flex-col items-center gap-4 py-8 text-center"
			>
				<Link2Off class="h-8 w-8 stroke-1.5 text-ink-gray-4" />
				<div>
					<div class="text-base font-medium text-ink-gray-9">
						{{ __('The join link is switched off') }}
					</div>
					<div class="mt-1 text-sm text-ink-gray-5">
						{{
							__(
								'Nobody can join with the old link. Create a new one when you are ready.',
							)
						}}
					</div>
				</div>
				<Button variant="solid" :loading="changing" @click="resetLink">
					<template #prefix>
						<Link2 class="h-4 w-4" />
					</template>
					{{ __('Create a new link') }}
				</Button>
			</div>

			<div
				v-else-if="link.error"
				class="py-8 text-center text-sm text-ink-red-4"
			>
				{{
					link.error.messages?.[0] ||
					link.error.message ||
					__('Could not load the link.')
				}}
			</div>
		</template>

		<template #actions="{ close }">
			<div class="flex flex-wrap items-center justify-between gap-2">
				<div v-if="link.data?.enabled" class="flex items-center gap-1">
					<Button variant="ghost" @click="confirmingReset = true">
						<template #prefix>
							<RefreshCw class="h-4 w-4" />
						</template>
						{{ __('Reset') }}
					</Button>
					<Button variant="ghost" :loading="changing" @click="disableLink">
						<template #prefix>
							<Link2Off class="h-4 w-4" />
						</template>
						{{ __('Turn off') }}
					</Button>
				</div>
				<div class="ml-auto flex items-center gap-2">
					<Button variant="ghost" @click="inviteByEmail(close)">
						<template #prefix>
							<Mail class="h-4 w-4" />
						</template>
						{{ __('Invite by email') }}
					</Button>
					<Button variant="subtle" @click="close">{{ __('Done') }}</Button>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Dialog, Button, call, createResource, toast } from 'frappe-ui'
import {
	Check,
	Copy,
	Download,
	Link2,
	Link2Off,
	Mail,
	RefreshCw,
} from 'lucide-vue-next'

const show = defineModel()

const props = defineProps({
	batch: {
		type: String,
		required: true,
	},
	title: {
		type: String,
		default: '',
	},
})

// The parent owns the email modal; this one only asks for it to be opened.
const emit = defineEmits(['invite-by-email'])

const urlInput = ref(null)
const copied = ref(false)
const changing = ref(false)
const confirmingReset = ref(false)

// Minted server-side on first use, so opening this dialog is what switches the
// link on. Fetched on every open rather than cached: another facilitator may
// have reset or turned it off since.
const link = createResource({
	url: 'placid_drip.api.batch_join.get_link',
	makeParams() {
		return { batch: props.batch }
	},
})

watch(show, (isOpen) => {
	if (isOpen) {
		copied.value = false
		confirmingReset.value = false
		link.fetch()
	}
})

const selectAll = (event) => event.target.select()

const copyLink = async () => {
	const url = link.data?.url
	if (!url) return

	try {
		await navigator.clipboard.writeText(url)
	} catch (e) {
		// Clipboard API is unavailable over plain http and in some embedded
		// browsers. Fall back to selecting the text so Ctrl+C still works.
		urlInput.value?.focus()
		urlInput.value?.select()
		try {
			document.execCommand('copy')
		} catch (err) {
			toast.error(__('Could not copy. Select the link and copy it by hand.'))
			return
		}
	}

	copied.value = true
	toast.success(__('Link copied'))
	setTimeout(() => (copied.value = false), 2000)
}

const fileStem = () =>
	(props.title || props.batch)
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, '-')
		.replace(/^-+|-+$/g, '') || 'batch'

// The server hands us an SVG, which is right for the screen but awkward to
// paste into a slide or a chat. Rasterise it here so the download is a PNG.
const downloadQr = () => {
	const source = link.data?.qr
	if (!source) return

	const trigger = (href, extension) => {
		const a = document.createElement('a')
		a.href = href
		a.download = `${fileStem()}-join-qr.${extension}`
		document.body.appendChild(a)
		a.click()
		a.remove()
	}

	const image = new Image()
	image.onload = () => {
		const size = 1024
		const canvas = document.createElement('canvas')
		canvas.width = size
		canvas.height = size
		const context = canvas.getContext('2d')
		context.fillStyle = '#ffffff'
		context.fillRect(0, 0, size, size)
		context.drawImage(image, 0, 0, size, size)
		try {
			trigger(canvas.toDataURL('image/png'), 'png')
		} catch (e) {
			trigger(source, 'svg')
		}
	}
	image.onerror = () => trigger(source, 'svg')
	image.src = source
}

const change = (method, successMessage) => {
	if (changing.value) return
	changing.value = true

	call(method, { batch: props.batch })
		.then((data) => {
			link.setData(data)
			confirmingReset.value = false
			copied.value = false
			toast.success(successMessage)
		})
		.catch((err) => {
			toast.error(err.messages?.[0] || err.message || String(err))
		})
		.finally(() => {
			changing.value = false
		})
}

const resetLink = () =>
	change('placid_drip.api.batch_join.reset_link', __('New link ready'))

const disableLink = () =>
	change('placid_drip.api.batch_join.disable_link', __('Join link turned off'))

const inviteByEmail = (close) => {
	close()
	emit('invite-by-email')
}
</script>
