// pages/calc/tax/tax.js - 税费计算器
const { calcTax } = require('../../../utils/calc');

Page({
  data: {
    totalPrice: '',
    area: '',
    houseType: 'ordinary',
    isFirst: true,
    isOnly: true,
    years: 'gt5',
    result: null,
  },

  onLoad(options) {
    if (options.price) this.setData({ totalPrice: options.price });
    if (options.area) this.setData({ area: options.area });
  },

  onInput(e) {
    this.setData({ [e.currentTarget.dataset.field]: e.detail.value });
  },

  onHouseTypeChange(e) {
    this.setData({ houseType: e.currentTarget.dataset.value, result: null });
  },
  onFirstChange(e) {
    this.setData({ isFirst: e.currentTarget.dataset.value === 'true', result: null });
  },
  onOnlyChange(e) {
    this.setData({ isOnly: e.currentTarget.dataset.value === 'true', result: null });
  },
  onYearsChange(e) {
    this.setData({ years: e.currentTarget.dataset.value, result: null });
  },

  calculate() {
    const totalPrice = parseFloat(this.data.totalPrice);
    const area = parseFloat(this.data.area);

    if (!totalPrice || totalPrice <= 0) {
      return wx.showToast({ title: '请输入有效的房屋总价', icon: 'none' });
    }
    if (!area || area <= 0) {
      return wx.showToast({ title: '请输入有效的面积', icon: 'none' });
    }

    const yearsMap = { 'lt2': 1, '2to5': 3, 'gt5': 6 };
    const result = calcTax({
      price: totalPrice * 10000, // 转为元
      area,
      isFirst: this.data.isFirst,
      isOnly: this.data.isOnly,
      years: yearsMap[this.data.years],
      houseType: this.data.houseType,
      city: 'default',
    });

    // 格式化
    const fmt = (v) => v > 10000 ? `${(v / 10000).toFixed(2)}万` : `${v.toFixed(2)}元`;
    const allInCost = totalPrice * 10000 + result.total;

    this.setData({
      result: {
        ...result,
        deedTaxStr: fmt(result.deedTax),
        valueAddedTaxStr: fmt(result.valueAddedTax),
        personalTaxStr: fmt(result.personalTax),
        maintenanceStr: fmt(result.maintenance),
        totalStr: fmt(result.total),
        allInCostStr: fmt(allInCost),
      },
    });

    wx.showToast({ title: '计算完成', icon: 'success' });
  },
});
