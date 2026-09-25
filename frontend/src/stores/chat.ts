// 对话 store：AI 助手消息流 + 历史（支持携带歌单上下文 + 删除/清空）
import { defineStore } from 'pinia'
import { api } from '@/api'
import type { ChatEvent, ChatMessage } from '@/api/types'

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [] as ChatMessage[],
    streaming: false,
  }),
  actions: {
    async loadHistory() {
      try {
        this.messages = await api.chatHistory()
      } catch {
        this.messages = []
      }
    },
    push(msg: ChatMessage) {
      this.messages.push(msg)
    },
    async send(text: string, playlistId?: number): Promise<void> {
      this.push({ role: 'user', content: text })
      this.streaming = true
      const assistant: ChatMessage = { role: 'assistant', content: '', songs: [] }
      this.push(assistant)

      try {
        await api.chatStream(text, (e: ChatEvent) => {
          if (e.type === 'delta' && e.content) {
            assistant.content += e.content
          } else if (e.type === 'songs' && e.songs) {
            assistant.songs = e.songs
          }
        }, playlistId)
      } catch {
        // 后端不可用：Mock 回复
        assistant.content = '（Mock 模式）我理解你想听' + text + '相关的音乐，可以试试在推荐页选择「健身/学习/助眠」场景。'
      } finally {
        this.streaming = false
      }
    },

    /** 删除单条对话（本地移除 + 后端删除） */
    async removeMessage(id: number) {
      this.messages = this.messages.filter((m) => m.id !== id)
      try {
        await api.deleteChatMessage(id)
      } catch {
        /* 已本地删除，后端不可用时忽略 */
      }
    },

    /** 删除一段对话（user + 紧邻的 assistant 一对） */
    removePair(messageId: number) {
      const idx = this.messages.findIndex((m) => m.id === messageId)
      if (idx < 0) return
      // 找相邻的 user/assistant 配对一起删
      const idsToRemove: number[] = [messageId]
      // 如果是 user，往后找下一个 assistant；如果是 assistant，往前找 user
      const cur = this.messages[idx]
      if (cur.role === 'user' && idx + 1 < this.messages.length && this.messages[idx + 1].role === 'assistant') {
        const nextId = this.messages[idx + 1].id
        if (nextId != null) idsToRemove.push(nextId)
      } else if (cur.role === 'assistant' && idx - 1 >= 0 && this.messages[idx - 1].role === 'user') {
        const prevId = this.messages[idx - 1].id
        if (prevId != null) idsToRemove.push(prevId)
      }
      // 本地移除
      this.messages = this.messages.filter((m) => !idsToRemove.includes(m.id ?? -1))
      // 后端逐条删除（不存在的 id 后端会 404，已被忽略）
      void Promise.all(
        idsToRemove.filter((id) => id != null).map((id) =>
          api.deleteChatMessage(id).catch(() => undefined),
        ),
      )
    },

    /** 清空全部历史 */
    async clearAll() {
      this.messages = []
      try {
        await api.clearChatHistory()
      } catch {
        /* 忽略 */
      }
    },
  },
})