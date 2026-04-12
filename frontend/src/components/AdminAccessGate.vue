<script setup lang="ts">
import { onMounted, ref } from "vue";

import { clearAdminAccessCode, setAdminAccessCode } from "../auth/adminAccess";
import { fetchAdminAccessStatus, verifyAdminAccess } from "../api/admin";

const props = defineProps<{
  onUnlock: () => void | Promise<void>;
}>();

const checking = ref(true);
const authEnabled = ref(false);
const verified = ref(false);
const password = ref("");
const errorMessage = ref("");
const submitting = ref(false);

async function hydrateAccess() {
  checking.value = true;
  errorMessage.value = "";

  try {
    authEnabled.value = await fetchAdminAccessStatus();

    if (!authEnabled.value) {
      verified.value = true;
      await props.onUnlock();
      return;
    }

    try {
      verified.value = await verifyAdminAccess();
      if (verified.value) {
        await props.onUnlock();
      }
    } catch {
      verified.value = false;
      clearAdminAccessCode();
    }
  } catch (error) {
    verified.value = false;
    errorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法检查后台访问状态。";
  } finally {
    checking.value = false;
  }
}

async function submit() {
  const code = password.value.trim();
  if (!code) {
    errorMessage.value = "请输入管理员访问码。";
    return;
  }

  submitting.value = true;
  errorMessage.value = "";

  try {
    setAdminAccessCode(code);
    const allowed = await verifyAdminAccess();
    if (!allowed) {
      clearAdminAccessCode();
      errorMessage.value = "管理员访问码校验失败。";
      return;
    }

    verified.value = true;
    password.value = "";
    await props.onUnlock();
  } catch (error) {
    clearAdminAccessCode();
    errorMessage.value =
      error instanceof Error ? error.message : "未知错误，无法验证管理员访问码。";
  } finally {
    submitting.value = false;
  }
}

function logout() {
  clearAdminAccessCode();
  verified.value = false;
  password.value = "";
  errorMessage.value = "";
}

onMounted(() => {
  void hydrateAccess();
});
</script>

<template>
  <section v-if="checking" class="panel p-6">
    <p class="text-sm text-slate-600">正在检查后台访问权限...</p>
  </section>

  <div v-else-if="verified" class="space-y-4">
    <section
      v-if="authEnabled"
      class="panel flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <p class="text-sm font-semibold text-slate-900">后台访问已验证</p>
        <p class="mt-1 text-sm leading-6 text-slate-600">
          当前浏览器会话内会自动携带管理员访问码。需要切换访问码时，可先退出再重新输入。
        </p>
      </div>

      <button
        type="button"
        class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
        @click="logout"
      >
        退出后台验证
      </button>
    </section>

    <slot />
  </div>

  <section v-else class="panel overflow-hidden">
    <div class="grid gap-6 px-6 py-8 lg:grid-cols-[1.04fr_0.96fr] lg:px-8">
      <div>
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-700">
          Admin Access
        </p>
        <h1 class="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
          后台访问需要验证
        </h1>
        <p class="mt-5 max-w-3xl text-base leading-8 text-slate-600">
          你已经进入 `/admin/*` 工作区。当前后端已启用最小管理员访问码校验，
          需要先完成验证，才能查看系统诊断、知识库维护和商品目录维护模块。
        </p>

        <div class="mt-6 rounded-3xl bg-slate-50 p-5">
          <p class="text-sm font-semibold text-slate-800">当前策略</p>
          <ul class="mt-3 space-y-2 text-sm leading-7 text-slate-600">
            <li>1. 访问码只保存在当前浏览器会话中。</li>
            <li>2. 管理接口请求会自动携带访问码请求头。</li>
            <li>3. 关闭标签页或清理会话后，需要重新输入。</li>
          </ul>
        </div>
      </div>

      <div class="rounded-[28px] bg-ink p-6 text-white">
        <p class="text-sm font-semibold uppercase tracking-[0.24em] text-amber-300">
          输入访问码
        </p>
        <p class="mt-4 text-sm leading-7 text-slate-200">
          如果当前环境没有配置 `ADMIN_ACCESS_CODE`，这里会自动放行，不会停留在这一步。
        </p>

        <label class="mt-6 block">
          <span class="text-xs uppercase tracking-[0.18em] text-slate-300">管理员访问码</span>
          <input
            v-model="password"
            type="password"
            class="field-input mt-3 bg-white text-slate-900"
            placeholder="输入后台访问码"
            @keydown.enter="submit"
          />
        </label>

        <button
          type="button"
          class="mt-5 rounded-full bg-amber-500 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-amber-600 disabled:cursor-wait disabled:opacity-70"
          :disabled="submitting"
          @click="submit"
        >
          {{ submitting ? "正在验证..." : "进入后台工作区" }}
        </button>

        <p
          v-if="errorMessage"
          class="mt-4 rounded-2xl bg-rose-500/15 px-4 py-3 text-sm text-rose-100"
        >
          {{ errorMessage }}
        </p>
      </div>
    </div>
  </section>
</template>
