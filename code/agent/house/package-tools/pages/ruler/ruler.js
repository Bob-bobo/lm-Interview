// package-tools/pages/ruler/ruler.js
Page({
  data: { area: '', ratio: '80', innerArea: '--', sharedArea: '--' },
  onInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ [field]: e.detail.value });
    const area = parseFloat(this.data.area) || 0;
    const ratio = parseFloat(field === 'ratio' ? e.detail.value : this.data.ratio) || 0;
    if (area > 0 && ratio > 0) {
      this.setData({
        innerArea: (area * ratio / 100).toFixed(2),
        sharedArea: (area * (1 - ratio / 100)).toFixed(2),
      });
    }
  },
});
