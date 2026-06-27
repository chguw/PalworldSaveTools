<script lang="ts">
  let { size = 20, class: klass = '' }: { size?: number; class?: string } = $props();
</script>

<span
  class={klass}
  style="width:{size}px;height:{size}px;border-radius:9999px;border:{Math.max(2, size / 8)}px solid rgba(59,142,208,0.25);border-top-color:#3B8ED0;display:inline-block;animation:spin 0.7s linear infinite;"
></span>

<style>
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
