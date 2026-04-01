// pages/diary/detail/detail.js - 日记详情（云开发版）
const { getById, STORAGE_KEYS } = require('../../../utils/storage');
const { formatDate } = require('../../../utils/format');

Page({
  data: { diary: null },

  async onLoad(options) {
    const diary = await getById(STORAGE_KEYS.DIARIES, options.id);
    if (!diary) return wx.showToast({ title: '日记不存在', icon: 'none' });
    this.setData({
      diary: {
        ...diary,
        dateStr: formatDate(diary.createTime),
        ratingStars: diary.rating ? '★'.repeat(diary.rating) + '☆'.repeat(5 - diary.rating) : '',
      },
    });
  },

  previewImage(e) {
    wx.previewImage({ current: this.data.diary.images[e.currentTarget.dataset.index], urls: this.data.diary.images });
  },
});
