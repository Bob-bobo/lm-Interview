Page({
  data: { area: '', level: 'mid', total: '' },
  onInput(e) { this.setData({ area: e.detail.value }); this.calc(); },
  setLevel(e) { this.setData({ level: e.currentTarget.dataset.v }); this.calc(); },
  calc() {
    const area = parseFloat(this.data.area) || 0;
    const ranges = { simple: [800, 1200], mid: [1500, 2500], luxury: [3000, 5000] };
    const [min, max] = ranges[this.data.level];
    if (area > 0) {
      const avg = (min + max) / 2;
      this.setData({ total: (area * avg / 10000).toFixed(1) });
    }
  },
});
