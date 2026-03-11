// 应用状态
let appState = {
  currentView: 'home',
  currentCategory: null,
  currentDocIndex: -1,
  documents: [],
  categories: []
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
  loadCategories();
  loadRecentDocs();
});

// 加载分类列表
async function loadCategories() {
  try {
    const response = await fetch('/api/categories');
    const categories = await response.json();
    
    appState.categories = categories.filter(c => c.count > 0);
    
    const categoriesList = document.getElementById('categories-list');
    const hasCategories = appState.categories.length > 0;
    
    document.getElementById('total-categories').textContent = hasCategories ? appState.categories.length : '-';
    
    if (!hasCategories) {
      categoriesList.innerHTML = '<div class="loading-card">暂无分类</div>';
      return;
    }
    
    categoriesList.innerHTML = appState.categories.map(cat => `
      <div class="category-card" onclick="showCategory('${cat.id}')">
        <span class="category-icon">${cat.icon}</span>
        <div class="category-info">
          <div class="category-name">${cat.name}</div>
          <div class="category-count">${cat.count} 篇文档</div>
        </div>
      </div>
    `).join('');
    
  } catch (error) {
    console.error('加载分类失败:', error);
    document.getElementById('categories-list').innerHTML = 
      '<div class="loading-card">加载失败，请刷新重试</div>';
  }
}

// 加载最近文档
async function loadRecentDocs() {
  try {
    const response = await fetch('/api/notes');
    const notes = await response.json();
    
    // 按时间倒序
    notes.sort((a, b) => new Date(b.modifiedTime) - new Date(a.modifiedTime));
    
    // 更新统计
    document.getElementById('total-docs').textContent = notes.length || '-';
    if (notes.length > 0) {
      document.getElementById('last-updated').textContent = 
        notes[0].modifiedTimeFormatted.split(' ')[0];
    }
    
    const recentDocs = document.getElementById('recent-docs');
    
    if (notes.length === 0) {
      recentDocs.innerHTML = '<div class="loading-card">暂无文档</div>';
      return;
    }
    
    // 显示最近 5 篇
    const recent = notes.slice(0, 5);
    recentDocs.innerHTML = recent.map(doc => `
      <div class="document-item" onclick="showDocument('${doc.filename}', -1, '${doc.category}')">
        <span class="document-icon">📄</span>
        <div class="document-info">
          <div class="document-title">${escapeHtml(doc.title)}</div>
          <div class="document-preview">${escapeHtml(doc.preview)}...</div>
        </div>
        <div class="document-meta">
          <div class="document-time">${doc.modifiedTimeFormatted}</div>
        </div>
      </div>
    `).join('');
    
  } catch (error) {
    console.error('加载文档失败:', error);
    document.getElementById('recent-docs').innerHTML = 
      '<div class="loading-card">加载失败，请刷新重试</div>';
  }
}

// 显示分类下的文档列表
async function showCategory(categoryId) {
  try {
    const category = appState.categories.find(c => c.id === categoryId);
    if (!category) return;

    document.getElementById('category-title').textContent =
      `${category.icon} ${category.name}`;

    const response = await fetch(`/api/category/${categoryId}`);
    const documents = await response.json();

    appState.documents = documents;

    const documentsList = document.getElementById('documents-list');

    if (documents.length === 0) {
      documentsList.innerHTML = '<div class="loading-card">该分类下暂无文档</div>';
    } else {
      documentsList.innerHTML = documents.map((doc, index) => `
        <div class="document-item" onclick="showDocument('${doc.filename}', ${index}, '${doc.category}')">
          <span class="document-icon">📄</span>
          <div class="document-info">
            <div class="document-title">${escapeHtml(doc.title)}</div>
            <div class="document-preview">${escapeHtml(doc.preview)}...</div>
          </div>
          <div class="document-meta">
            <div class="document-time">${doc.modifiedTimeFormatted}</div>
          </div>
        </div>
      `).join('');
    }

    switchView('category');

  } catch (error) {
    console.error('加载分类文档失败:', error);
    alert('加载失败，请重试');
  }
}

// 显示文档
async function showDocument(filename, index = -1, category = null) {
  try {
    // 如果在分类视图中点击，更新当前索引
    if (index >= 0) {
      appState.currentDocIndex = index;
    } else {
      // 否则查找文档索引
      const docIndex = appState.documents.findIndex(d => d.filename === filename);
      if (docIndex >= 0) {
        appState.currentDocIndex = docIndex;
      } else {
        // 如果当前 documents 为空（直接从外部链接访问），需要加载同分类下的所有文档
        if (category) {
          const response = await fetch(`/api/category/${encodeURIComponent(category)}`);
          const docs = await response.json();
          appState.documents = docs;
          appState.currentDocIndex = appState.documents.findIndex(d => d.filename === filename);
          if (appState.currentDocIndex < 0) {
            appState.currentDocIndex = 0;
          }
        } else {
          appState.currentDocIndex = 0;
        }
      }
    }

    const response = await fetch(`/api/notes/${encodeURIComponent(filename)}`);
    const data = await response.json();

    if (data.error) {
      alert('加载失败：' + data.error);
      return;
    }

    // 更新文档信息
    const doc = appState.documents[appState.currentDocIndex];
    document.getElementById('note-title').textContent = data.filename.replace('.md', '');
    document.getElementById('note-body').innerHTML = data.html;

    if (doc) {
      document.getElementById('note-time').textContent = '🕐 ' + doc.modifiedTimeFormatted;
      const categoryInfo = appState.categories.find(c => c.id === doc.category);
      document.getElementById('note-category').textContent =
        '📁 ' + (categoryInfo ? categoryInfo.name : doc.category || '其他');
    } else {
      // 如果找不到文档信息，使用默认值
      document.getElementById('note-time').textContent = '';
      document.getElementById('note-category').textContent = '';
    }

    // 更新底部导航
    updateDocNavigation();

    switchView('document');

  } catch (error) {
    console.error('加载文档失败:', error);
    alert('加载失败，请重试');
  }
}

// 更新文档导航
function updateDocNavigation() {
  const footerPrevBtn = document.getElementById('footer-prev-btn');
  const footerNextBtn = document.getElementById('footer-next-btn');

  const hasPrev = appState.currentDocIndex > 0;
  const hasNext = appState.currentDocIndex < appState.documents.length - 1;

  // 更新底部导航文本
  document.getElementById('footer-prev-title').textContent =
    hasPrev ? appState.documents[appState.currentDocIndex - 1].title : '已经是第一篇';
  document.getElementById('footer-next-title').textContent =
    hasNext ? appState.documents[appState.currentDocIndex + 1].title : '已经是最后一篇';
}

// 文档导航（上一篇/下一篇）
function navigateDoc(direction) {
  const newIndex = appState.currentDocIndex + direction;
  
  if (newIndex < 0 || newIndex >= appState.documents.length) {
    return;
  }
  
  const doc = appState.documents[newIndex];
  showDocument(doc.filename, newIndex);
  window.scrollTo(0, 0);
}

// 切换视图
function switchView(viewName) {
  document.querySelectorAll('.view').forEach(v => v.style.display = 'none');
  document.getElementById('view-' + viewName).style.display = 'block';
  
  const homeBtn = document.getElementById('home-btn');
  homeBtn.style.display = viewName === 'home' ? 'none' : 'flex';
  
  appState.currentView = viewName;
  window.scrollTo(0, 0);
}

// 显示首页
function showHome() {
  switchView('home');
}

// HTML 转义
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
