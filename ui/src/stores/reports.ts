import { defineStore } from "pinia";
import { ref } from "vue";
import { api, addDays, todayIso, type ReportDraft } from "../api/client";

export const useReportsStore = defineStore("reports", () => {
  const periodFrom = ref(addDays(todayIso(), -6));
  const periodTo = ref(todayIso());
  const useAi = ref(true);
  const recipient = ref("");
  const draft = ref<ReportDraft | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const lastMessageId = ref<string | null>(null);

  async function loadConfig() {
    const cfg = await api.emailConfig();
    if (!recipient.value && cfg.default_to) {
      recipient.value = cfg.default_to;
    }
  }

  async function loadDraft() {
    draft.value = await api.getReportDraft();
  }

  async function generate() {
    loading.value = true;
    error.value = null;
    try {
      draft.value = await api.generateWeeklyReport({
        from: periodFrom.value,
        to: periodTo.value,
        use_ai: useAi.value,
      });
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      loading.value = false;
    }
  }

  async function send() {
    if (!draft.value) {
      error.value = "Generate a draft first";
      return;
    }
    loading.value = true;
    error.value = null;
    try {
      const res = await api.sendReportDraft(recipient.value || undefined);
      lastMessageId.value = res.provider_message_id ?? null;
      await loadDraft();
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      loading.value = false;
    }
  }

  async function cancel() {
    loading.value = true;
    error.value = null;
    try {
      await api.cancelReportDraft();
      draft.value = null;
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      loading.value = false;
    }
  }

  return {
    periodFrom,
    periodTo,
    useAi,
    recipient,
    draft,
    loading,
    error,
    lastMessageId,
    loadConfig,
    loadDraft,
    generate,
    send,
    cancel,
  };
});
