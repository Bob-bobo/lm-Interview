// app.js - 买房助手小程序入口（云开发版）
const { cloudDB } = require('./utils/cloud');

App({
  onLaunch(options) {
    // 初始化云开发
    if (!wx.cloud) {
      console.error('请使用 2.2.3 或以上的基础库以使用云能力');
      return;
    }
    wx.cloud.init({
      env: '', // TODO: 替换为你的云开发环境ID
      traceUser: true,
    });

    // 初始化云数据库
    cloudDB.init();

    // 静默登录
    this.silentLogin();

    // 检查更新
    this.checkUpdate();

    // 获取系统信息
    this.getSystemInfo();
  },

  onShow(options) {
    // 从后台恢复时刷新用户信息
    if (this.globalData.userId) {
      this.refreshUserInfo();
    }
  },

  onHide() {},

  globalData: {
    userInfo: null,      // 用户昵称/头像等
    userId: null,        // 云数据库用户ID
    openid: null,        // 用户openid
    systemInfo: null,
    isLoggedIn: false,   // 登录状态
  },

  /**
   * 静默登录 - 通过云函数获取 openid
   */
  async silentLogin() {
    try {
      const res = await wx.cloud.callFunction({ name: 'login' });
      const result = res.result;

      if (result.code === 0 && result.data) {
        const { userId, openid, nickName, avatarUrl, isNewUser } = result.data;

        this.globalData.userId = userId;
        this.globalData.openid = openid;
        this.globalData.userInfo = { nickName, avatarUrl };
        this.globalData.isLoggedIn = true;

        // 缓存登录状态
        wx.setStorageSync('loginInfo', {
          userId,
          openid,
          nickName,
          avatarUrl,
          loginTime: Date.now(),
        });

        // 通知所有页面登录完成
        this._loginCallbacks.forEach(cb => cb({ userId, openid, nickName, avatarUrl, isNewUser }));
        this._loginCallbacks = [];

        // 新用户引导
        if (isNewUser) {
          console.log('[App] 新用户注册成功');
        }
      }
    } catch (err) {
      console.error('[App] 静默登录失败:', err);
      // 降级：使用本地缓存
      const cached = wx.getStorageSync('loginInfo');
      if (cached) {
        this.globalData.userId = cached.userId;
        this.globalData.openid = cached.openid;
        this.globalData.userInfo = { nickName: cached.nickName, avatarUrl: cached.avatarUrl };
        this.globalData.isLoggedIn = true;
      }
    }
  },

  /**
   * 刷新用户信息（从数据库重新获取）
   */
  async refreshUserInfo() {
    // TODO: 可增加 getUserInfo 云函数
  },

  /**
   * 登录完成回调注册（页面在 onShow 中注册，登录完成后自动触发）
   */
  _loginCallbacks: [],

  onLoginReady(callback) {
    if (this.globalData.isLoggedIn) {
      callback(this.globalData.userInfo);
    } else {
      this._loginCallbacks.push(callback);
    }
  },

  /**
   * 检查小程序更新
   */
  checkUpdate() {
    if (wx.canIUse('getUpdateManager')) {
      const updateManager = wx.getUpdateManager();
      updateManager.onCheckForUpdate(res => {
        if (res.hasUpdate) {
          updateManager.onUpdateReady(() => {
            wx.showModal({
              title: '更新提示',
              content: '新版本已经准备好，是否重启应用？',
              success: res => {
                if (res.confirm) updateManager.applyUpdate();
              }
            });
          });
          updateManager.onUpdateFailed(() => {
            wx.showModal({
              title: '更新提示',
              content: '新版本下载失败，请检查网络后重试',
            });
          });
        }
      });
    }
  },

  /**
   * 获取系统信息
   */
  getSystemInfo() {
    try {
      const systemInfo = wx.getSystemInfoSync();
      this.globalData.systemInfo = systemInfo;
    } catch (e) {
      console.error('获取系统信息失败', e);
    }
  }
});
