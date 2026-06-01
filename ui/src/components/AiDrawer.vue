<script setup lang="ts">
import { ref } from "vue";
import { usePlannerStore } from "../stores/planner";

const store = usePlannerStore();
const input = ref("");

const presets = [
  "What should I focus on today?",
  "Move low-priority tasks to next week",
  "Show proposal tasks due this week",
  "Break down my biggest open task",
];

function send() {
  if (!input.value.trim()) return;
  store.sendDrawerMessage(input.value);
  input.value = "";
}

function usePreset(p: string) {
  input.value = p;
  send();
}
</script>

<template>
  <div v-if="store.drawerOpen" class="drawer">
    <div class="drawer-head">
      <strong>Ask AI</strong>
      <button type="button" class="close" @click="store.drawerOpen = false">×</button>
    </div>
    <div class="presets">
      <button
        v-for="p in presets"
        :key="p"
        type="button"
        class="chip"
        @click="usePreset(p)"
      >
        {{ p }}
      </button>
    </div>
    <div v-if="store.drawerReply" class="reply">{{ store.drawerReply }}</div>
    <div v-if="store.actionPreview" class="preview">
      <p>{{ store.actionPreview.description }}</p>
      <ul>
        <li v-for="p in store.actionPreview.patches" :key="p.todo_id">
          Todo #{{ p.todo_id }}
          <span v-if="p.due_date"> → {{ p.due_date }}</span>
          <span v-if="p.clear_due"> → clear due</span>
          <span v-if="p.completed"> → done</span>
        </li>
      </ul>
      <div class="preview-actions">
        <button type="button" class="ghost" @click="store.actionPreview = null">Cancel</button>
        <button type="button" class="primary" @click="store.applyActionPreview">Apply</button>
      </div>
    </div>
    <div class="input-row">
      <input v-model="input" placeholder="Ask anything..." @keyup.enter="send" />
      <button type="button" class="primary" @click="send">Send</button>
    </div>
  </div>
</template>

<style scoped>
.drawer {
  position: fixed;
  right: 0;
  bottom: 0;
  width: min(400px, 100%);
  max-height: 45vh;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px 12px 0 0;
  box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.1);
  z-index: 50;
  display: flex;
  flex-direction: column;
  padding: 0.75rem 1rem;
}
.drawer-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.close {
  border: none;
  background: transparent;
  font-size: 1.25rem;
  line-height: 1;
}
.presets {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-bottom: 0.5rem;
}
.chip {
  font-size: 0.7rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg);
}
.reply {
  flex: 1;
  overflow-y: auto;
  font-size: 0.85rem;
  white-space: pre-wrap;
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background: var(--bg);
  border-radius: 8px;
}
.preview {
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}
.preview ul {
  margin: 0.35rem 0;
  padding-left: 1.2rem;
}
.preview-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}
.input-row {
  display: flex;
  gap: 0.35rem;
}
.input-row input {
  flex: 1;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.45rem;
}
.primary {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.45rem 0.75rem;
}
.ghost {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.35rem 0.75rem;
}
</style>
