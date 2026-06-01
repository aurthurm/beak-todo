<script setup lang="ts">
import { onMounted, ref } from "vue";
import { usePlannerStore } from "./stores/planner";
import { api } from "./api/client";
import SourceFilterPanel from "./components/SourceFilterPanel.vue";
import BrainDumpPanel from "./components/BrainDumpPanel.vue";
import CalendarStrip from "./components/CalendarStrip.vue";
import DayView from "./components/DayView.vue";
import TaskDetailModal from "./components/TaskDetailModal.vue";
import AiDrawer from "./components/AiDrawer.vue";
import ReportsPanel from "./components/ReportsPanel.vue";

const store = usePlannerStore();
const searchQuery = ref("");

async function runSearch() {
  if (!searchQuery.value.trim()) {
    await store.refresh();
    return;
  }
  store.inbox = await api.listTodos({ search: searchQuery.value });
}

onMounted(() => store.refresh());
</script>

<template>
  <div class="app">
    <header class="topbar">
      <span class="brand">Beak Flow</span>
      <input
        v-model="searchQuery"
        class="search desktop-only"
        placeholder="Search tasks..."
        @keyup.enter="runSearch"
      />
      <div class="top-actions">
        <button type="button" @click="store.goToday">Today</button>
        <button type="button" @click="store.goThisWeek">This Week</button>
        <button type="button" @click="store.runAiPlan">AI Plan</button>
        <button type="button" @click="store.drawerOpen = true">AI</button>
        <button
          type="button"
          :class="{ active: store.mobileTab === 'reports' }"
          class="desktop-only"
          @click="store.mobileTab = 'reports'"
        >
          Reports
        </button>
      </div>
    </header>

    <nav class="mobile-tabs">
      <button
        :class="{ active: store.mobileTab === 'inbox' }"
        @click="store.mobileTab = 'inbox'"
      >
        Inbox
      </button>
      <button
        :class="{ active: store.mobileTab === 'calendar' }"
        @click="store.mobileTab = 'calendar'"
      >
        Calendar
      </button>
      <button
        :class="{ active: store.mobileTab === 'today' }"
        @click="store.mobileTab = 'today'"
      >
        Today
      </button>
      <button
        :class="{ active: store.mobileTab === 'ai' }"
        @click="store.drawerOpen = true; store.mobileTab = 'ai'"
      >
        AI
      </button>
      <button
        :class="{ active: store.mobileTab === 'reports' }"
        @click="store.mobileTab = 'reports'"
      >
        Reports
      </button>
    </nav>

    <p v-if="store.error" class="error">{{ store.error }}</p>
    <p v-if="store.loading" class="loading">Loading…</p>

    <div
      v-if="store.mobileTab === 'reports'"
      class="reports-view"
      :class="{ 'mobile-show': store.mobileTab === 'reports' }"
    >
      <ReportsPanel />
    </div>

    <main v-show="store.mobileTab !== 'reports'" class="layout-grid">
      <div
        class="col-left desktop-only"
        :class="{ 'mobile-show': store.mobileTab === 'inbox' }"
      >
        <SourceFilterPanel />
        <BrainDumpPanel />
      </div>
      <div
        class="col-mid"
        :class="{ 'mobile-show': store.mobileTab === 'calendar' }"
      >
        <CalendarStrip />
      </div>
      <div
        class="col-right desktop-only"
        :class="{ 'mobile-show': store.mobileTab === 'today' }"
      >
        <DayView />
      </div>
    </main>

    <TaskDetailModal />
    <AiDrawer />
  </div>
</template>

<style scoped>
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.topbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.6rem 1rem;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}
.brand {
  font-weight: 700;
  font-size: 1.1rem;
  white-space: nowrap;
}
.search {
  flex: 1;
  max-width: 280px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.35rem 0.6rem;
}
.top-actions {
  display: flex;
  gap: 0.35rem;
  margin-left: auto;
  flex-wrap: wrap;
}
.top-actions button {
  border: 1px solid var(--border);
  background: var(--bg);
  border-radius: 8px;
  padding: 0.35rem 0.6rem;
  font-size: 0.8rem;
}
.layout-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr 280px;
  min-height: 0;
}
.col-left,
.col-mid,
.col-right {
  min-height: 0;
  overflow: hidden;
}
.error {
  color: var(--prio-critical);
  padding: 0.25rem 1rem;
  margin: 0;
  font-size: 0.85rem;
}
.loading {
  padding: 0.25rem 1rem;
  margin: 0;
  font-size: 0.85rem;
  color: var(--muted);
}
.reports-view {
  flex: 1;
  overflow: auto;
  min-height: 0;
}
@media (max-width: 900px) {
  .reports-view {
    display: none;
  }
  .reports-view.mobile-show {
    display: block;
  }
  .layout-grid > * {
    display: none;
  }
  .layout-grid > .mobile-show {
    display: block;
  }
  .col-mid.mobile-show {
    display: flex;
    flex-direction: column;
  }
}
</style>
