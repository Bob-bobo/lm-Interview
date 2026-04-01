// pages/calc/mortgage/mortgage.js - 房贷计算器
const { calcEqualPayment, calcEqualPrincipal, calcCombinedLoan, assessAffordability } = require('../../../utils/calc');
const { formatMoney } = require('../../../utils/format');

Page({
  data: {
    method: 'equal_payment',
    totalPrice: '',
    downPaymentRatio: 30,
    downPayment: '0.00',
    loanAmount: '0.00',
    loanTerm: 30,
    rate: '3.5',
    termOptions: [5, 10, 15, 20, 25, 30],
    // 组合贷
    fundAmount: '',
    fundRate: '3.1',
    commercialAmount: '',
    commercialRate: '3.5',
    // 结果
    result: null,
    showSchedule: false,
    principalPercent: 0,
    interestPercent: 0,
    // 还款能力
    monthlyIncome: '',
    affordability: {},
  },

  onLoad(options) {
    // 从房源详情页跳转时自动填充
    if (options.price) {
      this.setData({ totalPrice: options.price });
      this.calcDownPayment();
    }
  },

  onInput(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({ [field]: e.detail.value });
    if (field === 'totalPrice') this.calcDownPayment();
    if (field === 'downPaymentRatio') this.calcDownPayment();
    if (field === 'monthlyIncome') this.evaluateAffordability();
    if (field === 'fundAmount') this.calcCommercialAmount();
  },

  calcDownPayment() {
    const totalPrice = parseFloat(this.data.totalPrice) || 0;
    const ratio = this.data.downPaymentRatio;
    const downPayment = totalPrice * ratio / 100;
    const loanAmount = totalPrice - downPayment;
    this.setData({
      downPayment: downPayment.toFixed(2),
      loanAmount: loanAmount.toFixed(2),
    });
  },

  calcCommercialAmount() {
    const loanAmount = parseFloat(this.data.loanAmount) || 0;
    const fundAmount = parseFloat(this.data.fundAmount) || 0;
    const commercialAmount = Math.max(0, loanAmount - fundAmount);
    this.setData({ commercialAmount: commercialAmount.toFixed(2) });
  },

  switchMethod(e) {
    const method = e.currentTarget.dataset.method;
    this.setData({
      method,
      result: null,
      showSchedule: false,
    });
    if (method === 'combined') this.calcCommercialAmount();
  },

  onRatioChange(e) {
    this.setData({ downPaymentRatio: parseInt(e.detail.value) });
    this.calcDownPayment();
  },

  setRatio(e) {
    const value = parseInt(e.currentTarget.dataset.value);
    this.setData({ downPaymentRatio: value });
    this.calcDownPayment();
  },

  setTerm(e) {
    this.setData({ loanTerm: parseInt(e.currentTarget.dataset.value) });
  },

  setRate(e) {
    this.setData({ rate: e.currentTarget.dataset.value });
  },

  calculate() {
    const loanAmount = parseFloat(this.data.loanAmount);
    const rate = parseFloat(this.data.rate);
    const months = this.data.loanTerm * 12;

    if (!loanAmount || loanAmount <= 0) {
      return wx.showToast({ title: '请输入有效的房屋总价', icon: 'none' });
    }
    if (!rate || rate <= 0) {
      return wx.showToast({ title: '请输入有效的年利率', icon: 'none' });
    }

    let result;

    if (this.data.method === 'combined') {
      const fundAmount = parseFloat(this.data.fundAmount);
      const fundRate = parseFloat(this.data.fundRate);
      const commercialRate = parseFloat(this.data.commercialRate);

      if (!fundAmount || fundAmount <= 0) {
        return wx.showToast({ title: '请输入公积金贷款金额', icon: 'none' });
      }

      result = calcCombinedLoan({
        fundAmount, fundRate: fundRate || 3.1, fundMonths: months,
        commercialAmount: parseFloat(this.data.commercialAmount) || 0,
        commercialRate: commercialRate || 3.5, commercialMonths: months,
      });
    } else if (this.data.method === 'equal_principal') {
      result = calcEqualPrincipal(loanAmount, rate, months);
    } else {
      result = calcEqualPayment(loanAmount, rate, months);
    }

    // 格式化结果
    const totalPaymentWan = result.totalPayment / 10000;
    const totalInterestWan = result.totalInterest / 10000;
    const totalLoanWan = loanAmount;
    const principalPercent = Math.round(totalLoanWan / totalPaymentWan * 100);
    const interestPercent = 100 - principalPercent;

    const formatted = {
      ...result,
      monthlyPayment: result.monthlyPayment ? result.monthlyPayment.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : null,
      firstMonthPaymentStr: result.firstMonthPayment ? result.firstMonthPayment.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : null,
      lastMonthPaymentStr: result.lastMonthPayment ? result.lastMonthPayment.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : null,
      monthlyDecreaseStr: result.monthlyDecrease ? result.monthlyDecrease.toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : null,
      totalPaymentStr: totalPaymentWan.toFixed(2),
      totalInterestStr: totalInterestWan.toFixed(2),
    };

    this.setData({
      result: formatted,
      principalPercent,
      interestPercent,
    });

    // 如果已填月收入，自动评估
    if (this.data.monthlyIncome) {
      this.evaluateAffordability();
    }

    wx.showToast({ title: '计算完成', icon: 'success' });
  },

  evaluateAffordability() {
    const income = parseFloat(this.data.monthlyIncome);
    const payment = this.data.result && this.data.result.monthlyPayment;
    if (!income || !payment) return;

    this.setData({
      affordability: assessAffordability(income, payment),
    });
  },

  toggleSchedule() {
    this.setData({ showSchedule: !this.data.showSchedule });
  },
});
