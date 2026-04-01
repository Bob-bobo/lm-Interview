// pages/house/compare/compare.js - 房源对比（云开发版）
const { get, STORAGE_KEYS } = require('../../../utils/storage');
const { formatUnitPrice } = require('../../../utils/format');

Page({
  data: {
    houses: [], analysis: [], recommended: null,
    minPrice: 0, maxPrice: 0, maxTransport: 0, maxEducation: 0, maxEnvironment: 0, maxTotal: 0,
  },

  async onLoad(options) {
    if (!options.ids) return;
    const ids = options.ids.split(',');
    await this.loadHouses(ids);
  },

  async loadHouses(ids) {
    const allHouses = await get(STORAGE_KEYS.HOUSES);
    const houses = ids.map(id => {
      const house = allHouses.find(h => h.id === id);
      if (!house) return null;
      return { ...house, unitPrice: formatUnitPrice(house.totalPrice, house.area) };
    }).filter(Boolean);

    const prices = houses.map(h => h.totalPrice || 0);
    const transports = houses.map(h => h.transportScore || 0);
    const educations = houses.map(h => h.educationScore || 0);
    const environments = houses.map(h => h.environmentScore || 0);

    const avgArea = houses.reduce((s, h) => s + (h.area || 0), 0) / houses.length;
    const maxArea = Math.max(...houses.map(h => h.area || 0));
    const minPriceVal = Math.min(...prices);
    const maxPriceVal = Math.max(...prices);
    const priceRange = maxPriceVal - minPriceVal || 1;

    houses.forEach(h => {
      const priceScore = maxPriceVal > minPriceVal ? ((maxPriceVal - (h.totalPrice || 0)) / priceRange) * 30 : 15;
      const transScore = (h.transportScore || 0) / 5 * 20;
      const eduScore = (h.educationScore || 0) / 5 * 20;
      const envScore = (h.environmentScore || 0) / 5 * 20;
      const areaScore = maxArea > 0 ? (h.area || 0) / maxArea * 10 : 5;
      h.totalScore = Math.round(priceScore + transScore + eduScore + envScore + areaScore);
    });

    const maxTotal = Math.max(...houses.map(h => h.totalScore));
    const recommended = houses.reduce((best, h) => h.totalScore > ((best && best.totalScore) || 0) ? h : best, null);
    const analysis = this.generateAnalysis(houses, recommended);

    this.setData({
      houses, recommended, minPrice: minPriceVal, maxPrice: maxPriceVal,
      maxTransport: Math.max(...transports), maxEducation: Math.max(...educations),
      maxEnvironment: Math.max(...environments), maxTotal, analysis,
    });
  },

  generateAnalysis(houses, recommended) {
    const list = [];
    if (!recommended) return list;

    const prices = houses.map(h => h.totalPrice);
    const minP = Math.min(...prices);
    const maxP = Math.max(...prices);
    const minHouse = houses.find(h => h.totalPrice === minP);
    list.push(`💰 价格区间：${minP}-${maxP}万，最低价${(minHouse && minHouse.community) || ''}（${minP}万）`);

    const unitPrices = houses.filter(h => h.unitPrice).map(h => { const m = h.unitPrice.match(/(\d+)/); return m ? parseInt(m[1]) : 0; });
    if (unitPrices.length > 0) {
      list.push(`📐 平均单价约${Math.round(unitPrices.reduce((a, b) => a + b, 0) / unitPrices.length)}元/㎡`);
    }

    const goodOrientations = houses.filter(h => h.orientation && ['南', '南北', '东南'].some(o => h.orientation.includes(o)));
    if (goodOrientations.length > 0) list.push(`🧭 ${goodOrientations.map(h => h.community).join('、')}朝向优秀`);

    if (recommended) {
      const reasons = [];
      if (recommended.totalPrice === Math.min(...prices)) reasons.push('价格最低');
      if (recommended.transportScore >= 4) reasons.push('交通便捷');
      if (recommended.educationScore >= 4) reasons.push('教育资源优');
      if (recommended.environmentScore >= 4) reasons.push('环境评分高');
      list.push(`⭐ 综合推荐：${recommended.community}（${recommended.totalScore}分），${reasons.join('、') || '综合性价比最高'}`);
    }
    return list;
  },

  goBack() { wx.navigateBack(); },
  goToAI() { wx.switchTab({ url: '/pages/ai/analyze/analyze' }); },
});
