const scenarios = {
  vuln: {
    material: `漏洞挖掘专家材料：
1. 对上传接口必须检查文件扩展名、MIME 类型和内容魔数，不能只信任客户端 filename。
2. 任意重定向、SSRF、路径穿越、命令注入都需要同时记录触发输入和危险 sink。
3. 对鉴权绕过要检查直接对象引用、角色边界和租户隔离。
4. 输出报告必须包含 vulnerability_type、evidence、impact、reproduction_steps、recommended_fix。
5. 高风险规则需要保留证据 trace，避免只输出规则编号。`,
    compactV1Rules: ["R001 上传类型校验", "R002 危险 sink 识别", "R003 鉴权与租户边界"],
    missingRules: ["R004 输出契约字段", "R005 高风险证据 trace"],
    patchedRules: ["R004 报告必须包含类型、证据、影响、复现步骤和修复建议", "R005 高风险漏洞必须给出输入证据与 sink 证据 trace"],
    task: "审查一个文件上传 + URL fetch 组合接口",
    failure: "missing_rule + trace_contract_gap",
    v1Coverage: "3 / 5",
    v2Coverage: "5 / 5",
    traceCost: "184 / 260",
  },
  api: {
    material: `API Review 专家材料：
1. 接口必须说明鉴权方式和权限边界。
2. 所有写操作必须描述输入校验规则。
3. 错误码需要覆盖参数错误、权限错误和服务异常。
4. 敏感字段不能在响应或日志中泄露。
5. 响应结构必须保持统一 envelope。
6. 重试或提交类接口必须说明幂等策略。`,
    compactV1Rules: ["R001 鉴权方式", "R002 输入校验", "R003 错误码覆盖", "R004 敏感信息泄露"],
    missingRules: ["R005 响应 envelope", "R006 幂等策略"],
    patchedRules: ["R005 检查响应是否使用统一 envelope", "R006 检查重复提交、重试和幂等 key"],
    task: "审查一个订单创建 OpenAPI 片段",
    failure: "missing_rule",
    v1Coverage: "4 / 6",
    v2Coverage: "6 / 6",
    traceCost: "183 / 237",
  },
  config: {
    material: `配置安全专家材料：
1. 生产环境不能开启 debug、verbose error 或未授权管理端口。
2. Secret 不能以明文写入配置文件。
3. 服务必须配置资源限制，避免无界内存或 CPU。
4. 审计日志需要保留关键安全事件。
5. 输出必须包含 config_path、risk_level、evidence、fix。`,
    compactV1Rules: ["C001 禁止生产 debug", "C002 禁止明文 secret", "C003 资源限制", "OUTPUT 输出 schema"],
    missingRules: ["C006 审计日志保留策略"],
    patchedRules: ["C006 对登录、权限变更、密钥轮换等事件检查审计保留"],
    task: "审查一份 Kubernetes/应用混合配置",
    failure: "missing_rule + regression_risk",
    v1Coverage: "0.825",
    v2Coverage: "1.00",
    traceCost: "166 / 260",
  },
};

const materialInput = document.querySelector("#materialInput");
const scenarioSelect = document.querySelector("#scenarioSelect");
const runButton = document.querySelector("#runButton");
const resetButton = document.querySelector("#resetButton");
const runStatus = document.querySelector("#runStatus");

const fields = {
  coverageV1: document.querySelector("#coverageV1"),
  coverageV2: document.querySelector("#coverageV2"),
  traceCost: document.querySelector("#traceCost"),
  gateDecision: document.querySelector("#gateDecision"),
  initialSkill: document.querySelector("#initialSkill"),
  executionFeedback: document.querySelector("#executionFeedback"),
  patchPlan: document.querySelector("#patchPlan"),
  finalSkill: document.querySelector("#finalSkill"),
  initialBadge: document.querySelector("#initialBadge"),
  feedbackBadge: document.querySelector("#feedbackBadge"),
  patchBadge: document.querySelector("#patchBadge"),
  finalBadge: document.querySelector("#finalBadge"),
};

function currentScenario() {
  return scenarios[scenarioSelect.value];
}

function setScenario() {
  materialInput.value = currentScenario().material;
  clearOutputs();
}

function clearOutputs() {
  runStatus.textContent = "Ready";
  for (const key of ["coverageV1", "coverageV2", "traceCost", "gateDecision"]) {
    fields[key].textContent = "-";
  }
  for (const key of ["initialSkill", "executionFeedback", "patchPlan", "finalSkill"]) {
    fields[key].textContent = "";
  }
  for (const key of ["initialBadge", "feedbackBadge", "patchBadge", "finalBadge"]) {
    fields[key].textContent = "pending";
  }
  document.querySelectorAll(".step").forEach((step, index) => step.classList.toggle("active", index === 0));
}

function buildSkill(rules, includeTrace) {
  const traceLine = includeTrace
    ? "\nTrace contract: high-risk or newly patched findings must include rule_id, trigger evidence, and affected target."
    : "";
  return `Compact deployment skill

Task boundary:
- Review only evidence present in the task input.
- Emit actionable findings, not generic advice.

Rules:
${rules.map((rule) => `- ${rule}`).join("\n")}

Output contract:
- finding_id
- rule_id
- evidence
- risk_level
- recommended_fix${traceLine}`;
}

function runPipeline() {
  const scenario = currentScenario();
  const customText = materialInput.value.trim();
  const materialLines = customText.split(/\n+/).filter(Boolean).length;

  runStatus.textContent = "Running";
  document.querySelectorAll(".step").forEach((step) => step.classList.add("active"));

  fields.initialBadge.textContent = "compact v1";
  fields.initialSkill.textContent = buildSkill(scenario.compactV1Rules, false);

  fields.feedbackBadge.textContent = "failed";
  fields.executionFeedback.textContent = `Execution target:
- ${scenario.task}

Verifier feedback:
- failure_type: ${scenario.failure}
- compact_v1 coverage: ${scenario.v1Coverage}
- missing / weak rules: ${scenario.missingRules.join(", ")}

Posterior signal:
- The failure appeared after deployment execution, so it should guide patch selection rather than trigger a blind full rewrite.`;

  fields.patchBadge.textContent = "typed patch";
  fields.patchPlan.textContent = `Revision operator:
- missing_rule -> patch affected domain rules
- trace_contract_gap -> require selective trace
- regression_risk -> validate against previously covered rules

Patch proposal:
${scenario.patchedRules.map((rule) => `- ${rule}`).join("\n")}

Validation gate:
- reject if regression is introduced
- reject if trace protocol exceeds budget
- accept if task failure is resolved under budget`;

  const finalRules = [...scenario.compactV1Rules, ...scenario.patchedRules];
  fields.finalBadge.textContent = "accepted";
  fields.finalSkill.textContent = buildSkill(finalRules, true);

  fields.coverageV1.textContent = scenario.v1Coverage;
  fields.coverageV2.textContent = scenario.v2Coverage;
  fields.traceCost.textContent = scenario.traceCost;
  fields.gateDecision.textContent = materialLines > 2 ? "accept" : "needs evidence";
  runStatus.textContent = "Complete";
}

scenarioSelect.addEventListener("change", setScenario);
resetButton.addEventListener("click", setScenario);
runButton.addEventListener("click", runPipeline);

setScenario();
