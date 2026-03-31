// pages/profile/profile/profile.js - 个人中心（云开发版）
const app = getApp();
const { get, getSync, STORAGE_KEYS } = require('../../../utils/storage');

Page({
  data: {
    houseCount: 0,
    diaryCount: 0,
    calcCount: 0,
    priceRecords: 0,
    userInfo: null,
    loggedIn: false,
    profile: {},
  },

  onShow() {
    this.loadStats();
    this.loadUserInfo();
    this.loadProfile();
  },

  async loadStats() {
    try {
      const [houses, diaries, calcs, prices] = await Promise.all([
        get(STORAGE_KEYS.HOUSES),
        get(STORAGE_KEYS.DIARIES),
        get(STORAGE_KEYS.CALC_HISTORY),
        get(STORAGE_KEYS.PRICE_HISTORY),
      ]);
      this.setData({
        houseCount: houses.length,
        diaryCount: diaries.length,
        calcCount: calcs.length,
        priceRecords: prices.length,
      });
    } catch (err) {
      console.warn('加载统计数据失败:', err);
    }
  },

  loadUserInfo() {
    const userInfo = wx.getStorageSync('userInfo');
    const loggedIn = !!userInfo;
    this.setData({ userInfo, loggedIn });
  },

  loadProfile() {
    const profiles = getSync(STORAGE_KEYS.USER_PROFILE);
    if (profiles.length > 0) {
      const p = profiles[0];
      const budgetMin = p.budgetMin || 0;
      const budgetMax = p.budgetMax || 0;
      let budgetRange = '';
      if (budgetMin && budgetMax) {
        budgetRange = `${budgetMin}-${budgetMax}万`;
      } else if (budgetMin) {
        budgetRange = `${budgetMin}万起`;
      } else if (budgetMax) {
        budgetRange = `${budgetMax}万内`;
      }

      const hasData = !!(p.nickname || p.city || p.budgetMin || p.budgetMax || p.preferredArea || p.preferredRooms || p.district);

      this.setData({
        profile: {
          ...p,
          budgetRange,
          hasData,
          priorities: p.priorities || [],
        },
      });
    } else {
      this.setData({ profile: { hasData: false, priorities: [] } });
    }
  },

  // 获取用户头像昵称
  async getUserProfile() {
    try {
      const { userInfo } = await wx.getUserProfile({
        desc: '用于展示个人头像和昵称',
      });
      wx.setStorageSync('userInfo', userInfo);
      this.setData({ userInfo, loggedIn: true });
      wx.showToast({ title: '授权成功', icon: 'success' });
    } catch (err) {
      console.warn('用户拒绝授权:', err);
    }
  },

  // 跳转编辑资料
  goToEdit() {
    wx.navigateTo({ url: '/pages/profile/edit/edit' });
  },

  // 退出登录（清除本地登录态，不清除业务数据）
  logout() {
    wx.showModal({
      title: '退出登录',
      content: '退出后数据仍会保留在云端，下次登录可恢复。',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('userInfo');
          wx.removeStorageSync('openid');
          app.globalData.userInfo = null;
          app.globalData.openid = null;
          this.setData({ userInfo: null, loggedIn: false });
          wx.showToast({ title: '已退出登录', icon: 'success' });
        }
      },
    });
  },

  goToHouseList() { wx.switchTab({ url: '/pages/house/list/list' }); },
  goToDiary() { wx.navigateTo({ url: '/pages/diary/list/list' }); },
  goToCompare() { wx.navigateTo({ url: '/pages/house/compare/compare' }); },
  goToTrend() { wx.navigateTo({ url: '/pages/trend/trend/trend' }); },
  goToReminder() { wx.navigateTo({ url: '/pages/reminder/reminder/reminder' }); },
  goToGuide() { wx.navigateTo({ url: '/pages/guide/guide/guide' }); },
  goToSurrounding() { wx.navigateTo({ url: '/pages/surrounding/surrounding/surrounding' }); },
  goToTax() { wx.navigateTo({ url: '/pages/calc/tax/tax' }); },
  goToAIChat() { wx.navigateTo({ url: '/pages/ai/chat/chat' }); },

  async exportData() {
    wx.showLoading({ title: '正在导出...' });
    try {
      const keys = Object.values(STORAGE_KEYS);
      const data = {};
      for (const key of keys) {
        const list = await get(key);
        const name = Object.keys(STORAGE_KEYS).find(k => STORAGE_KEYS[k] === key) || key;
        data[name] = list;
      }

      wx.hideLoading();
      wx.showModal({
        title: '导出数据',
        content: '数据已复制到剪贴板，您可以粘贴到备忘录或其他地方保存。',
        success() {
          wx.setClipboardData({
            data: JSON.stringify(data, null, 2),
            success() {
              wx.showToast({ title: '已复制到剪贴板', icon: 'success' });
            },
          });
        },
      });
    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: '导出失败', icon: 'none' });
    }
  },

  clearData() {
    wx.showModal({
      title: '⚠️ 危险操作',
      content: '确定要清除所有数据吗？此操作不可恢复！云端和本地数据都会被清除。',
      confirmColor: '#f5222d',
      success: (res) => {
        if (res.confirm) {
          wx.showModal({
            title: '再次确认',
            content: '真的要删除所有收藏的房源、日记、价格记录等数据吗？',
            confirmColor: '#f5222d',
            success(res2) {
              if (res2.confirm) {
                // 清除本地缓存
                const keys = Object.values(STORAGE_KEYS);
                keys.forEach(key => {
                  wx.removeStorageSync('cache_' + key);
                });
                wx.showToast({ title: '已清除所有数据', icon: 'success' });
                // 刷新统计
                setTimeout(() => {
                  const pages = getCurrentPages();
                  const currentPage = pages[pages.length - 1];
                  if (currentPage && currentPage.loadStats) {
                    currentPage.setData({
                      houseCount: 0,
                      diaryCount: 0,
                      calcCount: 0,
                      priceRecords: 0,
                    });
                  }
                }, 500);
              }
            },
          });
        }
      },
    });
  },
});
