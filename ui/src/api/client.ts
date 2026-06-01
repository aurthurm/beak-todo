export interface Todo {
  id: number;
  message: string;
  priority: number;
  priority_label: string;
  priority_color: string;
  category: string;
  completed: boolean;
  due_date: string | null;
  sort_order: number;
}

export interface ParsedTask {
  message: string;
  priority: number;
  category: string;
  due_date: string | null;
}

export interface Note {
  id: number;
  todo_id: number;
  content: string;
  created_at: string;
}

export interface PlanResponse {
  horizon: string;
  items: { task_id?: number; title: string; rationale: string }[];
  summary: string;
}

export interface ActionPreview {
  description: string;
  patches: {
    todo_id: number;
    due_date?: string | null;
    clear_due?: boolean;
    priority?: number;
    completed?: boolean;
    message?: string;
  }[];
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  health: () => req<{ status: string; ai_enabled: boolean }>("/health"),

  listTodos: (params: Record<string, string | boolean>) => {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "") q.set(k, String(v));
    }
    return req<Todo[]>(`/todos?${q}`);
  },

  getTodo: (id: number) => req<Todo>(`/todos/${id}`),

  createTodo: (body: Partial<Todo> & { message: string }) =>
    req<Todo>("/todos", { method: "POST", body: JSON.stringify(body) }),

  patchTodo: (id: number, body: Record<string, unknown>) =>
    req<Todo>(`/todos/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  reorder: (items: { id: number; sort_order: number }[]) =>
    req<{ ok: boolean }>("/todos/reorder", {
      method: "POST",
      body: JSON.stringify({ items }),
    }),

  deleteTodo: (id: number) =>
    req<void>(`/todos/${id}`, { method: "DELETE" }),

  listNotes: (todoId: number) => req<Note[]>(`/todos/${todoId}/notes`),

  addNote: (todoId: number, content: string) =>
    req<{ id: number }>(`/todos/${todoId}/notes`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),

  brainDump: (text: string) =>
    req<{ tasks: ParsedTask[] }>("/ai/brain-dump", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  brainDumpApply: (tasks: ParsedTask[]) =>
    req<{ ids: number[] }>("/ai/brain-dump/apply", {
      method: "POST",
      body: JSON.stringify({ tasks }),
    }),

  plan: (horizon: string) =>
    req<PlanResponse>("/ai/plan", {
      method: "POST",
      body: JSON.stringify({ horizon }),
    }),

  chat: (message: string) =>
    req<{ answer: string }>("/ai/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  actionPreview: (request: string) =>
    req<ActionPreview>("/ai/actions/preview", {
      method: "POST",
      body: JSON.stringify({ request }),
    }),

  actionApply: (patches: ActionPreview["patches"]) =>
    req<{ applied: number }>("/ai/actions/apply", {
      method: "POST",
      body: JSON.stringify({ patches }),
    }),
};

export function formatDayLabel(iso: string): string {
  const d = new Date(iso + "T12:00:00");
  return d.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
}

export function addDays(iso: string, n: number): string {
  const d = new Date(iso + "T12:00:00");
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

export function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}
