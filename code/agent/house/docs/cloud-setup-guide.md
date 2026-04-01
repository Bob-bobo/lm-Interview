# ☁️ 买房助手 - 云数据库配置文档

> 本文档指导你完成云开发环境的开通、数据库集合创建和安全规则配置。

---

## 一、开通云开发环境

1. 打开**微信开发者工具**，加载本项目
2. 点击工具栏 **「云开发」** 按钮（或在菜单栏选择：工具 → 云开发控制台）
3. 首次使用需同意协议并创建云开发环境
4. **环境名称**建议：`house-dev`（开发）/ `house-prod`（生产）
5. 选择**免费基础版**即可满足初期使用

## 二、创建数据库集合

在云开发控制台 → **数据库** 中，依次创建以下 **9 个集合**：

| 序号 | 集合名 | 说明 | 数据量预估 |
|:----:|--------|------|:---------:|
| 1 | `users` | 用户信息（登录云函数自动管理） | 少量 |
| 2 | `houses` | 房源列表 | 中等 |
| 3 | `diaries` | 看房日记（含云存储照片） | 中等 |
| 4 | `price_history` | 房源价格历史记录 | 较多 |
| 5 | `user_profile` | 用户购房需求画像 | 少量 |
| 6 | `reminders` | 提醒事项 | 少量 |
| 7 | `ai_history` | AI 对话历史记录 | 较多 |
| 8 | `calc_history` | 计算历史记录 | 中等 |
| 9 | `compare_list` | 房源对比记录 | 少量 |

### 操作步骤

点击数据库页面左上角 **「+」** 按钮，输入集合名称，点击确定。

---

## 三、各集合字段详细说明

### 1. `users` — 用户信息

> 由 `login` 云函数自动创建和管理，无需手动操作。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `_openid` | string | 用户唯一标识（云开发自动注入） |
| `nickName` | string | 用户昵称 |
| `avatarUrl` | string | 用户头像 URL |
| `lastLoginTime` | Date | 最后登录时间 |
| `createTime` | Date | 注册时间 |
| `updateTime` | Date | 更新时间 |

---

### 2. `houses` — 房源列表

> 用户手动添加的房源记录，含周边配套评分。

| 字段名 | 类型 | 必填 | 说明 |
|--------|:----:|:----:|------|
| `community` | string | ✅ | 小区名称 |
| `district` | string | ✅ | 区域（东城区/朝阳区/…） |
| `address` | string | | 详细地址 |
| `buildingNo` | string | | 楼栋号 |
| `source` | string | | 来源（链家/贝壳/…） |
| `rooms` | number | | 室数（0-6） |
| `halls` | number | | 厅数（0-6） |
| `orientation` | string | | 朝向（南/南北通透/…） |
| `area` | number | ✅ | 面积（㎡） |
| `floor` | number | | 楼层 |
| `totalFloor` | number | | 总楼层 |
| `decoration` | string | | 装修（毛坯/简装/精装/豪装） |
| `buildingType` | string | | 建筑类型（板楼/塔楼/…） |
| `buildYear` | string | | 建造年代 |
| `totalPrice` | number | ✅ | 总价（万元） |
| `askPrice` | number | | 挂牌价（万元） |
| `expectedPrice` | number | | 期望价（万元） |
| `remark` | string | | 备注 |
| `images` | array | | 房源图片（本地临时路径） |
| `transportScore` | number | | 交通便利评分（0-5） |
| `educationScore` | number | | 教育配套评分（0-5） |
| `medicalScore` | number | | 医疗配套评分（0-5） |
| `shoppingScore` | number | | 商业配套评分（0-5） |
| `environmentScore` | number | | 居住环境评分（0-5） |
| `facilityData` | object | | 周边设施清单（JSON） |
| `surroundingNotes` | string | | 周边配套备注 |

---

### 3. `diaries` — 看房日记

> 记录每次看房的感受、评分和照片。

| 字段名 | 类型 | 必填 | 说明 |
|--------|:----:|:----:|------|
| `houseId` | string | | 关联房源 ID |
| `houseName` | string | | 关联房源名称（冗余存储） |
| `visitDate` | string | | 看房日期（YYYY-MM-DD） |
| `rating` | number | | 整体评分（1-5 星） |
| `content` | string | ✅ | 看房感受文字 |
| `images` | array | | 照片列表（云存储 fileID） |
| `tags` | array | | 快速标签（如「采光好」「户型佳」） |

---

### 4. `price_history` — 价格历史

> 追踪房源价格变化，用于趋势分析。

| 字段名 | 类型 | 必填 | 说明 |
|--------|:----:|:----:|------|
| `houseId` | string | ✅ | 关联房源 ID |
| `price` | number | ✅ | 价格（万元） |
| `date` | number | ✅ | 记录时间（时间戳） |
| `note` | string | | 备注 |

---

### 5. `user_profile` — 用户需求画像

> AI 分析时自动提取和保存的购房需求。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `budgetMin` | number | 最低预算（万元） |
| `budgetMax` | number | 最高预算（万元） |
| `preferredArea` | number | 偏好面积（㎡） |
| `preferredRooms` | number | 偏好户型（室数） |
| `preferredDistricts` | array | 偏好区域列表 |
| `priorities` | array | 优先级列表（学区/交通/…） |
| `lastInput` | string | 最后一次输入的需求描述 |

---

### 6. `reminders` — 提醒事项

> 购房相关的时间提醒（还款日、合同到期等）。

| 字段名 | 类型 | 必填 | 说明 |
|--------|:----:|:----:|------|
| `title` | string | ✅ | 提醒标题（如「贷款还款日」） |
| `remindDate` | number | ✅ | 提醒日期（时间戳） |
| `remindTime` | string | | 提醒时间（HH:mm） |
| `note` | string | | 备注 |
| `done` | boolean | | 是否已完成 |

---

### 7. `ai_history` — AI 对话历史

> AI 聊天记录，用于上下文和回溯。

| 字段名 | 类型 | 必填 | 说明 |
|--------|:----:|:----:|------|
| `role` | string | ✅ | 角色（bot） |
| `content` | string | ✅ | 回复内容 |
| `question` | string | | 用户问题 |

---

### 8. `calc_history` — 计算历史

> 房贷/税费计算记录（预留）。

> ⚠️ 该集合当前代码中仅定义了映射，暂无写入逻辑。可先行创建备用。

---

### 9. `compare_list` — 房源对比

> 对比记录（预留）。

> ⚠️ 该集合当前代码中仅定义了映射，暂无写入逻辑。可先行创建备用。

---

## 四、配置安全规则

在数据库控制台，点击每个集合右侧 **「权限设置」**，选择 **「自定义安全规则」**，粘贴以下 JSON：

### 推荐规则：仅创建者可读写

```json
{
  "read": "doc._openid == auth.openid",
  "write": "doc._openid == auth.openid"
}
```

### 逐集合配置

| 集合 | 推荐规则 | 说明 |
|------|----------|------|
| `users` | 仅创建者可读写 | 用户只能看/改自己的信息 |
| `houses` | 仅创建者可读写 | 每个用户的房源数据隔离 |
| `diaries` | 仅创建者可读写 | 日记数据隔离 |
| `price_history` | 仅创建者可读写 | 价格记录隔离 |
| `user_profile` | 仅创建者可读写 | 需求画像隔离 |
| `reminders` | 仅创建者可读写 | 提醒数据隔离 |
| `ai_history` | 仅创建者可读写 | 对话记录隔离 |
| `calc_history` | 仅创建者可读写 | 计算记录隔离 |
| `compare_list` | 仅创建者可读写 | 对比记录隔离 |

> **提示**：`_openid` 是云开发自动注入的字段，小程序端所有写操作会自动附加当前用户的 `_openid`，无需代码手动设置。

---

## 五、部署登录云函数

1. 在微信开发者工具左侧找到 `cloudfunctions/login` 目录
2. **右键** → **「上传并部署：云端安装依赖」**
3. 等待部署完成（约 10-30 秒）
4. 部署成功后，该云函数会在小程序启动时自动调用完成静默登录

---

## 六、验证配置

完成以上步骤后，按以下流程验证：

1. ✅ **编译并预览**小程序
2. ✅ 打开**调试器 Console**，确认无红色报错
3. ✅ 在个人中心查看统计数据是否正常加载
4. ✅ 添加一条房源 → 检查云开发控制台 `houses` 集合是否有新记录
5. ✅ 添加一条看房日记（带照片）→ 检查云存储 `diary/` 文件夹是否有文件

---

## 七、常见问题

### Q: 数据库操作报错 "collection not exists"
**A**: 集合名称拼写必须与本文档完全一致，区分大小写。检查云开发控制台中集合名是否正确。

### Q: 报错 "permission denied"
**A**: 安全规则未配置或配置错误。请确保设置了自定义规则 `doc._openid == auth.openid`。

### Q: 云函数部署失败
**A**: 确保已在云开发控制台创建了环境，且 `cloudbaserc.json` 中环境 ID 与实际环境一致。

### Q: 照片上传失败
**A**: 检查云存储权限。在云开发控制台 → 存储 → 权限设置，选择「所有用户可读，仅创建者可写」。

### Q: 数据显示为空
**A**: 可能是首次加载时本地缓存为空，云端数据还在加载中。下拉刷新页面即可。如果持续为空，检查网络和云开发环境状态。
