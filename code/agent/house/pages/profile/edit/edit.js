// pages/profile/edit/edit.js - 用户信息编辑
var storageMod = require('../../../utils/storage');
var add = storageMod.add;
var update = storageMod.update;
var getSync = storageMod.getSync;
var STORAGE_KEYS = storageMod.STORAGE_KEYS;
var cloudMod = require('../../../utils/cloud');
var uploadFile = cloudMod.uploadFile;
var citiesMod = require('../../../utils/cities');
var getCities = citiesMod.getCities;
var getDistricts = citiesMod.getDistricts;

Page({
  data: {
    avatarUrl: '',
    form: {
      nickname: '',
      phone: '',
      city: '',
      district: '',
      budgetMin: '',
      budgetMax: '',
      preferredArea: '',
      preferredRooms: '',
      preferredDistricts: '',
      priorities: [],
    },
    roomsOptions: ['不限', '1室', '2室', '3室', '4室', '5室及以上'],
    priorityOptions: ['地段', '价格', '学区', '交通', '户型', '环境', '物业', '品牌'],
    prioritySelected: {},
    loading: false,
    profileId: null,
    avatarChanged: false,
    // 城市相关
    cities: [],
    cityIndex: -1,
    districts: [],
    districtIndex: -1,
  },

  onLoad: function () {
    this.loadProfile();
  },

  loadProfile: function () {
    // 加载微信头像
    var userInfo = wx.getStorageSync('userInfo') || {};
    var cities = getCities();
    var initDist = [];

    // 从本地缓存快速读取用户画像
    var profiles = getSync(STORAGE_KEYS.USER_PROFILE);
    var defaultCityIndex = -1;
    var defaultDistricts = [];
    var defaultDistrictIndex = -1;

    if (profiles.length > 0) {
      var profile = profiles[0];
      var priorities = profile.priorities || [];

      // 构建选中映射
      var prioritySelected = {};
      this.data.priorityOptions.forEach(function (tag) {
        prioritySelected[tag] = priorities.indexOf(tag) >= 0;
      });

      // 城市和区域
      var cityIndex = cities.indexOf(profile.city || '');
      if (cityIndex >= 0) {
        defaultCityIndex = cityIndex;
        defaultDistricts = getDistricts(profile.city);
        var dIdx = defaultDistricts.indexOf(profile.district || '');
        if (dIdx >= 0) defaultDistrictIndex = dIdx;
      }

      this.setData({
        profileId: profile.id || profile._id,
        avatarUrl: profile.avatarUrl || userInfo.avatarUrl || '',
        form: {
          nickname: profile.nickname || '',
          phone: profile.phone || '',
          city: profile.city || '',
          district: profile.district || '',
          budgetMin: profile.budgetMin ? String(profile.budgetMin) : '',
          budgetMax: profile.budgetMax ? String(profile.budgetMax) : '',
          preferredArea: profile.preferredArea || '',
          preferredRooms: profile.preferredRooms || '',
          preferredDistricts: profile.preferredDistricts || '',
          priorities: priorities,
        },
        prioritySelected: prioritySelected,
        cities: cities,
        cityIndex: defaultCityIndex,
        districts: defaultDistricts,
        districtIndex: defaultDistrictIndex,
      });
    } else {
      this.setData({
        avatarUrl: userInfo.avatarUrl || '',
        cities: cities,
      });
    }
  },

  // ========== 头像相关 ==========

  changeAvatar: function () {
    var that = this;
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: function (res) {
        var tempFilePath = res.tempFiles[0].tempFilePath;
        that.setData({
          avatarUrl: tempFilePath,
          avatarChanged: true,
        });
      },
    });
  },

  // ========== 城市/区域联动 ==========

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
    this.setData({
      districtIndex: index,
      'form.district': this.data.districts[index],
    });
  },

  // ========== 表单输入 ==========

  onInput: function (e) {
    var field = e.currentTarget.dataset.field;
    this.setData({ ['form.' + field]: e.detail.value });
  },

  onBudgetInput: function (e) {
    var field = e.currentTarget.dataset.field;
    var val = e.detail.value.replace(/[^\d.]/g, '');
    if (val && val.split('.').length > 2) val = val.slice(0, -1);
    this.setData({ ['form.' + field]: val });
  },

  onRoomChange: function (e) {
    var idx = e.detail.value;
    var val = this.data.roomsOptions[idx] === '不限' ? '' : this.data.roomsOptions[idx];
    this.setData({ 'form.preferredRooms': val });
  },

  // ========== 优先级标签 ==========

  togglePriority: function (e) {
    var tag = e.currentTarget.dataset.tag;
    var priorities = this.data.form.priorities.slice();
    var isSelected = this.data.prioritySelected[tag];

    if (!isSelected) {
      if (priorities.length >= 5) {
        return wx.showToast({ title: '最多选5个优先级', icon: 'none' });
      }
      priorities.push(tag);
    } else {
      var idx = priorities.indexOf(tag);
      if (idx !== -1) priorities.splice(idx, 1);
    }

    this.setData({
      'form.priorities': priorities,
      ['prioritySelected.' + tag]: !isSelected,
    });
  },

  // ========== 保存 ==========

  save: function () {
    var that = this;
    var form = that.data.form;
    var profileId = that.data.profileId;
    var avatarUrl = that.data.avatarUrl;
    var avatarChanged = that.data.avatarChanged;

    // 校验
    if (form.phone && !/^1[3-9]\d{9}$/.test(form.phone)) {
      return wx.showToast({ title: '手机号格式不正确', icon: 'none' });
    }
    if (form.budgetMin && form.budgetMax && Number(form.budgetMin) > Number(form.budgetMax)) {
      return wx.showToast({ title: '最低预算不能大于最高预算', icon: 'none' });
    }

    that.setData({ loading: true });
    wx.showLoading({ title: '保存中...' });

    // 上传头像
    var uploadPromise = Promise.resolve(avatarUrl);
    if (avatarChanged && avatarUrl && avatarUrl.indexOf('cloud://') !== 0) {
      uploadPromise = new Promise(function (resolve) {
        var ext = avatarUrl.split('.').pop() || 'jpg';
        var cloudPath = 'avatar/' + Date.now() + '.' + ext;
        uploadFile(avatarUrl, cloudPath).then(function (fileID) {
          resolve(fileID || avatarUrl);
        }).catch(function () {
          resolve(avatarUrl);
        });
      });
    }

    uploadPromise.then(function (finalAvatarUrl) {
      var now = Date.now();
      var profileData = {
        nickname: form.nickname.trim(),
        phone: form.phone.trim(),
        city: form.city.trim(),
        district: form.district.trim(),
        budgetMin: form.budgetMin ? Number(form.budgetMin) : 0,
        budgetMax: form.budgetMax ? Number(form.budgetMax) : 0,
        preferredArea: form.preferredArea.trim(),
        preferredRooms: form.preferredRooms,
        preferredDistricts: form.preferredDistricts.trim(),
        priorities: form.priorities,
        avatarUrl: finalAvatarUrl,
        updateTime: now,
      };

      var savePromise;
      if (profileId) {
        savePromise = update(STORAGE_KEYS.USER_PROFILE, profileId, profileData);
      } else {
        savePromise = add(STORAGE_KEYS.USER_PROFILE, profileData).then(function (record) {
          that.setData({ profileId: record && record.id });
        });
      }

      return savePromise.then(function () {
        // 同步更新本地 userInfo
        var userInfo = wx.getStorageSync('userInfo') || {};
        if (form.nickname.trim()) userInfo.nickName = form.nickname.trim();
        if (finalAvatarUrl) userInfo.avatarUrl = finalAvatarUrl;
        wx.setStorageSync('userInfo', userInfo);

        wx.hideLoading();
        wx.showToast({ title: '保存成功', icon: 'success' });
        setTimeout(function () { wx.navigateBack(); }, 800);
      });
    }).catch(function (err) {
      console.error('保存用户资料失败:', err);
      wx.hideLoading();
      wx.showToast({ title: '保存失败，请重试', icon: 'none' });
      that.setData({ loading: false });
    });
  },
});
