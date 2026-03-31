/**
 * utils/calc.js - 房贷计算引擎
 * 支持等额本息、等额本金两种还款方式
 */

/**
 * 等额本息（每月还款额固定）
 * 公式：M = P × r × (1+r)^n / [(1+r)^n - 1]
 * @param {number} principal - 贷款总额（万元）
 * @param {number} annualRate - 年利率（如 4.2 表示 4.2%）
 * @param {number} months - 贷款月数
 * @returns {object} 计算结果
 */
const calcEqualPayment = (principal, annualRate, months) => {
  const P = principal * 10000; // 转换为元
  const r = annualRate / 100 / 12; // 月利率
  const n = months;

  if (r === 0) {
    // 利率为0的特殊情况
    const monthlyPayment = P / n;
    const totalPayment = P;
    const totalInterest = 0;
    return buildResult(monthlyPayment, totalPayment, totalInterest, n, P, 'equal_payment');
  }

  const pow = Math.pow(1 + r, n);
  const monthlyPayment = P * r * pow / (pow - 1);
  const totalPayment = monthlyPayment * n;
  const totalInterest = totalPayment - P;

  return buildResult(monthlyPayment, totalPayment, totalInterest, n, P, 'equal_payment');
};

/**
 * 等额本金（每月还款递减）
 * 每月本金固定，利息递减
 * @param {number} principal - 贷款总额（万元）
 * @param {number} annualRate - 年利率（如 4.2 表示 4.2%）
 * @param {number} months - 贷款月数
 * @returns {object} 计算结果
 */
const calcEqualPrincipal = (principal, annualRate, months) => {
  const P = principal * 10000;
  const r = annualRate / 100 / 12;
  const n = months;
  const monthlyPrincipal = P / n;

  let totalInterest = 0;
  let firstMonthPayment = 0;
  let lastMonthPayment = 0;

  const schedule = [];

  for (let i = 1; i <= n; i++) {
    const remainingPrincipal = P - monthlyPrincipal * (i - 1);
    const interest = remainingPrincipal * r;
    const payment = monthlyPrincipal + interest;
    totalInterest += interest;

    if (i === 1) firstMonthPayment = payment;
    if (i === n) lastMonthPayment = payment;

    // 每年记录一条，避免数据量过大
    if (i === 1 || i === n || i % 12 === 0) {
      schedule.push({
        month: i,
        payment: parseFloat(payment.toFixed(2)),
        principal: parseFloat(monthlyPrincipal.toFixed(2)),
        interest: parseFloat(interest.toFixed(2)),
        remaining: parseFloat(Math.max(0, remainingPrincipal - monthlyPrincipal).toFixed(2)),
      });
    }
  }

  const totalPayment = P + totalInterest;
  const monthlyDecrease = monthlyPrincipal * r;

  return {
    method: 'equal_principal',
    methodName: '等额本金',
    loanAmount: principal,
    totalPayment: parseFloat(totalPayment.toFixed(2)),
    totalInterest: parseFloat(totalInterest.toFixed(2)),
    firstMonthPayment: parseFloat(firstMonthPayment.toFixed(2)),
    lastMonthPayment: parseFloat(lastMonthPayment.toFixed(2)),
    monthlyDecrease: parseFloat(monthlyDecrease.toFixed(2)),
    months: n,
    schedule: schedule,
  };
};

/**
 * 构建等额本息还款结果
 */
const buildResult = (monthlyPayment, totalPayment, totalInterest, n, P, method) => {
  const schedule = [];
  let remaining = P;

  for (let i = 1; i <= n; i++) {
    const interest = remaining * (totalInterest > 0 ? (monthlyPayment * n - P) / P / n : 0);
    const actualInterest = remaining * (monthlyPayment * n - P) / (P * n);
    const principalPart = monthlyPayment - actualInterest;
    remaining = Math.max(0, remaining - principalPart);

    if (i === 1 || i === n || i % 12 === 0) {
      schedule.push({
        month: i,
        payment: parseFloat(monthlyPayment.toFixed(2)),
        principal: parseFloat(principalPart.toFixed(2)),
        interest: parseFloat(actualInterest.toFixed(2)),
        remaining: parseFloat(remaining.toFixed(2)),
      });
    }
  }

  return {
    method: method,
    methodName: '等额本息',
    loanAmount: P / 10000,
    totalPayment: parseFloat(totalPayment.toFixed(2)),
    totalInterest: parseFloat(totalInterest.toFixed(2)),
    monthlyPayment: parseFloat(monthlyPayment.toFixed(2)),
    months: n,
    schedule: schedule,
  };
};

/**
 * 组合贷计算（公积金+商业贷）
 */
const calcCombinedLoan = (options) => {
  const { fundAmount, fundRate, fundMonths, commercialAmount, commercialRate, commercialMonths } = options;

  const fundResult = calcEqualPayment(fundAmount, fundRate, fundMonths);
  const commercialResult = calcEqualPayment(commercialAmount, commercialRate, commercialMonths);

  return {
    method: 'combined',
    methodName: '组合贷',
    fund: fundResult,
    commercial: commercialResult,
    totalPayment: fundResult.totalPayment + commercialResult.totalPayment,
    totalInterest: fundResult.totalInterest + commercialResult.totalInterest,
    monthlyPayment: fundResult.monthlyPayment + commercialResult.monthlyPayment,
    months: Math.max(fundMonths, commercialMonths),
  };
};

/**
 * 税费计算
 * @param {object} options - { price, area, isFirst, isOnly, years, houseType, city }
 */
const calcTax = (options) => {
  const { price, area, isFirst, isOnly, years, houseType, city } = options;
  const isOrdinary = houseType === 'ordinary'; // 普通住宅
  const result = {
    deedTax: 0,          // 契税
    valueAddedTax: 0,    // 增值税
    personalTax: 0,      // 个人所得税
    maintenance: 0,      // 维修基金
    total: 0,
    details: {},
  };

  // 1. 契税（买方缴纳）
  if (isFirst) {
    if (area <= 90) {
      result.deedTax = price * 0.01;
      result.details.deedTaxDesc = '首套 ≤90㎡: 1%';
    } else {
      result.deedTax = price * 0.015;
      result.details.deedTaxDesc = '首套 >90㎡: 1.5%';
    }
  } else {
    if (area <= 90) {
      result.deedTax = price * 0.01;
      result.details.deedTaxDesc = '二套 ≤90㎡: 1%';
    } else {
      result.deedTax = price * 0.02;
      result.details.deedTaxDesc = '二套 >90㎡: 2%';
    }
  }

  // 2. 增值税（卖方缴纳，满2年免征）
  if (years < 2) {
    result.valueAddedTax = price / 1.05 * 0.056;
    result.details.vatDesc = '不满2年: 5.6%';
  } else if (!isOrdinary && years < 5) {
    // 非普通住宅满2年不满5年
    result.valueAddedTax = (price - originalPrice) / 1.05 * 0.056;
    result.details.vatDesc = '非普通住宅2-5年: 差额5.6%';
  } else {
    result.details.vatDesc = '免征（满2年）';
  }

  // 3. 个人所得税（卖方缴纳，满5年唯一免征）
  if (years >= 5 && isOnly) {
    result.details.personalTaxDesc = '免征（满5年唯一）';
  } else {
    result.personalTax = price * 0.01;
    result.details.personalTaxDesc = '1%（不满5年或非唯一）';
  }

  // 4. 住宅维修基金
  if (isOrdinary) {
    result.maintenance = area * (city === 'bj' ? 100 : 60);
    result.details.maintenanceDesc = `普通住宅: ${area}㎡ × ${city === 'bj' ? 100 : 60}元/㎡`;
  } else {
    result.maintenance = area * (city === 'bj' ? 200 : 120);
    result.details.maintenanceDesc = `非普通住宅: ${area}㎡ × ${city === 'bj' ? 200 : 120}元/㎡`;
  }

  result.total = result.deedTax + result.valueAddedTax + result.personalTax + result.maintenance;

  return result;
};

/**
 * 根据LPR计算商业贷款利率
 */
const getLPRRate = (lprValue, bp = 0) => {
  // LPR加点模式：房贷利率 = LPR + BP
  return parseFloat((lprValue + bp / 100).toFixed(3));
};

/**
 * 首付计算
 */
const calcDownPayment = (totalPrice, downPaymentRatio) => {
  const downPayment = totalPrice * (downPaymentRatio / 100);
  const loanAmount = totalPrice - downPayment;
  return {
    totalPrice,
    downPaymentRatio,
    downPayment: parseFloat(downPayment.toFixed(2)),
    loanAmount: parseFloat(loanAmount.toFixed(2)),
  };
};

/**
 * 还款能力评估
 * 月供不应超过月收入的50%（建议不超过30%）
 */
const assessAffordability = (monthlyIncome, monthlyPayment) => {
  const ratio = monthlyPayment / monthlyIncome;
  let level, advice;

  if (ratio <= 0.3) {
    level = 'safe';
    advice = '月供占收入比在安全范围内，还款压力较小';
  } else if (ratio <= 0.5) {
    level = 'warning';
    advice = '月供占收入比偏高，建议适当降低贷款金额或延长还款期限';
  } else {
    level = 'danger';
    advice = '月供超过收入50%，还款压力过大，存在断供风险';
  }

  return {
    ratio: parseFloat((ratio * 100).toFixed(1)),
    level,
    advice,
    maxLoan: monthlyIncome * 0.5, // 最大可承受月供
  };
};

module.exports = {
  calcEqualPayment,
  calcEqualPrincipal,
  calcCombinedLoan,
  calcTax,
  getLPRRate,
  calcDownPayment,
  assessAffordability,
};
