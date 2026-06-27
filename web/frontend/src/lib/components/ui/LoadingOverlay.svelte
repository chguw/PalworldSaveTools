<script lang="ts">
  import { untrack } from 'svelte';
  import Icon from '@iconify/svelte';

  let { open = false, onCancel }: { open: boolean; onCancel?: () => void } = $props();

  const phrases = [
    'FORCING PALS TO WORK OVERTIME...',
    'CONDENSING EXTRA PALS INTO JUICE...',
    'CRACKING THE PROGRESSIVE WORK WHIP...',
    'PETTING THE CHILLETS FOR LUCK...',
    'IGNORING SANITY DEPLETION...',
    'FEEDING BERRIES TO DEPRESSED LAMBALLS...',
    'CALIBRATING PALBOX COORDINATES...',
    'CLEANING UP AFTER A RAID...',
    'SEARCHING FOR LUCKY PALS...',
    'OPTIMIZING WORKFLOW EFFICIENCY...',
    'REPLACING TIRED PALS WITH FRESHER MODELS...',
    'CONVINCING DEPRESSED PALS THE VIEW IS BETTER FROM THE ASSEMBLY LINE...',
    'RECYCLING UNSATISFACTORY SPECIMENS...',
    'UPDATING WORKER CONTRACTS (NOW WITH 0% BREAK TIME)...',
    'TELLING THE LOVEANDERS TO SETTLE DOWN...',
    'HARVESTING PAL FLUIDS... DON\'T ASK HOW...',
    'SHARPENING THE BUTCHER\'S CLEAVER FOR VALUATION...',
    'TELLING THE GUMOSS IT\'S JUST A HAIRCUT...',
    'UPGRADING THE ELECTRICITY GENERATOR WITH MORE SPARKITS...',
    'REASSURING THE CREW THAT THE PAL FLUID IS JUST BLUE GATORADE...',
  ];

  let phraseIdx = $state(0);
  let seconds = $state(0);
  let fading = $state(false);

  let tick: ReturnType<typeof setInterval> | undefined;
  let cycle: ReturnType<typeof setInterval> | undefined;

  function stop() {
    if (tick !== undefined) { clearInterval(tick); tick = undefined; }
    if (cycle !== undefined) { clearInterval(cycle); cycle = undefined; }
  }

  $effect(() => {
    if (open) {
      untrack(() => {
        seconds = 0;
        phraseIdx = Math.floor(Math.random() * phrases.length);
        tick = setInterval(() => seconds++, 1000);
        cycle = setInterval(() => {
          fading = true;
          setTimeout(() => {
            phraseIdx = (phraseIdx + 1) % phrases.length;
            fading = false;
          }, 350);
        }, 3000);
      });
    } else {
      stop();
    }
    return stop;
  });

  function fmtTime(s: number): string {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape' && open && onCancel) onCancel();
  }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in"
    role="dialog" aria-modal="true">
    <div class="w-[420px] rounded-2xl bg-[rgba(18,20,24,0.95)] border border-accent/10 shadow-2xl animate-slide-up">
      <div class="flex flex-col items-center gap-4 px-10 py-8">
        <Icon icon="eos-icons:loading" width={40} class="text-accent" />

        <div class="w-full h-1 rounded-full overflow-hidden bg-white/5">
          <div class="h-full w-1/3 rounded-full bg-gradient-to-r from-sky-400 to-violet-500 animate-loading-bar"></div>
        </div>

        <p class="text-sm font-semibold text-ink-emphasis text-center h-10 flex items-center justify-center leading-snug transition-opacity duration-300"
          class:opacity-0={fading}>
          {phrases[phraseIdx]}
        </p>

        <p class="text-xs text-ink-dim/40 tabular-nums">{fmtTime(seconds)}</p>

        {#if onCancel}
          <button
            onclick={onCancel}
            class="text-xs text-ink-dim/60 hover:text-ink-secondary transition-colors px-3 py-1 rounded-md bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06]"
          >
            ESC to cancel
          </button>
        {/if}
      </div>
    </div>
  </div>
{/if}
