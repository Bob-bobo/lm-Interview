/**
 * utils/storage.js - 数据访问层（云开发版）
 * 
 * 兼容原有 API（get/set/add/update/remove/getById），
 * 底层自动使用云数据库，同时维护本地缓存用于离线降级。
 * 
 * 页面层代码无需修改即可完成云开发迁移。
 */

const { cloudDB, STORAGE_KEYS, COLLECTIONS } = require('./cloud');

/**
 * 云集合名映射（storage key -> 云数据库集合名）
 */
const KEY_TO_COLLECTION = {
  [STORAGE_KEYS.HOUSES]: COLLECTIONS.HOUSES,
  [STORAGE_KEYS.DIARIES]: COLLECTIONS.DIARIES,
  [STORAGE_KEYS.PRICE_HISTORY]: COLLECTIONS.PRICE_HISTORY,
  [STORAGE_KEYS.USER_PROFILE]: COLLECTIONS.USER_PROFILE,
  [STORAGE_KEYS.REMINDERS]: COLLECTIONS.REMINDERS,
  [STORAGE_KEYS.AI_HISTORY]: COLLECTIONS.AI_HISTORY,
  [STORAGE_KEYS.CALC_HISTORY]: COLLECTIONS.CALC_HISTORY,
  [STORAGE_KEYS.COMPARE_LIST]: COLLECTIONS.COMPARE_LIST,
};

/**
 * 本地缓存 key 前缀
 */
const CACHE_PREFIX = 'cache_';

/**
 * 获取本地缓存
 */
function getLocalCache(key) {
  try {
    const data = wx.getStorageSync(CACHE_PREFIX + key);
    return data || [];
  } catch (e) {
    return [];
  }
}

/**
 * 设置本地缓存
 */
function setLocalCache(key, data) {
  try {
    wx.setStorageSync(CACHE_PREFIX + key, data);
  } catch (e) {
    console.warn('本地缓存写入失败:', e);
  }
}

/**
 * 生成唯一ID
 */
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
}

// ========== 对外兼容 API（全部改为异步，但保持命名一致）==========

/**
 * 获取列表数据
 * 优先读本地缓存（即时返回），后台静默从云端同步
 * @param {string} key STORAGE_KEYS 中的 key
 * @param {object} options 云查询选项 { where, orderBy, limit, skip }
 * @returns {Promise<Array>}
 */
async function get(key, options = {}) {
  const collection = KEY_TO_COLLECTION[key];
  if (!collection) {
    console.warn(`[Storage] 未知 key: ${key}，使用本地存储`);
    return getLocalCache(key);
  }

  // 先返回本地缓存（保证页面快速渲染）
  const localData = getLocalCache(key);

  // 后台从云端拉取最新数据
  const cloudData = await cloudDB.get(collection, options);

  // 更新本地缓存
  setLocalCache(key, cloudData);

  return cloudData;
}

/**
 * 同步获取（仅读本地缓存，用于页面初始化快速展示）
 */
function getSync(key) {
  return getLocalCache(key);
}

/**
 * 设置数据（全量替换，一般不推荐使用）
 */
async function set(key, data) {
  const collection = KEY_TO_COLLECTION[key];
  if (!collection) {
    wx.setStorageSync(key, data);
    return true;
  }

  // 清空云端集合，然后批量写入
  await cloudDB.clearCollection(collection);
  if (data.length > 0) {
    await cloudDB.batchAdd(collection, data);
  }

  setLocalCache(key, data);
  return true;
}

/**
 * 新增一条记录
 */
async function add(key, item) {
  const collection = KEY_TO_COLLECTION[key];
  if (!collection) {
    // 降级到本地存储
    const list = getLocalCache(key);
    const record = { id: generateId(), ...item, createTime: Date.now(), updateTime: Date.now() };
    list.unshift(record);
    setLocalCache(key, list);
    return record;
  }

  const record = await cloudDB.add(collection, item);
  if (record) {
    // 更新本地缓存
    const list = getLocalCache(key);
    list.unshift(record);
    setLocalCache(key, list);
    return record;
  }
  return null;
}

/**
 * 更新一条记录
 */
async function update(key, id, updates) {
  const collection = KEY_TO_COLLECTION[key];
  if (!collection) {
    const list = getLocalCache(key);
    const index = list.findIndex(item => item.id === id);
    if (index === -1) return false;
    list[index] = { ...list[index], ...updates, updateTime: Date.now() };
    setLocalCache(key, list);
    return true;
  }

  // 云端更新（注意：云数据库用 _id，本地缓存可能用 id）
  const cloudId = id; // 保持一致：add 返回的 id 就是 _id
  const success = await cloudDB.update(collection, cloudId, updates);

  if (success) {
    // 更新本地缓存
    const list = getLocalCache(key);
    const index = list.findIndex(item => item.id === id || item._id === id);
    if (index !== -1) {
      list[index] = { ...list[index], ...updates, updateTime: Date.now() };
      setLocalCache(key, list);
    }
  }
  return success;
}

/**
 * 删除一条记录
 */
async function remove(key, id) {
  const collection = KEY_TO_COLLECTION[key];
  if (!collection) {
    const list = getLocalCache(key);
    const filtered = list.filter(item => item.id !== id);
    setLocalCache(key, filtered);
    return true;
  }

  const success = await cloudDB.remove(collection, id);
  if (success) {
    const list = getLocalCache(key);
    const filtered = list.filter(item => item.id !== id && item._id !== id);
    setLocalCache(key, filtered);
  }
  return success;
}

/**
 * 根据ID获取单条记录
 */
async function getById(key, id) {
  const collection = KEY_TO_COLLECTION[key];
  if (!collection) {
    const list = getLocalCache(key);
    return list.find(item => item.id === id) || null;
  }

  const record = await cloudDB.getById(collection, id);
  return record;
}

/**
 * 从云端强制刷新指定集合
 */
async function refresh(key, options = {}) {
  const collection = KEY_TO_COLLECTION[key];
  if (!collection) return [];
  const cloudData = await cloudDB.get(collection, options);
  setLocalCache(key, cloudData);
  return cloudData;
}

/**
 * 统计数量
 */
async function count(key, where) {
  const collection = KEY_TO_COLLECTION[key];
  if (!collection) return getLocalCache(key).length;
  return cloudDB.count(collection, where);
}

module.exports = {
  STORAGE_KEYS,
  COLLECTIONS,
  get,
  getSync,
  set,
  add,
  update,
  remove,
  getById,
  generateId,
  refresh,
  count,
};
