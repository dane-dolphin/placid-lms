<template>
<!-- Top branding section -->
<div
  class="px-2 pt-2"
  :class="isCollapsed ? 'flex flex-col items-center' : ''"
>
  <!-- Full-width image (only when not collapsed) -->
  <div v-if="!isCollapsed" class="w-full items-center align-center">
    <img
      v-if="branding.data?.banner_image"
      :src="branding.data?.banner_image.file_url"
      class="w-full h-20 rounded-lg object-cover object-center"
      alt="Branding"
    />
    <div
      v-else
      class="w-full h-20 rounded-lg bg-surface-gray-2 flex items-center justify-center"
    >
      <LMSLogo class="w-10 h-10" />
    </div>

    <!-- <div class="mt-2 px-2 text-xs uppercase tracking-wide text-ink-gray-6">
      {{branding.data?.app_name}}
    </div> -->
  </div>

  <!-- Collapsed state: show small icon only -->
  <div v-else class="flex justify-center w-full">
    <img
      v-if="branding.data?.banner_image"
      :src="branding.data?.banner_image.file_url"
      class="w-10 h-10 rounded object-cover object-center"
      alt="Branding"
    />
    <LMSLogo v-else class="w-10 h-10 rounded" />
  </div>

  <!-- User dropdown row -->
  <Dropdown :options="userDropdownOptions">
    <template v-slot="{ open }">
      <button
        class="mt-1 flex items-center rounded-md duration-300 ease-in-out"
        :class="
          isCollapsed
            ? 'w-12 h-12 justify-center'
            : open
            ? 'bg-surface-white shadow-sm px-2 py-2 w-full'
            : 'hover:bg-surface-gray-3 px-2 py-2 w-full'
        "
      >
        <!-- User name + role -->
        <div
          class="flex flex-1 flex-col text-left"
          :class="isCollapsed ? 'hidden' : ''"
        >
          <div class="text-sm font-semibold text-ink-gray-9 leading-tight">
            {{ convertToTitleCase(userResource.data?.full_name) }}
          </div>
          <div class="text-xs text-ink-gray-6 leading-tight truncate">
			{{ roleLabel }}
          </div>
        </div>

        <!-- Chevron -->
        <div :class="isCollapsed ? 'hidden' : ''">
          <ChevronDown class="h-4 w-4 text-ink-gray-7" />
        </div>

        <!-- Collapsed: show a generic user dot/icon or initials -->
        <div v-if="isCollapsed" class="text-xs font-semibold text-ink-gray-7">
          {{ (userResource.data?.full_name || 'U').slice(0, 1).toUpperCase() }}
        </div>
      </button>
    </template>
  </Dropdown>
</div>
	<SettingsModal
		v-if="userResource.data?.is_moderator"
		v-model="showSettingsModal"
	/>
</template>

<script setup>
import LMSLogo from '@/components/Icons/LMSLogo.vue'
import { sessionStore } from '@/stores/session'
import { Dropdown } from 'frappe-ui'
import Apps from '@/components/Apps.vue'
import { useRouter } from 'vue-router'
import { convertToTitleCase } from '@/utils'
import { usersStore } from '@/stores/user'
import { useSettings } from '@/stores/settings'
import { markRaw, watch, ref, onMounted, computed } from 'vue'
import { createDialog } from '@/utils/dialogs'
import SettingsModal from '@/components/Settings/Settings.vue'
import FrappeCloudIcon from '@/components/Icons/FrappeCloudIcon.vue'
import {
	ChevronDown,
	LogIn,
	LogOut,
	Moon,
	User,
	Settings,
	Sun,
	Zap,
} from 'lucide-vue-next'

const router = useRouter()
const { logout, branding } = sessionStore()
let { userResource } = usersStore()
const settingsStore = useSettings()
let { isLoggedIn } = sessionStore()
const showSettingsModal = ref(false)
const theme = ref('light')
const frappeCloudBaseEndpoint = 'https://frappecloud.com'
const $dialog = createDialog

const props = defineProps({
	isCollapsed: {
		type: Boolean,
		default: false,
	},
})

onMounted(() => {
	theme.value = localStorage.getItem('theme') || 'light'
	if (['light', 'dark'].includes(theme.value)) {
		document.documentElement.setAttribute('data-theme', theme.value)
	}
})

watch(
	() => settingsStore.isSettingsOpen,
	(value) => {
		showSettingsModal.value = value
	}
)

const roleLabel = computed(() => {
  if (!userResource.data) return 'Guest | Not logged in'

  if (userResource.data.is_system_manager) return 'Logged in as an Administrator'
  if (userResource.data.is_instructor) return 'Logged in as a Course Creator'
  if (userResource.data.is_evaluator) return 'Logged in as a Facilitator'
  if (userResource.data.is_student) return 'Logged in as a Student'

  return 'This role is Unintended.'
})

const toggleTheme = () => {
	const currentTheme = document.documentElement.getAttribute('data-theme')
	theme.value = currentTheme === 'dark' ? 'light' : 'dark'
	document.documentElement.setAttribute('data-theme', theme.value)
	localStorage.setItem('theme', theme.value)
}

const userDropdownOptions = computed(() => {
	return [
		{
			group: '',
			items: [
				{
					icon: User,
					label: 'My Profile',
					onClick: () => {
						router.push(`/user/${userResource.data?.username}`)
					},
					condition: () => {
						return isLoggedIn
					},
				},
				{
					icon: theme.value === 'light' ? Moon : Sun,
					label: 'Toggle Theme',
					onClick: () => {
						toggleTheme()
					},
				},
				{
					component: markRaw(Apps),
					condition: () => {
						let cookies = new URLSearchParams(
							document.cookie.split('; ').join('&')
						)
						let system_user = cookies.get('system_user')
						if (system_user === 'yes') return true
						else return false
					},
				},
				{
					icon: Settings,
					label: 'Settings',
					onClick: () => {
						settingsStore.isSettingsOpen = true
					},
					condition: () => {
						return userResource.data?.is_moderator
					},
				},
				{
					icon: FrappeCloudIcon,
					label: 'Login to Frappe Cloud',
					onClick: () => {
						$dialog({
							title: __('Login to Frappe Cloud?'),
							message: __(
								'Are you sure you want to login to your Frappe Cloud dashboard?'
							),
							actions: [
								{
									label: __('Confirm'),
									variant: 'solid',
									onClick(close) {
										loginToFrappeCloud()
										close()
									},
								},
							],
						})
					},
					condition: () => {
						return (
							userResource.data?.is_system_manager &&
							userResource.data?.is_fc_site
						)
					},
				},
				{
					icon: LogOut,
					label: 'Log out',
					onClick: () => {
						logout.submit().then(() => {
							isLoggedIn = false
						})
					},
					condition: () => {
						return isLoggedIn
					},
				},
				{
					icon: LogIn,
					label: 'Log in',
					onClick: () => {
						window.location.href = '/login'
					},
					condition: () => {
						return !isLoggedIn
					},
				},
			],
		},
	]
})

const loginToFrappeCloud = () => {
	let redirect_to = '/dashboard/sites/' + userResource.data.sitename
	window.open(`${frappeCloudBaseEndpoint}${redirect_to}`, '_blank')
}
</script>
