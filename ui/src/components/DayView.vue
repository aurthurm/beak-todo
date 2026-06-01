<script setup lang="ts">
import { computed } from "vue";
import { usePlannerStore } from "../stores/planner";
import { formatDayLabel } from "../api/client";
import TaskCard from "./TaskCard.vue";
import type { Todo } from "../api/client";

const store = usePlannerStore();

const buckets = computed(() => {
  const overdue: Todo[] = [];
  const byPriority: Record<number, Todo[]> = { 3: [], 2: [], 1: [], 0: [] };
  const done: Todo[] = [];
  const today = new Date().toISOString().slice(0, 10);

  for (const t of store.dayTodos) {
    if (t.completed) {
      done.push(t);
      continue;
    }
    if (t.due_date && t.due_date < today) {
      overdue.push(t);
    } else {
      byPriority[t.priority]?.push(t);
    }
  }
  const labels: Record<number, string> = {
    3: "Critical",
    2: "High",
    1: "Medium",
    0: "Low",
  };
  return { overdue, byPriority, done, labels };
});
</script>

<template>
  <section class="day-panel">
    <h2>{{ formatDayLabel(store.selectedDate) }}</h2>

    <div v-if="buckets.overdue.length" class="bucket">
      <h3>Overdue</h3>
      <TaskCard
        v-for="t in buckets.overdue"
        :key="t.id"
        :todo="t"
        @click="store.detailTodoId = t.id"
      />
    </div>

    <template v-for="p in [3, 2, 1, 0]" :key="p">
      <div v-if="buckets.byPriority[p].length" class="bucket">
        <h3>{{ buckets.labels[p] }}</h3>
        <TaskCard
          v-for="t in buckets.byPriority[p]"
          :key="t.id"
          :todo="t"
          @click="store.detailTodoId = t.id"
        />
      </div>
    </template>

    <div v-if="buckets.done.length" class="bucket">
      <h3>Done</h3>
      <TaskCard
        v-for="t in buckets.done"
        :key="t.id"
        :todo="t"
        @click="store.detailTodoId = t.id"
      />
    </div>

    <p v-if="!store.dayTodos.length" class="muted">No tasks for this day</p>
  </section>
</template>

<style scoped>
.day-panel {
  padding: 1rem;
  height: 100%;
  overflow-y: auto;
  background: var(--surface);
  border-left: 1px solid var(--border);
}
h2 {
  margin: 0 0 1rem;
  font-size: 1.1rem;
}
h3 {
  margin: 0.75rem 0 0.35rem;
  font-size: 0.8rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.muted {
  color: var(--muted);
  font-size: 0.85rem;
}
</style>
