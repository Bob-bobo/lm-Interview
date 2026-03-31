// pages/diary/add/add.js - 添加看房日记（云开发版 - 云存储照片）
const { add, get, STORAGE_KEYS } = require('../../../utils/storage');
const { batchUploadFiles, deleteFile } = require('../../../utils/cloud');

Page({
  data: {
    houseId: '', houseIndex: -1, houseNames: [], visitDate: '', rating: 0,
    content: '', images: [], uploadedFileIDs: [],
    selectedTags: [],
    quickTags: ['采光好', '户型佳', '交通便利', '周边配套好', '环境安静', '物业好', '装修满意', '价格偏高', '楼层不理想', '面积偏小', '中介热情', '需再考虑'],
  },

  async onLoad(options) {
    const houses = await get(STORAGE_KEYS.HOUSES);
    const houseNames = houses.map(h => h.community || '未命名');
    let houseIndex = -1, houseId = '';
    if (options.houseId) { houseId = options.houseId; houseIndex = houses.findIndex(h => h.id === houseId); }
    const today = new Date();
    const visitDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    this.setData({ houseNames, houseIndex, houseId, visitDate });
  },

  async onHouseSelect(e) {
    const index = parseInt(e.detail.value);
    const houses = await get(STORAGE_KEYS.HOUSES);
    this.setData({ houseIndex: index, houseId: houses[index] && houses[index].id ? houses[index].id : '' });
  },

  onInput(e) { this.setData({ [e.currentTarget.dataset.field]: e.detail.value }); },
  setRating(e) { this.setData({ rating: parseInt(e.currentTarget.dataset.value) }); },

  toggleTag(e) {
    const tag = e.currentTarget.dataset.tag;
    let tags = [...this.data.selectedTags];
    const idx = tags.indexOf(tag);
    if (idx >= 0) tags.splice(idx, 1); else tags.push(tag);
    this.setData({ selectedTags: tags });
  },

  chooseImage() {
    const remaining = 9 - this.data.images.length;
    if (remaining <= 0) return;
    wx.chooseMedia({
      count: remaining,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      sizeType: ['compressed'],
      success: (res) => {
        const newImages = res.tempFiles.map(f => f.tempFilePath);
        this.setData({ images: [...this.data.images, ...newImages] });
      },
    });
  },

  previewImage(e) {
    wx.previewImage({ current: this.data.images[e.currentTarget.dataset.index], urls: this.data.images });
  },

  deleteImage(e) {
    const index = e.currentTarget.dataset.index;
    const images = [...this.data.images];
    const uploadedFileIDs = [...this.data.uploadedFileIDs];
    // 如果已上传，同时删除云文件
    if (uploadedFileIDs[index] && uploadedFileIDs[index].startsWith('cloud://')) {
      deleteFile(uploadedFileIDs[index]);
    }
    images.splice(index, 1);
    uploadedFileIDs.splice(index, 1);
    this.setData({ images, uploadedFileIDs });
  },

  async submit() {
    if (!this.data.content.trim()) return wx.showToast({ title: '请记录看房感受', icon: 'none' });

    wx.showLoading({ title: '保存中...' });

    // 上传照片到云存储
    let cloudImages = [];
    if (this.data.images.length > 0) {
      wx.showLoading({ title: '上传照片中...' });
      cloudImages = await batchUploadFiles(this.data.images, 'diary');
    }

    await add(STORAGE_KEYS.DIARIES, {
      houseId: this.data.houseId,
      houseName: this.data.houseIndex >= 0 ? this.data.houseNames[this.data.houseIndex] : '',
      visitDate: this.data.visitDate, rating: this.data.rating,
      content: this.data.content,
      images: cloudImages,  // 存储云文件ID列表
      tags: this.data.selectedTags,
    });

    wx.hideLoading();
    wx.showToast({ title: '保存成功', icon: 'success' });
    setTimeout(() => wx.navigateBack(), 1500);
  },
});
