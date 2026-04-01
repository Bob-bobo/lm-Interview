// pages/guide/guide/guide.js - 购房攻略
const app = getApp();
const { getSync } = require('../../../utils/storage');

const CUSTOM_GUIDES_KEY = 'custom_guides';

// 预置攻略（不可编辑删除）
const BUILTIN_GUIDES = [
  {
    id: 'budget', icon: '💰', title: '预算规划指南',
    content: ['【首付准备】', '• 首套房首付最低20%（部分城市30%）', '• 二套房首付最低30%（部分城市40-70%）', '• 首付来源：积蓄+家庭支持+公积金提取', '', '【月供控制】', '• 建议月供 ≤ 家庭月收入的 30%', '• 极限月供 ≤ 家庭月收入的 50%', '• 需预留6个月以上月供作为应急储备', '', '【隐藏成本】', '• 契税：1%-3%（根据面积和套数）', '• 维修基金：60-200元/㎡', '• 中介费：1%-3%', '• 装修费：1000-3000元/㎡', '• 物业费：2-8元/㎡/月'],
  },
  {
    id: 'choose', icon: '🔍', title: '选房技巧',
    content: ['【核心原则】', '• 明确哪些是必须项，哪些是加分项', '• 不要追求完美，找到最适合的', '• 不要被样板间迷惑，看实际房源', '', '【看房检查清单】', '• 采光：白天去两次（上午+下午）', '• 噪音：关窗听环境噪音', '• 通风：检查窗户朝向和通风效果', '• 水压：打开水龙头检查水压', '• 漏水：查看天花板、墙角有无水渍', '• 电梯：高峰期测试等梯时间', '', '【小区考察】', '• 物业管理水平', '• 车位配比和价格', '• 绿化率和公共设施', '• 周边生活配套'],
  },
  {
    id: 'contract', icon: '📋', title: '合同注意事项',
    content: ['【合同必看】', '• 房屋面积和公摊比例', '• 交房时间和违约责任', '• 产权年限和性质', '• 配套设施承诺（写入合同）', '• 付款方式和时间节点', '', '【重要条款】', '• 逾期交房的违约金比例', '• 面积差异处理方式', '• 产权证办理时限', '• 退房条件和流程', '', '【签约提醒】', '• 不签阴阳合同', '• 口头承诺必须写进合同', '• 保留所有票据和凭证', '• 重要文件拍照备份'],
  },
  {
    id: 'loan', icon: '🏦', title: '贷款全攻略',
    content: ['【商贷流程】', '1. 提交贷款申请', '2. 银行审批（1-2周）', '3. 签订借款合同', '4. 办理抵押登记', '5. 银行放款', '', '【公积金贷款】', '• 利率更低（首套2.85%）', '• 需连续缴存6-12个月', '• 额度因城市而异（60-120万）', '• 可以和商贷组合使用', '', '【省利息技巧】', '• 优先使用公积金', '• 选择较短的贷款期限', '• 有能力的话等额本金更省', '• 利率下降时可申请转为LPR'],
  },
];

Page({
  data: {
    expandedId: '',
    steps: [
      { title: '明确需求', desc: '确定预算、区域、户型等核心需求' },
      { title: '准备资金', desc: '首付资金+税费+装修预留，月供不超过收入50%' },
      { title: '看房选房', desc: '线上线下结合，至少看10套以上做对比' },
      { title: '核实资质', desc: '查五证、核实产权、了解学区政策' },
      { title: '签订合同', desc: '仔细阅读条款，注意违约责任和交房时间' },
      { title: '办理贷款', desc: '准备资料，选择还款方式，关注利率变化' },
      { title: '缴纳税费', desc: '契税、维修基金等，了解各项税费标准' },
      { title: '收房验收', desc: '检查房屋质量，核对面积，交接物业' },
      { title: '装修入住', desc: '装修预算规划，选择靠谱装修公司' },
    ],
    guides: [],        // 预置攻略
    customGuides: [],  // 用户自定义攻略
    checklist: [
      { text: '确认购房预算和首付来源', checked: false },
      { text: '查询个人征信报告', checked: false },
      { text: '了解目标区域房价行情', checked: false },
      { text: '确定核心需求（户型/面积/区域）', checked: false },
      { text: '实地看房至少5套以上', checked: false },
      { text: '查验房源五证', checked: false },
      { text: '核实学区政策（如需要）', checked: false },
      { text: '对比至少3家银行贷款利率', checked: false },
      { text: '计算月供和总还款额', checked: false },
      { text: '准备好首付资金和税费', checked: false },
      { text: '仔细审阅购房合同', checked: false },
      { text: '了解收房验收标准', checked: false },
    ],
    checkedCount: 0,
    progressPercent: 0,
    showAddModal: false,
    // 新增攻略表单
    newGuide: { title: '', icon: '📝', content: '' },
    iconOptions: ['📝', '💡', '⚠️', '🏠', '🚗', '🏥', '🏫', '🛒', '🌳', '🔧', '💼', '📈'],
    iconSelected: '📝',
  },

  onShow() {
    // 每次显示时刷新自定义攻略
    this.loadCustomGuides();
    this.loadChecklist();
  },

  onReady() {
    this.setData({ guides: BUILTIN_GUIDES });
  },

  // ========== 自定义攻略 ==========

  loadCustomGuides() {
    try {
      const raw = wx.getStorageSync(CUSTOM_GUIDES_KEY) || '[]';
      const customGuides = JSON.parse(raw);
      this.setData({ customGuides });
    } catch (e) {
      this.setData({ customGuides: [] });
    }
  },

  saveCustomGuides() {
    wx.setStorageSync(CUSTOM_GUIDES_KEY, JSON.stringify(this.data.customGuides));
  },

  showAddForm() {
    this.setData({
      showAddModal: true,
      newGuide: { title: '', icon: '📝', content: '' },
      iconSelected: '📝',
    });
  },

  hideAddForm() {
    this.setData({ showAddModal: false });
  },

  // 点击遮罩关闭（只响应直接点击遮罩空白区域，不响应弹窗内容区的冒泡）
  onMaskTap(e) {
    // 使用 catchtap + 判断 e.target.id 来确保只有点击遮罩本身才关闭
    if (e.target.id === 'modalMask') {
      this.hideAddForm();
    }
  },

  onTitleInput(e) {
    this.setData({ 'newGuide.title': e.detail.value });
  },

  onContentInput(e) {
    this.setData({ 'newGuide.content': e.detail.value });
  },

  selectIcon(e) {
    const { icon } = e.currentTarget.dataset;
    this.setData({ iconSelected: icon, 'newGuide.icon': icon });
  },

  addGuide() {
    const { newGuide, customGuides } = this.data;
    const title = newGuide.title.trim();
    const content = newGuide.content.trim();

    if (!title) {
      return wx.showToast({ title: '请输入攻略标题', icon: 'none' });
    }
    if (!content) {
      return wx.showToast({ title: '请输入攻略内容', icon: 'none' });
    }

    // 将换行符转为数组
    const contentLines = content.split('\n').filter(line => line.trim());

    const guide = {
      id: 'custom_' + Date.now(),
      icon: newGuide.icon,
      title,
      content: contentLines,
      isCustom: true,
      createTime: Date.now(),
    };

    customGuides.unshift(guide);
    this.setData({ customGuides, showAddModal: false });
    this.saveCustomGuides();
    wx.showToast({ title: '添加成功', icon: 'success' });
  },

  deleteGuide(e) {
    const { id } = e.currentTarget.dataset;
    wx.showModal({
      title: '删除攻略',
      content: '确定要删除这条攻略吗？',
      confirmColor: '#f5222d',
      success: (res) => {
        if (res.confirm) {
          const customGuides = this.data.customGuides.filter(g => g.id !== id);
          this.setData({ customGuides });
          this.saveCustomGuides();
          wx.showToast({ title: '已删除', icon: 'success' });
        }
      },
    });
  },

  editGuide(e) {
    const { id } = e.currentTarget.dataset;
    const guide = this.data.customGuides.find(g => g.id === id);
    if (!guide) return;

    wx.showModal({
      title: '编辑攻略标题',
      editable: true,
      placeholderText: guide.title,
      success: (res) => {
        if (res.confirm && res.content.trim()) {
          const customGuides = [...this.data.customGuides];
          const idx = customGuides.findIndex(g => g.id === id);
          if (idx !== -1) {
            customGuides[idx].title = res.content.trim();
            this.setData({ customGuides });
            this.saveCustomGuides();
            wx.showToast({ title: '已更新', icon: 'success' });
          }
        }
      },
    });
  },

  // ========== 攻略展开/收起 ==========

  toggleGuide(e) {
    const id = e.currentTarget.dataset.id;
    this.setData({ expandedId: this.data.expandedId === id ? '' : id });
  },

  // ========== 清单 ==========

  loadChecklist() {
    try {
      const saved = wx.getStorageSync('guide_checklist');
      if (saved) {
        const checklist = JSON.parse(saved);
        const checkedCount = checklist.filter(i => i.checked).length;
        this.setData({
          checklist,
          checkedCount,
          progressPercent: Math.round(checkedCount / checklist.length * 100),
        });
      }
    } catch (e) {
      // ignore
    }
  },

  saveChecklist() {
    wx.setStorageSync('guide_checklist', JSON.stringify(this.data.checklist));
  },

  toggleCheck(e) {
    const index = e.currentTarget.dataset.index;
    const checklist = [...this.data.checklist];
    checklist[index].checked = !checklist[index].checked;
    const checkedCount = checklist.filter(i => i.checked).length;
    this.setData({
      checklist,
      checkedCount,
      progressPercent: Math.round(checkedCount / checklist.length * 100),
    });
    this.saveChecklist();
  },
});
