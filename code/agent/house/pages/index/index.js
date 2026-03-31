// pages/index/index.js - 首页（云开发版）
const { get, STORAGE_KEYS } = require('../../utils/storage');
const { formatUnitPrice, formatDate } = require('../../utils/format');

Page({
  data: {
    greeting: '',
    dateStr: '',
    houseCount: 0,
    recentHouses: [],
    tips: [
      {
        title: '首套房认定',
        content: '认房不认贷政策已在全国推行，以家庭为单位，只要在当地名下无房，再购房均可按首套房执行。'
      },
      {
        title: '公积金贷款额度',
        content: '各地公积金贷款上限不同，一般为60-120万。部分城市支持公积金组合贷，可大幅降低利息支出。'
      },
      {
        title: '看房必查五证',
        content: '购房前务必查验：建设用地规划许可证、建设工程规划许可证、建筑工程施工许可证、国有土地使用证、商品房预售许可证。'
      },
    ],
  },

  onLoad() {
    this.updateGreeting();
    this.loadRecentHouses();
  },

  onShow() {
    this.loadRecentHouses();
  },

  onPullDownRefresh() {
    this.loadRecentHouses();
    wx.stopPullDownRefresh();
  },

  updateGreeting() {
    const now = new Date();
    const hour = now.getHours();
    let greeting = '你好 👋';
    if (hour < 6) greeting = '夜深了 🌙';
    else if (hour < 9) greeting = '早上好 ☀️';
    else if (hour < 12) greeting = '上午好 🌤️';
    else if (hour < 14) greeting = '中午好 🍽️';
    else if (hour < 18) greeting = '下午好 ☕';
    else greeting = '晚上好 🌆';

    const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const dateStr = `${now.getMonth() + 1}月${now.getDate()}日 ${weekDays[now.getDay()]}`;
    this.setData({ greeting, dateStr });
  },

  async loadRecentHouses() {
    const houses = await get(STORAGE_KEYS.HOUSES);
    const recent = houses.slice(0, 5).map(house => ({
      ...house,
      unitPrice: formatUnitPrice(house.totalPrice, house.area),
    }));
    this.setData({
      houseCount: houses.length,
      recentHouses: recent,
    });
  },

  goToAddHouse() { wx.navigateTo({ url: '/pages/house/add/add' }); },
  goToHouseList() { wx.switchTab({ url: '/pages/house/list/list' }); },
  goToHouseDetail(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/house/detail/detail?id=${id}` });
  },
  goToMortgage() { wx.switchTab({ url: '/pages/calc/mortgage/mortgage' }); },
  goToTax() { wx.navigateTo({ url: '/pages/calc/tax/tax' }); },
  goToTrend() { wx.navigateTo({ url: '/pages/trend/trend/trend' }); },
  goToAI() { wx.switchTab({ url: '/pages/ai/analyze/analyze' }); },
  goToCompare() { wx.navigateTo({ url: '/pages/house/compare/compare' }); },
  goToDiary() { wx.navigateTo({ url: '/pages/diary/list/list' }); },
  goToGuide() { wx.navigateTo({ url: '/pages/guide/guide/guide' }); },
  goToSurrounding() { wx.navigateTo({ url: '/pages/surrounding/surrounding/surrounding' }); },

  onShareAppMessage() {
    return { title: '买房助手 - 帮你选房、算价、避坑', path: '/pages/index/index' };
  },
});
