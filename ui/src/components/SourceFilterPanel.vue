<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, type GitHubSourcesTree, type TagInfo } from "../api/client";
import { usePlannerStore } from "../stores/planner";

const store = usePlannerStore();
const sources = ref<GitHubSourcesTree | null>(null);
const tags = ref<TagInfo[]>([]);

onMounted(async () => {
  try {
    sources.value = await api.githubSources();
    tags.value = await api.listTags();
  } catch {
    /* optional when API unavailable */
  }
});

function isRepoActive(org: string, repo: string) {
  return (
    store.filterSource === "github" &&
    store.filterOrganisation === org &&
    store.filterRepository === repo
  );
}
</script>

<template>
  <aside class="filter-panel">
    <h3>Sources</h3>
    <button
      type="button"
      class="filter-item"
      :class="{ active: store.filterSource === 'all' && !store.filterOrganisation }"
      @click="store.setSourceFilter('all')"
    >
      All tasks
    </button>
    <button
      type="button"
      class="filter-item"
      :class="{ active: store.filterSource === 'local' }"
      @click="store.setSourceFilter('local')"
    >
      Local tasks
    </button>
    <button
      type="button"
      class="filter-item"
      :class="{ active: store.filterSource === 'github' && !store.filterOrganisation }"
      @click="store.setSourceFilter('github')"
    >
      GitHub (all)
    </button>
    <button type="button" class="sync-btn" @click="store.syncGitHub">Sync GitHub</button>

    <template v-if="sources?.organisations">
      <div v-for="(repos, org) in sources.organisations" :key="org" class="org-block">
        <div class="org-name">{{ org }}</div>
        <button
          v-for="r in repos"
          :key="r.repository"
          type="button"
          class="filter-item repo"
          :class="{ active: isRepoActive(org, r.repository) }"
          @click="store.setSourceFilter('github', org, r.repository)"
        >
          {{ r.repository }}
        </button>
      </div>
    </template>

    <h3>Tags</h3>
    <button
      v-for="t in tags"
      :key="t.id"
      type="button"
      class="filter-item tag"
      :class="{ active: store.filterTags.includes(t.name) }"
      @click="store.toggleTagFilter(t.name)"
    >
      {{ t.name }}
      <span class="count">{{ t.todo_count }}</span>
    </button>
    <p v-if="!tags.length" class="muted">No tags yet</p>
  </aside>
</template>

<style scoped>
.filter-panel {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border);
  max-height: 220px;
  overflow-y: auto;
  font-size: 0.8rem;
}
h3 {
  margin: 0.5rem 0 0.25rem;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
}
.filter-item {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  padding: 0.25rem 0.4rem;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text);
}
.filter-item.active {
  background: var(--accent-soft, #e8f0fe);
  font-weight: 600;
}
.filter-item.repo {
  padding-left: 1rem;
}
.filter-item.tag {
  display: flex;
  justify-content: space-between;
}
.count {
  color: var(--muted);
  font-size: 0.7rem;
}
.org-name {
  font-weight: 600;
  margin-top: 0.35rem;
  padding-left: 0.2rem;
}
.sync-btn {
  margin: 0.35rem 0;
  width: 100%;
  border: 1px solid var(--border);
  background: var(--bg);
  border-radius: 6px;
  padding: 0.3rem;
  font-size: 0.75rem;
  cursor: pointer;
}
.muted {
  color: var(--muted);
  margin: 0.25rem 0;
}
</style>
