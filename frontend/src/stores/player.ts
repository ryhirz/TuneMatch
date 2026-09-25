// 全局播放器 store：真实音频播放(Web Audio) + 10 段 EQ + 队列 + 进度
// - 有 audio_url 的歌曲走真实 <audio> + Web Audio 图(source → 10×BiquadFilter → gain → out)
// - 无音频的曲库内置歌单走模拟进度(保留原逻辑)
import { defineStore } from 'pinia'
import { useToastStore } from '@/stores/toast'
import type { Song } from '@/api/types'

let progressTimer: ReturnType<typeof setInterval> | null = null

/** 10 段 EQ 频率(Hz) */
export const EQ_FREQS = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
export const EQ_RANGE = 12 // ±12dB

/** 常用预设 */
export const EQ_PRESETS: Record<string, number[]> = {
  平直: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  低音增强: [6, 5, 3, 1, 0, 0, 0, 0, 0, 0],
  高音增强: [0, 0, 0, 0, 0, 1, 3, 5, 6, 6],
  人声突出: [0, 0, 1, 3, 4, 3, 1, 0, 0, 0],
  爵士: [3, 2, 1, 2, -1, 2, 3, 2, 1, 1],
  摇滚: [5, 3, 0, -1, 2, 3, 4, 4, 3, 2],
  古典: [4, 3, 2, 1, -1, 0, 1, 3, 4, 4],
  流行: [-1, 1, 3, 3, 2, 0, 0, 1, 1, 1],
}

function loadEqFromStorage(): Record<string, number> {
  try {
    const raw = localStorage.getItem('tm_eq')
    if (raw) {
      const parsed = JSON.parse(raw) as Record<string, number>
      if (parsed && typeof parsed === 'object') return parsed
    }
  } catch {
    /* ignore */
  }
  return {}
}

// ---------- 单例 Web Audio 引擎 ----------
// 注意：MediaElementSource 接管 audioEl 后 audioEl.setSinkId() 会失效，
// 必须用 AudioContext({ sinkId }) 在创建 ctx 时指定，或重建 ctx 来切换设备。
let audioEl: HTMLAudioElement | null = null
let audioCtx: AudioContext | null = null
let mediaSource: MediaElementAudioSourceNode | null = null
let filters: BiquadFilterNode[] = []
let masterGain: GainNode | null = null

/** 当前播放状态快照(用于 ctx 重建后恢复) */
function snapshotPlayer() {
  if (!audioEl) return null
  return {
    src: audioEl.src,
    currentTime: audioEl.currentTime,
    paused: audioEl.paused,
    volume: audioEl.volume,
  }
}

/** 关闭并销毁音频图(释放 MediaElementSource / AudioContext) */
async function destroyAudioGraph() {
  if (audioEl) {
    try {
      audioEl.pause()
      audioEl.ontimeupdate = null
      audioEl.onended = null
      audioEl.onpause = null
      audioEl.onplay = null
      audioEl.onerror = null
    } catch {
      /* 忽略 */
    }
  }
  if (audioCtx && audioCtx.state !== 'closed') {
    try {
      await audioCtx.close()
    } catch {
      /* 忽略 */
    }
  }
  audioEl = null
  audioCtx = null
  mediaSource = null
  filters = []
  masterGain = null
}

/** 构建音频图（可指定 sinkId 切换输出设备）。返回 audioEl。 */
function buildAudioGraph(sinkId: string | null) {
  const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
  try {
    audioCtx = sinkId ? new Ctx({ sinkId } as AudioContextOptions) : new Ctx()
  } catch {
    audioCtx = new Ctx() // 兜底：sinkId 不支持时普通创建
  }

  audioEl = new Audio()
  audioEl.preload = 'auto'
  // 关键：MediaElementSource 接管 audioEl 后，浏览器（Chrome/Edge）会强制要求
  // audioEl 必须有 crossOrigin 属性（即使同源），否则解码失败报 "no supported source"。
  // 必须在 createMediaElementSource 之前设置，source 创建后此属性无法再改。
  audioEl.crossOrigin = 'anonymous'
  if (sinkId && typeof (audioEl as HTMLAudioElement & { setSinkId?: (id: string) => Promise<void> }).setSinkId === 'function') {
    ;(audioEl as HTMLAudioElement & { setSinkId: (id: string) => Promise<void> }).setSinkId(sinkId).catch(() => {})
  }

  mediaSource = audioCtx.createMediaElementSource(audioEl)
  masterGain = audioCtx.createGain()
  masterGain.gain.value = 0.8

  filters = EQ_FREQS.map((freq) => {
    const f = audioCtx!.createBiquadFilter()
    f.type = 'peaking'
    f.frequency.value = freq
    f.Q.value = 1.0
    f.gain.value = 0
    return f
  })

  let node: AudioNode = mediaSource
  for (const flt of filters) {
    node.connect(flt)
    node = flt
  }
  node.connect(masterGain)
  masterGain.connect(audioCtx.destination)
}

/** 首次播放时确保音频图存在(不指定 sinkId,走系统默认) */
function ensureAudioGraph() {
  if (audioCtx) return
  buildAudioGraph(null)
}

/** 绑定 audioEl 事件到 store(重建 ctx 后需重新绑定) */
function bindAudioEvents(self: {
  isRealAudio: boolean
  playing: boolean
  duration: number
  progress: number
  _startTick: () => void
}) {
  if (!audioEl) return
  audioEl.ontimeupdate = () => {
    if (audioEl!.duration && isFinite(audioEl!.duration)) {
      self.duration = audioEl!.duration
      self.progress = (audioEl!.currentTime / audioEl!.duration) * 100
    }
  }
  audioEl.onended = () => usePlayerStore().next()
  audioEl.onpause = () => {
    if (audioEl!.ended) return
    self.playing = false
  }
  audioEl.onplay = () => {
    self.playing = true
  }
  audioEl.onerror = () => {
    useToastStore().show('音频加载失败（CORS/路径/格式）', 'error', 4000)
    self.isRealAudio = false
    self._startTick()
  }
}

function applyEqToFilters(eq: Record<string, number>) {
  filters.forEach((flt, i) => {
    const freq = EQ_FREQS[i]
    const val = eq[String(freq)] ?? 0
    flt.gain.setTargetAtTime(val, audioCtx!.currentTime, 0.02)
  })
}

export const usePlayerStore = defineStore('player', {
  state: () => ({
    queue: [] as Song[],
    index: -1,
    playing: false,
    progress: 0, // 0-100
    duration: 0, // 秒
    volume: 0.8,
    showQueue: false,
    showEq: false,
    showDevice: false,
    eq: loadEqFromStorage() as Record<string, number>,
    isRealAudio: false, // 当前是否为真实音频(有 audio_url)
    audioUrl: '', // 当前真实播放的 URL（远程/本地）
    outputDevices: [] as MediaDeviceInfo[],
    outputDeviceId: '' as string,
  }),
  getters: {
    current: (s): Song | null => (s.index >= 0 && s.index < s.queue.length ? s.queue[s.index] : null),
    hasQueue: (s): boolean => s.queue.length > 0,
    currentEq: (s): number[] => EQ_FREQS.map((f) => s.eq[String(f)] ?? 0),
  },
  actions: {
    playSong(song: Song, queue?: Song[]) {
      if (queue && queue.length) {
        this.queue = queue
        this.index = queue.findIndex((x) => x.id === song.id)
        if (this.index < 0) this.index = 0
      } else {
        if (!this.queue.some((x) => x.id === song.id)) {
          this.queue.unshift(song)
          this.index = 0
        } else {
          this.index = this.queue.findIndex((x) => x.id === song.id)
        }
      }
      this.progress = 0
      this.duration = (song.duration || 200000) / 1000
      void this._loadCurrent()
    },
    toggle() {
      if (!this.current) return
      this.playing = !this.playing
      if (this.playing) {
        void this._play()
      } else {
        this._pause()
      }
    },
    next() {
      if (!this.queue.length) return
      this.index = (this.index + 1) % this.queue.length
      this.progress = 0
      void this._loadCurrent()
    },
    prev() {
      if (!this.queue.length) return
      this.index = (this.index - 1 + this.queue.length) % this.queue.length
      this.progress = 0
      void this._loadCurrent()
    },
    seek(p: number) {
      this.progress = Math.min(100, Math.max(0, p))
      if (this.isRealAudio && audioEl) {
        audioEl.currentTime = (this.progress / 100) * this.duration
      }
    },
    setVolume(v: number) {
      this.volume = Math.min(1, Math.max(0, v))
      if (masterGain) masterGain.gain.setTargetAtTime(this.volume, audioCtx!.currentTime, 0.02)
      if (audioEl) audioEl.volume = this.volume
    },
    // ---------- EQ ----------
    setEq(freq: number, gain: number) {
      this.eq[String(freq)] = Math.max(-EQ_RANGE, Math.min(EQ_RANGE, gain))
      this._persistEq()
      if (audioCtx && filters.length) {
        const idx = EQ_FREQS.indexOf(freq)
        if (idx >= 0) {
          filters[idx].gain.setTargetAtTime(this.eq[String(freq)], audioCtx.currentTime, 0.02)
        }
      }
    },
    applyPreset(name: string) {
      const vals = EQ_PRESETS[name]
      if (!vals) return
      EQ_FREQS.forEach((f, i) => {
        this.eq[String(f)] = vals[i]
      })
      this._persistEq()
      if (audioCtx && filters.length) applyEqToFilters(this.eq)
    },
    resetEq() {
      EQ_FREQS.forEach((f) => {
        this.eq[String(f)] = 0
      })
      this._persistEq()
      if (audioCtx && filters.length) applyEqToFilters(this.eq)
    },
    _persistEq() {
      try {
        localStorage.setItem('tm_eq', JSON.stringify(this.eq))
      } catch {
        /* ignore */
      }
    },

    /** 让外部(如自定义预设)即时刷新 Web Audio 滤波器 */
    refreshFilters() {
      if (audioCtx && filters.length) applyEqToFilters(this.eq)
    },

    // ---------- 内部：真实播放 ----------
    _loadCurrent() {
      const song = this.current
      if (!song) return
      const url = song.audio_url
      this.isRealAudio = Boolean(url && url.trim())
      this.playing = true

      if (this.isRealAudio) {
        // 远程音频（iTunes 等）直接 <audio> 播放：零 CORS 图负担，最稳
        if (/^https?:\/\//i.test(url!)) {
          void this._setupRemoteAudio(url!)
        } else {
          // 本地上传音频：走 Web Audio 图（EQ 可用）
          void this._setupRealAudio(url!)
        }
      } else {
        this._teardownRealAudio()
        this._startTick()
      }
    },
    /** 远程音频（https 链接，如 iTunes previewUrl）：直接用 audio 元素播放，不建 Web Audio 图 */
    async _setupRemoteAudio(url: string) {
      this._teardownRealAudio()
      audioEl = new Audio()
      audioEl.preload = 'auto'
      audioEl.src = url
      audioEl.volume = this.volume
      bindAudioEvents(this)
      this.audioUrl = url

      try {
        await audioEl.play()
        if (audioEl.readyState < 2) {
          useToastStore().show('音频正在缓冲...', 'info', 1800)
        }
      } catch (e) {
        useToastStore().show(`浏览器拒绝播放：${(e as Error).message || 'autoplay policy'}`, 'error', 4000)
        this.playing = false
      }
    },
    async _setupRealAudio(url: string) {
      ensureAudioGraph()
      if (!audioEl || !audioCtx) return

      // 注：前端预检（用临时 Audio 探测）曾在 Edge 上对合法 WAV 误判 onerror，
      // 把标准 PCM WAV 都误杀。改为完全不预检，直接走真实播放链路，
      // 真正有问题时依赖 audioEl.onerror 兜底（toast 提示 + 降级模拟）。
      // 后端 upload 时 _is_valid_audio 已作为守门。

      // 1) 等待 ctx 真正 running（autoplay policy）
      try {
        if (audioCtx.state === 'suspended') await audioCtx.resume()
      } catch {
        /* 忽略 */
      }
      const t0 = performance.now()
      while (audioCtx.state !== 'running' && performance.now() - t0 < 500) {
        await new Promise((r) => setTimeout(r, 20))
      }

      if (audioCtx.state !== 'running') {
        useToastStore().show('音频引擎未启动，请点击页面任意位置后再播放', 'error', 4000)
        this.playing = false
        return
      }

      // 2) 应用 EQ + 音量
      applyEqToFilters(this.eq)
      masterGain!.gain.setTargetAtTime(this.volume, audioCtx.currentTime, 0.02)

      // 3) 设置 src（注意：MediaElementSource 已接管 audio 元素，声音只从 ctx 流出）
      audioEl.src = url
      audioEl.volume = this.volume
      audioEl.currentTime = (this.progress / 100) * this.duration
      bindAudioEvents(this)

      // 4) 播放
      try {
        await audioEl.play()
        // 验证 readyState（0=HAVE_NOTHING, 1=HAVE_METADATA, 2=HAVE_CURRENT_DATA, 3=HAVE_FUTURE_DATA, 4=HAVE_ENOUGH_DATA）
        if (audioEl.readyState < 2) {
          useToastStore().show('音频正在缓冲...', 'info', 1800)
        }
      } catch (e) {
        useToastStore().show(`浏览器拒绝播放：${(e as Error).message || 'autoplay policy'}`, 'error', 4000)
        this.playing = false
      }
    },
    async _play() {
      if (this.isRealAudio && audioEl) {
        // 远程音频：直接 play，不建 Web Audio 图
        if (/^https?:\/\//i.test(this.audioUrl)) {
          try {
            await audioEl.play()
          } catch (e) {
            useToastStore().show(`浏览器拒绝播放：${(e as Error).message || 'autoplay policy'}`, 'error', 4000)
          }
          return
        }
        // 本地音频：走 Web Audio 图
        ensureAudioGraph()
        try {
          if (audioCtx!.state === 'suspended') await audioCtx!.resume()
        } catch {
          /* 忽略 */
        }
        const t0 = performance.now()
        while (audioCtx!.state !== 'running' && performance.now() - t0 < 300) {
          await new Promise((r) => setTimeout(r, 20))
        }
        try {
          await audioEl.play()
        } catch (e) {
          useToastStore().show(`浏览器拒绝播放：${(e as Error).message || 'autoplay policy'}`, 'error', 4000)
        }
      } else {
        this._startTick()
      }
    },

    // ---------- 输出设备 ----------
    /**
     * 枚举所有音频输出设备。先申请麦克风权限（getUserMedia）拿到设备 label，
     * 因为浏览器只有获得过设备权限后 enumerateDevices 才会返回完整 label。
     */
    async refreshOutputDevices(): Promise<void> {
      if (!navigator.mediaDevices?.enumerateDevices) {
        this.outputDevices = []
        return
      }
      try {
        // 1) 短暂打开麦克风流触发设备权限授权（立即关闭）
        if (navigator.mediaDevices.getUserMedia) {
          try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            stream.getTracks().forEach((t) => t.stop())
          } catch {
            /* 用户拒绝授权：依然能 enumerateDevices，但 label 会是空 */
          }
        }
        // 2) 枚举设备
        const devs = await navigator.mediaDevices.enumerateDevices()
        this.outputDevices = devs.filter((d) => d.kind === 'audiooutput')
      } catch {
        this.outputDevices = []
      }
    },
    /**
     * 切换音频输出设备。MediaElementSource 接管 audioEl 后 audioEl.setSinkId 无效，
     * 所以采用重建 AudioContext({ sinkId }) 的方式切换，并保留播放进度。
     * Chrome 110+ / Edge 110+ 都支持 AudioContext sinkId 选项。
     */
    async setOutputDevice(deviceId: string): Promise<boolean> {
      this.outputDeviceId = deviceId

      // 检测浏览器是否支持 AudioContext sinkId 选项（Chrome 110+/Edge 110+ 都支持）
      const supportsCtxSinkId = typeof window !== 'undefined' && 'AudioContext' in window
      // 简化判断：直接尝试创建 sinkId ctx；浏览器不支持会抛错或被忽略
      if (!supportsCtxSinkId) {
        useToastStore().show('当前浏览器不支持切换输出设备', 'error', 3500)
        return false
      }

      // 快照当前播放状态
      const snap = snapshotPlayer()
      const wasRealAudio = this.isRealAudio
      const wasPlaying = !snap?.paused && snap?.src

      // 关闭旧 ctx
      await destroyAudioGraph()

      try {
        // 用新 sinkId 重建
        buildAudioGraph(deviceId || null)
        // 重新应用 EQ + 音量
        applyEqToFilters(this.eq)
        if (masterGain && audioEl) {
          masterGain.gain.value = this.volume
          audioEl.volume = this.volume
        }
        // 重新绑定事件
        bindAudioEvents({
          isRealAudio: this.isRealAudio,
          playing: this.playing,
          duration: this.duration,
          progress: this.progress,
          _startTick: () => this._startTick(),
        })
        // 恢复播放（如果之前在播放）
        if (wasRealAudio && snap?.src && audioEl && audioCtx) {
          if (audioCtx.state === 'suspended') {
            try { await audioCtx.resume() } catch { /* ignore */ }
          }
          audioEl.src = snap.src
          audioEl.currentTime = snap.currentTime
          if (wasPlaying) {
            try { await audioEl.play() } catch { /* 用户手势失效时静音 */ }
          }
        }
        const dev = this.outputDevices.find((d) => d.deviceId === deviceId)
        useToastStore().show(
          `已切换到「${dev?.label || '系统默认输出'}」${this.outputDeviceId ? '' : '（系统默认）'}`,
          'success',
          2500,
        )
        return true
      } catch (e) {
        useToastStore().show('切换设备失败：' + ((e as Error).message || '未知错误'), 'error', 3500)
        return false
      }
    },
    _pause() {
      if (this.isRealAudio && audioEl) {
        audioEl.pause()
      } else if (progressTimer) {
        clearInterval(progressTimer)
        progressTimer = null
      }
    },
    _teardownRealAudio() {
      if (audioEl) {
        audioEl.pause()
        audioEl.src = ''
        audioEl.ontimeupdate = null
        audioEl.onended = null
        audioEl.onpause = null
        audioEl.onplay = null
        audioEl.onerror = null
      }
    },

    // ---------- 内部：模拟进度 ----------
    _startTick() {
      if (progressTimer) clearInterval(progressTimer)
      const durMs = this.current?.duration || 200000
      const step = 100 / (durMs / 1000)
      progressTimer = setInterval(() => {
        if (!this.playing) return
        this.progress += step
        if (this.progress >= 100) {
          this.progress = 0
          this.next()
        }
      }, 1000)
    },
  },
})
