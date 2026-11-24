<template>
	<div>
		<label v-if="label" class="mb-1 block text-sm text-ink-gray-5">
			{{ label }}
			<span v-if="required" class="text-ink-red-3">*</span>
		</label>
		<FileUploader
			v-if="!modelValue"
			:fileTypes="['image/*']"
			:validateFile="validateFile"
			@success="(file) => emit('update:modelValue', file.file_url)"
		>
			<template v-slot="{ uploading, progress, openFileSelector }">
				<button
					type="button"
					class="image-picker-drop"
					:class="wide ? 'aspect-[3/1]' : 'aspect-square w-32'"
					@click="openFileSelector"
				>
					<ImageIcon class="size-5 stroke-1.5" />
					<span class="text-sm">
						{{ uploading ? __('Uploading {0}%').format(progress) : __('Upload') }}
					</span>
				</button>
			</template>
		</FileUploader>
		<div v-else class="relative w-fit" :class="{ 'w-full': wide }">
			<img
				:src="modelValue"
				class="rounded-md border object-cover"
				:class="wide ? 'aspect-[3/1] w-full' : 'size-32'"
				alt=""
			/>
			<Button
				class="!absolute right-2 top-2"
				size="sm"
				@click="emit('update:modelValue', '')"
			>
				{{ __('Remove') }}
			</Button>
		</div>
		<p v-if="hint" class="mt-1.5 text-sm leading-5 text-ink-gray-5">
			{{ hint }}
		</p>
	</div>
</template>
<script setup>
import { Button, FileUploader } from 'frappe-ui'
import { Image as ImageIcon } from 'lucide-vue-next'
import { validateFile } from '@/utils'

/* One image field: an upload target while empty, a preview with Remove once
   set. `wide` is for covers; the default is a square picture. The value is the
   uploaded file's URL. */
defineProps({
	modelValue: { type: String, default: '' },
	label: { type: String, default: '' },
	hint: { type: String, default: '' },
	wide: { type: Boolean, default: false },
	required: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
</script>
<style scoped>
.image-picker-drop {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 0.375rem;
	width: 100%;
	border: 1.5px dashed var(--pa-hairline);
	border-radius: 0.5rem;
	background: var(--pa-wash);
	color: var(--ink-gray-7);
	transition: border-color var(--pa-fast, 160ms) var(--pa-ease, ease);
}

.image-picker-drop.aspect-square {
	width: 8rem;
}

.image-picker-drop:hover,
.image-picker-drop:focus-visible {
	border-color: var(--surface-gray-7);
	outline: none;
}
</style>
