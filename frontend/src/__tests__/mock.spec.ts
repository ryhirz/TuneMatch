// 前端单元测试：mock API 推荐逻辑 + Toast store
import { describe, expect, it } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

import { mockApi } from '../api/mock'
import { useToastStore } from '../stores/toast'

describe('mockApi.recommend', () => {
  it('按标签返回推荐歌曲且字段完整', async () => {
    const res = await mockApi.recommend({ mode: 'tags', tags: ['摇滚'], limit: 4 })
    expect(res.code).toBe(0)
    expect(res.data.songs.length).toBeGreaterThan(0)
    expect(res.data.songs.length).toBeLessThanOrEqual(4)
    for (const s of res.data.songs) {
      expect(s.title).toBeTruthy()
      expect(s.artist).toBeTruthy()
      expect(s.match).toBeGreaterThanOrEqual(0)
      expect(s.match).toBeLessThanOrEqual(100)
    }
  })

  it('无匹配标签时回退全库', async () => {
    const res = await mockApi.recommend({ mode: 'tags', tags: ['不存在的标签XYZ'], limit: 5 })
    expect(res.data.songs.length).toBeGreaterThan(0)
  })

  it('文本模式按标题搜索', async () => {
    const res = await mockApi.recommend({ mode: 'text', text: '晴天', limit: 5 })
    expect(res.data.songs.some((s) => s.title.includes('晴天'))).toBe(true)
  })
})

describe('toast store', () => {
  it('show 后 items 增加,dismiss 后移除', () => {
    setActivePinia(createPinia())
    const toast = useToastStore()
    toast.show('测试提示', 'success')
    expect(toast.items.length).toBe(1)
    expect(toast.items[0].type).toBe('success')
    toast.dismiss(toast.items[0].id)
    expect(toast.items.length).toBe(0)
  })
})
