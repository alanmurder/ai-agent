# AI Agent Framework

一个原生AI产品框架，具备迭代进化能力和持久记忆系统，分为**个人版**和**企业版**两个版本。

---

## 核心特性

### 🧠 迭代进化能力（三层进化机制）

| 层级 | 名称 | 功能 | 实现方式 |
|------|------|------|----------|
| **Level 1** | 记忆进化 | 自动学习用户偏好、习惯、重要事实 | MemoryEvolver |
| **Level 2** | Skill进化 | 辅助创建自定义Skill、性能优化反馈 | SkillEvolver |
| **Level 3** | 自主进化 | 识别功能缺口、自动编写代码、安全沙箱测试 | AutonomousEvolver |

### 💾 持久记忆系统（类OpenClaw设计）

| 类型 | 存储位置 | 内容 | 生命周期 |
|------|----------|------|----------|
| **长期记忆** | MEMORY.md + 向量数据库 | 用户偏好、习惯、重要事实 | 永久 |
| **中期记忆** | PostgreSQL | 会话总结、任务历史、知识积累 | 30天→归档 |
| **短期记忆** | Redis缓存 | 当前对话上下文、临时状态 | 会话期间 |
| **工作记忆** | 内存 | Agent当前任务、工具调用结果 | 任务执行期间 |

### 🔧 Skill扩展系统

- **内置模式**: 13个预置Skills，覆盖个人和企业场景
- **扩展模式**: SKILL.md标准格式，动态加载
- **自定义创建**: Agent辅助编写新Skill

### 🤖 国产模型优先

| 模型 | Provider | Context Window | 特点 |
|------|----------|----------------|------|
| **DeepSeek-V3** | 首选 | 64K | 低成本、高性能 |
| **GLM-4** | 智谱 | 128K | 长上下文、工具调用 |
| **Qwen-Max** | 阿里 | 32K | 稳定可靠 |
| **ERNIE-4.0** | 百度 | 8K | 中文优化 |

国际模型（GPT-4/Claude）作为备选，支持故障切换。

### 🌐 多渠道Gateway

- **Web UI**: FastAPI + WebSocket实时聊天
- **微信**: 企业号API集成
- **钉钉**: 机器人消息推送
- **飞书**: Lark API集成

### 🔄 HEARTBEAT主动机制

类似OpenClaw的HEARTBEAT.md系统，支持：
- 主动任务调度（每日总结、记忆整理、Skill检查）
- 定期进化检查
- 无用户触发时的自主执行

---

## 项目架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        应用层 (Application)                        │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐         │
│  │    个人版     │  │    企业版     │  │    Web UI     │         │
│  │  生活/学习    │  │  直播/电商    │  │  FastAPI      │         │
│  │  协作/技术    │  │  客服/分析    │  │  WebSocket    │         │
│  └───────────────┘  └───────────────┘  └───────────────┘         │
├─────────────────────────────────────────────────────────────────┤
│                        Skill层 (Extensibility)                    │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  内置Skills  │  扩展Skills  │  SkillHub  │  Skill进化器  │   │
│  │  (13个预置)  │  (自定义)    │  (社区)    │  (L2/L3进化)  │   │
│  └───────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                      Agent核心层 (Core)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │  模型路由   │  │  工具执行   │  │  循环引擎   │  │ 记忆层  │ │
│  │  多模型切换 │  │  参数验证   │  │  上下文构建 │  │ 4层存储 │ │
│  │  故障转移   │  │  安全执行   │  │  响应解析   │  │ 检索引擎│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    基础设施层 (Infrastructure)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │  Gateway    │  │  消息适配   │  │  配置管理   │  │ 日志监控│ │
│  │  路由分发   │  │  多渠道接入 │  │  YAML+环境  │  │ 结构化  │ │
│  │  会话管理   │  │  标准化格式 │  │  热加载    │  │ 指标收集│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                     高级特性层 (Advanced)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │  HEARTBEAT  │  │  多Agent    │  │  企业权限   │  │ 安全机制│ │
│  │  主动调度   │  │  协作框架   │  │  RBAC控制  │  │ 认证授权│ │
│  │  进化检查   │  │  任务分配   │  │  数据隔离  │  │ 审计沙箱│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              并发基础设施层 (Concurrency)                    ││
│  │  连接池 │ 分布式锁 │ 分布式限流 │ 任务队列 │ 缓存 │ 会话存储││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              集群部署层 (Kubernetes)                         ││
│  │  Deployment │ HPA │ Ingress │ Service │ 监控 │ 健康检查     ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 项目目录结构

```
ai-agent/
├── core/                        # 核心层
│   ├── agent/                   # Agent引擎模块
│   │   ├── engine.py            # Agent循环引擎
│   │   ├── types.py             # Agent输入输出类型
│   │   └── __init__.py
│   │
│   ├── memory/                  # 记忆系统模块
│   │   ├── manager.py           # 记忆管理器
│   │   ├── types.py             # 记忆类型定义
│   │   └── __init__.py
│   │
│   ├── model/                   # 模型路由模块
│   │   ├── router.py            # 多模型路由器
│   │   ├── types.py             # 模型配置类型
│   │   └── __init__.py
│   │
│   ├── tools/                   # 工具框架模块
│   │   ├── registry.py          # 工具注册器
│   │   ├── executor.py          # 工具执行器
│   │   ├── types.py             # 工具类型定义
│   │   └── __init__.py
│   │
│   ├── evolution/               # 进化机制模块
│   │   ├── evolver.py           # 三层进化器
│   │   └── __init__.py
│   │
│   ├── heartbeat/               # HEARTBEAT模块
│   │   ├── scheduler.py         # 主动任务调度器
│   │   └── __init__.py
│   │
│   ├── multi_agent/             # 多Agent协作模块
│   │   ├── orchestrator.py      # 多Agent编排器
│   │   └── __init__.py
│   │
│   ├── enterprise/              # 企业权限模块
│   │   ├── permissions.py       # RBAC权限管理
│   │   └── __init__.py
│   │
│   ├── security/                # 安全机制模块
│   │   ├── auth.py              # API认证层
│   │   ├── audit.py             # 审计日志
│   │   ├── isolation.py         # 数据隔离
│   │   ├── sandbox.py           # 安全沙箱+审批
│   │   ├── concurrent.py        # 并发安全组件
│   │   └── __init__.py
│   │
│   ├── concurrency/             # 并发基础设施模块
│   │   ├── __init__.py          # 连接池、锁、限流、队列
│   │
│   ├── health/                  # 健康检查模块
│   │   ├── __init__.py          # Liveness/Readiness探针
│   │
│   ├── logging.py               # 结构化日志
│   ├── metrics.py               # 指标收集
│   ├── utils.py                 # 工具函数
│   └── cli.py                   # CLI入口
│
├── skills/                      # Skill层
│   ├── builtin/                 # 内置Skills
│   │   ├── personal/            # 个人版Skills
│   │   │   ├── file_manager/    # 文件管理
│   │   │   ├── code_helper/     # 代码辅助
│   │   │   ├── daily_planner/   # 日程管理
│   │   │   ├── study_assistant/ # 学习助手
│   │   │   └── collaboration/   # 协作助手
│   │   │
│   │   └── enterprise/          # 企业版Skills
│   │       ├── live_analytics/  # 直播数据分析
│   │       ├── product_manager/ # 商品管理
│   │       ├── customer_service/# 客服售后
│   │       └── market_analysis/ # 竞品分析
│   │
│   ├── extensions/              # 扩展Skills目录
│   ├── loader.py                # Skill加载器
│   ├── manager.py               # Skill管理器
│   ├── types.py                 # Skill类型定义
│   └── __init__.py
│
├── gateway/                     # Gateway层
│   ├── adapters/                # 消息适配器
│   │   ├── base.py              # 适配器基类
│   │   ├── web.py               # Web适配器
│   │   ├── wechat.py            # 微信适配器
│   │   ├── dingtalk.py          # 钉钉适配器
│   │   ├── feishu.py            # 飞书适配器
│   │   └── __init__.py
│   │
│   ├── router.py                # 消息路由器
│   ├── session.py               # 会话管理器
│   ├── server.py                # FastAPI服务器
│   ├── types.py                 # Gateway类型
│   └── __init__.py
│
├── config/                      # 配置管理
│   ├── settings.yaml            # 主配置文件
│   ├── manager.py               # 配置管理器
│   └── __init__.py
│
├── storage/                     # 存储层
│   ├── file/                    # 文件存储
│   │   └── init.sql             # 数据库初始化
│   └── db/                      # 数据库模块
│
├── web/                         # Web UI
│   ├── app/                     # 前端应用
│   ├── static/                  # 静态资源
│   └── templates/               # 模板文件
│
├── deploy/                      # 部署配置
│   ├── k8s/                     # Kubernetes配置
│   │   ├── namespace.yaml       # Namespace
│   │   ├── configmap.yaml       # 应用配置
│   │   ├── secrets.yaml         # 敏感信息
│   │   ├── deployment.yaml      # 应用部署
│   │   ├── service.yaml         # 服务配置
│   │   ├── ingress.yaml         # 外部访问
│   │   ├── hpa.yaml             # 自动扩缩容
│   │   ├── redis.yaml           # Redis部署
│   │   ├── postgres.yaml        # PostgreSQL部署
│   │   ├── monitoring.yaml      # Prometheus监控
│   │   └ grafana-dashboard.yaml # Grafana仪表盘
│   │   └── __init__.py
│   │
│   └── docker/                  # Docker配置
│
├── tests/                       # 测试
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   └── test_basic.py
│
├── docs/                        # 文档
├── pyproject.toml               # 项目配置
├── docker-compose.yml           # Docker配置
├── Dockerfile                   # 主镜像
├── Dockerfile.gateway           # Gateway镜像
├── .env.example                 # 环境变量模板
├── .gitignore                   # Git忽略
└── README.md                    # 本文档
```

---

## 模块功能详解

### 1. Agent核心层

#### Agent引擎 (`core/agent/engine.py`)

Agent执行循环的核心实现：

```
执行流程:
1. 接收输入 → 创建会话上下文
2. 构建上下文 → 加载记忆、Skills、工具
3. 调用模型 → 模型路由选择最佳模型
4. 解析响应 → 判断文本回复或工具调用
5. 执行工具 → 参数验证、安全执行、结果处理
6. 更新记忆 → 写入短期记忆、归档重要信息
7. 生成输出 → 返回响应内容
8. 循环判断 → 是否需要继续执行
```

#### 模型路由 (`core/model/router.py`)

```python
# 模型优先级配置
model:
  primary: deepseek          # 首选模型
  fallback:
    - zhipu                  # 备选1
    - qwen                   # 备选2
    - baidu                  # 备选3
    - openai                 # 国际备选
    - anthropic              # 国际备选

# 故障切换机制
当主模型调用失败时，自动切换到下一个备选模型
记录失败次数，用于健康监控
```

#### 工具框架 (`core/tools/`)

```python
# 工具注册流程
1. 定义工具: TOOL_DEFINITIONS列表
2. 注册到Registry: tool_registry.register(tool)
3. 注册处理器: tool_registry.register_handler(name, handler)
4. 执行调用: tool_executor.execute(call, context)

# 安全机制
- 参数验证（JSON Schema）
- 权限检查
- 超时控制
- 异常处理
```

### 2. 记忆系统 (`core/memory/`)

#### 四层记忆架构

```
┌─────────────────────────────────────┐
│         长期记忆 (MEMORY.md)          │  ← 永久存储
│  用户偏好、习惯、重要个人信息         │
├─────────────────────────────────────┤
│         中期记忆 (PostgreSQL)         │  ← 30天归档
│  会话总结、任务历史、知识积累         │
├─────────────────────────────────────┤
│         短期记忆 (Redis)              │  ← 会话期间
│  当前对话上下文、临时状态             │
├─────────────────────────────────────┤
│         工作记忆 (内存)               │  ← 任务执行
│  Agent当前任务、工具调用结果          │
└─────────────────────────────────────┘
```

#### 文件存储结构

```
~/.ai-agent/workspace/
├── SOUL.md              # 用户性格偏好设定
│   ├── Personality: 性格描述
│   ├── Preferences: 用户偏好
│   └── Tone: 语气风格
│
├── MEMORY.md            # 长期记忆索引
│   ├── User Information: 用户信息
│   ├── Important Facts: 重要事实
│   └── Interaction History: 交互历史
│
├── HEARTBEAT.md         # 主动任务配置
│   ├── interval: 心跳间隔
│   ├── evolution_enabled: 进化开关
│   └── Tasks: 任务列表
│
└── memory/
    ├── 2026-04-17.md    # 每日日志
    ├── sessions/        # 会话记录
    └── archive/         # 归档文件
```

### 3. Skill系统 (`skills/`)

#### Skill标准结构

每个Skill包含以下文件：

```
skill_name/
├── SKILL.md              # 元数据和描述
├── tools.py              # 工具定义
├── handlers.py           # 处理逻辑
├── prompts.py            # Prompt模板
└── tests/                # 测试文件
```

#### SKILL.md格式

```yaml
---
name: skill_name
version: 1.0.0
category: lifestyle/learning/work/ecommerce
description: 功能描述
author: builtin/user
dependencies: []
permissions: []
tags: []
enabled: true
priority: 100
---

## 功能描述
详细功能说明

## 使用场景
适用场景列表

## 工具列表
- tool_name: 功能说明
```

### 4. 进化机制 (`core/evolution/`)

#### Level 1: 记忆进化

```python
# 自动提取机制
1. 分析用户对话内容
2. 提取偏好: "我喜欢..." "我偏好..."
3. 提取事实: "我叫..." "我是..."
4. 提取模式: "经常..." "总是..."
5. 写入MEMORY.md和SOUL.md
```

#### Level 2: Skill进化

```python
# 辅助创建流程
1. 用户描述需求
2. 分析需求类型
3. 生成SKILL.md骨架
4. 生成tools.py和handlers.py
5. 保存到extensions目录

# 性能优化流程
1. 收集使用反馈
2. 分析性能问题
3. 提出优化建议
4. 自动或手动优化
```

#### Level 3: 自主进化

```python
# 自主进化流程
1. 识别功能缺口
   - 分析失败请求
   - 检查Skill覆盖率
   
2. 生成Skill代码
   - 分析能力需求
   - 使用模型生成代码
   
3. 沙箱测试验证
   - 语法检查
   - 功能测试
   
4. 安全审计
   - 检查危险代码
   - 权限验证
   
5. 部署上线
   - 写入extensions目录
   - 加载新Skill
```

### 5. HEARTBEAT机制 (`core/heartbeat/`)

```yaml
# HEARTBEAT.md配置
---
interval: 300              # 心跳间隔(秒)
evolution_enabled: true    # 进化开关
evolution_level: 1         # 进化级别
---

# 定期任务列表
- [ ] 每日总结 :: generate_daily_summary :: daily
- [ ] 记忆整理 :: organize_memory :: weekly
- [ ] Skill检查 :: check_skill_updates :: weekly

# 进化检查
- [ ] 功能缺口识别 :: identify_evolution_gaps :: hourly
- [ ] 记忆进化分析 :: analyze_memory_evolution :: daily
```

### 6. 多Agent协作 (`core/multi_agent/`)

```python
# Agent角色定义
AgentRole:
  - researcher: 研究信息
  - executor: 执行任务
  - analyst: 分析数据
  - coordinator: 协调汇总

# 协作模式
1. 并行执行: 多个独立任务同时执行
2. 顺序执行: 任务按依赖关系串行执行
3. 专家委派: 将任务委派给专家Agent
```

### 7. Gateway层 (`gateway/`)

#### 消息适配器接口

```python
class MessageAdapter:
    async def connect() -> bool      # 建立连接
    async def receive() -> List[Msg] # 接收消息
    async def send(msg) -> bool      # 发送消息
    async def disconnect() -> bool   # 断开连接
    def normalize(raw) -> Message    # 标准化格式
```

#### Web API端点

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/health` | 完整健康检查 |
| GET | `/health/live` | Kubernetes存活探针 |
| GET | `/health/ready` | Kubernetes就绪探针 |
| GET | `/metrics` | Prometheus指标 |
| POST | `/api/chat` | 同步聊天 |
| WebSocket | `/ws/chat` | 实时聊天 |
| GET | `/api/skills` | 列出Skills |
| POST | `/api/memory` | 更新记忆 |

### 8. 安全机制 (`core/security/`)

安全体系架构包含六大核心模块，实现全方位的安全防护。

#### 安全架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        安全机制架构                              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  API认证    │  │  权限控制   │  │  审计日志   │             │
│  │  (auth.py)  │  │(permissions)│  │ (audit.py)  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  数据隔离   │  │  安全沙箱   │  │  危险操作   │             │
│  │(isolation)  │  │ (sandbox)   │  │   审批      │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 1. API认证层 (`core/security/auth.py`)

支持双令牌认证机制：

| 组件 | 功能 | 适用场景 |
|------|------|----------|
| **TokenManager** | API Token管理 | 长期API访问 |
| **JWTManager** | JWT令牌管理 | 用户会话认证 |
| **AuthMiddleware** | 认证中间件 | 统一认证入口 |

```python
# API Token流程
1. generate_token(user_id, scopes) → "sk-xxx"
2. verify_token(raw_token) → APIToken
3. revoke_token(token_id) → bool

# JWT流程
1. generate_jwt(user) → "jwt-session.signature"
2. verify_jwt(token) → JWTPayload
3. refresh_jwt(token) → new_token

# 认证流程
AuthMiddleware.authenticate(auth_header, api_key) → EnterpriseUser
```

#### 2. 工具权限执行 (`core/tools/executor.py`)

SecureToolExecutor实现五步安全检查：

```
执行流程:
1. 用户验证 → 用户存在且活跃
2. 权限检查 → 用户拥有工具所需权限
3. 危险操作 → 检查DANGEROUS_TOOLS，可能需要审批
4. 参数验证 → JSON Schema校验
5. 安全执行 → 超时控制 + 异常处理 + 审计记录
```

**危险工具定义：**

```python
DANGEROUS_TOOLS = {
    "delete_file": "ADMIN",      # 删除文件需管理员
    "shell_execute": "ADMIN",    # Shell执行需管理员
    "write_file": "MANAGER",     # 写文件需经理
    "autonomous_create": "ADMIN", # 自主进化需管理员
}
```

**工具权限映射：**

```python
TOOL_PERMISSIONS = {
    "read_file": Permission.VIEW_DATA,
    "write_file": Permission.CREATE_CONTENT,
    "get_live_metrics": Permission.VIEW_ANALYTICS,
    "handle_refund": Permission.PROCESS_ORDERS,
    "update_product": Permission.MANAGE_PRODUCTS,
    ...
}
```

#### 3. 数据隔离 (`core/security/isolation.py`)

多层级数据访问控制：

| 范围类型 | 访问范围 | 适用角色 |
|----------|----------|----------|
| **user** | 仅个人数据 | Operator/Viewer |
| **team** | 团队数据 | Team Manager |
| **department** | 部门数据 | Department Manager |
| **organization** | 全组织数据 | Admin |

```python
# 数据隔离流程
1. set_user_scope(user_id, team_id, department_id)
2. filter_data(user_id, data_list, resource_type)
3. check_write_access(user_id, resource_type, resource_id)

# 响应过滤
DataIsolationMiddleware.filter_response(user_id, response)
```

#### 4. 审计日志 (`core/security/audit.py`)

全量安全事件记录：

| 事件类型 | 记录内容 |
|----------|----------|
| **LOGIN/LOGOUT** | 登录登出记录 |
| **TOOL_CALL** | 工具调用详情 |
| **TOOL_DENIED** | 权限拒绝记录 |
| **DATA_READ/WRITE** | 数据访问记录 |
| **AUTONOMOUS_CODE** | 自主代码生成 |

```python
# 审计功能
- log_event(event_type, user_id, details)
- log_tool_execution(user_id, tool_name, params, result)
- log_permission_denied(user_id, tool_name, required_permission)
- search_events(user_id, event_type, time_range)
- generate_report(start_time, end_time)
```

#### 5. 安全沙箱 (`core/security/sandbox.py`)

Level 3自主进化的隔离执行环境：

**沙箱配置：**

```python
SandboxConfig:
  max_memory_mb: 100      # 内存限制
  max_cpu_seconds: 10     # CPU时间限制
  max_wall_seconds: 30    # 执行超时
  network_access: false   # 禁止网络
  file_access: false      # 禁止文件操作
```

**代码验证规则：**

```python
# 禁止模式
forbidden_patterns = [
    "import os", "import sys", "import subprocess",
    "__import__", "eval", "exec", "compile",
    "open(", "socket", "requests",
]

# 允许模块白名单
allowed_modules = [
    "json", "datetime", "typing", "dataclasses",
    "collections", "itertools", "functools",
    "re", "math", "statistics", "enum",
]
```

#### 6. 危险操作审批 (`core/security/sandbox.py`)

工作流程：

```
审批流程:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  用户请求   │ → │  创建审批   │ → │  等待审批   │
│ 危险操作    │    │  request    │    │  pending    │
└─────────────┘    └─────────────┘    └─────────────┘
                                            ↓
                   ┌─────────────┐    ┌─────────────┐
                   │  执行操作   │ ← │  管理员审批 │
                   │  execute    │    │  approve    │
                   └─────────────┘    └─────────────┘
```

```python
# 审批API
request_approval(user_id, operation, details) → approval_id
approve_operation(approval_id, approver_id) → (success, error)
reject_operation(approval_id, rejector_id, reason) → (success, error)
check_approval(approval_id) → (approved, reason)
```

---

## 并发机制 (`core/concurrency/`)

企业级并发架构，支持高并发、多实例部署。

### 并发架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     并发基础设施架构                              │
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │  Redis连接池  │  │ PostgreSQL池  │  │  分布式锁     │        │
│  │  (aioredis)   │  │  (asyncpg)    │  │ (Distributed) │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │  分布式限流   │  │  异步任务队列 │  │  缓存管理     │        │
│  │  (RateLimit)  │  │  (TaskQueue)  │  │  (Cache)      │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐                           │
│  │  会话存储     │  │  并发安全组件 │                           │
│  │  (Session)    │  │  (Concurrent) │                           │
│  └───────────────┘  └───────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 功能 | 适用场景 |
|------|------|----------|
| **RedisConnectionPool** | Redis连接池 | 分布式存储、缓存、锁 |
| **PostgresConnectionPool** | PostgreSQL连接池 | 数据库访问、持久化 |
| **DistributedLock** | Redis分布式锁 | 多实例协调、防竞态 |
| **DistributedRateLimiter** | 分布式限流 | API限流、防滥用 |
| **AsyncTaskQueue** | 异步任务队列 | 后台处理、解耦执行 |
| **SessionStore** | Redis会话存储 | 多实例会话共享 |
| **CacheManager** | 缓存管理 | 减少数据库压力 |

### 连接池配置

```yaml
# config/settings.yaml
concurrency:
  redis:
    url: redis://localhost:6379/0
    min_pool_size: 5
    max_pool_size: 20
    connection_timeout: 10
    
  postgres:
    url: postgresql://user:pass@localhost:5432/aiagent
    min_pool_size: 5
    max_pool_size: 20
    command_timeout: 30
    
  task_queue:
    max_workers: 10
    queue_name: "tasks"
```

### 分布式锁使用

```python
from core.concurrency import DistributedLock, get_redis_pool

# 创建分布式锁
lock = DistributedLock(
    redis_pool=get_redis_pool(),
    lock_name="user_update:user123",
    timeout=30,
)

# 使用锁（推荐方式）
async with lock.locked():
    # 执行需要加锁的操作
    await update_user_data(user_id)

# 手动方式
acquired = await lock.acquire()
if acquired:
    await update_user_data(user_id)
    await lock.release()
```

### 分布式限流

```python
from core.concurrency import DistributedRateLimiter, get_redis_pool

# 创建限流器（60次/分钟）
rate_limiter = DistributedRateLimiter(
    redis_pool=get_redis_pool(),
    key="api:user123",
    limit=60,
    window=60,
)

# 检查是否允许
allowed, current, remaining = await rate_limiter.check()

if not allowed:
    raise RateLimitExceededError()
```

### 异步任务队列

```python
from core.concurrency import AsyncTaskQueue, get_task_queue

# 注册任务处理器
async def process_report(payload):
    # 处理报表生成
    pass

queue = get_task_queue()
queue.register_handler("generate_report", process_report)

# 启动工作线程
await queue.start_workers()

# 提交任务
task_id = await queue.enqueue(
    task_type="generate_report",
    payload={"report_type": "daily", "user_id": "user123"},
)

# 关闭
await queue.stop_workers()
```

### 并发安全组件

并发安全版本的安全组件，替代内存存储：

```python
# 并发安全认证
from core.security.concurrent import ConcurrentAuthMiddleware

auth = ConcurrentAuthMiddleware(redis_pool)
session = await auth.create_user_session(email, password)

# 并发安全数据隔离
from core.security.concurrent import ConcurrentDataIsolationManager

isolation = ConcurrentDataIsolationManager(redis_pool)
await isolation.set_user_scope(user_id, team_id, dept_id)
filtered_data = await isolation.filter_data(user_id, data_list, "orders")
```

### 并发初始化

```python
from core.concurrency import (
    init_concurrency_infrastructure,
    close_concurrency_infrastructure,
)

# 应用启动时
await init_concurrency_infrastructure()

# 应用关闭时
await close_concurrency_infrastructure()
```

### 高并发场景处理

| 场景 | 解决方案 |
|------|----------|
| **多实例部署** | Redis共享会话、Token、Scope |
| **热点数据竞争** | DistributedLock防竞态 |
| **API限流** | DistributedRateLimiter滑动窗口 |
| **后台任务** | AsyncTaskQueue异步处理 |
| **数据库压力** | CacheManager缓存热点查询 |
| **会话跨实例** | SessionStore Redis存储 |

---

## 集群部署 (`deploy/k8s/`)

完整的 Kubernetes 集群部署方案，支持生产级高可用。

### 集群架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                                │
│                                                                         │
│  ┌─────────────────── Ingress Layer ───────────────────┐               │
│  │  nginx-ingress-controller                          │               │
│  │  ├── SSL/TLS (Let's Encrypt)                        │               │
│  │  ├── Rate Limiting (100 RPS)                        │               │
│  │  ├── WebSocket Support                              │               │
│  │  └── Load Balancing                                 │               │
│  └─────────────────────────────────────────────────────┘               │
│                          ↓                                              │
│  ┌─────────────────── Service Layer ───────────────────┐               │
│  │  ai-agent Service (ClusterIP)                       │               │
│  │  ├── Port 8080 (HTTP API)                           │               │
│  │  └ Port 8081 (WebSocket)                            │               │
│  └─────────────────────────────────────────────────────┘               │
│                          ↓                                              │
│  ┌─────────────────── Application Layer ───────────────┐               │
│  │  Deployment: ai-agent (3-20 replicas)               │               │
│  │  ├── Pod 1 (ai-agent-pod-1)                         │               │
│  │  ├── Pod 2 (ai-agent-pod-2)                         │               │
│  │  ├── Pod 3 (ai-agent-pod-3)                         │               │
│  │  └── HPA (Auto-scaling 70% CPU)                     │               │
│  └─────────────────────────────────────────────────────┘               │
│                          ↓                                              │
│  ┌─────────────────── Data Layer ───────────────────────┐              │
│  │  ├── Redis (Cache + Session + Lock)                 │               │
│  │  │   └─ Deployment: redis                           │               │
│  │  │                                                   │               │
│  │  └── PostgreSQL (Persistent Storage)                │               │
│  │      └ StatefulSet: postgres (10Gi PVC)             │               │
│  └─────────────────────────────────────────────────────┘               │
│                                                                         │
│  ┌─────────────────── Monitoring Layer ─────────────────┐              │
│  │  ├── Prometheus (Metrics Collection)                 │               │
│  │  │   └ ServiceMonitor: ai-agent-monitor              │               │
│  │  │                                                   │               │
│  │  └── Grafana (Visualization)                         │               │
│  │      └ Dashboard: ai-agent-dashboard                 │               │
│  └─────────────────────────────────────────────────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Kubernetes 配置文件

| 文件 | 功能 |
|------|------|
| `namespace.yaml` | 创建 ai-agent namespace |
| `configmap.yaml` | 应用配置（环境变量） |
| `secrets.yaml` | 敏感信息（API密钥、密码） |
| `deployment.yaml` | 应用部署配置（3副本） |
| `service.yaml` | 服务暴露配置 |
| `ingress.yaml` | 外部访问入口 |
| `hpa.yaml` | 自动扩缩容配置 |
| `redis.yaml` | Redis 部署 |
| `postgres.yaml` | PostgreSQL StatefulSet |
| `monitoring.yaml` | Prometheus ServiceMonitor + Rules |
| `grafana-dashboard.yaml` | Grafana Dashboard 配置 |

### 部署命令

```bash
# 1. 创建 namespace
kubectl apply -f deploy/k8s/namespace.yaml

# 2. 创建配置和密钥
kubectl apply -f deploy/k8s/configmap.yaml
kubectl apply -f deploy/k8s/secrets.yaml

# 3. 部署基础设施（Redis + PostgreSQL）
kubectl apply -f deploy/k8s/redis.yaml
kubectl apply -f deploy/k8s/postgres.yaml

# 4. 等待基础设施就绪
kubectl wait --for=condition=ready pod -l app=redis -n ai-agent --timeout=60s
kubectl wait --for=condition=ready pod -l app=postgres -n ai-agent --timeout=60s

# 5. 部署应用
kubectl apply -f deploy/k8s/deployment.yaml
kubectl apply -f deploy/k8s/service.yaml

# 6. 配置自动扩缩容
kubectl apply -f deploy/k8s/hpa.yaml

# 7. 配置外部访问
kubectl apply -f deploy/k8s/ingress.yaml

# 8. 安装监控（需要 Prometheus Operator）
kubectl apply -f deploy/k8s/monitoring.yaml
kubectl apply -f deploy/k8s/grafana-dashboard.yaml

# 查看部署状态
kubectl get all -n ai-agent
kubectl get hpa -n ai-agent
kubectl logs -f deployment/ai-agent -n ai-agent
```

### 健康检查端点

| 端点 | 功能 | Kubernetes用途 |
|------|------|----------------|
| `/health` | 完整健康检查 | 人工检查 |
| `/health/live` | 存活探针 | Liveness Probe |
| `/health/ready` | 就绪探针 | Readiness Probe |
| `/metrics` | Prometheus指标 | 监控采集 |

### 自动扩缩容策略

```yaml
# HPA 配置
minReplicas: 3
maxReplicas: 20

# 扩容触发条件
- CPU > 70%
- Memory > 80%
- Active Sessions > 100/pod
- Request Rate > 50 RPS/pod

# 扩容策略
scaleUp:
  stabilizationWindow: 60s
  maxPods: 4 per minute
  maxPercent: 100%

# 缩容策略
scaleDown:
  stabilizationWindow: 300s
  maxPods: 2 per 2 minutes
  maxPercent: 10%
```

### Prometheus 监控指标

| 指标 | 类型 | 说明 |
|------|------|------|
| `http_requests_total` | Counter | HTTP请求总数 |
| `http_request_duration_seconds` | Histogram | 请求延迟分布 |
| `model_call_count` | Counter | 模型调用次数 |
| `model_latency_ms` | Gauge | 模型响应延迟 |
| `tool_execution_count` | Counter | 工具执行次数 |
| `tool_execution_time_ms` | Histogram | 工具执行时间 |
| `active_sessions` | Gauge | 当前活跃会话数 |
| `rate_limit_exceeded_total` | Counter | 限流触发次数 |

### Grafana 告警规则

| 告警 | 触发条件 | 严重性 |
|------|----------|--------|
| `HighErrorRate` | 错误率 > 5% | Warning |
| `HighLatency` | p95延迟 > 2s | Warning |
| `PodUnavailable` | Pod非Running | Critical |
| `ModelRouterDown` | 无可用模型 | Critical |
| `RedisDown` | Redis连接失败 | Critical |
| `HighMemory` | 内存 > 85% | Warning |

### 配置管理

**环境变量注入：**

```yaml
# Pod 环境变量
env:
  - name: POD_NAME         # 自动注入 Pod 名称
    valueFrom:
      fieldRef:
        fieldPath: metadata.name
  - name: POD_NAMESPACE    # 自动注入 Namespace
    valueFrom:
      fieldRef:
        fieldPath: metadata.namespace
  - name: POD_IP           # 自动注入 Pod IP
    valueFrom:
      fieldRef:
        fieldPath: status.podIP
```

**敏感信息管理：**

```bash
# 创建密钥（生产环境）
kubectl create secret generic ai-agent-secrets \
  --from-literal=DEEPSEEK_API_KEY='your-key' \
  --from-literal=DATABASE_URL='postgresql://...' \
  --from-literal=JWT_SECRET='random-string' \
  -n ai-agent

# 使用外部密钥管理（推荐）
# 安装 External Secrets Operator
# 从 AWS Secrets Manager / Vault 同步
```

### 滚动更新

```bash
# 更新镜像
kubectl set image deployment/ai-agent \
  ai-agent=ai-agent:v0.2.0 \
  -n ai-agent

# 查看滚动更新状态
kubectl rollout status deployment/ai-agent -n ai-agent

# 回滚
kubectl rollout undo deployment/ai-agent -n ai-agent
kubectl rollout undo deployment/ai-agent --to-revision=2 -n ai-agent
```

### 多区域部署（可选）

```yaml
# 跨区域部署配置
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        app: ai-agent

# 区域亲和性
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: topology.kubernetes.io/zone
              operator: In
              values: [zone-a, zone-b, zone-c]
```

---

## 企业版 vs 个人版

### 功能对比表

| 功能模块 | 个人版 | 企业版 |
|----------|--------|--------|
| **生活助手** | ✅ 日程管理、提醒、健康追踪 | ❌ |
| **学习助手** | ✅ 知识问答、笔记整理、学习计划 | ❌ |
| **协作助手** | ✅ 文档协作、任务分配、会议安排 | ✅ 基础功能 |
| **技术助手** | ✅ 代码辅助、调试、技术问答 | ✅ 基础功能 |
| **文件管理** | ✅ 文件操作、搜索、整理 | ✅ 基础功能 |
| **直播数据分析** | ❌ | ✅ 直播监控、观众分析、转化率 |
| **商品管理** | ❌ | ✅ 商品信息、库存同步、价格策略 |
| **客服售后** | ❌ | ✅ 订单查询、退款处理、自动回复 |
| **竞品分析** | ❌ | ✅ 竞品对比、趋势追踪、定价建议 |
| **多用户支持** | ❌ 单用户 | ✅ 多用户隔离 |
| **权限管理** | ❌ 无 | ✅ RBAC控制 |
| **数据隔离** | ❌ 无 | ✅ 部门/团队隔离 |
| **企业报表** | ❌ 无 | ✅ 经营分析报表 |
| **API认证** | ✅ 基础认证 | ✅ JWT + API Token双认证 |
| **审计日志** | ❌ 无 | ✅ 全量安全事件记录 |
| **安全沙箱** | ✅ 基础隔离 | ✅ 完整沙箱+审批流程 |
| **危险操作审批** | ❌ 无 | ✅ 工作流审批机制 |
| **分布式锁** | ❌ 无 | ✅ Redis分布式锁 |
| **连接池** | ❌ 单连接 | ✅ Redis/PostgreSQL连接池 |
| **分布式限流** | ❌ 无 | ✅ 滑动窗口算法 |
| **异步任务队列** | ❌ 无 | ✅ 后台任务处理 |
| **会话存储** | ✅ 内存 | ✅ Redis分布式存储 |
| **Kubernetes部署** | ❌ 无 | ✅ Deployment + HPA |
| **自动扩缩容** | ❌ 无 | ✅ CPU/Memory/请求率触发 |
| **健康检查** | ✅ 基础 | ✅ Liveness/Readiness/Metrics |
| **监控告警** | ❌ 无 | ✅ Prometheus + Grafana |
| **负载均衡** | ❌ 无 | ✅ Ingress + Rate Limit |

### 个人版Skills详解

#### 1. file_manager - 文件管理

| 工具 | 功能 |
|------|------|
| `read_file` | 读取文件内容 |
| `write_file` | 写入文件内容 |
| `list_directory` | 列出目录内容 |
| `search_files` | 搜索文件 |

#### 2. code_helper - 代码辅助

| 工具 | 功能 |
|------|------|
| `analyze_code` | 分析代码结构 |
| `explain_code` | 解释代码逻辑 |
| `debug_code` | 调试代码错误 |
| `generate_code` | 生成代码片段 |
| `refactor_code` | 重构代码 |
| `search_api_docs` | 搜索API文档 |

#### 3. daily_planner - 日程管理

| 工具 | 功能 |
|------|------|
| `create_event` | 创建日程事件 |
| `list_events` | 查询日程列表 |
| `create_reminder` | 创建提醒 |
| `list_tasks` | 查询待办事项 |

#### 4. study_assistant - 学习助手

| 工具 | 功能 |
|------|------|
| `create_note` | 创建学习笔记 |
| `organize_notes` | 整理笔记 |
| `create_study_plan` | 创建学习计划 |
| `track_progress` | 跟踪学习进度 |

#### 5. collaboration - 协作助手

| 工具 | 功能 |
|------|------|
| `create_document` | 创建协作文档 |
| `assign_task` | 分配任务 |
| `schedule_meeting` | 安排会议 |
| `list_tasks` | 查询任务 |
| `update_task_status` | 更新任务状态 |

### 企业版Skills详解

#### 1. live_analytics - 直播数据分析

| 工具 | 功能 | 适用场景 |
|------|------|----------|
| `get_live_metrics` | 获取实时数据 | 监控直播间状态 |
| `analyze_audience` | 观众画像分析 | 了解观众群体 |
| `calculate_conversion` | 转化率计算 | 评估直播效果 |
| `generate_report` | 生成分析报告 | 汇总直播数据 |

#### 2. product_manager - 商品管理

| 工具 | 功能 | 适用场景 |
|------|------|----------|
| `get_product_info` | 查询商品信息 | 商品详情查询 |
| `update_product` | 更新商品信息 | 商品信息维护 |
| `sync_inventory` | 同步库存 | 多平台库存同步 |
| `adjust_price` | 调整价格 | 价格策略执行 |

#### 3. customer_service - 客服售后

| 工具 | 功能 | 适用场景 |
|------|------|----------|
| `query_order` | 查询订单 | 订单状态查询 |
| `handle_refund` | 处理退款 | 退款申请处理 |
| `auto_reply` | 自动回复 | 客户咨询回复 |

#### 4. market_analysis - 竞品分析

| 工具 | 功能 | 适用场景 |
|------|------|----------|
| `analyze_competitors` | 竞品分析 | 竞品对比研究 |
| `track_market_trend` | 趋势追踪 | 市场趋势分析 |
| `suggest_pricing` | 定价建议 | 价格策略建议 |

### 企业权限管理

#### 用户角色

| 角色 | 权限范围 |
|------|----------|
| **Admin** | 全部权限，用户管理、设置管理 |
| **Manager** | 产品管理、订单管理、报表管理、数据分析 |
| **Operator** | 订单处理、客服处理、内容创建 |
| **Viewer** | 数据查看、报表查看 |

#### 权限类型

```python
# Admin权限
MANAGE_USERS       # 管理用户
MANAGE_SETTINGS    # 管理设置
MANAGE_SKILLS      # 管理Skills

# Manager权限
MANAGE_PRODUCTS    # 管理商品
MANAGE_ORDERS      # 管理订单
MANAGE_REPORTS     # 管理报表
VIEW_ANALYTICS     # 查看分析

# Operator权限
PROCESS_ORDERS     # 处理订单
HANDLE_CUSTOMER    # 处理客服
CREATE_CONTENT     # 创建内容

# Viewer权限
VIEW_DATA          # 查看数据
VIEW_REPORTS       # 查看报表
```

---

## 快速开始

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-org/ai-agent.git
cd ai-agent

# 安装Python依赖
pip install -e ".[dev]"
```

### 配置环境

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
# 填入API密钥等配置
```

### 本地启动

```bash
# 方式1: CLI启动
ai-agent start

# 方式2: 直接运行
python -m gateway.server

# 方式3: 初始化workspace
ai-agent init
```

### Docker部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 配置说明

### 主配置文件 (`config/settings.yaml`)

```yaml
# 部署模式
deploy_mode: local          # local 或 cloud

# 版本选择
version: personal           # personal 或 enterprise

# 模型配置
model:
  primary: deepseek         # 主模型
  fallback:                 # 备选模型列表
    - zhipu
    - qwen
    - baidu

# 记忆配置
memory:
  file_store:
    path: ~/.ai-agent/workspace
  database:
    type: postgres
    host: localhost
    port: 5432

# Skill配置
skills:
  builtin_path: ./skills/builtin
  extensions_path: ./skills/extensions
  default_skills:
    - file_manager
    - code_helper

# Gateway配置
gateway:
  channels:
    - web
    - wechat
    - dingtalk
  web:
    port: 8080
    websocket_enabled: true

# 心跳配置
heartbeat:
  enabled: true
  interval: 300
```

### 环境变量 (`.env`)

```bash
# 模型API密钥
DEPLOY_MODE=local
MODEL_PROVIDER=deepseek
MODEL_API_KEY=your-api-key

# 备选模型密钥
ZHIPU_API_KEY=
QWEN_API_KEY=
OPENAI_API_KEY=

# 数据库配置
DATABASE_URL=postgresql://user:pass@localhost:5432/aiagent
REDIS_URL=redis://localhost:6379/0

# 微信配置 (企业版)
WECHAT_CORP_ID=
WECHAT_AGENT_ID=
WECHAT_SECRET=

# 钉钉配置 (企业版)
DINGTALK_APP_KEY=
DINGTALK_APP_SECRET=
```

---

## API文档

### REST API

#### 健康检查

```http
GET /health

Response:
{
  "status": "healthy",
  "details": {
    "model_router": {...},
    "active_sessions": 5
  }
}
```

#### 聊天接口

```http
POST /api/chat
Content-Type: application/json

Request:
{
  "message": "你好，请帮我分析这段代码",
  "user_id": "user-123",
  "session_id": "session-abc"
}

Response:
{
  "content": "回复内容...",
  "session_id": "session-abc",
  "user_id": "user-123",
  "model_used": "deepseek",
  "timestamp": "2026-04-17T10:00:00"
}
```

#### Skill列表

```http
GET /api/skills?category=personal

Response:
{
  "skills": [
    {
      "name": "file_manager",
      "version": "1.0.0",
      "category": "system",
      "description": "文件管理",
      "enabled": true
    }
  ]
}
```

### WebSocket API

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8080/ws/chat');

// 发送消息
ws.send(JSON.stringify({
  message: "你好",
  user_id: "user-123"
}));

// 接收流式响应
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'chunk') {
    // 流式内容块
    console.log(data.content);
  }
  
  if (data.type === 'complete') {
    // 响应完成
    console.log('Session:', data.session_id);
  }
};
```

---

## 开发指南

### 创建自定义Skill

1. 创建Skill目录：

```bash
mkdir -p skills/extensions/my_skill
```

2. 编写SKILL.md：

```yaml
---
name: my_skill
version: 1.0.0
category: custom
description: 我的自定义技能
author: user
---

## 功能描述
自定义功能说明
```

3. 编写tools.py：

```python
TOOL_DEFINITIONS = [
    {
        "name": "my_tool",
        "description": "我的工具",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        },
        "handler": "my_skill.handlers.handle_my_tool"
    }
]
```

4. 编写handlers.py：

```python
async def handle_my_tool(params, context):
    input = params.get("input")
    
    return {
        "success": True,
        "result": f"处理: {input}"
    }
```

### 运行测试

```bash
# 单元测试
pytest tests/unit/

# 集成测试
pytest tests/integration/

# 全部测试
pytest tests/ -v

# 测试覆盖率
pytest tests/ --cov=core --cov=skills
```

### 代码检查

```bash
# Ruff检查
ruff check .

# 类型检查
mypy core/

# 格式化
black .
```

---

## 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| **语言** | Python 3.11+ | 主开发语言 |
| **Web框架** | FastAPI | 高性能异步API |
| **数据库** | PostgreSQL + pgvector | 向量检索支持 |
| **缓存** | Redis | 会话缓存 |
| **容器化** | Docker / Kubernetes | 部署方案 |
| **AI模型** | DeepSeek/GLM-4/Qwen | 国产模型优先 |
| **日志** | structlog | 结构化日志 |
| **配置** | Pydantic-settings | 类型安全配置 |
| **认证** | JWT + API Token | 双令牌认证机制 |
| **安全** | RBAC + 沙箱隔离 | 权限控制+代码隔离 |
| **并发** | aioredis + asyncpg | 异步连接池 |
| **分布式** | Redis Lock + RateLimit | 分布式锁+限流 |
| **任务队列** | AsyncTaskQueue | 后台任务处理 |
| **容器编排** | Kubernetes | 集群部署、自动扩缩容 |
| **监控** | Prometheus + Grafana | 指标采集、可视化告警 |
| **负载均衡** | NGINX Ingress | 外部访问、SSL、限流 |

---

## 许可证

MIT License

---

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing`)
5. 创建Pull Request

---

## 更新日志

### v0.1.0 (2026-04-17)

- ✅ MVP核心框架完成
- ✅ 13个内置Skills
- ✅ 三层进化机制
- ✅ 四层记忆系统
- ✅ 多渠道Gateway
- ✅ 企业权限管理
- ✅ 多Agent协作
- ✅ HEARTBEAT机制
- ✅ **安全机制实现**
  - API认证层（JWT + API Token）
  - 工具权限执行（SecureToolExecutor）
  - 数据隔离（多层级Scope控制）
  - 审计日志（全量安全事件记录）
  - 安全沙箱（Level 3自主进化隔离）
  - 危险操作审批（工作流审批机制）
- ✅ **并发基础设施实现**
  - Redis连接池（aioredis）
  - PostgreSQL连接池（asyncpg）
  - 分布式锁（Redis-based）
  - 分布式限流（滑动窗口算法）
  - 异步任务队列（后台处理）
  - 缓存管理（热点数据缓存）
  - 会话存储（Redis分布式）
  - 并发安全组件（Token/JWT/Isolation）
- ✅ **集群部署方案实现**
  - Kubernetes Deployment（3副本）
  - HPA自动扩缩容（CPU/内存/请求率触发）
  - Ingress配置（SSL + Rate Limit + WebSocket）
  - ServiceMonitor（Prometheus监控）
  - PrometheusRule（告警规则）
  - Grafana Dashboard（可视化面板）
  - 健康检查（Liveness/Readiness/Metrics端点）
  - Redis + PostgreSQL部署配置