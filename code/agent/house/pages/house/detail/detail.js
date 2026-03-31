// pages/house/detail/detail.js - 房源详情（云开发版）
const { getById, remove, STORAGE_KEYS, add, get, update } = require('../../../utils/storage');
const { formatUnitPrice, formatDate, formatDateTime } = require('../../../utils/format');
const { analyzePriceTrend } = require('../../../utils/ai');

Page({
  data: {
    house: null, houseId: '', unitPrice: '', priceDiff: 0,
    hasScores: false, avgScore: '0.0', priceHistory: [],
    trendData: null, createTimeStr: '', updateTimeStr: '',
  },

  onLoad(options) {
    const { id } = options;
    if (!id) { wx.showToast({ title: '参数错误', icon: 'none' }); return; }
    this.setData({ houseId: id });
    this.loadHouse(id);
    this.loadPriceHistory(id);
  },

  async loadHouse(id) {
    const house = await getById(STORAGE_KEYS.HOUSES, id);
    if (!house) { wx.showToast({ title: '房源不存在', icon: 'none' }); return; }

    const unitPrice = formatUnitPrice(house.totalPrice, house.area);
    const priceDiff = (house.askPrice && house.expectedPrice) ? (house.askPrice - house.expectedPrice) : 0;
    const scores = ['transportScore', 'educationScore', 'medicalScore', 'shoppingScore', 'environmentScore'];
    const hasScores = scores.some(k => house[k] > 0);
    const scoreSum = scores.reduce((sum, k) => sum + (house[k] || 0), 0);
    const avgScore = hasScores ? (scoreSum / scores.filter(k => house[k] > 0).length).toFixed(1) : '0.0';

    this.setData({
      house, unitPrice, priceDiff, hasScores, avgScore,
      createTimeStr: formatDateTime(house.createTime),
      updateTimeStr: house.updateTime !== house.createTime ? formatDateTime(house.updateTime) : '',
    });
  },

  async loadPriceHistory(houseId) {
    const allHistory = await get(STORAGE_KEYS.PRICE_HISTORY);
    const history = allHistory.filter(h => h.houseId === houseId).sort((a, b) => a.date - b.date);

    if (history.length === 0) {
      this.setData({ priceHistory: [] });
      return;
    }

    const prices = history.map(h => h.price);
    const maxPrice = Math.max(...prices);
    const minPrice = Math.min(...prices);

    const chartData = history.map(item => {
      const date = new Date(item.date);
      const height = maxPrice === minPrice ? 80 : ((item.price - minPrice) / (maxPrice - minPrice)) * 60 + 20;
      let color = '#1890ff';
      if (history.length > 1 && item.price > prices[0].price) color = '#f5222d';
      if (history.length > 1 && item.price < prices[0].price) color = '#52c41a';
      return { ...item, barHeight: height, color, dateLabel: `${date.getMonth() + 1}/${date.getDate()}` };
    });

    const trendData = analyzePriceTrend(houseId);

    this.setData({
      priceHistory: chartData,
      trendData: trendData.trend !== 'insufficient' ? trendData : null,
    });
  },

  addPriceRecord() {
    const that = this;
    wx.showModal({
      title: '记录价格',
      editable: true,
      placeholderText: `当前价格：${this.data.house.totalPrice}万，输入最新价格(万元)`,
      async success(res) {
        if (res.confirm && res.content) {
          const price = parseFloat(res.content);
          if (isNaN(price) || price <= 0) return wx.showToast({ title: '请输入有效价格', icon: 'none' });

          await add(STORAGE_KEYS.PRICE_HISTORY, {
            houseId: that.data.houseId,
            price,
            date: Date.now(),
            note: `从${that.data.house.totalPrice}万更新`,
          });

          await update(STORAGE_KEYS.HOUSES, that.data.houseId, { totalPrice: price });

          wx.showToast({ title: '价格已更新', icon: 'success' });
          that.loadHouse(that.data.houseId);
          that.loadPriceHistory(that.data.houseId);
        }
      },
    });
  },

  previewImage(e) {
    const { index } = e.currentTarget.dataset;
    wx.previewImage({ current: this.data.house.images[index], urls: this.data.house.images });
  },

  goToEdit() { wx.navigateTo({ url: `/pages/house/edit/edit?id=${this.data.houseId}` }); },

  goToMortgage() {
    const { totalPrice, area } = this.data.house;
    wx.navigateTo({ url: `/pages/calc/mortgage/mortgage?price=${totalPrice || ''}&area=${area || ''}` });
  },

  goToDiary() {
    wx.navigateTo({ url: `/pages/diary/add/add?houseId=${this.data.houseId}&houseName=${this.data.house.community || ''}` });
  },

  deleteHouse() {
    const that = this;
    wx.showModal({
      title: '确认删除',
      content: '删除后无法恢复，确定要删除这个房源吗？',
      confirmColor: '#f5222d',
      async success(res) {
        if (res.confirm) {
          await remove(STORAGE_KEYS.HOUSES, that.data.houseId);
          wx.showToast({ title: '已删除', icon: 'success' });
          setTimeout(() => wx.navigateBack(), 1000);
        }
      },
    });
  },

  onShareAppMessage() {
    const { house } = this.data;
    return { title: `${house.community || '房源'} - ${house.totalPrice}万 ${house.area}㎡`, path: `/pages/house/detail/detail?id=${house.id}` };
  },
});
