// pages/ai/analyze/analyze.js - AI智能分析（云开发版）
const { analyzeRequirement, matchHouses, saveUserProfile } = require('../../../utils/ai');
const { get, STORAGE_KEYS } = require('../../../utils/storage');
const { formatUnitPrice, getScoreColor } = require('../../../utils/format');

Page({
  data: { userInput: '', analysis: null, matchedHouses: [], analyzed: false },

  onInput(e) { this.setData({ userInput: e.detail.value }); },
  useQuickNeed(e) { this.setData({ userInput: e.currentTarget.dataset.text }); },

  async analyze() {
    const { userInput } = this.data;
    if (!userInput.trim()) return wx.showToast({ title: '请描述您的需求', icon: 'none' });

    wx.showLoading({ title: 'AI分析中...' });

    setTimeout(async () => {
      const analysis = analyzeRequirement(userInput);
      const houses = await get(STORAGE_KEYS.HOUSES);

      const profile = {
        budgetMin: analysis.budget && analysis.budget.min,
        budgetMax: analysis.budget && analysis.budget.max,
        preferredArea: analysis.area && analysis.area.value,
        preferredRooms: analysis.roomType,
        preferredDistricts: analysis.location,
      };

      const matched = matchHouses(profile).filter(h => h.matchScore > 20).map(h => ({
        ...h,
        unitPrice: formatUnitPrice(h.totalPrice, h.area),
        scoreColor: getScoreColor(h.matchScore),
      }));

      if (analysis.budget || analysis.area || analysis.priorities.length > 0) {
        saveUserProfile({
          budgetMin: analysis.budget && analysis.budget.min,
          budgetMax: analysis.budget && analysis.budget.max,
          preferredArea: analysis.area && analysis.area.value,
          preferredRooms: analysis.roomType,
          preferredDistricts: analysis.location,
          priorities: analysis.priorities,
          lastInput: userInput,
        });
      }

      wx.hideLoading();
      this.setData({ analysis, matchedHouses: matched, analyzed: true });
    }, 800);
  },

  goToDetail(e) {
    wx.navigateTo({ url: `/pages/house/detail/detail?id=${e.currentTarget.dataset.id}` });
  },

  onShareAppMessage() {
    return { title: '买房助手 - AI智能选房', path: '/pages/ai/analyze/analyze' };
  },
});
