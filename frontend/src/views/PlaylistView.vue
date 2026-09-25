<!-- 页面：歌单管理（独立路由）/playlists
我的歌单列表 + 新建/编辑/删除 + 详情 + 拖拽导入 -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { ImportResult, Playlist } from '@/api/types'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import DropZoneUpload from '@/components/DropZoneUpload.vue'
import PlaylistEditDialog from '@/components/PlaylistEditDialog.vue'
import PlaylistImportDialog from '@/components/PlaylistImportDialog.vue'
import { usePlayerStore } from '@/stores/player'
import { usePlaylistStore } from '@/stores/playlist'
import { useToastStore } from '@/stores/toast'

const importDialog = ref<InstanceType<typeof PlaylistImportDialog> | null>(null)

const playlistStore = usePlaylistStore()
const player = usePlayerStore()
const toast = useToastStore()

// 编辑弹窗
const editingPlaylist = ref<Playlist | null>(null)

// 删除确认
const showDeleteConfirm = ref(false)
const pendingDeleteId = ref(0)

// 当前选中的歌单（详情展示用）
const selectedId = ref<number>(0)

onMounted(async () => {
  await playlistStore.fetchAll()
  if (playlistStore.playlists.length && !selectedId.value) {
    selectedId.value = playlistStore.playlists[0].id
  }
})

const active = computed(() => playlistStore.playlists.find((p) => p.id === selectedId.value) || null)

function select(pl: Playlist) {
  selectedId.value = pl.id
  playlistStore.select(pl.id)
}

function createPlaylist() {
  playlistStore.create('新建歌单').then((pl) => {
    editingPlaylist.value = pl
    selectedId.value = pl.id
  })
}

function openEdit(pl: Playlist) {
  selectedId.value = pl.id
  editingPlaylist.value = pl
}

async function savePlaylist(patch: { name: string; cover_color: string }) {
  if (!editingPlaylist.value) return
  await playlistStore.update(editingPlaylist.value.id, patch)
  editingPlaylist.value = null
  toast.show('歌单已保存', 'success')
}

function deleteEditing() {
  if (!editingPlaylist.value) return
  pendingDeleteId.value = editingPlaylist.value.id
  editingPlaylist.value = null
  showDeleteConfirm.value = true
}

async function confirmDelete() {
  await playlistStore.remove(pendingDeleteId.value)
  showDeleteConfirm.value = false
  toast.show('歌单已删除', 'success')
  if (selectedId.value === pendingDeleteId.value) {
    selectedId.value = playlistStore.playlists[0]?.id || 0
  }
}

async function onImported(_result: ImportResult) {
  await playlistStore.fetchAll()
}

async function removeSong(songId: number) {
  if (!active.value) return
  try {
    const { api } = await import('@/api')
    await api.removeSongFromPlaylist(active.value.id, songId)
    await playlistStore.fetchAll()
    toast.show('已从歌单移除', 'success')
  } catch (e) {
    toast.show((e as Error).message || '移除失败', 'error')
  }
}
</script>

<template>
  <div class="max-w-[1120px] mx-auto px-7 py-10 max-[560px]:px-4">
    <div class="flex items-end justify-between mb-6 flex-wrap gap-3">
      <div>
        <p class="text-[13px] font-semibold tracking-[0.06em] text-brand uppercase mb-2">歌单 · Playlists</p>
        <h2 class="text-display text-ink">我的收藏夹</h2>
        <p class="mt-2 text-[13px] font-light text-ink-faint">新建歌单、编辑封面、拖拽导入本地歌曲</p>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <button class="flex items-center gap-2 px-4 py-2.5 rounded-pill text-[14px] font-medium text-brand bg-brand-soft hover:bg-brand hover:text-white transition-colors" @click="importDialog?.show()">
          <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12m0 0l-4-4m4 4l4-4" /><path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" /></svg>
          导入歌单
        </button>
        <button class="flex items-center gap-2 px-5 py-2.5 rounded-pill text-[14px] font-medium text-white bg-ink hover:bg-black transition-colors" @click="createPlaylist">
          <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14" stroke-linecap="round" /></svg>
          新建歌单
        </button>
      </div>
    </div>

    <!-- 歌单网格 -->
    <div v-if="playlistStore.playlists.length" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-10">
      <div
        v-for="pl in playlistStore.playlists"
        :key="pl.id"
        class="bg-card rounded-r-lg overflow-hidden border border-line cursor-pointer group hover:-translate-y-1 hover:shadow-hover transition-all duration-300"
        :class="{ 'ring-2 ring-brand': selectedId === pl.id }"
        @click="select(pl)"
      >
        <div class="h-28 grid place-items-center text-white text-3xl font-bold relative overflow-hidden">
          <img v-if="pl.cover_url" :src="pl.cover_url" class="absolute inset-0 w-full h-full object-cover" alt="封面" />
          <div v-else class="absolute inset-0 grid place-items-center" :style="{ background: `linear-gradient(150deg, ${pl.cover_color}, ${pl.cover_color}aa)` }">
            {{ pl.name.slice(0, 1) || '♪' }}
          </div>
          <button
            class="absolute top-2 right-2 w-7 h-7 rounded-full bg-white/90 text-ink grid place-items-center opacity-0 group-hover:opacity-100 transition-opacity z-10"
            title="编辑歌单"
            @click.stop="openEdit(pl)"
          >
            <svg viewBox="0 0 24 24" class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 20h9M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z" />
            </svg>
          </button>
        </div>
        <div class="p-3">
          <p class="text-[13px] font-semibold text-ink truncate">{{ pl.name }}</p>
          <p class="text-[11px] font-light text-ink-faint">{{ pl.song_count }} 首{{ pl.scene ? ' · ' + pl.scene : '' }}</p>
        </div>
      </div>
    </div>
    <div v-else class="text-center text-ink-faint py-12 text-[13px] font-light">
      还没有歌单，点「新建歌单」创建第一个吧
    </div>

    <!-- 当前歌单详情：拖拽区 + 歌曲列表 -->
    <div v-if="active">
      <div class="flex items-center gap-3 mb-4">
        <h3 class="text-h3 text-ink">「{{ active.name }}」的歌曲</h3>
        <span class="text-[12px] font-light text-ink-faint">{{ active.song_count }} 首</span>
      </div>

      <DropZoneUpload :playlist-id="active.id" @imported="onImported" />

      <div v-if="active.songs.length" class="mt-4 flex flex-col gap-2">
        <div
          v-for="(s, i) in active.songs"
          :key="s.id"
          class="flex items-center gap-3 bg-card rounded-r-md p-3 border border-line hover:border-brand/40 transition-colors cursor-pointer"
          @click="player.playSong(s, active!.songs)"
        >
          <span class="text-[12px] font-light text-ink-faint w-5 text-center">{{ i + 1 }}</span>
          <div
            class="w-10 h-10 rounded-r-sm grid place-items-center text-white text-sm font-semibold shrink-0"
            :style="{ background: `linear-gradient(150deg, ${s.cover_color}, ${s.cover_color}aa)` }"
          >
            {{ s.title.slice(0, 1) }}
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-[14px] text-ink truncate">{{ s.title }}</p>
            <p class="text-[12px] font-light text-ink-soft truncate">{{ s.artist }}{{ s.genre && s.genre !== 'local' ? ' · ' + s.genre : '' }}</p>
          </div>
          <span v-if="s.genre === 'local'" class="text-[11px] text-ink-faint bg-bg rounded-pill px-2 py-0.5 shrink-0">本地导入</span>
          <button
            class="w-8 h-8 rounded-full grid place-items-center text-ink-faint hover:text-danger hover:bg-danger/5 transition-colors shrink-0"
            title="从歌单移除"
            @click.stop="removeSong(s.id)"
          >
            <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
              <path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13" />
            </svg>
          </button>
        </div>
      </div>
      <p v-else class="text-[13px] font-light text-ink-faint py-4 text-center">
        这个歌单还是空的，拖拽歌曲文件到上方导入
      </p>
    </div>

    <!-- 弹窗 -->
    <PlaylistEditDialog
      :playlist="editingPlaylist"
      @close="editingPlaylist = null"
      @save="savePlaylist"
      @cover-uploaded="playlistStore.fetchAll()"
      @delete="deleteEditing"
    />
    <ConfirmDialog :open="showDeleteConfirm" title="删除歌单" message="删除后不可恢复，确定继续吗？" @confirm="confirmDelete" @cancel="showDeleteConfirm = false" />
    <PlaylistImportDialog ref="importDialog" @imported="playlistStore.fetchAll()" />
  </div>
</template>
