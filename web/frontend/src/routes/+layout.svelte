<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import type { Snippet } from 'svelte';
  import Sidebar from '$components/layout/Sidebar.svelte';
  import Header from '$components/layout/Header.svelte';
  import ToastContainer from '$components/ui/ToastContainer.svelte';
  import LoadingOverlay from '$components/ui/LoadingOverlay.svelte';
  import { api } from '$lib/api/client';
  import {
    health, wsConnected, languages, currentLang, i18n, saveState, loadingSave,
  } from '$stores/index';

  let { children }: { children: Snippet } = $props();
  let ws: WebSocket | null = null;

  onMount(() => {
    bootstrap();
    connectWs();
    return () => ws?.close();
  });

  async function bootstrap() {
    try {
      health.set(await api.health());
    } catch {
      health.set({ status: 'error', version: '?', app_version: '?', game_version: '?', save_loaded: false });
    }
    try {
      saveState.set(await api.saveState());
    } catch { /* ignore */ }
    try {
      const langs = await api.languages();
      languages.set(langs);
      currentLang.set(langs.current);
      const res = await api.i18n(langs.current);
      i18n.set(res.keys);
    } catch { /* ignore - i18n is non-fatal */ }
  }

  function connectWs() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    try {
      const socket = new WebSocket(`${proto}//${location.host}/ws`);
      socket.onopen = () => wsConnected.set(true);
      socket.onclose = () => wsConnected.set(false);
      socket.onerror = () => wsConnected.set(false);
      socket.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'save_state' || data.type === 'save_update') {
            saveState.set(await api.saveState());
          }
        } catch { /* ignore malformed */ }
      };
      ws = socket;
    } catch {
      wsConnected.set(false);
    }
  }
</script>

<div class="flex h-screen overflow-hidden relative z-[1]">
  <Sidebar />
  <div class="flex-1 flex flex-col overflow-hidden">
    <Header />
    <main class="flex-1 overflow-y-auto {$page.url.pathname === '/map' ? '' : 'opacity-[0.90]'}">
      {@render children()}
    </main>
  </div>
</div>

<div class="fixed inset-0 pointer-events-none z-0"
  style="  background: url('/bg-corner.png') no-repeat bottom right / 880px auto;">
</div>

<LoadingOverlay open={$loadingSave} />

<ToastContainer />
