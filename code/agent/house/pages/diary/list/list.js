// pages/diary/list/list.js - 看房日记列表（云开发版）
const { get, STORAGE_KEYS } = require('../../../utils/storage');
const { formatDate } = require('../../../utils/format');

Page({
  data: { diaries: [] },

  onShow() { this.loadDiaries(); },

  async loadDiaries() {
    const diaries = (await get(STORAGE_KEYS.DIARIES)).map(d => {
      const ratingLabels = ['', '很差', '较差', '一般', '不错', '很好'];
      const stars = d.rating ? '★'.repeat(d.rating) + '☆'.repeat(5 - d.rating) : '';
      return { ...d, dateStr: formatDate(d.createTime), ratingStars: stars, ratingLabel: ratingLabels[d.rating] || '' };
    });
    this.setData({ diaries });
  },

  goToDetail(e) { wx.navigateTo({ url: `/pages/diary/detail/detail?id=${e.currentTarget.dataset.id}` }); },
  goToAdd() { wx.navigateTo({ url: '/pages/diary/add/add' }); },
});
