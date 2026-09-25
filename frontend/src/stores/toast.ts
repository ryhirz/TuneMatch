// Toast store：全局轻提示
import { defineStore } from 'pinia'

export interface ToastItem {
  id: number
  text: string
  type: 'info' | 'success' | 'error'
}

let seed = 0

export const useToastStore = defineStore('toast', {
  state: () => ({
    items: [] as ToastItem[],
  }),
  actions: {
    show(text: string, type: ToastItem['type'] = 'info', duration = 2400) {
      const id = ++seed
      this.items.push({ id, text, type })
      setTimeout(() => this.dismiss(id), duration)
    },
    dismiss(id: number) {
      this.items = this.items.filter((t) => t.id !== id)
    },
  },
})
