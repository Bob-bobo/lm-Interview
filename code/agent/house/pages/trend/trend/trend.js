// pages/trend/trend/trend.js - 价格走势（云开发版）
const { get, add, update, STORAGE_KEYS } = require('../../../utils/storage');
const { analyzePriceTrend } = require('../../../utils/ai');
const { formatDate } = require('../../../utils/format');

Page({
  data: {
    houses: [], houseNames: [], houseIndex: -1, selectedHouse: null,
    priceRecords: [], trend: null, chartData: [], yLabels: [], avgLinePosition: 50,
  },

  onLoad() { this.loadHouses(); },

  async onShow() {
    await this.loadHouses();
    if (this.data.selectedHouse) this.loadPriceData(this.data.selectedHouse.id);
  },

  async loadHouses() {
    const houses = await get(STORAGE_KEYS.HOUSES);
    const houseNames = houses.map(h => `${h.community || '未命名'} (${h.totalPrice}万)`);
    this.setData({ houses, houseNames });
    if (this.data.selectedHouse) {
      const idx = houses.findIndex(h => h.id === this.data.selectedHouse.id);
      if (idx >= 0) this.setData({ houseIndex: idx });
    }
  },

  onHouseSelect(e) {
    const index = parseInt(e.detail.value);
    const house = this.data.houses[index];
    this.setData({ houseIndex: index, selectedHouse: house });
    this.loadPriceData(house.id);
  },

  async loadPriceData(houseId) {
    const allHistory = await get(STORAGE_KEYS.PRICE_HISTORY);
    const records = allHistory.filter(h => h.houseId === houseId).sort((a, b) => a.date - b.date);

    if (records.length === 0) {
      this.setData({ priceRecords: [], trend: null, chartData: [] });
      return;
    }

    const formatted = records.map((r, i) => {
      let change = 0;
      if (i > 0) change = parseFloat((r.price - records[i - 1].price).toFixed(1));
      return { ...r, price: r.price, dateStr: formatDate(r.date), change };
    });

    const trend = analyzePriceTrend(houseId);
    const prices = records.map(r => r.price);
    const maxPrice = Math.max(...prices);
    const minPrice = Math.min(...prices);
    const range = maxPrice - minPrice || 1;

    const chartData = records.map(item => {
      const height = ((item.price - minPrice) / range) * 70 + 15;
      let color = '#1890ff';
      if (records.length > 1) {
        if (item.price > records[0].price) color = '#f5222d';
        if (item.price < records[0].price) color = '#52c41a';
      }
      const date = new Date(item.date);
      return { price: item.price, height, color, dateLabel: `${date.getMonth() + 1}/${date.getDate()}` };
    });

    const yLabels = [maxPrice.toFixed(0), ((maxPrice + minPrice) / 2).toFixed(0), minPrice.toFixed(0)];
    const avgLinePosition = ((trend.avgPrice - minPrice) / range) * 70 + 15;

    this.setData({
      priceRecords: formatted,
      trend: trend.trend !== 'insufficient' ? trend : null,
      chartData, yLabels,
      avgLinePosition: Math.min(95, Math.max(5, avgLinePosition)),
    });
  },

  addRecord() {
    if (!this.data.selectedHouse) return wx.showToast({ title: '请先选择房源', icon: 'none' });

    const currentPrice = this.data.selectedHouse.totalPrice;
    const that = this;

    wx.showModal({
      title: '记录价格',
      editable: true,
      placeholderText: `当前价格：${currentPrice}万，输入最新价格(万元)`,
      async success(res) {
        if (res.confirm && res.content) {
          const price = parseFloat(res.content);
          if (isNaN(price) || price <= 0) return wx.showToast({ title: '请输入有效价格', icon: 'none' });

          await add(STORAGE_KEYS.PRICE_HISTORY, {
            houseId: that.data.selectedHouse.id, price, date: Date.now(), note: '',
          });

          await update(STORAGE_KEYS.HOUSES, that.data.selectedHouse.id, { totalPrice: price });

          wx.showToast({ title: '记录成功', icon: 'success' });
          that.loadHouses();
          that.loadPriceData(that.data.selectedHouse.id);
        }
      },
    });
  },
});
