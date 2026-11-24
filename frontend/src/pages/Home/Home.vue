<template>
	<!-- <header
		class="sticky flex items-center justify-between top-0 z-10 border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="[{ label: __('Home'), route: { name: 'Home' } }]" />
	</header> -->
	<div class="w-full px-5 pt-5 pb-10">
		<!-- The greeting, as a banner: who you are, what is waiting for you today. -->
		<div class="home-hero">
			<div class="min-w-0">
				<div class="text-sm font-medium text-ink-gray-6">{{ today }}</div>
				<h1
					class="mt-1 text-2xl font-semibold leading-tight text-ink-gray-9 sm:text-3xl"
				>
					{{ __('Welcome back, {0}').format(firstName) }}
				</h1>
				<p class="mt-1.5 text-base leading-6 text-ink-gray-7">
					{{ subtitle }}
				</p>
			</div>
			<div class="shrink-0">
				<TabButtons v-if="isAdmin" v-model="currentTab" :buttons="tabs" />
				<button
					v-else-if="!isEvaluatorOnly"
					type="button"
					@click="showStreakModal = true"
					class="home-streak"
					:title="__('Your learning streak')"
				>
					<Flame class="size-4 stroke-2" />
					<span class="font-semibold">
						{{ streakInfo.data?.current_streak || 0 }}
					</span>
					<span class="text-sm">{{ __('day streak') }}</span>
				</button>
			</div>
		</div>

		<AdminHome
			v-if="isAdmin && currentTab === 'instructor'"
			:liveClasses="adminLiveClasses"
			:evals="adminEvals"
		/>
		<FacilitatorHome v-if="isEvaluatorOnly" />
		<!-- Not alongside AdminHome: an admin on the Instructor tab used to get the
		     student sections stacked underneath their own. -->
		<StudentHome
			v-else-if="!(isAdmin && currentTab === 'instructor')"
			:myLiveClasses="myLiveClasses"
		/>
	</div>
	<Streak v-model="showStreakModal" :streakInfo="streakInfo" />
</template>
<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue'
import {
	Breadcrumbs,
	call,
	createResource,
	TabButtons,
	usePageMeta,
} from 'frappe-ui'
import { Flame } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import StudentHome from '@/pages/Home/StudentHome.vue'
import AdminHome from '@/pages/Home/AdminHome.vue'
import Streak from '@/pages/Home/Streak.vue'
import FacilitatorHome from './FacilitatorHome.vue'

const user = inject<any>('$user')
const { brand } = sessionStore()
const evalCount = ref(0)
const currentTab = ref<'student' | 'instructor'>('instructor')
const showStreakModal = ref(false)

onMounted(() => {
	call('lms.lms.utils.get_upcoming_evals').then((data: any) => {
		evalCount.value = data.length
	})
})

const firstName = computed(
	() => user.data?.first_name || user.data?.full_name?.split(' ')[0] || ''
)

const today = new Date().toLocaleDateString(undefined, {
	weekday: 'long',
	day: 'numeric',
	month: 'long',
})

const isAdmin = computed(() => {
	return (
		user.data?.is_moderator ||
		user.data?.is_instructor 
	)
})

const isEvaluatorOnly = computed(() => {
  if (!user.data) return false
  const isStaff = user.data.is_moderator || user.data.is_instructor
  return user.data.is_evaluator && !isStaff
})

const evaluatorDashboard = createResource({
  url: 'placid_drip.api.evaluator_dashboard.get_evaluator_dashboard',
  auto: false,
})

onMounted(() => {
  if (isEvaluatorOnly.value) evaluatorDashboard.reload()
})

watch(
  () => isEvaluatorOnly.value,
  (v) => {
    if (v) evaluatorDashboard.reload()
  },
  { immediate: true }
)

const myLiveClasses = createResource({
	url: 'lms.lms.utils.get_my_live_classes',
	auto: !isAdmin.value ? true : false,
})

const adminLiveClasses = createResource({
	url: 'lms.lms.utils.get_admin_live_classes',
	auto: isAdmin.value ? true : false,
})

const adminEvals = createResource({
	url: 'lms.lms.utils.get_admin_evals',
	auto: isAdmin.value ? true : false,
})

const streakInfo = createResource({
	url: 'lms.lms.utils.get_streak_info',
	auto: true,
})

const subtitle = computed(() => {
	if (isAdmin.value) {
		let liveClassSuffix =
			adminLiveClasses.data?.length > 1 ? __('live classes') : __('live class')
		let evalSuffix =
			adminEvals.data?.length > 1 ? __('evaluations') : __('evaluation')
		if (adminLiveClasses.data?.length > 0 && adminEvals.data?.length > 0) {
			return __('You have {0} upcoming {1} and {2} {3} scheduled.').format(
				adminLiveClasses.data.length,
				liveClassSuffix,
				adminEvals.data.length,
				evalSuffix
			)
		} else if (adminLiveClasses.data?.length > 0) {
			return __('You have {0} upcoming {1}.').format(
				adminLiveClasses.data.length,
				liveClassSuffix
			)
		} else if (adminEvals.data?.length > 0) {
			return __('You have {0} {1} scheduled.').format(
				adminEvals.data.length,
				evalSuffix
			)
		}
		return __('Manage your courses and batches at a glance')
	} else if (isEvaluatorOnly.value) { 
		return __('Manage your courses and batches at a glance')
 	} else {
		let liveClassSuffix =
			myLiveClasses.data?.length > 1 ? __('live classes') : __('live class')
		let evalSuffix = evalCount.value > 1 ? __('evaluations') : __('evaluation')
		if (myLiveClasses.data?.length > 0 && evalCount.value > 0) {
			return __('You have {0} upcoming {1} and {2} {3} scheduled.').format(
				myLiveClasses.data.length,
				liveClassSuffix,
				evalCount.value,
				evalSuffix
			)
		} else if (myLiveClasses.data?.length > 0) {
			return __('You have {0} upcoming {1}.').format(
				myLiveClasses.data.length,
				liveClassSuffix
			)
		} else if (evalCount.value > 0) {
			return __('You have {0} {1} scheduled.').format(
				evalCount.value,
				evalSuffix
			)
		}
		return __('Resume where you left off')
	}
})

const tabs = [
	{ label: __('Student'), value: 'student' },
	{ label: __('Instructor'), value: 'instructor' },
]

usePageMeta(() => {
	return {
		title: __('Home'),
		icon: brand.favicon,
	}
})
</script>
<style scoped>
.home-hero {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	justify-content: space-between;
	gap: 1rem;
	padding: 1.5rem 1.75rem;
	border: 1px solid var(--pa-hairline);
	border-radius: 0.875rem;
	background: radial-gradient(
			120% 140% at 100% 0%,
			rgba(106, 195, 175, 0.22),
			rgba(106, 195, 175, 0) 55%
		),
		var(--pa-wash);
}

.home-streak {
	display: inline-flex;
	align-items: center;
	gap: 0.4rem;
	padding: 0.5rem 0.875rem;
	border: 1px solid var(--pa-hairline);
	border-radius: 9999px;
	background: var(--surface-white);
	color: var(--ink-gray-8);
}

.home-streak svg {
	color: #d97706;
}
</style>
