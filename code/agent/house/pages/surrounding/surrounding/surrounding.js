// pages/surrounding/surrounding/surrounding.js - 周边配套评估（云开发版）
const { get, getSync, update, STORAGE_KEYS } = require('../../../utils/storage');

const FACILITY_GROUPS = [
  { name: '🚇 交通', items: [
    { text: '地铁站点（800m内）', checked: false, distance: '' },
    { text: '公交站点（300m内）', checked: false, distance: '' },
    { text: '主干道/快速路', checked: false, distance: '' },
    { text: '共享单车停放点', checked: false, distance: '' },
  ]},
  { name: '🏫 教育', items: [
    { text: '幼儿园', checked: false, distance: '' },
    { text: '小学', checked: false, distance: '' },
    { text: '中学', checked: false, distance: '' },
    { text: '教育培训机构', checked: false, distance: '' },
  ]},
  { name: '🏥 医疗', items: [
    { text: '三甲医院', checked: false, distance: '' },
    { text: '社区医院/诊所', checked: false, distance: '' },
    { text: '药店', checked: false, distance: '' },
    { text: '社区卫生中心', checked: false, distance: '' },
  ]},
  { name: '🛒 商业', items: [
    { text: '大型商场', checked: false, distance: '' },
    { text: '超市/便利店', checked: false, distance: '' },
    { text: '菜市场/生鲜超市', checked: false, distance: '' },
    { text: '餐饮美食街', checked: false, distance: '' },
  ]},
  { name: '🌳 休闲生活', items: [
    { text: '公园/绿地', checked: false, distance: '' },
    { text: '健身房/运动场', checked: false, distance: '' },
    { text: '银行网点', checked: false, distance: '' },
    { text: '快递驿站', checked: false, distance: '' },
  ]},
];

const SCORE_CONFIG = [
  { key: 'transportScore', icon: '🚇', name: '交通便利', color: '#1890ff', desc: '地铁/公交/道路通达性' },
  { key: 'educationScore', icon: '🏫', name: '教育配套', color: '#722ed1', desc: '幼儿园/小学/中学质量' },
  { key: 'medicalScore', icon: '🏥', name: '医疗配套', color: '#f5222d', desc: '医院/诊所/药店距离' },
  { key: 'shoppingScore', icon: '🛒', name: '商业配套', color: '#fa8c16', desc: '商场/超市/菜市场便利度' },
  { key: 'environmentScore', icon: '🌳', name: '居住环境', color: '#52c41a', desc: '公园/绿化/噪音/空气' },
];

Page({
  data: {
    houses: [],
    houseNames: [],
    houseIndex: -1,
    currentHouseId: null,
    scoreItems: SCORE_CONFIG.map(c => ({ ...c, value: 0 })),
    avgScore: 0,
    scoreLevel: '',
    scoreLevelColor: '',
    facilityGroups: JSON.parse(JSON.stringify(FACILITY_GROUPS)),
    facilityCount: 0,
    facilityTotal: 0,
    showRadar: false,
    radarCanvasReady: false,
    notes: '',
  },

  onLoad() {
    this.loadHouses();
  },

  onShow() {
    const oldIndex = this.data.houseIndex;
    this.loadHouses();
    if (oldIndex >= 0 && this.data.houses.length > 0) {
      const currentId = this.data.currentHouseId;
      if (currentId) {
        const newIdx = this.data.houses.findIndex(h => h.id === currentId);
        if (newIdx >= 0) {
          this.setData({ houseIndex: newIdx });
        }
      }
    }
  },

  onReady() {
    this.setData({ radarCanvasReady: true });
    if (this.data.houseIndex >= 0) {
      this.drawRadar();
    }
  },

  async loadHouses() {
    const houses = await get(STORAGE_KEYS.HOUSES);
    this.setData({
      houses,
      houseNames: houses.length > 0
        ? houses.map(h => `${h.community || '未命名小区'} ${h.totalPrice}万`)
        : ['暂无房源，请先添加'],
    });
  },

  onHouseSelect(e) {
    const index = parseInt(e.detail.value);
    if (this.data.houses.length === 0) {
      wx.showToast({ title: '请先添加房源', icon: 'none' });
      return;
    }

    const house = this.data.houses[index];
    this.setData({
      houseIndex: index,
      currentHouseId: house.id,
    });

    const scoreItems = this.data.scoreItems.map(item => ({
      ...item,
      value: house[item.key] || 0,
    }));

    const savedFacility = house.facilityData || null;
    let facilityGroups = JSON.parse(JSON.stringify(FACILITY_GROUPS));
    if (savedFacility) {
      facilityGroups = savedFacility;
    }

    const notes = house.surroundingNotes || '';

    this.calculateScore(scoreItems);
    this.setData({
      scoreItems,
      facilityGroups,
      notes,
      showRadar: true,
    });

    this.countFacilities();
    setTimeout(() => this.drawRadar(), 100);
  },

  onScoreChange(e) {
    const key = e.currentTarget.dataset.key;
    const value = parseInt(e.detail.value);
    const scoreItems = this.data.scoreItems.map(item =>
      item.key === key ? { ...item, value } : item
    );
    this.setData({ scoreItems });
    this.calculateScore(scoreItems);
    this.saveScores(scoreItems);
    setTimeout(() => this.drawRadar(), 50);
  },

  calculateScore(scoreItems) {
    const scores = scoreItems.map(s => s.value);
    const validScores = scores.filter(s => s > 0);
    let avgScore = 0;
    if (validScores.length > 0) {
      avgScore = validScores.reduce((a, b) => a + b, 0) / validScores.length;
    }

    let scoreLevel = '未评分';
    let scoreLevelColor = '#999';
    if (validScores.length > 0) {
      if (avgScore >= 4.5) { scoreLevel = '卓越 🌟🌟🌟'; scoreLevelColor = '#f5222d'; }
      else if (avgScore >= 3.5) { scoreLevel = '优秀 ⭐⭐⭐'; scoreLevelColor = '#fa8c16'; }
      else if (avgScore >= 2.5) { scoreLevel = '良好 ⭐⭐'; scoreLevelColor = '#1890ff'; }
      else if (avgScore >= 1.5) { scoreLevel = '一般 ⭐'; scoreLevelColor = '#999'; }
      else { scoreLevel = '待改善'; scoreLevelColor = '#999'; }
    }

    this.setData({
      avgScore: avgScore.toFixed(1),
      scoreLevel,
      scoreLevelColor,
    });
  },

  saveScores(scoreItems) {
    const house = this.data.houses[this.data.houseIndex];
    if (!house) return;
    const updates = {};
    scoreItems.forEach(item => { updates[item.key] = item.value; });
    update(STORAGE_KEYS.HOUSES, house.id, updates);
  },

  toggleFacility(e) {
    const { group, item } = e.currentTarget.dataset;
    const facilityGroups = [...this.data.facilityGroups];
    facilityGroups[group].items = facilityGroups[group].items.map(fi =>
      fi.text === item ? { ...fi, checked: !fi.checked } : fi
    );
    this.setData({ facilityGroups });
    this.countFacilities();
    this.saveFacilities();
  },

  onDistanceInput(e) {
    const { group, item } = e.currentTarget.dataset;
    const distance = e.detail.value;
    const facilityGroups = [...this.data.facilityGroups];
    facilityGroups[group].items = facilityGroups[group].items.map(fi =>
      fi.text === item ? { ...fi, distance } : fi
    );
    this.setData({ facilityGroups });
    this.saveFacilities();
  },

  countFacilities() {
    let count = 0;
    let total = 0;
    this.data.facilityGroups.forEach(g => {
      g.items.forEach(fi => {
        total++;
        if (fi.checked) count++;
      });
    });
    this.setData({ facilityCount: count, facilityTotal: total });
  },

  saveFacilities() {
    const house = this.data.houses[this.data.houseIndex];
    if (!house) return;
    update(STORAGE_KEYS.HOUSES, house.id, {
      facilityData: this.data.facilityGroups,
    });
  },

  onNotesInput(e) {
    this.setData({ notes: e.detail.value });
  },

  saveNotes() {
    const house = this.data.houses[this.data.houseIndex];
    if (!house) return;
    update(STORAGE_KEYS.HOUSES, house.id, {
      surroundingNotes: this.data.notes,
    });
    wx.showToast({ title: '备注已保存', icon: 'success' });
  },

  toggleGroup(e) {
    const { group } = e.currentTarget.dataset;
    const facilityGroups = [...this.data.facilityGroups];
    const allChecked = facilityGroups[group].items.every(fi => fi.checked);
    facilityGroups[group].items = facilityGroups[group].items.map(fi => ({
      ...fi, checked: !allChecked,
    }));
    this.setData({ facilityGroups });
    this.countFacilities();
    this.saveFacilities();
  },

  // ========== 雷达图绘制 ==========
  drawRadar() {
    if (!this.data.radarCanvasReady || this.data.houseIndex < 0) return;

    const query = wx.createSelectorQuery();
    query.select('#radarCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res[0]) return;
        const canvas = res[0].node;
        const ctx = canvas.getContext('2d');
        const dpr = wx.getWindowInfo().pixelRatio;
        const width = res[0].width;
        const height = res[0].height;
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        ctx.scale(dpr, dpr);

        this._renderRadar(ctx, width, height);
      });
  },

  _renderRadar(ctx, width, height) {
    const scores = this.data.scoreItems.map(s => s.value);
    const colors = this.data.scoreItems.map(s => s.color);
    const names = this.data.scoreItems.map(s => s.name);
    const count = scores.length;
    const cx = width / 2;
    const cy = height / 2;
    const maxR = Math.min(width, height) / 2 - 40;

    ctx.clearRect(0, 0, width, height);

    for (let level = 1; level <= 5; level++) {
      const r = (maxR / 5) * level;
      ctx.beginPath();
      for (let i = 0; i <= count; i++) {
        const angle = (Math.PI * 2 / count) * i - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.strokeStyle = level === 5 ? '#ddd' : '#eee';
      ctx.lineWidth = level === 5 ? 1.5 : 1;
      ctx.stroke();

      if (level % 2 === 0 || level === 5) {
        ctx.fillStyle = '#ccc';
        ctx.font = '10px sans-serif';
        ctx.fillText(level.toString(), cx + 4, cy - (maxR / 5) * level + 12);
      }
    }

    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 / count) * i - Math.PI / 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + maxR * Math.cos(angle), cy + maxR * Math.sin(angle));
      ctx.strokeStyle = '#eee';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    ctx.beginPath();
    for (let i = 0; i <= count; i++) {
      const idx = i % count;
      const angle = (Math.PI * 2 / count) * idx - Math.PI / 2;
      const r = (scores[idx] / 5) * maxR;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(24, 144, 255, 0.2)';
    ctx.fill();
    ctx.strokeStyle = '#1890ff';
    ctx.lineWidth = 2;
    ctx.stroke();

    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 / count) * i - Math.PI / 2;
      const r = (scores[i] / 5) * maxR;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);

      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = colors[i];
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 / count) * i - Math.PI / 2;
      const labelR = maxR + 24;
      const x = cx + labelR * Math.cos(angle);
      const y = cy + labelR * Math.sin(angle);
      ctx.fillStyle = '#333';
      ctx.fillText(names[i], x, y);

      ctx.fillStyle = colors[i];
      ctx.font = 'bold 11px sans-serif';
      ctx.fillText(scores[i].toFixed(1), x, y + 15);
      ctx.font = '12px sans-serif';
    }
  },

  resetScores() {
    wx.showModal({
      title: '确认重置',
      content: '将清除该房源的所有周边评分和设施记录，是否继续？',
      success: (res) => {
        if (res.confirm) {
          const scoreItems = this.data.scoreItems.map(item => ({ ...item, value: 0 }));
          const facilityGroups = JSON.parse(JSON.stringify(FACILITY_GROUPS));
          this.setData({ scoreItems, facilityGroups, notes: '' });
          this.calculateScore(scoreItems);
          this.countFacilities();

          const house = this.data.houses[this.data.houseIndex];
          if (house) {
            const updates = {};
            scoreItems.forEach(item => { updates[item.key] = 0; });
            updates.facilityData = null;
            updates.surroundingNotes = '';
            update(STORAGE_KEYS.HOUSES, house.id, updates);
          }

          setTimeout(() => this.drawRadar(), 100);
          wx.showToast({ title: '已重置', icon: 'success' });
        }
      },
    });
  },

  autoScore() {
    const { facilityGroups, scoreItems } = this.data;
    const newScores = [...scoreItems];

    const transportItems = facilityGroups[0].items;
    const transportChecked = transportItems.filter(i => i.checked).length;
    newScores[0].value = transportChecked >= 3 ? 5 : transportChecked >= 2 ? 4 : transportChecked >= 1 ? 3 : 0;

    const eduItems = facilityGroups[1].items;
    const eduChecked = eduItems.filter(i => i.checked).length;
    newScores[1].value = eduChecked >= 3 ? 5 : eduChecked >= 2 ? 4 : eduChecked >= 1 ? 3 : 0;

    const medItems = facilityGroups[2].items;
    const medChecked = medItems.filter(i => i.checked).length;
    newScores[2].value = medChecked >= 3 ? 5 : medChecked >= 2 ? 4 : medChecked >= 1 ? 3 : 0;

    const shopItems = facilityGroups[3].items;
    const shopChecked = shopItems.filter(i => i.checked).length;
    newScores[3].value = shopChecked >= 3 ? 5 : shopChecked >= 2 ? 4 : shopChecked >= 1 ? 3 : 0;

    newScores[4].value = newScores[4].value || 3;

    this.setData({ scoreItems: newScores });
    this.calculateScore(newScores);
    this.saveScores(newScores);
    setTimeout(() => this.drawRadar(), 50);
    wx.showToast({ title: '已根据设施自动评分', icon: 'success' });
  },
});
