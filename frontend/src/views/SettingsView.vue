<!-- 页面：设置 —— LLM 供应商配置 + AI 接口地址与鉴权
支持硅基流动 / DeepSeek / OpenAI / 自定义端点；Key 用 Password 输入；保存后立即生效 -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import type { Settings } from '@/api/types'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const toast = useToastStore()

const settings = ref<Settings | null>(null)
const loading = ref(false)
const saving = ref(false)
const resetting = ref(false)

// 表单字段
const providerKey = ref('siliconflow')
const baseUrl = ref('')
const apiKey = ref('')
const modelName = ref('')
const customMode = ref(false)

onMounted(async () => {
  await loadSettings()
})

async function loadSettings() {
  loading.value = true
  try {
    settings.value = await api.getConfig()
    baseUrl.value = settings.value.llm_base_url
    modelName.value = settings.value.llm_model_name
    // 推断当前 provider
    const matched = settings.value.providers.find((p) => p.base_url === settings.value!.llm_base_url)
    if (matched) {
      providerKey.value = matched.key
      customMode.value = false
    } else {
      providerKey.value = 'custom'
      customMode.value = true
    }
  } catch {
    toast.show('配置加载失败（后端未连接）', 'error')
  } finally {
    loading.value = false
  }
  loadJamendo()
}

const currentProvider = computed(() =>
  settings.value?.providers.find((p) => p.key === providerKey.value),
)

function applyProvider() {
  if (providerKey.value === 'custom') {
    customMode.value = true
    return
  }
  customMode.value = false
  const p = currentProvider.value
  if (p) {
    baseUrl.value = p.base_url
    if (!modelName.value && p.models.length) modelName.value = p.models[0]
  }
}

async function save() {
  if (!baseUrl.value.trim() || !modelName.value.trim()) {
    toast.show('Base URL 和模型名不能为空', 'error')
    return
  }
  saving.value = true
  try {
    const patch: { llm_base_url: string; llm_model_name: string; llm_api_key?: string } = {
      llm_base_url: baseUrl.value.trim(),
      llm_model_name: modelName.value.trim(),
    }
    if (apiKey.value.trim()) patch.llm_api_key = apiKey.value.trim()
    await api.updateConfig(patch)
    apiKey.value = ''
    await loadSettings()
    toast.show('配置已保存并生效', 'success')
  } catch (e) {
    toast.show((e as Error).message || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

async function reset() {
  if (!confirm('确定恢复默认配置吗？自定义的 Base URL / Key 会被清除。')) return
  resetting.value = true
  try {
    await api.resetConfig()
    apiKey.value = ''
    await loadSettings()
    toast.show('已恢复默认配置', 'success')
  } catch (e) {
    toast.show((e as Error).message || '重置失败', 'error')
  } finally {
    resetting.value = false
  }
}

// ---------- Jamendo 全首曲库 ----------
const JAMENDO_OFFICIAL_TEST_ID = '7d0b6f06'  // 来自开源项目的活跃 client_id（Jamendo 官方 709fa152 已封禁）
const jamendoKey = ref('')
const jamendoSyncing = ref(false)
const jamendoQuery = ref('')

function loadJamendo() {
  jamendoKey.value = settings.value?.jamendo_client_id || ''
}

function useOfficialDemoKey() {
  jamendoKey.value = JAMENDO_OFFICIAL_TEST_ID
  toast.show(`已填入 Jamendo 官方测试 client_id（${JAMENDO_OFFICIAL_TEST_ID}）`, 'success', 2500)
}

async function syncJamendo() {
  if (!jamendoKey.value.trim()) {
    toast.show('请先填写 Jamendo Client ID', 'error')
    return
  }
  jamendoSyncing.value = true
  try {
    await api.updateConfig({ jamendo_client_id: jamendoKey.value.trim() } as never)
    const result = await api.syncJamendo(jamendoKey.value.trim(), jamendoQuery.value.trim(), '', 20)
    toast.show(`Jamendo 同步完成：新增 ${result.imported} 首全首音乐`, 'success')
  } catch (e) {
    toast.show((e as Error).message || 'Jamendo 同步失败', 'error')
  } finally {
    jamendoSyncing.value = false
  }
}

</script>

<template>
  <div class="max-w-[720px] mx-auto px-7 py-10 max-[560px]:px-4">
    <div class="mb-6">
      <p class="text-[13px] font-semibold tracking-[0.06em] text-brand uppercase mb-2">设置 · Settings</p>
      <h2 class="text-display text-ink">AI 接口配置</h2>
      <p class="mt-2 text-[13px] font-light text-ink-faint">配置后立即生效，AI 助手与推荐理由将使用新供应商返回真实回答。</p>
    </div>

    <div v-if="loading" class="text-[13px] font-light text-ink-faint py-10 text-center">加载中…</div>

    <div v-else-if="settings" class="flex flex-col gap-5">
      <!-- 当前状态 -->
      <div class="bg-card rounded-r-lg p-5 border border-line">
        <h3 class="text-[14px] font-semibold text-ink mb-3">当前状态</h3>
        <div class="grid grid-cols-2 gap-y-2 text-[13px]">
          <span class="text-ink-faint">Base URL</span><span class="text-ink truncate">{{ settings.llm_base_url }}</span>
          <span class="text-ink-faint">模型</span><span class="text-ink">{{ settings.llm_model_name }}</span>
          <span class="text-ink-faint">API Key</span>
          <span class="text-ink">
            <span v-if="settings.llm_api_key_set" class="text-ai">✓ 已配置</span>
            <span v-else class="text-danger">未配置（AI 走规则降级）</span>
            <span v-if="settings.llm_api_key_mask" class="ml-2 text-ink-faint font-mono text-[12px]">{{ settings.llm_api_key_mask }}</span>
          </span>
        </div>
      </div>

      <!-- 供应商 -->
      <div class="bg-card rounded-r-lg p-5 border border-line">
        <h3 class="text-[14px] font-semibold text-ink mb-3">供应商</h3>
        <div class="flex flex-wrap gap-2 mb-4">
          <button
            v-for="p in settings.providers"
            :key="p.key"
            class="px-4 py-2 rounded-pill text-[13px] border border-line bg-card text-ink-soft transition-colors"
            :class="{ '!bg-brand !text-white !border-brand font-medium': providerKey === p.key }"
            @click="providerKey = p.key; applyProvider()"
          >
            {{ p.name }}
          </button>
        </div>
      </div>

      <!-- 表单 -->
      <div class="bg-card rounded-r-lg p-5 border border-line">
        <h3 class="text-[14px] font-semibold text-ink mb-4">接口参数</h3>

        <label class="block text-[12px] text-ink-faint mb-1.5">Base URL（OpenAI 兼容端点）</label>
        <input
          v-model="baseUrl"
          class="w-full bg-bg border border-line rounded-r-sm px-3 py-2 text-[14px] text-ink font-mono placeholder:text-ink-faint focus:outline-none focus:border-brand mb-4"
          :placeholder="customMode ? 'https://your-api.com/v1' : ''"
        />

        <label class="block text-[12px] text-ink-faint mb-1.5">
          API Key
          <span class="text-ink-faint/70">(留空表示不修改已保存的 Key)</span>
        </label>
        <input
          v-model="apiKey"
          type="password"
          class="w-full bg-bg border border-line rounded-r-sm px-3 py-2 text-[14px] text-ink font-mono placeholder:text-ink-faint focus:outline-none focus:border-brand mb-4"
          :placeholder="settings.llm_api_key_set ? '已配置（留空不修改）' : 'sk-...'"
          autocomplete="off"
        />

        <label class="block text-[12px] text-ink-faint mb-1.5">模型</label>
        <input
          v-model="modelName"
          class="w-full bg-bg border border-line rounded-r-sm px-3 py-2 text-[14px] text-ink font-mono placeholder:text-ink-faint focus:outline-none focus:border-brand mb-4"
          placeholder="如 deepseek-ai/DeepSeek-V3"
          list="model-suggestions"
        />
        <datalist id="model-suggestions">
          <option v-for="m in currentProvider?.models || []" :key="m" :value="m" />
        </datalist>

        <div class="flex items-center gap-2 pt-2">
          <button class="tm-btn !px-5" :disabled="saving" @click="save">
            {{ saving ? '保存中…' : '保存并生效' }}
          </button>
          <button class="tm-btn-ghost !px-4" :disabled="resetting" @click="reset">
            {{ resetting ? '重置中…' : '恢复默认' }}
          </button>
          <button class="ml-auto text-[13px] text-brand hover:underline" @click="router.push('/assistant')">
            去测试 AI 助手 →
          </button>
        </div>
      </div>

      <!-- 供应商说明 -->
      <div class="bg-card rounded-r-lg p-5 border border-line">
        <h3 class="text-[14px] font-semibold text-ink mb-3">使用说明</h3>
        <ul class="text-[12.5px] font-light text-ink-soft leading-relaxed space-y-1.5">
          <li>• 硅基流动 <a href="https://siliconflow.cn" target="_blank" class="text-brand">注册</a> 即送免费额度，填入 API Key 即可使用。</li>
          <li>• DeepSeek / OpenAI 同样兼容，按官网文档填入 Key。</li>
          <li>• 选择「自定义端点」可接入任何 OpenAI 兼容服务（如 vLLM / OneAPI）。</li>
          <li>• Key 不会在 GET 响应中明文返回，只显示脱敏后的 mask。</li>
        </ul>
      </div>

      <!-- Jamendo 全首曲库 -->
      <div class="bg-card rounded-r-lg p-5 border border-line">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-[14px] font-semibold text-ink">Jamendo 全首曲库</h3>
          <span v-if="settings?.jamendo_client_id_set" class="text-[11px] text-emerald-600 bg-emerald-50 rounded-pill px-2 py-0.5">已配置 ✓</span>
        </div>
        <p class="text-[12px] font-light text-ink-soft mb-3 leading-relaxed">
          接入 Jamendo 后，可一键导入 <b>CC 授权全首音乐</b>（非 30 秒试听）。
          到
          <a href="https://developer.jamendo.com" target="_blank" class="text-brand hover:underline">developer.jamendo.com</a>
          免费注册（选 Personal/Test）即可在 Dashboard 获取 Client ID。
        </p>
        <label class="block text-[12px] text-ink-faint mb-1.5">Jamendo Client ID</label>
        <div class="flex gap-2 mb-3">
          <input
            v-model="jamendoKey"
            class="flex-1 bg-bg border border-line rounded-r-sm px-3 py-2 text-[14px] text-ink font-mono placeholder:text-ink-faint focus:outline-none focus:border-brand"
            placeholder="如 709fa152 或自己注册后的 ID"
            autocomplete="off"
          />
          <button
            class="tm-btn-ghost !px-3 shrink-0"
            title="使用 Jamendo 官方公开的 read-only 测试 client_id"
            @click="useOfficialDemoKey"
          >
            使用测试 key
          </button>
        </div>
        <div class="flex items-center gap-2">
          <input
            v-model="jamendoQuery"
            class="flex-1 bg-bg border border-line rounded-r-sm px-3 py-2 text-[13px] text-ink placeholder:text-ink-faint focus:outline-none focus:border-brand"
            placeholder="按关键词搜索（如 lofi / guitar，留空导入热门）"
          />
          <button class="tm-btn !px-5 shrink-0" :disabled="jamendoSyncing" @click="syncJamendo">
            {{ jamendoSyncing ? '导入中…' : '导入 20 首全首' }}
          </button>
        </div>
        <p class="text-[11px] font-light text-ink-faint mt-2 leading-relaxed">
          导入后到「推荐 / 曲库」页即可播放全首；每首带封面与 CC 授权信息，完全免费合法。<br />
          <b>提示</b>:点「使用测试 key」可一键填入 Jamendo 官方公开的 <code class="bg-bg px-1 rounded">709fa152</code>(仅 read API,有调用限额,适合先体验)。要正式用,到
          <a href="https://developer.jamendo.com/v3.0/authentication" target="_blank" class="text-brand hover:underline">Developer Portal</a>
          注册并创建应用拿自己的 client_id。
        </p>
      </div>
    </div>
  </div>
</template>
