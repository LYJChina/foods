<script setup lang="ts">
import { Icon } from "@iconify/vue";

const scenarios = [
  {
    title: "AI+通用办公",
    icon: "ri:file-text-line",
    description: "文档解析、翻译、知识问答与会议报告辅助的交互流程。",
    boundary: "不连接企业办公系统，不处理真实企业文件。",
    status: "辅助展示",
    tone: "blue",
  },
  {
    title: "AI+研发",
    icon: "ri:flask-line",
    description: "行业公开知识、新品趋势、历史产品检索与法规校核示意。",
    boundary: "不接收配方比例、工艺参数等核心研发数据。",
    status: "辅助展示",
    tone: "violet",
  },
  {
    title: "AI+制造",
    icon: "ri:building-4-line",
    description: "排产建议、生产进度、设备诊断和损耗分析的流程示意。",
    boundary: "不连接 MES、设备或实时生产数据。",
    status: "辅助展示",
    tone: "cyan",
  },
  {
    title: "AI+质量",
    icon: "ri:scan-2-line",
    description: "视觉质检、包装检测、标签识别与异常分析。",
    boundary: "当前不提供真实视觉模型或检测结论。",
    status: "规划中",
    tone: "red",
  },
  {
    title: "AI+营销出海",
    icon: "ri:global-line",
    description: "客户文件解析、多语言资料与海外合规辅助流程。",
    boundary: "不使用真实客户文件，不代替专业合规判断。",
    status: "辅助展示",
    tone: "green",
  },
  {
    title: "AI+经营",
    icon: "ri:bar-chart-box-line",
    description: "知识助手、经营问数与企业 Agent 协同的闭环示意。",
    boundary: "经营数据留在企业侧，公共平台不获取超级权限。",
    status: "辅助展示",
    tone: "amber",
  },
];
</script>

<template>
  <main class="portal-page portal-container">
    <header class="portal-page__intro">
      <span class="portal-section__kicker">先看见，再验证</span>
      <h1>AI 场景服务专区</h1>
      <p>优先展示企业感知强、能说明实施条件与价值边界的场景；当前状态均按真实实现程度标注。</p>
    </header>

    <section class="portal-scenario-grid" aria-label="食品行业 AI 场景">
      <article v-for="scenario in scenarios" :key="scenario.title" class="portal-scenario-card" :class="'is-' + scenario.tone" data-testid="scenario-card">
        <div class="portal-scenario-card__top">
          <span class="portal-scenario-card__icon" aria-hidden="true"><Icon :icon="scenario.icon" /></span>
          <span class="portal-scenario-card__status">{{ scenario.status }}</span>
        </div>
        <h2>{{ scenario.title }}</h2>
        <p>{{ scenario.description }}</p>
        <div class="portal-scenario-card__boundary">
          <strong>能力边界</strong>
          <span>{{ scenario.boundary }}</span>
        </div>
      </article>
    </section>

    <section class="portal-scenario-next">
      <div>
        <span class="portal-section__kicker">从共性服务开始</span>
        <h2>体验可运行的出口合规预检流程</h2>
        <p>使用产品类别、目标市场和低敏材料类型生成确定性辅助结果。</p>
      </div>
      <RouterLink class="portal-button portal-button--primary" to="/portal/precheck">开始预检</RouterLink>
    </section>
  </main>
</template>
