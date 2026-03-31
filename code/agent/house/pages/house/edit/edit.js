// pages/house/edit/edit.js - 编辑房源（云开发版）
var storageMod = require('../../../utils/storage');
var getById = storageMod.getById;
var update = storageMod.update;
var STORAGE_KEYS = storageMod.STORAGE_KEYS;
var formatMod = require('../../../utils/format');
var formatUnitPrice = formatMod.formatUnitPrice;
var citiesMod = require('../../../utils/cities');
var getCities = citiesMod.getCities;
var getDistricts = citiesMod.getDistricts;

Page({
  data: {
    houseId: '', form: {}, unitPrice: '',
    cities: [],
    cityIndex: -1,
    districts: [],
    districtIndex: -1,
    sourceOptions: ['链家', '我爱我家', '中原地产', '安居客', '贝壳', '业主直售', '其他'],
    roomOptions: [0, 1, 2, 3, 4, 5, 6],
    orientationOptions: ['东', '南', '西', '北', '东南', '东北', '西南', '西北', '南北通透'],
    orientationIndex: -1,
    decorationOptions: ['毛坯', '简装', '精装', '豪装', '其他'],
    buildingTypeOptions: ['板楼', '塔楼', '板塔结合', '别墅', '其他'],
    scoreItems: [
      { key: 'transportScore', label: '🚇 交通便利' },
      { key: 'educationScore', label: '🏫 教育配套' },
      { key: 'medicalScore', label: '🏥 医疗配套' },
      { key: 'shoppingScore', label: '🛒 商业配套' },
      { key: 'environmentScore', label: '🌳 居住环境' },
    ],
  },

  onLoad: function (options) {
    var cities = getCities();
    this.setData({ cities: cities });

    var that = this;
    var id = options.id;
    if (!id) { wx.showToast({ title: '参数错误', icon: 'none' }); return; }

    getById(STORAGE_KEYS.HOUSES, id).then(function (house) {
      if (!house) { wx.showToast({ title: '房源不存在', icon: 'none' }); return; }

      // 城市和区域
      var cityIndex = cities.indexOf(house.city || '北京');
      if (cityIndex < 0) cityIndex = 0; // 兼容旧数据没有 city 字段
      var city = cities[cityIndex];
      var districts = getDistricts(city);
      var districtIndex = districts.indexOf(house.district);

      var orientationIndex = that.data.orientationOptions.indexOf(house.orientation);
      var roomIndex = that.data.roomOptions.indexOf(house.rooms);
      var hallIndex = that.data.roomOptions.indexOf(house.halls);

      that.setData({
        houseId: id,
        form: house,
        cityIndex: cityIndex,
        'form.city': house.city || city,
        districts: districts,
        districtIndex: districtIndex >= 0 ? districtIndex : -1,
        orientationIndex: orientationIndex >= 0 ? orientationIndex : -1,
        roomIndex: roomIndex >= 0 ? roomIndex : 0,
        hallIndex: hallIndex >= 0 ? hallIndex : 0,
        unitPrice: formatUnitPrice(house.totalPrice, house.area),
      });
    });
  },

  onCityChange: function (e) {
    var index = parseInt(e.detail.value);
    var city = this.data.cities[index];
    var districts = getDistricts(city);
    this.setData({
      cityIndex: index,
      'form.city': city,
      districts: districts,
      districtIndex: -1,
      'form.district': '',
    });
  },

  onDistrictChange: function (e) { var i = parseInt(e.detail.value); this.setData({ districtIndex: i, 'form.district': this.data.districts[i] }); },
  onRoomChange: function (e) { var i = parseInt(e.detail.value); this.setData({ roomIndex: i, 'form.rooms': this.data.roomOptions[i] }); },
  onHallChange: function (e) { var i = parseInt(e.detail.value); this.setData({ hallIndex: i, 'form.halls': this.data.roomOptions[i] }); },
  onOrientationChange: function (e) { var i = parseInt(e.detail.value); this.setData({ orientationIndex: i, 'form.orientation': this.data.orientationOptions[i] }); },
  onSourceChange: function (e) { this.setData({ 'form.source': e.currentTarget.dataset.value }); },
  onDecorationChange: function (e) { this.setData({ 'form.decoration': e.currentTarget.dataset.value }); },
  onBuildingTypeChange: function (e) { this.setData({ 'form.buildingType': e.currentTarget.dataset.value }); },
  onScoreChange: function (e) { this.setData({ ['form.' + e.currentTarget.dataset.key]: e.currentTarget.dataset.value }); },

  onInput: function (e) {
    var field = e.currentTarget.dataset.field;
    var value = e.detail.value;
    if (['area', 'floor', 'totalFloor', 'totalPrice', 'askPrice', 'expectedPrice'].indexOf(field) >= 0) {
      value = value ? parseFloat(value) : null;
    }
    this.setData({ ['form.' + field]: value });
    if (field === 'totalPrice' || field === 'area') this.calcUnitPrice();
  },

  calcUnitPrice: function () {
    var form = this.data.form;
    this.setData({ unitPrice: formatUnitPrice(form.totalPrice, form.area) });
  },

  chooseImage: function () {
    var remaining = 9 - (this.data.form.images || []).length;
    if (remaining <= 0) return;
    var that = this;
    wx.chooseImage({
      count: remaining, sizeType: ['compressed'], sourceType: ['album', 'camera'],
      success: function (res) {
        var images = (that.data.form.images || []).concat(res.tempFilePaths);
        that.setData({ 'form.images': images });
      },
    });
  },

  previewImage: function (e) {
    var index = e.currentTarget.dataset.index;
    wx.previewImage({ current: this.data.form.images[index], urls: this.data.form.images });
  },

  deleteImage: function (e) {
    var images = this.data.form.images.slice();
    images.splice(e.currentTarget.dataset.index, 1);
    this.setData({ 'form.images': images });
  },

  submitForm: function () {
    var form = this.data.form;
    if (!form.community) return wx.showToast({ title: '请输入小区名称', icon: 'none' });
    if (!form.totalPrice) return wx.showToast({ title: '请输入总价', icon: 'none' });

    wx.showLoading({ title: '保存中...' });
    var that = this;
    update(STORAGE_KEYS.HOUSES, this.data.houseId, form).then(function (success) {
      wx.hideLoading();
      if (success) {
        wx.showToast({ title: '更新成功', icon: 'success' });
        setTimeout(function () { wx.navigateBack(); }, 1500);
      } else {
        wx.showToast({ title: '更新失败', icon: 'none' });
      }
    });
  },
});
