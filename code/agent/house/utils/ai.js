/**
 * utils/ai.js - AI智能分析引擎（云开发版）
 * 分析用户需求，匹配最佳房源，提供购房建议
 */

const { get, getSync, STORAGE_KEYS } = require('./storage');

/**
 * 获取用户需求画像（同步读本地缓存）
 */
const getUserProfile = () => {
  const profiles = getSync(STORAGE_KEYS.USER_PROFILE);
  return profiles.length > 0 ? profiles[0] : null;
};

/**
 * 保存/更新用户需求画像
 */
const saveUserProfile = async (profile) => {
  const { get: doGet, add, update } = require('./storage');
  const list = await doGet(STORAGE_KEYS.USER_PROFILE);
  if (list.length > 0) {
    await update(STORAGE_KEYS.USER_PROFILE, list[0].id, {
      ...profile,
      updateTime: Date.now(),
    });
  } else {
    await add(STORAGE_KEYS.USER_PROFILE, {
      ...profile,
      createTime: Date.now(),
      updateTime: Date.now(),
    });
  }
};

/**
 * AI 需求分析 - 根据用户描述分析购房需求
 */
const analyzeRequirement = (userInput) => {
  const result = {
    budget: null, area: null, location: null, roomType: null,
    priorities: [], suggestions: [], keywords: [],
  };

  const rules = [
    { keywords: ['预算', '价格', '总价', '首付', '万', '万以内', '万左右'], type: 'budget', parse: parseBudget },
    { keywords: ['面积', '平方', '平米', '㎡', '几平'], type: 'area', parse: parseArea },
    { keywords: ['朝阳', '海淀', '西城', '东城', '丰台', '通州', '昌平', '大兴', '顺义', '房山', '区域', '地段', '位置', '附近'], type: 'location', parse: parseLocation },
    { keywords: ['一居', '两居', '三居', '四居', '户型', '几室', '卧室', '室'], type: 'roomType', parse: parseRoomType },
    { keywords: ['学区', '学校', '教育', '小学', '中学'], type: 'priority', value: '学区' },
    { keywords: ['地铁', '交通', '通勤', '上班'], type: 'priority', value: '交通便利' },
    { keywords: ['商场', '购物', '超市', '商业'], type: 'priority', value: '商业配套' },
    { keywords: ['医院', '医疗', '看病'], type: 'priority', value: '医疗配套' },
    { keywords: ['公园', '绿化', '环境'], type: 'priority', value: '居住环境' },
    { keywords: ['投资', '升值', '回报', '出租'], type: 'priority', value: '投资价值' },
    { keywords: ['自住', '刚需', '首套', '结婚', '落户'], type: 'priority', value: '自住需求' },
    { keywords: ['南北通透', '朝南', '采光', '通风'], type: 'priority', value: '房屋朝向' },
  ];

  rules.forEach(rule => {
    rule.keywords.forEach(keyword => {
      if (userInput.includes(keyword)) {
        result.keywords.push(keyword);
        if (rule.parse) {
          const parsed = rule.parse(userInput, keyword);
          if (parsed) result[rule.type] = parsed;
        } else if (rule.value) {
          if (!result.priorities.includes(rule.value)) {
            result.priorities.push(rule.value);
          }
        }
      }
    });
  });

  result.suggestions = generateSuggestions(result);
  return result;
};

const parseBudget = (text) => {
  const patterns = [
    /(\d+)\s*万[以左到上下]?[右内]?/g,
    /预算\s*[：:约大概]?\s*(\d+)\s*万/g,
    /(\d+)[-~到至](\d+)\s*万/g,
  ];
  for (const pattern of patterns) {
    const match = pattern.exec(text);
    if (match) {
      if (match[2]) return { min: parseInt(match[1]), max: parseInt(match[2]), unit: '万' };
      const val = parseInt(match[1]);
      return { min: val * 0.8, max: val * 1.2, unit: '万', target: val };
    }
  }
  return null;
};

const parseArea = (text) => {
  const match = text.match(/(\d+)\s*[平方平㎡平米]/);
  return match ? { value: parseInt(match[1]), unit: '㎡' } : null;
};

const parseLocation = (text) => {
  const areas = ['朝阳', '海淀', '西城', '东城', '丰台', '通州', '昌平', '大兴', '顺义', '房山', '石景山', '门头沟'];
  const found = areas.filter(area => text.includes(area));
  return found.length > 0 ? found : null;
};

const parseRoomType = (text) => {
  const match = text.match(/([一二三四五])\s*[居室室]/);
  if (match) {
    const map = { '一': 1, '二': 2, '三': 3, '四': 4, '五': 5 };
    return map[match[1]] || null;
  }
  return null;
};

const generateSuggestions = (analysis) => {
  const suggestions = [];
  if (analysis.budget) {
    const target = analysis.budget.target || ((analysis.budget.min + analysis.budget.max) / 2);
    suggestions.push(`根据您的预算，建议关注总价在${Math.round(analysis.budget.min)}-${Math.round(analysis.budget.max)}万区间的房源`);
  }
  if (analysis.area && analysis.budget) {
    const target = analysis.budget.target || ((analysis.budget.min + analysis.budget.max) / 2);
    const unitPrice = (target * 10000) / analysis.area.value;
    suggestions.push(`${analysis.area.value}㎡的均价参考约为${Math.round(unitPrice)}元/㎡，请根据目标区域实际行情判断`);
  }
  if (analysis.priorities.includes('学区')) suggestions.push('学区房建议重点关注：①对口小学排名 ②学区政策变化 ③落户时间要求');
  if (analysis.priorities.includes('投资价值')) suggestions.push('投资购房建议关注：①地铁规划 ②区域发展规划 ③租金回报率 ④空置率');
  if (analysis.priorities.includes('交通便利')) suggestions.push('通勤建议：地铁房步行800米内最佳，公交线路3条以上为优');
  if (analysis.priorities.includes('自住需求')) suggestions.push('自住建议：优先考虑采光通风、小区物业、周边生活配套是否完善');
  if (suggestions.length === 0) suggestions.push('建议您补充更多需求信息，如预算范围、面积需求、目标区域、户型偏好等，我能为您更精准地匹配房源');
  return suggestions;
};

/**
 * 房源匹配评分 - 异步版
 */
const matchHouses = async (profile) => {
  if (!profile) return [];
  const houses = await get(STORAGE_KEYS.HOUSES);
  const scored = houses.map(house => {
    let score = 0;
    const reasons = [];
    if (profile.budgetMin && profile.budgetMax) {
      if (house.totalPrice >= profile.budgetMin && house.totalPrice <= profile.budgetMax) {
        score += 30; reasons.push('预算范围内');
      } else if (house.totalPrice < profile.budgetMin) {
        score += 20; reasons.push('低于预算（可能面积较小）');
      } else if (house.totalPrice <= profile.budgetMax * 1.1) {
        score += 15; reasons.push('略超预算');
      } else {
        reasons.push('超出预算');
      }
    }
    if (profile.areaMin && profile.areaMax) {
      if (house.area >= profile.areaMin && house.area <= profile.areaMax) {
        score += 20; reasons.push('面积匹配');
      } else if (house.area >= profile.areaMin * 0.9) {
        score += 15; reasons.push('面积接近');
      }
    } else if (profile.preferredArea && house.area) {
      const diff = Math.abs(house.area - profile.preferredArea) / profile.preferredArea;
      if (diff < 0.1) { score += 20; reasons.push('面积匹配'); }
      else if (diff < 0.2) { score += 12; reasons.push('面积接近'); }
    }
    if (profile.preferredRooms && house.rooms) {
      if (house.rooms === profile.preferredRooms) { score += 15; reasons.push('户型匹配'); }
      else if (Math.abs(house.rooms - profile.preferredRooms) === 1) { score += 8; reasons.push('户型接近'); }
    }
    if (profile.preferredDistricts && house.district) {
      if (profile.preferredDistricts.includes(house.district)) { score += 15; reasons.push('区域匹配'); }
      else { score += 3; reasons.push('非目标区域'); }
    }
    if (house.orientation) {
      const goodOrientations = ['南', '南北', '东南', '西南', '南北通透'];
      if (goodOrientations.some(o => house.orientation.includes(o))) { score += 10; reasons.push('朝向优秀'); }
    }
    if (house.floor && house.totalFloor) {
      const floorRatio = house.floor / house.totalFloor;
      if (floorRatio >= 0.3 && floorRatio <= 0.7) { score += 5; reasons.push('楼层适中'); }
    }
    if (house.decoration) {
      if (['精装', '豪装'].some(d => house.decoration.includes(d))) { score += 5; reasons.push('装修精良'); }
    }
    return { ...house, matchScore: Math.min(score, 100), matchReasons: reasons };
  });
  scored.sort((a, b) => b.matchScore - a.matchScore);
  return scored;
};

/**
 * 价格趋势分析（异步版）
 */
const analyzePriceTrend = async (houseId) => {
  const histories = await get(STORAGE_KEYS.PRICE_HISTORY);
  const houseHistories = histories.filter(h => h.houseId === houseId);

  if (houseHistories.length < 2) {
    return { trend: 'insufficient', message: '数据不足，至少需要2条价格记录才能分析趋势' };
  }

  const sorted = [...houseHistories].sort((a, b) => a.date - b.date);
  const n = sorted.length;
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
  sorted.forEach((item, index) => {
    sumX += index; sumY += item.price; sumXY += index * item.price; sumX2 += index * index;
  });
  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const avgPrice = sumY / n;
  const changeRate = slope / avgPrice * 100;
  let trend, message, suggestion;
  if (changeRate > 2) {
    trend = 'up'; message = `价格呈上涨趋势，月均涨幅约${changeRate.toFixed(1)}%`; suggestion = '价格在上涨中，建议尽快决策或持续关注';
  } else if (changeRate < -2) {
    trend = 'down'; message = `价格呈下降趋势，月均跌幅约${Math.abs(changeRate).toFixed(1)}%`; suggestion = '价格在下跌中，可以观望等待更好的时机';
  } else {
    trend = 'stable'; message = `价格相对稳定，月均波动约${Math.abs(changeRate).toFixed(1)}%`; suggestion = '价格稳定，是比较好的入手时机';
  }
  const prices = sorted.map(s => s.price);
  const maxPrice = Math.max(...prices);
  const minPrice = Math.min(...prices);
  const currentPrice = sorted[sorted.length - 1].price;
  const predictedPrice = currentPrice + slope;
  const predictedChange = ((predictedPrice - currentPrice) / currentPrice * 100).toFixed(2);

  return {
    trend, message, suggestion, currentPrice, maxPrice, minPrice,
    avgPrice: parseFloat(avgPrice.toFixed(2)),
    changeRate: parseFloat(changeRate.toFixed(2)),
    predictedPrice: parseFloat(predictedPrice.toFixed(2)),
    predictedChange, dataPoints: sorted, dataLength: n,
  };
};

/**
 * 生成AI对话回复（同步版，用传入的houses做简单匹配）
 */
const generateAIResponse = (userInput, context = {}) => {
  const analysis = analyzeRequirement(userInput);
  let response = '';

  if (analysis.keywords.length === 0) {
    response = '我还没理解您的具体需求 😅 您可以告诉我：\n';
    response += '• 预算范围（如：预算300万左右）\n• 面积需求（如：想要90平米）\n';
    response += '• 区域偏好（如：在朝阳或海淀）\n• 户型偏好（如：三居室）\n• 最看重什么（如：学区、地铁、环境）';
    return { response, analysis };
  }

  response = '📋 我已分析您的需求：\n\n';
  if (analysis.budget) {
    const target = analysis.budget.target || Math.round((analysis.budget.min + analysis.budget.max) / 2);
    response += `💰 预算：${target}万左右\n`;
  }
  if (analysis.area) response += `📐 面积：${analysis.area.value}㎡\n`;
  if (analysis.location) response += `📍 区域：${analysis.location.join('、')}\n`;
  if (analysis.roomType) response += `🏠 户型：${analysis.roomType}居室\n`;
  if (analysis.priorities.length > 0) response += `⭐ 重点关注：${analysis.priorities.join('、')}\n`;

  if (context.houses && context.houses.length > 0) {
    const profile = {
      budgetMin: analysis.budget && analysis.budget.min,
      budgetMax: analysis.budget && analysis.budget.max,
      preferredArea: analysis.area && analysis.area.value,
      preferredRooms: analysis.roomType,
      preferredDistricts: analysis.location,
    };
    const houses = context.houses;
    const scored = houses.map(house => {
      let score = 0; const reasons = [];
      if (profile.budgetMin && profile.budgetMax && house.totalPrice >= profile.budgetMin && house.totalPrice <= profile.budgetMax) { score += 30; reasons.push('预算范围内'); }
      if (profile.preferredRooms && house.rooms === profile.preferredRooms) { score += 15; reasons.push('户型匹配'); }
      if (profile.preferredDistricts && house.district && profile.preferredDistricts.includes(house.district)) { score += 15; reasons.push('区域匹配'); }
      return { ...house, matchScore: Math.min(score, 100), matchReasons: reasons };
    }).sort((a, b) => b.matchScore - a.matchScore).slice(0, 3);

    if (scored.length > 0 && scored[0].matchScore > 0) {
      response += `\n🎯 为您匹配到 ${scored.length} 套推荐房源：\n\n`;
      scored.forEach((house, idx) => {
        response += `${idx + 1}. ${house.name || house.community || '房源'} - 匹配度${house.matchScore}%\n`;
        response += `   ${house.rooms || '?'}居室 ${house.area || '?'}㎡ ${house.totalPrice || '?'}万\n`;
        if (house.matchReasons.length > 0) response += `   ✅ ${house.matchReasons.slice(0, 2).join('、')}\n`;
        response += '\n';
      });
    } else {
      response += '\n📭 暂未找到匹配的房源，建议您先添加一些房源记录。\n';
    }
  }

  if (analysis.suggestions.length > 0) {
    response += '\n💡 建议：\n';
    analysis.suggestions.slice(0, 3).forEach(s => { response += `• ${s}\n`; });
  }

  return { response, analysis };
};

module.exports = {
  analyzeRequirement, matchHouses, analyzePriceTrend,
  generateAIResponse, getUserProfile, saveUserProfile,
};
