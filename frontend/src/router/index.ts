import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../components/DashboardView.vue'
import ScheduleView from '../components/ScheduleView.vue'
import JobsView from '../components/JobsView.vue'
import MediaLiveInputView from '../components/MediaLiveInputView.vue'
import SettingsView from '../components/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView, meta: { title: 'Dashboard' } },
    { path: '/schedule', name: 'schedule', component: ScheduleView, meta: { title: 'Schedule' } },
    {
      path: '/jobs/:tab?',
      name: 'jobs',
      component: JobsView,
      meta: { title: 'Jobs' },
      props: route => ({ initialTab: route.params.tab as string | undefined }),
    },
    { path: '/medialive', name: 'medialive', component: MediaLiveInputView, meta: { title: 'MediaLive Inputs' } },
    { path: '/settings', name: 'settings', component: SettingsView, meta: { title: 'Settings' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

export default router
