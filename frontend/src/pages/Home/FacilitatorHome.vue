<template>
  <div>
    <!-- Loading -->
    <div v-if="dashboard.loading" class="text-sm text-ink-gray-6 mt-10">
      {{ __('Loading...') }}
    </div>

    <div v-else>
      <!-- ============ BATCHES (top) ============ -->
      <div class="mt-10">
        <div class="flex items-center justify-between mb-3">
          <span class="font-semibold text-lg text-ink-gray-9">
            {{ __('My Batches') }}
          </span>

          <router-link
            :to="{ name: 'Batches' }"
            class="flex items-center space-x-1 text-ink-gray-5 text-xs"
          >
            <span>{{ __('See all') }}</span>
            <MoveRight class="size-3 stroke-1.5" />
          </router-link>
        </div>

        <div v-if="batchesPreview.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <router-link
            v-for="b in batchesPreview"
            :key="b.name"
            :to="{ name: 'BatchDetail', params: { batchName: b.name } }"
          >
            <BatchCard :batch="b" />
          </router-link>
        </div>

        <div v-else class="flex flex-col items-center justify-center mt-16">
          <PackageOpen class="size-10 mx-auto stroke-1 text-ink-gray-5" />
          <div class="text-lg font-semibold text-ink-gray-7 mb-1.5">
            {{ __('No batches assigned') }}
          </div>
          <div class="leading-5 text-base w-full md:w-2/5 text-center text-ink-gray-7">
            {{ __('You do not have any batches assigned yet.') }}
          </div>
        </div>
      </div>

      <!-- ============ COURSES (below) ============ -->
      <div class="mt-10">
        <div class="flex items-center justify-between mb-3">
          <span class="font-semibold text-lg text-ink-gray-9">
            {{ __('Facilitated Courses') }}
          </span>

          <router-link
            :to="{ name: 'Courses' }"
            class="flex items-center space-x-1 text-ink-gray-5 text-xs"
          >
            <span>{{ __('See all') }}</span>
            <MoveRight class="size-3 stroke-1.5" />
          </router-link>
        </div>

        <div v-if="coursesPreview.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <router-link
            v-for="c in coursesPreview"
            :key="c.name"
            :to="{ name: 'CourseDetail', params: { courseName: c.name } }"
            class="block"
          >
            <CourseCard :course="c" />
          </router-link>
        </div>

        <div v-else class="flex flex-col items-center justify-center mt-16">
          <GraduationCap class="size-10 mx-auto stroke-1 text-ink-gray-5" />
          <div class="text-lg font-semibold text-ink-gray-7 mb-1.5">
            {{ __('No courses assigned') }}
          </div>
          <div class="leading-5 text-base w-full md:w-2/5 text-center text-ink-gray-7">
            {{ __('You do not have any courses to facilitate yet.') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { createResource } from 'frappe-ui'
import { GraduationCap, MoveRight, PackageOpen } from 'lucide-vue-next'
import BatchCard from '@/components/BatchCard.vue'
import CourseCard from '@/components/CourseCard.vue'

type DashboardBatch = {
  name: string
  title?: string
  description?: string
  start_date?: string
  end_date?: string
}

type DashboardCourse = {
  name: string
  title?: string
  // include any extra fields your CourseCard expects
}

const dashboard = createResource({
  url: 'placid_drip.api.evaluator_dashboard.get_evaluator_dashboard',
  auto: true,
})

const batches = computed<DashboardBatch[]>(() => (dashboard.data?.batches || []) as DashboardBatch[])
const courses = computed<DashboardCourse[]>(() => (dashboard.data?.courses || []) as DashboardCourse[])

const batchesPreview = computed(() => batches.value.slice(0, 4))
const coursesPreview = computed(() => courses.value.slice(0, 4))
</script>