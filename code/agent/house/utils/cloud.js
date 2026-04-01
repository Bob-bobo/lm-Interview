/**
 * utils/cloud.js - 云数据库统一访问层
 * 提供与 storage.js 兼容的 API，底层使用云数据库
 * 
 * 云数据库集合设计：
 *   - users         用户信息（login 云函数管理）
 *   - houses        房源列表
 *   - diaries       看房日记
 *   - price_history 价格历史
 *   - reminders     提醒事项
 *   - ai_history    AI对话历史
 *   - calc_history  计算历史
 */

const COLLECTIONS = {
  HOUSES: 'houses',
  DIARIES: 'diaries',
  PRICE_HISTORY: 'price_history',
  USER_PROFILE: 'user_profile',
  REMINDERS: 'reminders',
  AI_HISTORY: 'ai_history',
  CALC_HISTORY: 'calc_history',
  COMPARE_LIST: 'compare_list',
};

// 保持与 STORAGE_KEYS 兼容，方便页面层迁移
const STORAGE_KEYS = COLLECTIONS;

/**
 * 云数据库操作封装
 * 所有操作自动附加 _openid 过滤（小程序端安全规则限制）
 */
class CloudDB {
  constructor() {
    this._db = null;
    this._ready = false;
    this._pendingQueue = []; // 云开发初始化前的操作队列
  }

  /**
   * 初始化云数据库引用（在 app.js onLaunch 中调用）
   */
  init() {
    if (this._db) return;
    this._db = wx.cloud.database();
    this._ready = true;
    // 执行队列中的待处理操作
    this._flushQueue();
  }

  _getDb() {
    if (!this._db) {
      console.warn('[CloudDB] 未初始化，操作已入队');
      return null;
    }
    return this._db;
  }

  _flushQueue() {
    const queue = [...this._pendingQueue];
    this._pendingQueue = [];
    queue.forEach(fn => fn());
  }

  /**
   * 生成唯一ID（云端用 ObjectId，本地用时间戳+随机数）
   */
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
  }

  // ========== CRUD 操作 ==========

  /**
   * 查询列表（兼容 storage.get）
   * @param {string} collection 集合名
   * @param {object} options 查询选项 { where, orderBy, limit, skip, field }
   * @returns {Promise<Array>}
   */
  async get(collection, options = {}) {
    const db = this._getDb();
    if (!db) return [];

    try {
      let query = db.collection(collection);

      if (options.where) {
        query = query.where(options.where);
      }

      // 默认按创建时间倒序
      const orderField = options.orderBy || 'createTime';
      const orderDir = options.orderDir || 'desc';
      query = query.orderBy(orderField, orderDir);

      const limit = options.limit || 100;
      const skip = options.skip || 0;
      query = query.skip(skip).limit(limit);

      if (options.field) {
        query = query.field(options.field);
      }

      const { data } = await query.get();
      return data;
    } catch (err) {
      console.error(`[CloudDB] 查询失败 [${collection}]:`, err);
      return [];
    }
  }

  /**
   * 获取单条记录（兼容 storage.getById）
   */
  async getById(collection, id) {
    const db = this._getDb();
    if (!db) return null;

    try {
      const { data } = await db.collection(collection).doc(id).get();
      return data;
    } catch (err) {
      // 可能是没权限或者不存在
      console.error(`[CloudDB] 获取单条失败 [${collection}/${id}]:`, err);
      return null;
    }
  }

  /**
   * 新增记录（兼容 storage.add）
   */
  async add(collection, item) {
    const db = this._getDb();
    if (!db) return null;

    try {
      const now = new Date();
      const record = {
        ...item,
        createTime: now,
        updateTime: now,
      };

      const { _id } = await db.collection(collection).add({ data: record });
      return { id: _id, ...record };
    } catch (err) {
      console.error(`[CloudDB] 新增失败 [${collection}]:`, err);
      return null;
    }
  }

  /**
   * 更新记录（兼容 storage.update）
   */
  async update(collection, id, updates) {
    const db = this._getDb();
    if (!db) return false;

    try {
      const data = {
        ...updates,
        updateTime: new Date(),
      };
      await db.collection(collection).doc(id).update({ data });
      return true;
    } catch (err) {
      console.error(`[CloudDB] 更新失败 [${collection}/${id}]:`, err);
      return false;
    }
  }

  /**
   * 删除记录（兼容 storage.remove）
   */
  async remove(collection, id) {
    const db = this._getDb();
    if (!db) return false;

    try {
      await db.collection(collection).doc(id).remove();
      return true;
    } catch (err) {
      console.error(`[CloudDB] 删除失败 [${collection}/${id}]:`, err);
      return false;
    }
  }

  /**
   * 统计数量
   */
  async count(collection, where) {
    const db = this._getDb();
    if (!db) return 0;

    try {
      let query = db.collection(collection);
      if (where) query = query.where(where);
      const { total } = await query.count();
      return total;
    } catch (err) {
      console.error(`[CloudDB] 统计失败 [${collection}]:`, err);
      return 0;
    }
  }

  /**
   * 批量新增
   */
  async batchAdd(collection, items) {
    const db = this._getDb();
    if (!db) return [];

    try {
      const now = new Date();
      const records = items.map(item => ({
        ...item,
        createTime: now,
        updateTime: now,
      }));

      // 云数据库批量操作每次最多 20 条
      const results = [];
      for (let i = 0; i < records.length; i += 20) {
        const batch = records.slice(i, i + 20);
        const res = await db.collection(collection).add({ data: batch });
        results.push(...(res.ids || []));
      }
      return results;
    } catch (err) {
      console.error(`[CloudDB] 批量新增失败 [${collection}]:`, err);
      return [];
    }
  }

  /**
   * 清空集合中当前用户的所有数据
   */
  async clearCollection(collection) {
    const db = this._getDb();
    if (!db) return false;

    try {
      // 分批删除（每次100条）
      let hasMore = true;
      while (hasMore) {
        const { data } = await db.collection(collection)
          .limit(100)
          .orderBy('createTime', 'asc')
          .get();

        if (data.length === 0) {
          hasMore = false;
          break;
        }

        const deletePromises = data.map(item =>
          db.collection(collection).doc(item._id).remove()
        );
        await Promise.all(deletePromises);
      }
      return true;
    } catch (err) {
      console.error(`[CloudDB] 清空失败 [${collection}]:`, err);
      return false;
    }
  }
}

// ========== 云存储操作 ==========

/**
 * 上传文件到云存储
 * @param {string} filePath 本地临时文件路径
 * @param {string} cloudPath 云存储路径，如 'diary/xxx.jpg'
 * @returns {Promise<string>} 文件ID
 */
async function uploadFile(filePath, cloudPath) {
  try {
    const { fileID } = await wx.cloud.uploadFile({
      cloudPath,
      filePath,
    });
    return fileID;
  } catch (err) {
    console.error('[CloudStorage] 上传失败:', err);
    return '';
  }
}

/**
 * 批量上传文件
 */
async function batchUploadFiles(filePaths, folder) {
  const results = [];
  for (let i = 0; i < filePaths.length; i++) {
    const ext = filePaths[i].split('.').pop() || 'jpg';
    const cloudPath = `${folder}/${Date.now()}_${i}.${ext}`;
    const fileID = await uploadFile(filePaths[i], cloudPath);
    results.push(fileID || filePaths[i]); // 上传失败则保留本地路径
  }
  return results;
}

/**
 * 删除云存储文件
 */
async function deleteFile(fileID) {
  try {
    await wx.cloud.deleteFile({ fileList: [fileID] });
    return true;
  } catch (err) {
    console.error('[CloudStorage] 删除失败:', err);
    return false;
  }
}

/**
 * 获取云文件临时链接（用于图片预览）
 */
async function getTempFileURL(fileIDs) {
  try {
    const { fileList } = await wx.cloud.getTempFileURL({ fileList: fileIDs });
    return fileList.map(f => f.tempFileURL || f.fileID);
  } catch (err) {
    console.error('[CloudStorage] 获取临时链接失败:', err);
    return fileIDs;
  }
}

// 单例
const cloudDB = new CloudDB();

module.exports = {
  cloudDB,
  COLLECTIONS,
  STORAGE_KEYS,
  uploadFile,
  batchUploadFiles,
  deleteFile,
  getTempFileURL,
};
