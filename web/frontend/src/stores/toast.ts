import { writable } from 'svelte/store';

export type ToastKind = 'info' | 'success' | 'warning' | 'error';
export interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

export const toasts = writable<Toast[]>([]);

let nextId = 1;

export function pushToast(kind: ToastKind, message: string, ttl = 4000): void {
  const id = nextId++;
  toasts.update((list) => [...list, { id, kind, message }]);
  if (ttl > 0) {
    setTimeout(() => dismissToast(id), ttl);
  }
}

export function dismissToast(id: number): void {
  toasts.update((list) => list.filter((t) => t.id !== id));
}

export const toast = {
  info: (m: string) => pushToast('info', m),
  success: (m: string) => pushToast('success', m),
  warning: (m: string) => pushToast('warning', m),
  error: (m: string) => pushToast('error', m, 8000),
};
