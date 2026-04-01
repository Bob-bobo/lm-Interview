// pages/reminder/reminder/reminder.js - 提醒管理（云开发版）
const { get, add, remove, STORAGE_KEYS } = require('../../../utils/storage');

Page({
  data: {
    reminders: [],
    templates: [
      { icon: '🏦', title: '贷款还款日', desc: '每月固定日期还款提醒' },
      { icon: '📋', title: '合同到期', desc: '购房合同/租赁合同到期' },
      { icon: '🏠', title: '交房验收', desc: '新房/二手房交房日期' },
      { icon: '📄', title: '办证日期', desc: '房产证/不动产权证办理' },
      { icon: '💰', title: '税费缴纳', desc: '契税/物业费等缴纳截止日' },
      { icon: '🔧', title: '装修完工', desc: '装修工程验收日期' },
    ],
  },

  onShow() { this.loadReminders(); },

  async loadReminders() {
    const reminders = (await get(STORAGE_KEYS.REMINDERS)).map(r => {
      const date = new Date(r.remindDate);
      return { ...r, dateStr: `${date.getMonth() + 1}月${date.getDate()}日`, timeStr: r.remindTime || '' };
    });
    this.setData({ reminders });
  },

  addReminder() {
    const that = this;
    wx.showModal({
      title: '添加提醒', editable: true, placeholderText: '输入提醒内容，如：1月15日还房贷',
      async success(res) {
        if (res.confirm && res.content) {
          const nextMonth = new Date(); nextMonth.setMonth(nextMonth.getMonth() + 1, 15);
          await add(STORAGE_KEYS.REMINDERS, { title: res.content, remindDate: nextMonth.getTime(), remindTime: '10:00', note: '', done: false });
          that.loadReminders();
          wx.showToast({ title: '已添加', icon: 'success' });
        }
      },
    });
  },

  addFromTemplate(e) {
    const template = e.currentTarget.dataset.template;
    const that = this;
    wx.showModal({
      title: template.title, editable: true, placeholderText: '输入具体日期（如：2026-05-15）',
      async success(res) {
        if (res.confirm) {
          let remindDate;
          if (res.content) remindDate = new Date(res.content).getTime();
          if (!remindDate || isNaN(remindDate)) { const next = new Date(); next.setDate(next.getDate() + 30); remindDate = next.getTime(); }
          await add(STORAGE_KEYS.REMINDERS, { title: template.title, remindDate, remindTime: '09:00', note: template.desc, done: false });
          that.loadReminders();
          wx.showToast({ title: '已添加', icon: 'success' });
        }
      },
    });
  },

  deleteReminder(e) {
    const id = e.currentTarget.dataset.id;
    const that = this;
    wx.showModal({
      title: '删除提醒', content: '确定删除这条提醒吗？',
      async success(res) {
        if (res.confirm) { await remove(STORAGE_KEYS.REMINDERS, id); that.loadReminders(); }
      },
    });
  },
});
