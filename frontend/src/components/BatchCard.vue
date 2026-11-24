<template>
	<div
		class="pa-card flex h-full flex-col overflow-auto rounded-md text-ink-gray-9"
		style="min-height: 350px"
	>
		<!-- Same shape as a course card. The pine tag, the parish line and the
		     dates are what say "this is a batch". -->
		<div
			class="batch-card-cover relative h-[168px] w-full rounded-t-md border-x border-t bg-cover bg-center bg-no-repeat"
			:style="cover ? { backgroundImage: `url('${encodeURI(cover)}')` } : {}"
		>
			<span class="pa-tag is-batch">
				<Users class="size-3 stroke-2" />
				{{ __('Batch') }}
			</span>
			<span
				v-if="batch.seat_count && batch.seats_left > 0"
				class="batch-card-seats bg-surface-green-2 text-ink-green-3"
			>
				{{ batch.seats_left }}
				{{ batch.seats_left == 1 ? __('Seat Left') : __('Seats Left') }}
			</span>
			<span
				v-else-if="batch.seat_count && batch.seats_left <= 0"
				class="batch-card-seats bg-surface-red-2 text-ink-red-3"
			>
				{{ __('Full') }}
			</span>
			<div
				v-if="!cover"
				class="flex h-full items-center justify-center px-5 text-center font-extrabold leading-6 text-white"
				:class="
					batch.title?.length > 32
						? 'text-lg'
						: batch.title?.length > 20
						? 'text-xl'
						: 'text-2xl'
				"
			>
				{{ batch.title }}
			</div>
		</div>

		<div class="flex flex-auto flex-col rounded-b-md border-x-2 border-b-2 p-4">
			<div
				v-if="batch.parish_name"
				class="mb-2 flex items-center gap-2 text-xs font-medium text-ink-gray-6"
			>
				<img
					v-if="batch.parish_image"
					:src="batch.parish_image"
					class="size-5 rounded-full object-cover"
					alt=""
				/>
				<Church v-else class="size-4 stroke-1.5" />
				<span class="truncate">{{ batch.parish_name }}</span>
			</div>

			<div
				v-if="cover"
				class="font-semibold leading-6"
				:class="batch.title?.length > 32 ? 'text-lg' : 'text-xl'"
			>
				{{ batch.title }}
			</div>

			<div class="short-introduction text-sm text-ink-gray-7">
				{{ batch.description }}
			</div>

			<div class="mt-auto space-y-2 text-sm text-ink-gray-7">
				<DateRange
					v-if="batch.start_date"
					:startDate="batch.start_date"
					:endDate="batch.end_date"
				/>
				<div v-if="batch.amount" class="font-semibold text-ink-gray-9">
					{{ batch.price }}
				</div>
			</div>

			<div class="mt-4 flex items-center justify-between gap-3">
				<div
					v-if="batch.instructors?.length"
					class="avatar-group overlap flex min-w-0"
				>
					<div
						class="mr-1 h-6"
						:class="{ 'avatar-group overlap': batch.instructors.length > 1 }"
					>
						<UserAvatar
							v-for="instructor in batch.instructors"
							:user="instructor"
						/>
					</div>
					<CourseInstructors :instructors="batch.instructors" />
				</div>
				<span v-else></span>
				<Tooltip
					v-if="batch.students_count"
					:text="__('Students in this batch')"
				>
					<span class="flex shrink-0 items-center text-sm text-ink-gray-7">
						<Users class="mr-1 h-4 w-4 stroke-1.5" />
						{{ batch.students_count }}
					</span>
				</Tooltip>
			</div>
		</div>
	</div>
</template>
<script setup>
import { computed } from 'vue'
import { Tooltip } from 'frappe-ui'
import { Church, Users } from 'lucide-vue-next'
import DateRange from '@/components/Common/DateRange.vue'
import CourseInstructors from '@/components/CourseInstructors.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const props = defineProps({
	batch: {
		type: Object,
		default: null,
	},
})

// The batch's own picture, else its parish's church. With neither, the card
// falls back to a pine panel carrying the title, as course cards do.
const cover = computed(() => props.batch?.image || props.batch?.parish_cover || '')
</script>
<style>
.batch-card-cover {
	background-color: #315d54;
	background-image: linear-gradient(135deg, #3d7266 0%, #315d54 45%, #1f4039 100%);
}

.batch-card-seats {
	position: absolute;
	top: 0.75rem;
	right: 0.75rem;
	padding: 0.2rem 0.55rem;
	border-radius: 9999px;
	font-size: 0.6875rem;
	font-weight: 600;
	line-height: 1.2;
}

.short-introduction {
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	text-overflow: ellipsis;
	width: 100%;
	overflow: hidden;
	margin: 0.25rem 0 1rem;
	line-height: 1.5;
}

.avatar-group {
	display: inline-flex;
	align-items: center;
}

.avatar-group .avatar {
	transition: margin 0.1s ease-in-out;
}

.avatar-group.overlap .avatar + .avatar {
	margin-left: calc(-8px);
}
</style>
