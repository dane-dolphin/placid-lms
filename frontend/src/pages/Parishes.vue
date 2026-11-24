<template>
	<header
		class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="[{ label: __('Parishes'), route: { name: 'Parishes' } }]" />
		<Button variant="solid" @click="openForm()">
			<template #prefix>
				<Plus class="h-4 w-4 stroke-1.5" />
			</template>
			{{ __('Add parish') }}
		</Button>
	</header>

	<div class="p-5 pb-16">
		<div class="mb-6 max-w-2xl">
			<h1 class="text-2xl font-semibold text-ink-gray-9">{{ __('Parishes') }}</h1>
			<p class="mt-1.5 text-base leading-6 text-ink-gray-7">
				{{
					__(
						'Facilitators choose one of these when they create a batch. The cover picture is shown above the parish\'s batches.',
					)
				}}
			</p>
		</div>

		<div
			v-if="parishes.data?.length"
			class="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3"
		>
			<article
				v-for="parish in parishes.data"
				:key="parish.name"
				class="overflow-hidden rounded-xl border bg-surface-white"
			>
				<div
					class="parish-cover h-32 bg-cover bg-center"
					:style="
						parish.cover_image
							? { backgroundImage: `url('${encodeURI(parish.cover_image)}')` }
							: {}
					"
				></div>
				<div class="relative px-5 pb-5">
					<div class="parish-avatar">
						<img
							v-if="parish.image"
							:src="parish.image"
							class="size-full rounded-full object-cover"
							alt=""
						/>
						<Church v-else class="size-6 stroke-1.5 text-ink-gray-6" />
					</div>
					<div class="mt-3 flex items-start justify-between gap-3">
						<div class="min-w-0">
							<div class="truncate text-lg font-semibold text-ink-gray-9">
								{{ parish.organization_name }}
							</div>
							<div class="mt-0.5 text-sm text-ink-gray-6">
								{{
									parish.batch_count == 1
										? __('1 batch')
										: __('{0} batches').format(parish.batch_count || 0)
								}}
							</div>
						</div>
						<Button @click="openForm(parish)">{{ __('Edit') }}</Button>
					</div>
					<p
						v-if="parish.description"
						class="mt-3 line-clamp-2 text-sm leading-5 text-ink-gray-7"
					>
						{{ parish.description }}
					</p>
					<p
						v-if="!parish.cover_image || !parish.image"
						class="mt-3 text-xs text-ink-amber-3"
					>
						{{
							!parish.cover_image && !parish.image
								? __('No pictures yet')
								: !parish.cover_image
								? __('No cover picture yet')
								: __('No picture yet')
						}}
					</p>
				</div>
			</article>
		</div>

		<div
			v-else-if="!parishes.loading"
			class="mx-auto mt-24 max-w-md text-center"
		>
			<Church class="mx-auto size-10 stroke-1 text-ink-gray-5" />
			<div class="mt-3 text-lg font-semibold text-ink-gray-8">
				{{ __('No parishes yet') }}
			</div>
			<p class="mt-2 text-base leading-6 text-ink-gray-7">
				{{
					__(
						'Add the parishes your batches run in. Until there is at least one, the batch form does not ask for a parish.',
					)
				}}
			</p>
			<Button class="mt-4" variant="solid" @click="openForm()">
				{{ __('Add parish') }}
			</Button>
		</div>
	</div>

	<Dialog
		v-model="showForm"
		:options="{
			title: form.name ? __('Edit parish') : __('Add parish'),
			size: 'xl',
		}"
	>
		<template #body-content>
			<div class="space-y-5">
				<FormControl
					v-model="form.parish_name"
					:label="__('Parish name')"
					:required="true"
					:disabled="!!form.name"
					:placeholder="__('St. Thomas Syro-Malabar Church, Dallas')"
				/>
				<p v-if="form.name" class="!mt-1.5 text-sm text-ink-gray-5">
					{{ __('The name cannot be changed once batches and people use it.') }}
				</p>
				<ImagePicker
					v-model="form.cover_image"
					:label="__('Cover picture')"
					:hint="__('A wide photo of the church. Shown above the parish\'s batches.')"
					wide
				/>
				<ImagePicker
					v-model="form.image"
					:label="__('Picture')"
					:hint="__('A square picture or logo. Shown next to the parish name.')"
				/>
				<FormControl
					v-model="form.description"
					:label="__('Description')"
					type="textarea"
					:rows="3"
				/>
				<p v-if="error" class="text-sm text-ink-red-3" role="alert">{{ error }}</p>
			</div>
		</template>
		<template #actions="{ close }">
			<div class="flex items-center justify-between">
				<Button
					v-if="form.name"
					theme="red"
					variant="subtle"
					:loading="removing"
					@click="remove(close)"
				>
					{{ __('Delete') }}
				</Button>
				<span v-else></span>
				<div class="flex gap-2">
					<Button @click="close">{{ __('Cancel') }}</Button>
					<Button variant="solid" :loading="saving" @click="save(close)">
						{{ __('Save') }}
					</Button>
				</div>
			</div>
		</template>
	</Dialog>
</template>
<script setup>
import {
	Breadcrumbs,
	Button,
	call,
	createResource,
	Dialog,
	FormControl,
	toast,
	usePageMeta,
} from 'frappe-ui'
import { inject, reactive, ref, watch } from 'vue'
import { Church, Plus } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { sessionStore } from '@/stores/session'
import ImagePicker from '@/components/Controls/ImagePicker.vue'

/* Admin page for parishes: the list a facilitator picks from when creating a
   batch, each with the two pictures the batches page draws. */
const user = inject('$user')
const router = useRouter()
const { brand } = sessionStore()

const parishes = createResource({
	url: 'placid_drip.api.parishes.get_parishes',
	params: { with_counts: 1 },
	auto: true,
})

// Staff only. The server refuses the writes regardless; this just keeps a
// facilitator who types the address from seeing a page they cannot use.
watch(
	() => user.data,
	(data) => {
		if (data && !data.is_moderator) router.replace({ name: 'Batches' })
	},
	{ immediate: true },
)

const showForm = ref(false)
const saving = ref(false)
const removing = ref(false)
const error = ref('')
const form = reactive({
	name: '',
	parish_name: '',
	description: '',
	image: '',
	cover_image: '',
})

const openForm = (parish = null) => {
	error.value = ''
	form.name = parish?.name || ''
	form.parish_name = parish?.organization_name || ''
	form.description = parish?.description || ''
	form.image = parish?.image || ''
	form.cover_image = parish?.cover_image || ''
	showForm.value = true
}

const message = (err) => err?.messages?.[0] || err?.message || String(err)

const save = async (close) => {
	error.value = ''
	if (!form.parish_name.trim()) {
		error.value = __('Please enter the parish name.')
		return
	}
	saving.value = true
	try {
		await call('placid_drip.api.parishes.save_parish', { ...form })
		toast.success(__('Parish saved'))
		parishes.reload()
		close()
	} catch (err) {
		error.value = message(err)
	} finally {
		saving.value = false
	}
}

const remove = async (close) => {
	error.value = ''
	removing.value = true
	try {
		await call('placid_drip.api.parishes.delete_parish', { name: form.name })
		toast.success(__('Parish deleted'))
		parishes.reload()
		close()
	} catch (err) {
		error.value = message(err)
	} finally {
		removing.value = false
	}
}

usePageMeta(() => ({ title: __('Parishes'), icon: brand.favicon }))
</script>
<style scoped>
.parish-cover {
	background-color: var(--pa-pine);
	background-image: linear-gradient(135deg, var(--pa-pine), #1f4039);
}

.parish-avatar {
	display: grid;
	place-items: center;
	width: 3.5rem;
	height: 3.5rem;
	margin-top: -1.75rem;
	overflow: hidden;
	border: 3px solid var(--surface-white);
	border-radius: 9999px;
	background: var(--pa-wash);
}
</style>
