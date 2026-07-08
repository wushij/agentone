<script setup lang="ts">
import BrandMark from '@/components/BrandMark.vue'
</script>

<template>
  <section class="auth-brand">
    <div class="auth-brand-inner">
      <div class="auth-logo">
        <BrandMark :size="40" />
      </div>
      <h1>AgentOne</h1>
      <p class="auth-brand-desc">企业级 AI 智能体平台</p>
      <ul class="auth-features">
        <li>多轮对话与流式输出</li>
        <li>LangGraph 工作流与 Tool 调用</li>
        <li>知识库检索与多 Agent 协作</li>
      </ul>
    </div>
    <div class="auth-brand-deco-1" />
    <div class="auth-brand-deco-2" />
  </section>
</template>

<style scoped>
.auth-brand {
  position: relative;
  padding: 48px 40px;
  background: rgba(255, 251, 251, 0.88);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  color: #0f172a;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  overflow: hidden;
  border-right: 1px solid rgba(240, 212, 212, 0.72);
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.6);
}

.auth-brand-deco-1,
.auth-brand-deco-2 {
  display: none;
}

.auth-brand-inner {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.auth-logo {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 28px;
  border: 1px solid rgba(240, 212, 212, 0.72);
  box-shadow:
    0 6px 28px rgba(239, 68, 68, 0.08),
    0 2px 10px rgba(239, 68, 68, 0.05);
}

.auth-brand h1 {
  margin: 0 0 14px;
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 1.2;
  color: #0f172a;
}

.auth-brand-desc {
  margin: 0 0 40px;
  font-size: 15px;
  line-height: 1.6;
  color: #64748b;
  letter-spacing: 0.5px;
}

.auth-features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
  width: 100%;
  max-width: 290px;
  align-items: stretch;
  counter-reset: feature;
}

.auth-features li {
  position: relative;
  padding: 12px 16px 12px 42px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(240, 212, 212, 0.55);
  color: #334155;
  line-height: 1.5;
  text-align: left;
  box-shadow: 0 2px 10px rgba(239, 68, 68, 0.05);
  counter-increment: feature;
}

.auth-features li::before {
  content: counter(feature);
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #ffffff;
  border: 1.5px solid rgba(240, 212, 212, 0.85);
  color: #0f172a;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 840px) {
  .auth-brand {
    display: none;
  }
}
</style>
