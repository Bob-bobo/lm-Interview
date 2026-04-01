// cloudfunctions/login/index.js - 用户登录云函数
// 静默登录：用 code 换取 openid，自动注册/更新用户记录

const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();
const _ = db.command;

exports.main = async (event, context) => {
  const wxContext = cloud.getWXContext();
  const openid = wxContext.OPENID;
  const unionid = wxContext.UNIONID || '';
  const appid = wxContext.APPID;

  try {
    // 查找用户是否已存在
    const { data: users } = await db.collection('users')
      .where({ _openid: openid })
      .limit(1)
      .get();

    let user;

    if (users.length > 0) {
      // 已有用户 - 更新登录时间
      user = users[0];
      await db.collection('users').doc(user._id).update({
        data: {
          lastLoginTime: db.serverDate(),
          loginCount: _.inc(1),
        },
      });
      user.lastLoginTime = new Date();
    } else {
      // 新用户 - 创建记录
      const newUser = {
        _openid: openid,
        nickName: '买房人',
        avatarUrl: '',
        gender: 0,
        phone: '',
        city: '',
        createTime: db.serverDate(),
        lastLoginTime: db.serverDate(),
        loginCount: 1,
        settings: {
          notifyEnabled: true,
          themeMode: 'auto',
        },
      };
      const { _id } = await db.collection('users').add({ data: newUser });
      user = { _id, ...newUser, lastLoginTime: new Date() };
    }

    return {
      code: 0,
      message: '登录成功',
      data: {
        userId: user._id,
        openid,
        nickName: user.nickName,
        avatarUrl: user.avatarUrl,
        isNewUser: users.length === 0,
      },
    };
  } catch (err) {
    console.error('登录失败:', err);
    return {
      code: -1,
      message: '登录失败: ' + err.message,
      data: null,
    };
  }
};
