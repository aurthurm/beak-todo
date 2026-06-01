<script setup lang="ts">
import { VueDraggable } from "vue-draggable-plus";
import { usePlannerStore } from "../stores/planner";
import { addDays, formatDayLabel, todayIso } from "../api/client";
import TaskCard from "./TaskCard.vue";

const store = usePlannerStore();

function shiftCal(n: number) {
  store.calendarStart = addDays(store.calendarStart, n);
  store.refresh();
}

function selectDay(date: string) {
  store.selectedDate = date;
  store.refresh();
}

function onDropToDate(date: string, evt: { item?: HTMLElement }) {
  const id = Number(evt.item?.dataset?.id);
  if (!id) return;
  const todo =
    store.inbox.find((t) => t.id === id) ||
    store.calendarTodos.find((t) => t.id === id);
  if (todo) store.moveToDate(todo, date);
}

function onDropInbox(evt: { item?: HTMLElement }) {
  const id = Number(evt.item?.dataset?.id);
  const todo = store.calendarTodos.find((t) => t.id === id);
  if (todo) store.moveToDate(todo, null);
}

function onDropDone(evt: { item?: HTMLElement }) {
  const id = Number(evt.item?.dataset?.id);
  const todo =
    store.inbox.find((t) => t.id === id) ||
    store.calendarTodos.find((t) => t.id === id);
  if (todo) store.markDone(todo);
}
</script>

<template>
  <section class="calendar-panel">
    <div class="cal-nav">
      <button type="button" @click="shiftCal(-7)">←</button>
      <span>Calendar</span>
      <button type="button" @click="shiftCal(7)">→</button>
    </div>
    <div class="strip">
      <div class="col inbox-col">
        <div class="col-head">Inbox</div>
        <VueDraggable
          v-model="store.inbox"
          group="tasks"
          class="col-body"
          :animation="150"
          @add="onDropInbox"
        >
          <div v-for="t in store.inbox" :key="t.id" :data-id="t.id">
            <TaskCard :todo="t" @click="store.detailTodoId = t.id" />
          </div>
        </VueDraggable>
      </div>
      <div
        v-for="col in store.dayColumns"
        :key="col.date"
        class="col"
        :class="{ selected: col.date === store.selectedDate, today: col.date === todayIso() }"
        @click="selectDay(col.date)"
      >
        <div class="col-head">{{ formatDayLabel(col.date) }}</div>
        <VueDraggable
          :model-value="col.todos"
          group="tasks"
          class="col-body"
          :animation="150"
          @add="(e) => onDropToDate(col.date, e)"
        >
          <div
            v-for="t in col.todos"
            :key="t.id"
            :data-id="t.id"
            @click.stop="store.detailTodoId = t.id"
          >
            <TaskCard :todo="t" />
          </div>
        </VueDraggable>
      </div>
      <div class="col done-col">
        <div class="col-head">Done</div>
        <VueDraggable
          :model-value="[]"
          group="tasks"
          class="col-body done-drop"
          :animation="150"
          @add="onDropDone"
        >
          <p class="drop-hint">Drop to complete</p>
        </VueDraggable>
      </div>
    </div>
  </section>
</template>

<style scoped>
.calendar-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: var(--bg);
}
.cal-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid var(--border);
}
.cal-nav button {
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: 6px;
  padding: 0.25rem 0.6rem;
}
.strip {
  display: flex;
  flex: 1;
  overflow-x: auto;
  padding: 0.5rem;
  gap: 0.5rem;
}
.col {
  min-width: 160px;
  max-width: 180px;
  flex-shrink: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
}
.col.selected {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent);
}
.col.today .col-head {
  color: var(--accent);
  font-weight: 600;
}
.col-head {
  padding: 0.5rem;
  font-size: 0.75rem;
  border-bottom: 1px solid var(--border);
  text-align: center;
}
.col-body {
  flex: 1;
  min-height: 120px;
  padding: 0.35rem;
  overflow-y: auto;
}
.done-drop {
  min-height: 80px;
}
.drop-hint {
  color: var(--muted);
  font-size: 0.7rem;
  text-align: center;
  margin: 1rem 0;
}
.inbox-col {
  min-width: 140px;
}
.done-col {
  min-width: 100px;
}
</style>
