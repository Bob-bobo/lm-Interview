/**
 * utils/format.js - 格式化工具函数
 */

/**
 * 格式化价格（万元）
 */
const formatPrice = (price, unit = '万') => {
  if (price == null) return '--';
  return `${parseFloat(price.toFixed(2))}${unit}`;
};

/**
 * 格式化面积
 */
const formatArea = (area) => {
  if (area == null) return '--';
  return `${parseFloat(area.toFixed(2))}㎡`;
};

/**
 * 格式化金额（元）
 */
const formatMoney = (amount) => {
  if (amount == null) return '--';
  if (amount >= 10000) {
    return `${(amount / 10000).toFixed(2)}万`;
  }
  return `${amount.toFixed(2)}元`;
};

/**
 * 格式化日期
 */
const formatDate = (timestamp) => {
  if (!timestamp) return '--';
  const date = new Date(timestamp);
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * 格式化日期时间
 */
const formatDateTime = (timestamp) => {
  if (!timestamp) return '--';
  const date = new Date(timestamp);
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  const hour = date.getHours().toString().padStart(2, '0');
  const minute = date.getMinutes().toString().padStart(2, '0');
  return `${year}-${month}-${day} ${hour}:${minute}`;
};

/**
 * 格式化月份
 */
const formatMonth = (month) => {
  const years = Math.floor(month / 12);
  const months = month % 12;
  if (years > 0 && months > 0) {
    return `${years}年${months}个月`;
  } else if (years > 0) {
    return `${years}年`;
  }
  return `${months}个月`;
};

/**
 * 计算时间差（相对时间）
 */
const timeAgo = (timestamp) => {
  const now = Date.now();
  const diff = now - timestamp;
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;

  if (diff < minute) return '刚刚';
  if (diff < hour) return `${Math.floor(diff / minute)}分钟前`;
  if (diff < day) return `${Math.floor(diff / hour)}小时前`;
  if (diff < 30 * day) return `${Math.floor(diff / day)}天前`;
  return formatDate(timestamp);
};

/**
 * 格式化单价
 */
const formatUnitPrice = (totalPrice, area) => {
  if (!totalPrice || !area) return '--';
  const unitPrice = (totalPrice * 10000) / area;
  return `${Math.round(unitPrice)}元/㎡`;
};

/**
 * 截取文字
 */
const truncate = (text, maxLen = 20) => {
  if (!text) return '';
  return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
};

/**
 * 匹配度颜色
 */
const getScoreColor = (score) => {
  if (score >= 80) return '#52c41a';
  if (score >= 60) return '#1890ff';
  if (score >= 40) return '#faad14';
  return '#f5222d';
};

/**
 * 匹配度文字
 */
const getScoreLabel = (score) => {
  if (score >= 80) return '非常匹配';
  if (score >= 60) return '比较匹配';
  if (score >= 40) return '一般';
  return '匹配度低';
};

module.exports = {
  formatPrice,
  formatArea,
  formatMoney,
  formatDate,
  formatDateTime,
  formatMonth,
  timeAgo,
  formatUnitPrice,
  truncate,
  getScoreColor,
  getScoreLabel,
};
