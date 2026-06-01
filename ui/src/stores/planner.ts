import { defineStore } from "pinia";
import { ref, computed } from "vue";
import {
  api,
  todayIso,
  addDays,
  type Todo,
  type ParsedTask,
  type ActionPreview,
} from "../api/client";

export const usePlannerStore = defineStore("planner", () => {
  const selectedDate = ref(todayIso());
  const calendarStart = ref(addDays(todayIso(), -3));
  const calendarDays = 14;
  const inbox = ref<Todo[]>([]);
  const calendarTodos = ref<Todo[]>([]);
  const dayTodos = ref<Todo[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const brainDumpText = ref("");
  const suggestions = ref<ParsedTask[]>([]);
  const selectedSuggestions = ref<Set<number>>(new Set());

  const drawerOpen = ref(false);
  const drawerMessage = ref("");
  const drawerReply = ref("");
  const actionPreview = ref<ActionPreview | null>(null);

  const detailTodoId = ref<number | null>(null);
  const mobileTab = ref<"inbox" | "calendar" | "today" | "ai">("inbox");

  const calendarEnd = computed(() =>
    addDays(calendarStart.value, calendarDays - 1)
  );

  const dayColumns = computed(() => {
    const cols: { date: string; todos: Todo[] }[] = [];
    for (let i = 0; i < calendarDays; i++) {
      const date = addDays(calendarStart.value, i);
      cols.push({
        date,
        todos: calendarTodos.value.filter(
          (t) => t.due_date === date && !t.completed
        ),
      });
    }
    return cols;
  });

  async function refresh() {
    loading.value = true;
    error.value = null;
    try {
      const [inboxData, calData, dayData] = await Promise.all([
        api.listTodos({ inbox: true }),
        api.listTodos({
          due_from: calendarStart.value,
          due_to: calendarEnd.value,
          completed: false,
        }),
        api.listTodos({ due_date: selectedDate.value }),
      ]);
      inbox.value = inboxData;
      calendarTodos.value = calData;
      dayTodos.value = dayData;
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      loading.value = false;
    }
  }

  async function patchTodo(id: number, patch: Record<string, unknown>) {
    await api.patchTodo(id, patch);
    await refresh();
  }

  async function moveToDate(todo: Todo, date: string | null) {
    if (date) {
      await patchTodo(todo.id, { due_date: date, clear_due: false });
    } else {
      await patchTodo(todo.id, { clear_due: true });
    }
  }

  async function markDone(todo: Todo) {
    await patchTodo(todo.id, { completed: true });
  }

  async function organiseBrainDump() {
    const res = await api.brainDump(brainDumpText.value);
    suggestions.value = res.tasks;
    selectedSuggestions.value = new Set(res.tasks.map((_, i) => i));
  }

  async function applySuggestions() {
    const tasks = suggestions.value.filter((_, i) =>
      selectedSuggestions.value.has(i)
    );
    await api.brainDumpApply(tasks);
    suggestions.value = [];
    brainDumpText.value = "";
    await refresh();
  }

  function goToday() {
    const t = todayIso();
    selectedDate.value = t;
    calendarStart.value = addDays(t, -3);
    refresh();
  }

  function goThisWeek() {
    const t = todayIso();
    const day = new Date(t + "T12:00:00").getDay();
    const mondayOffset = day === 0 ? -6 : 1 - day;
    calendarStart.value = addDays(t, mondayOffset);
    selectedDate.value = t;
    refresh();
  }

  async function runAiPlan() {
    drawerOpen.value = true;
    drawerReply.value = "";
    const plan = await api.plan("today");
    drawerReply.value =
      (plan.summary ? plan.summary + "\n\n" : "") +
      plan.items.map((it, i) => `${i + 1}. ${it.title}${it.rationale ? " — " + it.rationale : ""}`).join("\n");
  }

  async function sendDrawerMessage(msg: string) {
    drawerMessage.value = msg;
    actionPreview.value = null;
    try {
      const preview = await api.actionPreview(msg);
      if (preview.patches?.length) {
        actionPreview.value = preview;
        drawerReply.value = preview.description;
      } else {
        const chat = await api.chat(msg);
        drawerReply.value = chat.answer;
      }
    } catch {
      const chat = await api.chat(msg);
      drawerReply.value = chat.answer;
    }
  }

  async function applyActionPreview() {
    if (!actionPreview.value) return;
    await api.actionApply(actionPreview.value.patches);
    actionPreview.value = null;
    await refresh();
  }

  return {
    selectedDate,
    calendarStart,
    calendarDays,
    inbox,
    calendarTodos,
    dayTodos,
    loading,
    error,
    brainDumpText,
    suggestions,
    selectedSuggestions,
    drawerOpen,
    drawerMessage,
    drawerReply,
    actionPreview,
    detailTodoId,
    mobileTab,
    dayColumns,
    refresh,
    patchTodo,
    moveToDate,
    markDone,
    organiseBrainDump,
    applySuggestions,
    goToday,
    goThisWeek,
    runAiPlan,
    sendDrawerMessage,
    applyActionPreview,
  };
});
