const seedState = {
  activeId: "general",
  channels: [
    {
      id: "general",
      type: "channel",
      name: "general",
      topic: "团队公告、产品方向和日常同步。",
      unread: 0,
      messages: [
        {
          author: "Lin",
          role: "Founder",
          avatar: "L",
          time: "09:14",
          text: "欢迎来到 Da Chat。目标很简单：做一个轻量、开源、自托管的团队协作框架。"
        },
        {
          author: "Maya",
          role: "Design",
          avatar: "M",
          time: "09:21",
          text: "我把信息架构拆成工作区、频道、线程和集成四层。今天先把频道体验跑顺。"
        },
        {
          author: "Bai",
          role: "Maintainer",
          avatar: "B",
          time: "09:32",
          text: "前端原型已经本地持久化，后面可以接 Supabase、Postgres 或 Matrix 协议。"
        }
      ]
    },
    {
      id: "engineering",
      type: "channel",
      name: "engineering",
      topic: "架构、后端、部署和集成讨论。",
      unread: 3,
      messages: [
        {
          author: "Noah",
          role: "Backend",
          avatar: "N",
          time: "10:03",
          text: "建议核心模型先保持干净：workspace、channel、message、member、reaction、attachment。"
        },
        {
          author: "Bai",
          role: "Maintainer",
          avatar: "B",
          time: "10:08",
          text: "同意。插件系统可以先用 webhook + bot token 抽象，避免早期把权限模型做复杂。"
        }
      ]
    },
    {
      id: "design",
      type: "channel",
      name: "design",
      topic: "界面、交互、品牌和可访问性。",
      unread: 1,
      messages: [
        {
          author: "Maya",
          role: "Design",
          avatar: "M",
          time: "10:26",
          text: "视觉上别复制 Slack。Da 应该更安静、更开源工具感，但保留熟悉的信息密度。"
        }
      ]
    }
  ],
  dms: [
    {
      id: "dm-lin",
      type: "dm",
      name: "Lin",
      topic: "和 Lin 的私信。",
      unread: 0,
      messages: [
        {
          author: "Lin",
          role: "Founder",
          avatar: "L",
          time: "昨天",
          text: "我们先把 Da 做成可演示的开源 Slack，然后再考虑真实后端。"
        }
      ]
    },
    {
      id: "dm-maya",
      type: "dm",
      name: "Maya",
      topic: "和 Maya 的私信。",
      unread: 2,
      messages: [
        {
          author: "Maya",
          role: "Design",
          avatar: "M",
          time: "10:41",
          text: "频道详情右栏可以放成员、固定消息和路线图。"
        }
      ]
    }
  ],
  members: [
    { name: "Bai", role: "Maintainer", status: "online", avatar: "B" },
    { name: "Lin", role: "Founder", status: "online", avatar: "L" },
    { name: "Maya", role: "Design", status: "away", avatar: "M" },
    { name: "Noah", role: "Backend", status: "offline", avatar: "N" }
  ]
};

const storageKey = "daChatState";
const savedState = JSON.parse(localStorage.getItem(storageKey) || "null");
const state = savedState || seedState;

const nodes = {
  channelList: document.querySelector("#channelList"),
  dmList: document.querySelector("#dmList"),
  searchInput: document.querySelector("#searchInput"),
  clearSearch: document.querySelector("#clearSearch"),
  channelKicker: document.querySelector("#channelKicker"),
  channelTitle: document.querySelector("#channelTitle"),
  channelTopic: document.querySelector("#channelTopic"),
  detailsTopic: document.querySelector("#detailsTopic"),
  messageList: document.querySelector("#messageList"),
  composerForm: document.querySelector("#composerForm"),
  messageInput: document.querySelector("#messageInput"),
  messageCount: document.querySelector("#messageCount"),
  memberCount: document.querySelector("#memberCount"),
  channelCount: document.querySelector("#channelCount"),
  memberList: document.querySelector("#memberList"),
  detailsPanel: document.querySelector("#detailsPanel"),
  toggleDetails: document.querySelector("#toggleDetails"),
  newChannelButton: document.querySelector("#newChannelButton"),
  channelDialog: document.querySelector("#channelDialog"),
  closeChannelDialog: document.querySelector("#closeChannelDialog"),
  channelForm: document.querySelector("#channelForm")
};

function persist() {
  localStorage.setItem(storageKey, JSON.stringify(state));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function allRooms() {
  return [...state.channels, ...state.dms];
}

function activeRoom() {
  return allRooms().find((room) => room.id === state.activeId) || state.channels[0];
}

function setActiveRoom(id) {
  state.activeId = id;
  const room = activeRoom();
  room.unread = 0;
  persist();
  render();
}

function roomButton(room) {
  const prefix = room.type === "channel" ? "#" : "";
  const unread = room.unread ? `<span class="unread">${room.unread}</span>` : "";
  return `
    <button class="channel-button ${room.id === state.activeId ? "active" : ""}" type="button" data-room="${escapeHtml(room.id)}">
      <span>${prefix}${escapeHtml(room.name)}</span>
      ${unread}
    </button>
  `;
}

function renderRooms() {
  nodes.channelList.innerHTML = state.channels.map(roomButton).join("");
  nodes.dmList.innerHTML = state.dms.map(roomButton).join("");
}

function highlightText(text, query) {
  const safeText = escapeHtml(text);
  if (!query) return safeText;
  const safeQuery = escapeRegExp(escapeHtml(query));
  return safeText.replace(new RegExp(`(${safeQuery})`, "ig"), "<mark>$1</mark>");
}

function renderMessages() {
  const room = activeRoom();
  const query = nodes.searchInput.value.trim();
  const roomMatches = query && `${room.name} ${room.topic}`.toLowerCase().includes(query.toLowerCase());
  const messages = query
    ? room.messages.filter((message) => `${message.author} ${message.role} ${message.text}`.toLowerCase().includes(query.toLowerCase()))
    : room.messages;

  nodes.messageList.innerHTML = messages.length
    ? messages.map((message) => `
      <article class="message">
        <div class="avatar">${escapeHtml(message.avatar)}</div>
        <div class="message-body">
          <header>
            <strong>${escapeHtml(message.author)}</strong>
            <span>${escapeHtml(message.role)}</span>
            <time>${escapeHtml(message.time)}</time>
          </header>
          <p>${highlightText(message.text, query)}</p>
          <div class="message-actions">
            <button type="button">回复</button>
            <button type="button">固定</button>
            <button type="button">分享</button>
          </div>
        </div>
      </article>
    `).join("")
    : roomMatches
      ? `<div class="empty-state">当前频道名称或主题匹配搜索，但还没有匹配的消息。</div>`
      : `<div class="empty-state">没有匹配的消息。</div>`;

  nodes.messageList.scrollTop = nodes.messageList.scrollHeight;
}

function renderHeader() {
  const room = activeRoom();
  const prefix = room.type === "channel" ? "#" : "";
  nodes.channelKicker.textContent = room.type === "channel" ? "频道" : "私信";
  nodes.channelTitle.textContent = `${prefix}${room.name}`;
  nodes.channelTopic.textContent = room.topic;
  nodes.detailsTopic.textContent = room.topic;
}

function renderMembers() {
  nodes.memberList.innerHTML = state.members.map((member) => `
    <div class="member">
      <div class="avatar">${escapeHtml(member.avatar)}</div>
      <div>
        <strong>${escapeHtml(member.name)}</strong>
        <span>${escapeHtml(member.role)}</span>
      </div>
      <i class="${escapeHtml(member.status)}" title="${escapeHtml(member.status)}"></i>
    </div>
  `).join("");
}

function renderStats() {
  const totalMessages = allRooms().reduce((sum, room) => sum + room.messages.length, 0);
  nodes.messageCount.textContent = totalMessages;
  nodes.memberCount.textContent = state.members.length;
  nodes.channelCount.textContent = state.channels.length;
}

function render() {
  renderRooms();
  renderHeader();
  renderMessages();
  renderMembers();
  renderStats();
}

function createMessage(text) {
  const room = activeRoom();
  room.messages.push({
    author: "Bai",
    role: "Maintainer",
    avatar: "B",
    time: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
    text
  });
  persist();
  render();
}

function createChannel(form) {
  const data = new FormData(form);
  const name = String(data.get("name") || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");

  if (!name) return;
  if (state.channels.some((channel) => channel.name === name)) {
    alert("这个频道已经存在。");
    return;
  }

  state.channels.push({
    id: `channel-${Date.now()}`,
    type: "channel",
    name,
    topic: data.get("topic"),
    unread: 0,
    messages: [
      {
        author: "Da",
        role: "System",
        avatar: "D",
        time: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
        text: `#${name} 已创建。`
      }
    ]
  });
  state.activeId = state.channels[state.channels.length - 1].id;
  form.reset();
  nodes.channelDialog.close();
  persist();
  render();
}

document.addEventListener("click", (event) => {
  const roomButtonNode = event.target.closest("[data-room]");
  if (roomButtonNode) setActiveRoom(roomButtonNode.dataset.room);
});

nodes.composerForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = nodes.messageInput.value.trim();
  if (!text) return;
  createMessage(text);
  nodes.messageInput.value = "";
  nodes.messageInput.focus();
});

nodes.searchInput.addEventListener("input", renderMessages);
nodes.clearSearch.addEventListener("click", () => {
  nodes.searchInput.value = "";
  renderMessages();
});

nodes.toggleDetails.addEventListener("click", () => {
  nodes.detailsPanel.classList.toggle("collapsed");
});

nodes.newChannelButton.addEventListener("click", () => {
  nodes.channelDialog.showModal();
});

nodes.closeChannelDialog.addEventListener("click", () => {
  nodes.channelDialog.close();
});

nodes.channelForm.addEventListener("submit", (event) => {
  event.preventDefault();
  createChannel(event.currentTarget);
});

nodes.messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
    nodes.composerForm.requestSubmit();
  }
});

render();
