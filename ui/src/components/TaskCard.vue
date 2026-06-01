<script setup lang="ts">
import type { Todo } from "../api/client";

defineProps<{
  todo: Todo;
}>();
defineEmits<{ click: [] }>();
</script>

<template>
  <div
    class="task-card"
    :class="'prio-stripe-' + todo.priority"
    @click="$emit('click')"
  >
    <div class="title">{{ todo.message }}</div>
    <div class="meta">{{ todo.category }} · {{ todo.priority_label }}</div>
  </div>
</template>

<style scoped>
.task-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem 0.65rem;
  margin-bottom: 0.4rem;
  box-shadow: var(--shadow);
  cursor: grab;
}
.task-card:active {
  cursor: grabbing;
}
.title {
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.3;
}
.meta {
  font-size: 0.7rem;
  color: var(--muted);
  margin-top: 0.2rem;
}
</style>
