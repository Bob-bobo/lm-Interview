// pages/house/add/add.js - 添加房源（云开发版）
var storageMod = require('../../../utils/storage');
var add = storageMod.add;
var STORAGE_KEYS = storageMod.STORAGE_KEYS;
var getSync = storageMod.getSync;
var formatMod = require('../../../utils/format');
var formatUnitPrice = formatMod.formatUnitPrice;
var citiesMod = require('../../../utils/cities');
var getCities = citiesMod.getCities;
var getDistricts = citiesMod.getDistricts;

Page({
  data: {
    form: {
      community: '', buildingNo: '', city: '', district: '', address: '', source: '',
      rooms: null, halls: null, orientation: '', area: null, floor: null, totalFloor: null,
      decoration: '', buildingType: '', buildYear: '',
      totalPrice: null, askPrice: null, expectedPrice: null, remark: '', images: [],
      transportScore: 0, educationScore: 0, medicalScore: 0, shoppingScore: 0, environmentScore: 0,
    },
    unitPrice: '',
    cities: [],
    cityIndex: -1,
    districts: [],
    districtIndex: -1,
    sourceOptions: ['链家', '我爱我家', '中原地产', '安居客', '贝壳', '业主直售', '其他'],
    roomOptions: [0, 1, 2, 3, 4, 5, 6],
    roomIndex: 0,
    hallIndex: 0,
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

  onLoad: function () {
    var cities = getCities();
    // 读取用户画像中的意向城市，设置默认值
    var profiles = getSync(STORAGE_KEYS.USER_PROFILE);
    var defaultCityIndex = -1;
    var defaultCity = '';
    if (profiles.length > 0 && profiles[0].city) {
      defaultCity = profiles[0].city;
      var idx = cities.indexOf(defaultCity);
      if (idx >= 0) defaultCityIndex = idx;
    }

    var initialDistricts = defaultCityIndex >= 0 ? getDistricts(defaultCity) : [];

    this.setData({
      cities: cities,
      cityIndex: defaultCityIndex,
      districts: initialDistricts,
      'form.city': defaultCity,
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

  onDistrictChange: function (e) {
    var index = parseInt(e.detail.value);
    this.setData({ districtIndex: index, 'form.district': this.data.districts[index] });
  },

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

  onRoomChange: function (e) { var i = parseInt(e.detail.value); this.setData({ roomIndex: i, 'form.rooms': this.data.roomOptions[i] }); },
  onHallChange: function (e) { var i = parseInt(e.detail.value); this.setData({ hallIndex: i, 'form.halls': this.data.roomOptions[i] }); },
  onOrientationChange: function (e) { var i = parseInt(e.detail.value); this.setData({ orientationIndex: i, 'form.orientation': this.data.orientationOptions[i] }); },
  onSourceChange: function (e) { this.setData({ 'form.source': e.currentTarget.dataset.value }); },
  onDecorationChange: function (e) { this.setData({ 'form.decoration': e.currentTarget.dataset.value }); },
  onBuildingTypeChange: function (e) { this.setData({ 'form.buildingType': e.currentTarget.dataset.value }); },
  onScoreChange: function (e) { this.setData({ ['form.' + e.currentTarget.dataset.key]: e.currentTarget.dataset.value }); },

  chooseImage: function () {
    var remaining = 9 - this.data.form.images.length;
    if (remaining <= 0) return;
    var that = this;
    wx.chooseImage({
      count: remaining, sizeType: ['compressed'], sourceType: ['album', 'camera'],
      success: function (res) { that.setData({ 'form.images': that.data.form.images.concat(res.tempFilePaths) }); },
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
    if (!form.city) return wx.showToast({ title: '请选择城市', icon: 'none' });
    if (!form.district) return wx.showToast({ title: '请选择区域', icon: 'none' });
    if (!form.area) return wx.showToast({ title: '请输入面积', icon: 'none' });
    if (!form.totalPrice) return wx.showToast({ title: '请输入总价', icon: 'none' });

    wx.showLoading({ title: '保存中...' });
    var that = this;
    var data = {};
    Object.keys(form).forEach(function (k) { data[k] = form[k]; });
    add(STORAGE_KEYS.HOUSES, data).then(function (record) {
      wx.hideLoading();
      if (record) {
        wx.showToast({ title: '保存成功', icon: 'success' });
        setTimeout(function () { wx.navigateBack(); }, 1500);
      } else {
        wx.showToast({ title: '保存失败', icon: 'none' });
      }
    });
  },

  onShareAppMessage: function () {
    return { title: '买房助手 - 记录心仪房源', path: '/pages/index/index' };
  },
});
