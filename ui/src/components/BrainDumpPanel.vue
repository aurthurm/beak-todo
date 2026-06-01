<script setup lang="ts">
import { usePlannerStore } from "../stores/planner";

const store = usePlannerStore();
</script>

<template>
  <section class="panel">
    <h2>Brain Dump</h2>
    <textarea
      v-model="store.brainDumpText"
      placeholder="Type everything on your mind..."
      rows="5"
    />
    <button class="primary" :disabled="!store.brainDumpText.trim()" @click="store.organiseBrainDump">
      AI Organise
    </button>

    <div v-if="store.suggestions.length" class="suggestions">
      <h3>Suggested Tasks</h3>
      <label v-for="(t, i) in store.suggestions" :key="i" class="sug-row">
        <input
          type="checkbox"
          :checked="store.selectedSuggestions.has(i)"
          @change="
            (e) => {
              const s = new Set(store.selectedSuggestions);
              if ((e.target as HTMLInputElement).checked) s.add(i);
              else s.delete(i);
              store.selectedSuggestions = s;
            }
          "
        />
        <div>
          <strong>{{ t.message }}</strong>
          <div class="meta">{{ t.category }} · P{{ t.priority }} · {{ t.due_date || "No date" }}</div>
        </div>
      </label>
      <button class="primary" @click="store.applySuggestions">Add Selected</button>
    </div>

    <h3 class="inbox-title">Inbox</h3>
    <p v-if="!store.inbox.length" class="muted">No undated tasks</p>
  </section>
</template>

<style scoped>
.panel {
  padding: 1rem;
  height: 100%;
  overflow-y: auto;
  background: var(--surface);
  border-right: 1px solid var(--border);
}
h2, h3 {
  margin: 0 0 0.5rem;
  font-size: 0.95rem;
}
textarea {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem;
  resize: vertical;
  margin-bottom: 0.5rem;
}
.primary {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.45rem 0.75rem;
  width: 100%;
  margin-bottom: 1rem;
}
.suggestions {
  margin-bottom: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border);
}
.sug-row {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}
.meta {
  color: var(--muted);
  font-size: 0.75rem;
}
.inbox-title {
  margin-top: 1rem;
}
.muted {
  color: var(--muted);
  font-size: 0.8rem;
}
</style>
