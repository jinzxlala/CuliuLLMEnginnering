async function postJson(url, payload) {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return await resp.json();
}

function pretty(obj) {
  return JSON.stringify(obj, null, 2);
}

document.getElementById("btnHealth").addEventListener("click", async () => {
  const resp = await fetch("/api/portal/health");
  const data = await resp.json();
  document.getElementById("healthOutput").textContent = pretty(data);
});

document.getElementById("btnPromptAB").addEventListener("click", async () => {
  const task = document.getElementById("promptTask").value;
  const data = await postJson("/api/portal/prompt_ab", { task });
  document.getElementById("promptOutput").textContent = pretty(data);
});

document.getElementById("btnRagAsk").addEventListener("click", async () => {
  const query = document.getElementById("ragQuery").value;
  const data = await postJson("/api/portal/rag_ask", { query, top_k: 3 });
  document.getElementById("ragOutput").textContent = pretty(data);
});

document.getElementById("btnAgentChat").addEventListener("click", async () => {
  const query = document.getElementById("agentQuery").value;
  let context = {};
  try {
    context = JSON.parse(document.getElementById("agentContext").value || "{}");
  } catch (_e) {
    context = {};
  }
  const data = await postJson("/api/portal/agent_chat", { query, context });
  document.getElementById("agentOutput").textContent = pretty(data);
});

document.getElementById("btnSafetyCheck").addEventListener("click", async () => {
  const text = document.getElementById("safetyText").value;
  const tool = document.getElementById("safetyTool").value;
  const data = await postJson("/api/portal/safety_check", { text, tool });
  document.getElementById("safetyOutput").textContent = pretty(data);
});
