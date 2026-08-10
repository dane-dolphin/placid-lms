<template>
	<div
		class="flex flex-col h-full rounded-md overflow-hidden text-ink-gray-9 border-2 cursor-pointer transition hover:shadow-md"
	>
		<div
			class="w-full h-[120px] bg-cover bg-center bg-no-repeat flex items-center justify-center"
			:style="
				level.image
					? { backgroundImage: `url('${encodeURI(level.image)}')` }
					: { backgroundImage: gradient, backgroundBlendMode: 'screen' }
			"
		>
			<div
				v-if="!level.image"
				class="text-white font-extrabold px-5 text-center leading-7"
				:class="level.level_name.length > 20 ? 'text-xl' : 'text-2xl'"
			>
				{{ level.level_name }}
			</div>
		</div>

		<div class="flex flex-col flex-auto p-4">
			<div
				v-if="level.image"
				class="font-semibold leading-6 mb-1"
				:class="level.level_name.length > 32 ? 'text-lg' : 'text-xl'"
			>
				{{ level.level_name }}
			</div>

			<div class="flex items-center text-sm text-ink-gray-7 mb-2">
				<BookOpen class="h-4 w-4 stroke-1.5 mr-1.5" />
				<span>
					{{ level.course_count }}
					{{ level.course_count === 1 ? __('course') : __('courses') }}
				</span>
			</div>

			<div v-if="level.description" class="level-description text-sm text-ink-gray-7">
				{{ level.description }}
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from 'vue'
import { BookOpen } from 'lucide-vue-next'
import { theme } from '@/utils/theme'

const props = defineProps({
	level: {
		type: Object,
		required: true,
	},
})

// LMS Course carries an author-chosen `card_gradient`; Course Level deliberately
// does not, because a level is picked once and the admin should not have to make
// a colour decision to add one. Hashing the name keeps a given level the same
// colour across reloads and across users, which a random pick would not.
const PALETTE = ['blue', 'green', 'amber', 'cyan', 'orange', 'pink', 'purple', 'red']

const gradient = computed(() => {
	let hash = 0
	for (const char of props.level.level_name) {
		hash = (hash * 31 + char.charCodeAt(0)) % 997
	}
	const color = PALETTE[hash % PALETTE.length]
	const colorMap = theme.backgroundColor[color]
	return `linear-gradient(to top right, black, ${colorMap[400]})`
})
</script>

<style scoped>
.level-description {
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}
</style>
