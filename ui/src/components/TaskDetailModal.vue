<script setup lang="ts">
import { ref, watch } from "vue";
import { usePlannerStore } from "../stores/planner";
import { api, type Note, type Todo } from "../api/client";

const store = usePlannerStore();
const todo = ref<Todo | null>(null);
const notes = ref<Note[]>([]);
const noteText = ref("");
const edit = ref({
  message: "",
  priority: 0,
  category: "",
  due_date: "",
  completed: false,
});

watch(
  () => store.detailTodoId,
  async (id) => {
    if (!id) {
      todo.value = null;
      return;
    }
    todo.value = await api.getTodo(id);
    notes.value = await api.listNotes(id);
    edit.value = {
      message: todo.value.message,
      priority: todo.value.priority,
      category: todo.value.category,
      due_date: todo.value.due_date || "",
      completed: todo.value.completed,
    };
  },
  { immediate: true }
);

async function save() {
  if (!todo.value) return;
  await store.patchTodo(todo.value.id, {
    message: edit.value.message,
    priority: edit.value.priority,
    category: edit.value.category,
    due_date: edit.value.due_date || undefined,
    clear_due: !edit.value.due_date,
    completed: edit.value.completed,
  });
  store.detailTodoId = null;
}

async function addNote() {
  if (!todo.value || !noteText.value.trim()) return;
  await api.addNote(todo.value.id, noteText.value);
  noteText.value = "";
  notes.value = await api.listNotes(todo.value.id);
}

function close() {
  store.detailTodoId = null;
}
</script>

<template>
  <div v-if="store.detailTodoId && todo" class="overlay" @click.self="close">
    <div class="modal">
      <h2>Task Details</h2>
      <label>Message<input v-model="edit.message" /></label>
      <label>Priority
        <select v-model.number="edit.priority">
          <option :value="0">Low</option>
          <option :value="1">Medium</option>
          <option :value="2">High</option>
          <option :value="3">Critical</option>
        </select>
      </label>
      <label>Category<input v-model="edit.category" /></label>
      <label>Due Date<input v-model="edit.due_date" type="date" /></label>
      <label><input v-model="edit.completed" type="checkbox" /> Completed</label>

      <div class="notes">
        <h3>Notes</h3>
        <ul>
          <li v-for="n in notes" :key="n.id">{{ n.content }}</li>
        </ul>
        <div class="note-add">
          <input v-model="noteText" placeholder="Add note..." />
          <button type="button" @click="addNote">Add</button>
        </div>
      </div>

      <div class="actions">
        <button type="button" class="ghost" @click="close">Cancel</button>
        <button type="button" class="primary" @click="save">Save</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal {
  background: var(--surface);
  border-radius: 12px;
  padding: 1.25rem;
  width: min(420px, 92vw);
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}
label {
  display: block;
  margin-bottom: 0.65rem;
  font-size: 0.8rem;
  color: var(--muted);
}
input,
select {
  display: block;
  width: 100%;
  margin-top: 0.2rem;
  padding: 0.4rem;
  border: 1px solid var(--border);
  border-radius: 6px;
}
.notes {
  margin-top: 1rem;
  border-top: 1px solid var(--border);
  padding-top: 0.75rem;
}
.notes ul {
  margin: 0;
  padding-left: 1.2rem;
  font-size: 0.85rem;
}
.note-add {
  display: flex;
  gap: 0.35rem;
  margin-top: 0.5rem;
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}
.primary {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.45rem 1rem;
}
.ghost {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.45rem 1rem;
}
</style>
