// pages/house/list/list.js - 房源列表（云开发版，支持城市筛选）
var storageMod = require('../../../utils/storage');
var get = storageMod.get;
var STORAGE_KEYS = storageMod.STORAGE_KEYS;
var getSync = storageMod.getSync;
var formatMod = require('../../../utils/format');
var formatUnitPrice = formatMod.formatUnitPrice;
var timeAgo = formatMod.timeAgo;
var citiesMod = require('../../../utils/cities');
var getCities = citiesMod.getCities;
var getDistricts = citiesMod.getDistricts;

Page({
  data: {
    houses: [],
    filteredHouses: [],
    keyword: '',
    total: 0,
    currentFilter: 'all',
    // 城市筛选
    cities: [],
    selectedCity: '',
    cityFilter: 'all', // all | city
    // 区域筛选
    districts: [],
    selectedDistrict: '',
    // 排序
    currentSort: 'time',
    compareIds: [],
  },

  onLoad: function () {
    var cities = getCities();

    // 读取用户画像中的意向城市，设置默认城市筛选
    var defaultCity = '';
    var profiles = getSync(STORAGE_KEYS.USER_PROFILE);
    if (profiles.length > 0 && profiles[0].city) {
      defaultCity = profiles[0].city;
    }

    var districts = defaultCity ? getDistricts(defaultCity) : [];

    this.setData({
      cities: cities,
      selectedCity: defaultCity,
      districts: districts,
    });

    this.loadHouses();
  },

  onShow: function () {
    this.loadHouses();
  },

  loadHouses: function () {
    var that = this;
    get(STORAGE_KEYS.HOUSES).then(function (houses) {
      houses = houses.map(function (house) {
        return {
          city: house.city || '北京',
          district: house.district || '',
          community: house.community || '',
          address: house.address || '',
          rooms: house.rooms,
          halls: house.halls,
          orientation: house.orientation,
          area: house.area,
          floor: house.floor,
          totalFloor: house.totalFloor,
          decoration: house.decoration,
          totalPrice: house.totalPrice,
          source: house.source,
          images: house.images || [],
          createTime: house.createTime,
          id: house.id,
          unitPrice: formatUnitPrice(house.totalPrice, house.area),
          timeAgo: timeAgo(house.createTime),
        };
      });
      that.setData({ houses: houses, total: houses.length }, function () { that.applyFilters(); });
    });
  },

  onSearch: function (e) {
    this.setData({ keyword: e.detail.value }, function () { this.applyFilters(); });
  },

  clearSearch: function () {
    this.setData({ keyword: '' }, function () { this.applyFilters(); });
  },

  onFilter: function (e) {
    var filter = e.currentTarget.dataset.filter;
    if (filter === 'all') {
      this.setData({
        currentFilter: 'all',
        selectedCity: '',
        cityFilter: 'all',
        selectedDistrict: '',
        districts: [],
      }, function () { this.applyFilters(); });
    }
  },

  // 城市筛选
  showCityPicker: function () {
    var that = this;
    var cityList = ['全部城市'].concat(this.data.cities);
    wx.showActionSheet({
      itemList: cityList,
      success: function (res) {
        var city = res.tapIndex === 0 ? '' : that.data.cities[res.tapIndex - 1];
        var districts = city ? getDistricts(city) : [];
        that.setData({
          selectedCity: city,
          cityFilter: city ? 'city' : 'all',
          selectedDistrict: '',
          districts: districts,
        }, function () { that.applyFilters(); });
      },
    });
  },

  // 区域筛选
  showDistrictPicker: function () {
    if (!this.data.selectedCity) {
      wx.showToast({ title: '请先选择城市', icon: 'none' });
      return;
    }
    var that = this;
    wx.showActionSheet({
      itemList: ['全部'].concat(this.data.districts),
      success: function (res) {
        var district = res.tapIndex === 0 ? '' : that.data.districts[res.tapIndex - 1];
        that.setData({ selectedDistrict: district, currentFilter: district ? 'district' : (that.data.cityFilter) }, function () { that.applyFilters(); });
      },
    });
  },

  showPricePicker: function () {
    var that = this;
    wx.showActionSheet({
      itemList: ['不限', '200万以下', '200-300万', '300-500万', '500-800万', '800万以上'],
      success: function (res) {
        var ranges = [null, [0, 200], [200, 300], [300, 500], [500, 800], [800, Infinity]];
        that.setData({ priceRange: ranges[res.tapIndex], currentFilter: res.tapIndex > 0 ? 'price' : that.data.cityFilter }, function () { that.applyFilters(); });
      },
    });
  },

  showSortPicker: function () {
    var that = this;
    wx.showActionSheet({
      itemList: ['最新添加', '价格升序', '价格降序', '面积升序'],
      success: function (res) {
        var sorts = ['time', 'price', 'priceDesc', 'area'];
        that.setData({ currentSort: sorts[res.tapIndex] }, function () { that.applyFilters(); });
      },
    });
  },

  applyFilters: function () {
    var that = this;
    var list = that.data.houses.slice();
    // 城市筛选
    if (that.data.selectedCity) {
      list = list.filter(function (h) { return h.city === that.data.selectedCity; });
    }
    // 搜索
    if (that.data.keyword) {
      var kw = that.data.keyword.toLowerCase();
      list = list.filter(function (h) {
        return (h.community && h.community.toLowerCase().indexOf(kw) >= 0) ||
          (h.address && h.address.toLowerCase().indexOf(kw) >= 0) ||
          (h.district && h.district.indexOf(kw) >= 0);
      });
    }
    // 区域筛选
    if (that.data.selectedDistrict) {
      list = list.filter(function (h) { return h.district === that.data.selectedDistrict; });
    }
    // 价格筛选
    if (that.data.priceRange) {
      var minP = that.data.priceRange[0];
      var maxP = that.data.priceRange[1];
      list = list.filter(function (h) { return h.totalPrice >= minP && h.totalPrice < maxP; });
    }
    // 排序
    switch (that.data.currentSort) {
      case 'price': list.sort(function (a, b) { return (a.totalPrice || 0) - (b.totalPrice || 0); }); break;
      case 'priceDesc': list.sort(function (a, b) { return (b.totalPrice || 0) - (a.totalPrice || 0); }); break;
      case 'area': list.sort(function (a, b) { return (a.area || 0) - (b.area || 0); }); break;
      default: list.sort(function (a, b) { return (b.createTime || 0) - (a.createTime || 0); });
    }
    that.setData({ filteredHouses: list });
  },

  toggleCompare: function (e) {
    var id = e.currentTarget.dataset.id;
    var compareIds = this.data.compareIds.slice();
    var index = compareIds.indexOf(id);
    if (index >= 0) compareIds.splice(index, 1);
    else if (compareIds.length < 4) compareIds.push(id);
    else return wx.showToast({ title: '最多选择4套房源对比', icon: 'none' });
    this.setData({ compareIds: compareIds });
  },

  goToDetail: function (e) {
    var id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: '/pages/house/detail/detail?id=' + id });
  },

  goToAdd: function () {
    wx.navigateTo({ url: '/pages/house/add/add' });
  },

  goToCompare: function () {
    if (this.data.compareIds.length < 2) return wx.showToast({ title: '请至少选择2套房源', icon: 'none' });
    wx.navigateTo({ url: '/pages/house/compare/compare?ids=' + this.data.compareIds.join(',') });
  },

  onShareAppMessage: function () {
    return { title: '买房助手 - 我的房源收藏', path: '/pages/house/list/list' };
  },
});
