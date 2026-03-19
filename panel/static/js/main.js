/**
 * GOST 管理面板 - 前端逻辑
 */

const API_BASE = "";

// 认证信息（Base64）
let authHeader = "";

function setAuth(user, pass) {
  authHeader = "Basic " + btoa(user + ":" + pass);
  localStorage.setItem("gost_panel_auth", authHeader);
}

function getAuth() {
  if (!authHeader) {
    authHeader = localStorage.getItem("gost_panel_auth");
  }
  return authHeader;
}

function clearAuth() {
  authHeader = "";
  localStorage.removeItem("gost_panel_auth");
}

function api(method, path, body) {
  const opts = {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: getAuth(),
    },
  };
  if (body) opts.body = JSON.stringify(body);
  return fetch(API_BASE + path, opts).then((res) => {
    if (res.status === 401) {
      clearAuth();
      showLogin();
      throw new Error("未授权");
    }
    return res.json().then((data) => {
      if (!res.ok) throw new Error(data.error || "请求失败");
      return data;
    });
  });
}

function showLogin() {
  document.getElementById("loginBox").style.display = "block";
  document.getElementById("content").style.display = "none";
}

function showContent() {
  document.getElementById("loginBox").style.display = "none";
  document.getElementById("content").style.display = "block";
}

function toast(msg, type = "success") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

// 加载规则列表
function loadRules() {
  const tbody = document.getElementById("rulesBody");
  api("GET", "/api/rules")
    .then((data) => {
      if (data.rules.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty">暂无规则，点击「新增规则」添加</td></tr>';
        return;
      }
      tbody.innerHTML = data.rules
        .map(
          (r) => `
        <tr>
          <td>${r.id}</td>
          <td>${r.typeLabel || r.type}</td>
          <td>${r.sourcePort}</td>
          <td>${r.destAddr}</td>
          <td>${r.destPort}</td>
          <td class="actions">
            <button type="button" class="btn btn-secondary btn-sm btn-edit" data-id="${r.id}">编辑</button>
            <button type="button" class="btn btn-danger btn-sm btn-delete" data-id="${r.id}">删除</button>
          </td>
        </tr>
      `
        )
        .join("");
      bindRowActions();
    })
    .catch((e) => {
      tbody.innerHTML = `<tr><td colspan="6" class="empty">加载失败: ${e.message}</td></tr>`;
    });
}

function bindRowActions() {
  document.querySelectorAll(".btn-edit").forEach((btn) => {
    btn.addEventListener("click", () => openEditModal(parseInt(btn.dataset.id)));
  });
  document.querySelectorAll(".btn-delete").forEach((btn) => {
    btn.addEventListener("click", () => openDeleteModal(parseInt(btn.dataset.id)));
  });
}

// 更新表单标签（根据协议类型）
function updateFormLabels(type) {
  const proxyTypes = ["ss", "socks", "http"];
  const peerTypes = ["peerno", "peertls", "peerws", "peerwss"];
  const cdnTypes = ["cdnno", "cdnws", "cdnwss"];

  const labelSource = document.getElementById("labelSourcePort");
  const labelDest = document.getElementById("labelDestAddr");
  const labelPort = document.getElementById("labelDestPort");

  const fgDest = document.getElementById("fgDestAddr");
  const fgPort = document.getElementById("fgDestPort");

  if (proxyTypes.includes(type)) {
    labelSource.textContent = type === "ss" ? "密码" : type === "socks" ? "密码" : "密码";
    labelDest.textContent = type === "ss" ? "加密方式" : type === "socks" ? "用户名" : "用户名";
    labelPort.textContent = "端口";
    fgDest.style.display = "";
    fgPort.style.display = "";
  } else if (peerTypes.includes(type)) {
    labelSource.textContent = "本地端口";
    labelDest.textContent = "落地列表文件名(不含.txt)";
    labelPort.textContent = "策略(round/random/fifo)";
    fgDest.style.display = "";
    fgPort.style.display = "";
  } else if (cdnTypes.includes(type)) {
    labelSource.textContent = "本地端口";
    labelDest.textContent = "自选IP:端口";
    labelPort.textContent = "Host";
    fgDest.style.display = "";
    fgPort.style.display = "";
  } else {
    labelSource.textContent = "本地端口";
    labelDest.textContent = "目标地址";
    labelPort.textContent = "目标端口";
    fgDest.style.display = "";
    fgPort.style.display = "";
  }
}

// 弹窗：新增/编辑
const ruleModal = document.getElementById("ruleModal");
const ruleForm = document.getElementById("ruleForm");

function openAddModal() {
  document.getElementById("modalTitle").textContent = "新增规则";
  document.getElementById("ruleId").value = "";
  ruleForm.reset();
  updateFormLabels(document.getElementById("ruleType").value);
  ruleModal.classList.add("show");
}

function openEditModal(id) {
  api("GET", "/api/rules")
    .then((data) => {
      const rule = data.rules.find((r) => r.id === id);
      if (!rule) return;
      document.getElementById("modalTitle").textContent = "编辑规则";
      document.getElementById("ruleId").value = rule.id;
      document.getElementById("ruleType").value = rule.type;
      document.getElementById("ruleSourcePort").value = rule.sourcePort;
      document.getElementById("ruleDestAddr").value = rule.destAddr;
      document.getElementById("ruleDestPort").value = rule.destPort;
      updateFormLabels(rule.type);
      ruleModal.classList.add("show");
    })
    .catch((e) => toast(e.message, "error"));
}

function closeRuleModal() {
  ruleModal.classList.remove("show");
}

ruleForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const id = document.getElementById("ruleId").value;
  const payload = {
    type: document.getElementById("ruleType").value,
    sourcePort: document.getElementById("ruleSourcePort").value.trim(),
    destAddr: document.getElementById("ruleDestAddr").value.trim(),
    destPort: document.getElementById("ruleDestPort").value.trim(),
  };

  const req = id
    ? api("PUT", `/api/rules/${id}`, payload)
    : api("POST", "/api/rules", payload);

  req
    .then(() => {
      toast(id ? "修改成功" : "添加成功");
      closeRuleModal();
      loadRules();
    })
    .catch((e) => toast(e.message, "error"));
});

document.getElementById("ruleType").addEventListener("change", (e) => {
  updateFormLabels(e.target.value);
});

// 删除确认
const deleteModal = document.getElementById("deleteModal");
let deleteTargetId = null;

function openDeleteModal(id) {
  deleteTargetId = id;
  deleteModal.classList.add("show");
}

function closeDeleteModal() {
  deleteTargetId = null;
  deleteModal.classList.remove("show");
}

document.getElementById("btnDeleteConfirm").addEventListener("click", () => {
  if (!deleteTargetId) return;
  api("DELETE", `/api/rules/${deleteTargetId}`)
    .then(() => {
      toast("删除成功");
      closeDeleteModal();
      loadRules();
    })
    .catch((e) => toast(e.message, "error"));
});

// 重启服务
document.getElementById("btnRestart").addEventListener("click", () => {
  if (!confirm("确定要重启 GOST 服务吗？")) return;
  api("POST", "/api/restart")
    .then(() => {
      toast("重启成功");
      setTimeout(fetchStatus, 2000);
    })
    .catch((e) => toast(e.message, "error"));
});

// 服务状态
function fetchStatus() {
  api("GET", "/api/status")
    .then((data) => {
      const badge = document.getElementById("statusBadge");
      badge.textContent = data.status === "active" ? "运行中" : "已停止";
      badge.className = "status-badge " + (data.status === "active" ? "active" : "inactive");
    })
    .catch(() => {
      document.getElementById("statusBadge").textContent = "未知";
      document.getElementById("statusBadge").className = "status-badge unknown";
    });
}

// 登录
document.getElementById("loginForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const user = document.getElementById("loginUser").value.trim();
  const pass = document.getElementById("loginPass").value;
  if (!user || !pass) {
    toast("请输入用户名和密码", "error");
    return;
  }
  setAuth(user, pass);
  api("GET", "/api/rules")
    .then(() => {
      showContent();
      loadRules();
      fetchStatus();
    })
    .catch((err) => {
      toast(err.message || "登录失败", "error");
    });
});

// 关闭弹窗
document.getElementById("modalClose").addEventListener("click", closeRuleModal);
document.getElementById("btnCancel").addEventListener("click", closeRuleModal);
document.getElementById("deleteModalClose").addEventListener("click", closeDeleteModal);
document.getElementById("btnDeleteCancel").addEventListener("click", closeDeleteModal);

ruleModal.addEventListener("click", (e) => {
  if (e.target === ruleModal) closeRuleModal();
});
deleteModal.addEventListener("click", (e) => {
  if (e.target === deleteModal) closeDeleteModal();
});

document.getElementById("btnAdd").addEventListener("click", openAddModal);

// 初始化
if (getAuth()) {
  api("GET", "/api/rules")
    .then(() => {
      showContent();
      loadRules();
      fetchStatus();
    })
    .catch(() => showLogin());
} else {
  showLogin();
}
