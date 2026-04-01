// pages/ai/chat/chat.js - AI对话（云开发版）
const { generateAIResponse, analyzeRequirement, matchHouses } = require('../../../utils/ai');
const { get, STORAGE_KEYS, add } = require('../../../utils/storage');
const { formatUnitPrice, getScoreColor } = require('../../../utils/format');

const knowledgeBase = {
  '市场趋势': '📊 当前房地产市场趋势分析：\n\n1. 政策层面：各地因城施策，多个城市已优化限购、降首付、降利率\n2. 利率环境：LPR持续下调，当前房贷利率处于历史低位\n3. 市场分化：核心城市核心区域价格相对坚挺，远郊区域调整较大\n4. 购房时机：对于刚需自住者，当前利率低、选择多，是比较好的入市窗口\n\n💡 建议：不要试图"抄底"，而应关注自身需求和还款能力。市场回归理性后，选择配套成熟、交通便利的房源更为稳妥。',
  '避坑指南': '⚠️ 买房十大避坑指南：\n\n1. 五证不全不买：预售许可证是最重要的，没有就是违规销售\n2. 口头承诺不信：所有承诺必须写入合同\n3. 学区房要核实：学区划片每年可能有变化\n4. 周边不利因素：查看是否有高架、垃圾站、工厂等\n5. 采光要实测：不同楼层、朝向采光差异很大\n6. 物业很重要：差的物业会让居住体验大打折扣\n7. 户型图不等于实际：实际得房率可能低于宣传\n8. 车位要确认：车位比、是否可购买都要了解\n9. 交房时间：期房要确认交房时间和违约责任\n10. 产权年限：注意土地使用剩余年限',
  '还款方式': '💰 两种还款方式对比：\n\n【等额本息】每月还款固定\n• 优点：月供压力稳定，前期负担较轻\n• 缺点：总利息较高\n• 适合：收入稳定、不想压力变动的上班族\n\n【等额本金】月供逐月递减\n• 优点：总利息更少\n• 缺点：前期还款压力较大\n• 适合：当前收入较高、希望省利息的购房者\n\n💡 简单总结：如果月收入足够承受前期高月供，选等额本金更省钱；否则选等额本息更安心。',
  '公积金贷款': '🏦 公积金贷款优势：\n\n【利率优势】\n• 首套公积金利率：2.85%\n• 首套商贷利率：约3.5-4.0%\n• 100万贷30年，公积金比商贷省约20-30万利息\n\n【使用限制】\n• 贷款额度上限（各地不同，一般为60-120万）\n• 需连续缴存公积金6-12个月以上\n\n【组合贷】\n• 公积金额度不够时，可以公积金+商贷组合\n• 兼顾低利率和充足额度',
  '学区房': '🏫 学区房选购指南：\n\n【关键要点】\n1. 核实对口学校：直接咨询教育局或学校\n2. 了解入学政策：关注落户年限要求\n3. 学区变动风险：学区划片可能调整\n4. 学位占用：确认前业主子女是否已毕业\n\n【性价比考量】\n• 学区溢价通常20-50%\n• 避免纯为学区买极小户型',
};

Page({
  data: { messages: [], inputText: '', scrollToId: '' },

  onInput(e) { this.setData({ inputText: e.detail.value }); },

  askQuestion(e) {
    this.setData({ inputText: e.currentTarget.dataset.text });
    this.sendMessage();
  },

  sendMessage() {
    const text = this.data.inputText.trim();
    if (!text) return;

    const userMsg = { role: 'user', content: text };
    const messages = [...this.data.messages, userMsg];
    this.setData({ messages, inputText: '', scrollToId: '' });

    setTimeout(async () => {
      const reply = this.getAIReply(text);
      const newMessages = [...messages, { role: 'bot', content: reply }];
      this.setData({ messages: newMessages, scrollToId: 'msg-bottom' });

      await add(STORAGE_KEYS.AI_HISTORY, { role: 'bot', content: reply, question: text });
    }, 600);

    this.setData({ scrollToId: 'msg-bottom' });
  },

  getAIReply(text) {
    for (const [key, value] of Object.entries(knowledgeBase)) {
      if (text.includes(key)) return value;
    }

    if (text.includes('推荐') || text.includes('匹配') || text.includes('适合') || text.includes('帮我找')) {
      // 使用本地缓存快速展示
      const houses = require('../../../utils/storage').getSync(STORAGE_KEYS.HOUSES);
      if (houses.length === 0) {
        return '📭 你还没有收藏任何房源，暂时无法为你推荐。\n\n先去"房源"页面添加一些感兴趣的房子，我就能帮你智能筛选了！';
      }
      const analysis = analyzeRequirement(text);
      const matched = matchHouses({
        budgetMin: analysis.budget && analysis.budget.min,
        budgetMax: analysis.budget && analysis.budget.max,
        preferredArea: analysis.area && analysis.area.value,
        preferredRooms: analysis.roomType,
        preferredDistricts: analysis.location,
      }).filter(h => h.matchScore > 20);

      if (matched.length === 0) {
        return `🔍 我分析了你的需求，但目前收藏的 ${houses.length} 套房源中没有完全匹配的。`;
      }

      let reply = `🎯 根据你的需求，我从${houses.length}套房源中筛选出${matched.length}套推荐：\n\n`;
      matched.slice(0, 5).forEach((h, i) => {
        reply += `${i + 1}. ${h.community || '未命名'} — 匹配度${h.matchScore}%\n   ${h.rooms || '?'}室${h.halls || 0}厅 ${h.area || '?'}㎡ ${h.totalPrice || '?'}万\n`;
        if (h.matchReasons.length > 0) reply += `   ✅ ${h.matchReasons.slice(0, 2).join('、')}\n\n`;
      });
      return reply;
    }

    const replies = [
      `感谢你的提问！关于"${text}"，建议多看多比较、关注目标区域价格走势、考虑自身还款能力。\n\n你可以试试告诉我你的具体需求（如预算、面积、区域），我能给出更有针对性的推荐！`,
      `这是个好问题！关于"${text}"：\n\n最重要的是明确核心需求排序——价格、面积、地段、学区、交通哪个最优先。\n\n💡 小技巧：去"房贷计算"页面算算月供，看看压力是否可控。`,
    ];
    return replies[Math.floor(Math.random() * replies.length)];
  },
});
