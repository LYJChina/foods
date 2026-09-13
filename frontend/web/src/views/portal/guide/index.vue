<template>
  <main class="portal-page">
    <div class="portal-container">
      <header class="portal-page__intro">
        <span class="portal-section__kicker">服务说明</span>
        <h1>使用指南</h1>
        <p>本平台面向食品行业提供公共、低敏的 AI 辅助服务，帮助企业了解适用能力与办理边界。</p>
      </header>

      <section class="portal-guide-grid" aria-label="公共服务使用说明">
        <article class="portal-guide-card">
          <h2>服务范围</h2>
          <p>可使用智能文档解析、出口合规预检、AI 场景匹配和企业数智化诊断等公共服务，结果仅作为辅助参考。</p>
        </article>
        <article class="portal-guide-card">
          <h2>支持材料</h2>
          <p>请提交公开政策、产品标签、包装、规格书等公开或低敏材料，并确认材料来源合法、内容真实。</p>
        </article>
        <article class="portal-guide-card portal-guide-card--boundary">
          <h2>不得提交核心数据</h2>
          <ul>
            <li>配方、工艺、成本、客户、订单等经营核心数据</li>
            <li>生产经营数据、个人信息或其他未公开敏感信息</li>
          </ul>
        </article>
        <article class="portal-guide-card">
          <h2>开始办理</h2>
          <p>请先在服务大厅选择适合的公共服务，再按页面提示提交必要的低敏材料。</p>
          <RouterLink class="portal-button portal-button--primary" to="/portal/services">前往智能服务大厅</RouterLink>
        </article>
      </section>
    </div>
  </main>
</template>
