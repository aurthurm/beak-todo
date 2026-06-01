<script setup lang="ts">
import { onMounted } from "vue";
import { useReportsStore } from "../stores/reports";

const store = useReportsStore();

onMounted(async () => {
  await store.loadConfig();
  await store.loadDraft();
});
</script>

<template>
  <section class="reports-panel">
    <h2>Weekly reports</h2>
    <p class="hint">Generate a draft, review it, then send via Resend.</p>

    <div class="row">
      <label>
        From
        <input v-model="store.periodFrom" type="date" />
      </label>
      <label>
        To
        <input v-model="store.periodTo" type="date" />
      </label>
    </div>

    <label class="check">
      <input v-model="store.useAi" type="checkbox" />
      Use AI for narrative
    </label>

    <label>
      Recipient
      <input
        v-model="store.recipient"
        type="email"
        placeholder="boss@company.com"
      />
    </label>

    <div class="actions">
      <button type="button" :disabled="store.loading" @click="store.generate">
        Generate draft
      </button>
      <button
        type="button"
        :disabled="store.loading || !store.draft"
        @click="store.send"
      >
        Send email
      </button>
      <button
        type="button"
        class="muted"
        :disabled="store.loading || !store.draft"
        @click="store.cancel"
      >
        Cancel draft
      </button>
    </div>

    <p v-if="store.error" class="error">{{ store.error }}</p>
    <p v-if="store.lastMessageId" class="success">
      Sent (message id: {{ store.lastMessageId }})
    </p>

    <article v-if="store.draft" class="preview">
      <h3>{{ store.draft.subject }}</h3>
      <pre>{{ store.draft.body_text }}</pre>
      <p class="meta">
        Draft #{{ store.draft.id }} · {{ store.draft.status }}
      </p>
    </article>
    <p v-else class="empty">No draft yet.</p>
  </section>
</template>

<style scoped>
.reports-panel {
  padding: 1rem;
  max-width: 42rem;
}
.hint {
  color: var(--muted, #666);
  font-size: 0.9rem;
}
.row {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin: 0.75rem 0;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
}
input[type="date"],
input[type="email"] {
  padding: 0.4rem 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.check {
  flex-direction: row;
  align-items: center;
  margin-bottom: 0.75rem;
}
.actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 1rem 0;
}
button {
  padding: 0.45rem 0.9rem;
  border-radius: 4px;
  border: 1px solid #333;
  background: #1a1a2e;
  color: #fff;
  cursor: pointer;
}
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
button.muted {
  background: #eee;
  color: #333;
  border-color: #ccc;
}
.preview {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f8fa;
  border-radius: 8px;
  border: 1px solid #e0e0e8;
}
.preview pre {
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 0.9rem;
  margin: 0.5rem 0;
}
.meta {
  font-size: 0.8rem;
  color: #666;
}
.error {
  color: #b00020;
}
.success {
  color: #0a6b0a;
}
.empty {
  color: #888;
  font-style: italic;
}
</style>
