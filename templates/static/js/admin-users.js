/**
 * IdeaSphere 用户管理页面功能
 */

// 获取CSRF令牌
function getCSRFToken() {
    return document.querySelector('input[name="csrf_token"]').value;
}

// 显示通知
function showNotification(type, message) {
    console.log(`${type}: ${message}`); // 添加控制台日志，方便调试
    
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `<div class="notification-message">${message}</div>`;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 显示通知
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // 设置自动关闭
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// 显示加载遮罩
function showLoadingOverlay() {
    console.log('显示加载遮罩'); // 添加控制台日志
    
    let loadingOverlay = document.getElementById('loadingOverlay');
    
    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loadingOverlay';
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>处理中...</p>
            </div>
        `;
        document.body.appendChild(loadingOverlay);
    }
    
    setTimeout(() => {
        loadingOverlay.classList.add('show');
    }, 10);
}

// 隐藏加载遮罩
function hideLoadingOverlay() {
    console.log('隐藏加载遮罩'); // 添加控制台日志
    
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('show');
        setTimeout(() => {
            if (loadingOverlay.parentNode) {
                loadingOverlay.parentNode.removeChild(loadingOverlay);
            }
        }, 300);
    }
}

// 初始化下拉菜单
function initDropdowns() {
    console.log('初始化下拉菜单'); // 添加控制台日志
    
    const dropdowns = document.querySelectorAll('.dropdown');
    
    dropdowns.forEach(dropdown => {
        const toggleBtn = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (!toggleBtn || !menu) return;
        
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // 关闭其他下拉菜单
            dropdowns.forEach(d => {
                if (d !== dropdown) {
                    d.classList.remove('show');
                    const m = d.querySelector('.dropdown-menu');
                    if (m) m.style.display = 'none';
                }
            });
            
            // 切换当前下拉菜单
            dropdown.classList.toggle('show');
            menu.style.display = dropdown.classList.contains('show') ? 'block' : 'none';
        });
        
        // 下拉菜单项点击事件
        const items = menu.querySelectorAll('.dropdown-item');
        items.forEach(item => {
            item.addEventListener('click', function() {
                // 处理筛选
                if (item.hasAttribute('data-filter')) {
                    const filterType = item.getAttribute('data-filter');
                    toggleBtn.innerHTML = `<i class="fas fa-filter"></i> ${item.textContent.trim()}`;
                    filterUserRows('filter', filterType);
                }
                // 处理排序
                else if (item.hasAttribute('data-sort')) {
                    const sortType = item.getAttribute('data-sort');
                    toggleBtn.innerHTML = `<i class="fas fa-sort"></i> ${item.textContent.trim()}`;
                    sortUserTable(sortType);
                }
                
                // 关闭下拉菜单
                dropdown.classList.remove('show');
                menu.style.display = 'none';
            });
        });
    });
    
    // 点击页面其他地方关闭下拉菜单
    document.addEventListener('click', function(e) {
        dropdowns.forEach(dropdown => {
            if (!dropdown.contains(e.target)) {
                dropdown.classList.remove('show');
                const menu = dropdown.querySelector('.dropdown-menu');
                if (menu) menu.style.display = 'none';
            }
        });
    });
}

// 更新当前时间
function updateCurrentTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const seconds = now.getSeconds().toString().padStart(2, '0');
        timeElement.textContent = `${hours}:${minutes}:${seconds}`;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，初始化功能'); // 添加控制台日志
    
    // 初始化用户搜索和筛选功能
    initUserSearchAndFilter();
    
    // 初始化表格选择和批量操作
    initUserSelectionAndBulkActions();
    
    // 初始化添加用户功能
    initAddUserModal();
    
    // 初始化用户行操作按钮
    initUserRowActions();
    
    // 初始化下拉菜单功能
    initDropdowns();
    
    // 初始化当前时间显示
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
});

/**
 * 用户搜索和筛选功能
 */
function initUserSearchAndFilter() {
    console.log('初始化用户搜索和筛选'); // 添加控制台日志
    
    const searchInput = document.getElementById('userSearchInput');
    const clearSearch = document.getElementById('clearSearch');
    const filterButtons = document.querySelectorAll('.filter-btn');
    const userRows = document.querySelectorAll('#usersTable tbody tr');
    
    // 搜索输入事件
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            
            // 显示/隐藏清除按钮
            if (clearSearch) {
                clearSearch.style.display = query ? 'block' : 'none';
            }
            
            // 根据搜索内容筛选用户
            filterUserRows('search', query);
        });
        
        // 清除搜索
        if (clearSearch) {
            clearSearch.addEventListener('click', function() {
                searchInput.value = '';
                clearSearch.style.display = 'none';
                filterUserRows('search', '');
            });
        }
    }
    
    // 筛选按钮切换
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 切换激活状态
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // 根据筛选条件过滤用户
            const filterType = this.getAttribute('data-filter');
            filterUserRows('filter', filterType);
        });
    });
}

// 筛选用户行
function filterUserRows(type, value) {
    console.log(`筛选用户: ${type} = ${value}`); // 添加控制台日志
    
    const userRows = document.querySelectorAll('#usersTable tbody tr');
    const searchInput = document.getElementById('userSearchInput');
    const searchQuery = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const activeFilter = document.querySelector('.filter-btn.active');
    const filterType = activeFilter ? activeFilter.getAttribute('data-filter') : 'all';
    
    // 如果是通过搜索筛选，使用传入的值
    const finalSearchQuery = type === 'search' ? value : searchQuery;
    // 如果是通过按钮筛选，使用传入的值
    const finalFilterType = type === 'filter' ? value : filterType;
    
    userRows.forEach(row => {
        const userName = row.querySelector('.user-name').textContent.toLowerCase();
        const userEmail = row.querySelector('.user-email').textContent.toLowerCase();
        const userRole = row.getAttribute('data-role');
        const matchesSearch = !finalSearchQuery || userName.includes(finalSearchQuery) || userEmail.includes(finalSearchQuery);
        
        let matchesFilter = true;
        // 根据不同筛选类型进行过滤
        if (finalFilterType === 'admin') {
            matchesFilter = userRole === 'admin';
        } else if (finalFilterType === 'moderator') {
            matchesFilter = userRole === 'moderator';
        } else if (finalFilterType === 'active') {
            matchesFilter = row.querySelector('.status-active') !== null;
        } else if (finalFilterType === 'inactive') {
            matchesFilter = row.querySelector('.status-inactive') !== null;
        } else if (finalFilterType === 'recent') {
            // 此处假设最近注册的用户有特定标记或属性
            // 实际实现可能需要根据注册日期进行计算
            const regDate = new Date(row.querySelector('td:nth-child(4)').textContent);
            const thirtyDaysAgo = new Date();
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            matchesFilter = regDate >= thirtyDaysAgo;
        }
        
        row.style.display = matchesSearch && matchesFilter ? '' : 'none';
    });
    
    // 更新显示的记录数
    updateVisibleRecordsCount();
}

// 排序用户表格
function sortUserTable(sortType) {
    console.log(`排序用户表: ${sortType}`); // 添加控制台日志
    
    const tbody = document.querySelector('#usersTable tbody');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // 根据排序类型进行排序
    rows.sort((a, b) => {
        if (sortType === 'username-asc') {
            const nameA = a.querySelector('.user-name').textContent.toLowerCase();
            const nameB = b.querySelector('.user-name').textContent.toLowerCase();
            return nameA.localeCompare(nameB);
        } else if (sortType === 'username-desc') {
            const nameA = a.querySelector('.user-name').textContent.toLowerCase();
            const nameB = b.querySelector('.user-name').textContent.toLowerCase();
            return nameB.localeCompare(nameA);
        } else if (sortType === 'date-asc') {
            const dateA = new Date(a.querySelector('td:nth-child(4)').textContent);
            const dateB = new Date(b.querySelector('td:nth-child(4)').textContent);
            return dateA - dateB;
        } else if (sortType === 'date-desc') {
            const dateA = new Date(a.querySelector('td:nth-child(4)').textContent);
            const dateB = new Date(b.querySelector('td:nth-child(4)').textContent);
            return dateB - dateA;
        } else if (sortType === 'posts-asc') {
            const postsA = parseInt(a.querySelector('td:nth-child(5)').textContent);
            const postsB = parseInt(b.querySelector('td:nth-child(5)').textContent);
            return postsA - postsB;
        } else if (sortType === 'posts-desc') {
            const postsA = parseInt(a.querySelector('td:nth-child(5)').textContent);
            const postsB = parseInt(b.querySelector('td:nth-child(5)').textContent);
            return postsB - postsA;
        }
        return 0;
    });
    
    // 重新添加排序后的行
    rows.forEach(row => tbody.appendChild(row));
    
    // 更新显示的记录数
    updateVisibleRecordsCount();
}

// 更新当前可见记录数的显示
function updateVisibleRecordsCount() {
    const userRows = document.querySelectorAll('#usersTable tbody tr');
    const paginationInfo = document.querySelector('.pagination-info');
    if (paginationInfo) {
        const visibleCount = [...userRows].filter(row => row.style.display !== 'none').length;
        const totalCount = userRows.length;
        paginationInfo.textContent = `显示 ${visibleCount} 条，共 ${totalCount} 条记录`;
    }
}

/**
 * 表格选择和批量操作
 */
function initUserSelectionAndBulkActions() {
    console.log('初始化用户选择和批量操作'); // 添加控制台日志
    
    const selectAllCheckbox = document.getElementById('selectAllUsers');
    const userCheckboxes = document.querySelectorAll('.user-checkbox');
    const bulkActions = document.getElementById('bulkActions');
    const selectedCountSpan = document.getElementById('selectedCount');
    const bulkActivateBtn = document.getElementById('bulkActivateBtn');
    const bulkDeactivateBtn = document.getElementById('bulkDeactivateBtn');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    const cancelSelectionBtn = document.getElementById('cancelSelection');
    
    // 全选/取消全选
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            userCheckboxes.forEach(checkbox => {
                if (checkbox.closest('tr').style.display !== 'none') { // 只选择可见行
                    checkbox.checked = this.checked;
                    toggleRowSelected(checkbox);
                }
            });
            updateBulkActionsPanel();
        });
    }
    
    // 单个选择
    userCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            toggleRowSelected(this);
            updateSelectAllState();
            updateBulkActionsPanel();
        });
    });
    
    // 取消选择按钮
    if (cancelSelectionBtn) {
        cancelSelectionBtn.addEventListener('click', function() {
            userCheckboxes.forEach(checkbox => {
                checkbox.checked = false;
                toggleRowSelected(checkbox);
            });
            if (selectAllCheckbox) {
                selectAllCheckbox.checked = false;
            }
            updateBulkActionsPanel();
        });
    }
    
    // 批量启用
    if (bulkActivateBtn) {
        bulkActivateBtn.addEventListener('click', function() {
            const selectedIds = getSelectedUserIds();
            if (selectedIds.length === 0) return;
            
            if (confirm(`确定要启用选中的 ${selectedIds.length} 个用户吗？`)) {
                // 发送启用请求
                sendBulkAction('activate', selectedIds);
            }
        });
    }
    
    // 批量禁用
    if (bulkDeactivateBtn) {
        bulkDeactivateBtn.addEventListener('click', function() {
            const selectedIds = getSelectedUserIds();
            if (selectedIds.length === 0) return;
            
            if (confirm(`确定要禁用选中的 ${selectedIds.length} 个用户吗？`)) {
                // 发送禁用请求
                sendBulkAction('deactivate', selectedIds);
            }
        });
    }
    
    // 批量删除
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', function() {
            const selectedIds = getSelectedUserIds();
            if (selectedIds.length === 0) return;
            
            if (confirm(`警告：此操作不可恢复！确定要删除选中的 ${selectedIds.length} 个用户吗？`)) {
                // 发送删除请求
                sendBulkAction('delete', selectedIds);
            }
        });
    }
    
    // 更新选中行的样式
    function toggleRowSelected(checkbox) {
        const row = checkbox.closest('tr');
        if (row) {
            row.classList.toggle('table-row-selected', checkbox.checked);
        }
    }
    
    // 更新全选框状态
    function updateSelectAllState() {
        if (!selectAllCheckbox) return;
        
        const visibleCheckboxes = [...userCheckboxes].filter(
            checkbox => checkbox.closest('tr').style.display !== 'none'
        );
        const allChecked = visibleCheckboxes.every(checkbox => checkbox.checked);
        const someChecked = visibleCheckboxes.some(checkbox => checkbox.checked) && !allChecked;
        
        selectAllCheckbox.checked = allChecked;
        selectAllCheckbox.indeterminate = someChecked;
    }
    
    // 更新批量操作面板
    function updateBulkActionsPanel() {
        if (!bulkActions || !selectedCountSpan) return;
        
        const selectedCount = [...userCheckboxes].filter(checkbox => checkbox.checked).length;
        selectedCountSpan.textContent = selectedCount;
        
        if (selectedCount > 0) {
            bulkActions.classList.add('show');
        } else {
            bulkActions.classList.remove('show');
        }
    }
    
    // 获取选中的用户ID
    function getSelectedUserIds() {
        return [...userCheckboxes]
            .filter(checkbox => checkbox.checked)
            .map(checkbox => checkbox.closest('tr').getAttribute('data-user-id'));
    }
    
    // 发送批量操作请求
    async function sendBulkAction(action, userIds) {
        try {
            showLoadingOverlay();
            
            const response = await fetch('/admin/users/bulk-action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    action: action,
                    user_ids: userIds
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                showNotification('success', data.message || '操作成功');
                // 重新加载页面以显示更新后的状态
                setTimeout(() => window.location.reload(), 1000);
            } else {
                const errorData = await response.json();
                showNotification('error', errorData.error || '操作失败');
            }
        } catch (error) {
            console.error('批量操作请求失败:', error);
            showNotification('error', '请求失败，请检查网络连接');
        } finally {
            hideLoadingOverlay();
        }
    }
}

/**
 * 初始化添加用户模态框
 */
function initAddUserModal() {
    console.log('初始化添加用户模态框'); // 添加控制台日志
    
    const addUserBtn = document.getElementById('addUserBtn');
    const addUserModal = document.getElementById('addUserModal');
    
    if (!addUserBtn || !addUserModal) {
        console.error('添加用户按钮或模态框不存在');
        return;
    }
    
    // 打开模态框
    addUserBtn.addEventListener('click', function() {
        console.log('点击添加用户按钮，显示模态框');
        // 使用jQuery显示模态框（确保jQuery和Bootstrap正确加载）
        try {
            $('#addUserModal').modal('show');
        } catch (e) {
            console.error('显示模态框失败:', e);
            alert('无法显示添加用户窗口，请检查页面是否正确加载。');
        }
    });
}

/**
 * 初始化用户行操作按钮
 */
function initUserRowActions() {
    console.log('初始化用户行操作按钮'); // 添加控制台日志
    
    // 查看用户详情
    document.querySelectorAll('.view-user-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const userId = this.closest('tr').getAttribute('data-user-id');
            if (userId) {
                console.log(`查看用户详情: ${userId}`);
                // 直接打开新页面查看用户详情
                window.open(`/admin/users/${userId}`, '_blank');
            }
        });
    });
    
    // 编辑用户
    document.querySelectorAll('.edit-user-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            const username = this.getAttribute('data-username');
            const email = this.getAttribute('data-email');
            const role = this.getAttribute('data-role');
            
            console.log(`编辑用户: ${userId}, ${username}, ${email}, ${role}`);
            
            // 打开编辑模态框并填充数据
            const editModal = document.getElementById('editUserModal');
            if (editModal) {
                const form = editModal.querySelector('form');
                if (form) {
                    document.getElementById('edit_user_id').value = userId;
                    document.getElementById('edit_username').value = username;
                    document.getElementById('edit_email').value = email;
                    const roleSelect = document.getElementById('edit_role');
                    if (roleSelect) {
                        [...roleSelect.options].forEach(option => {
                            option.selected = option.value === role;
                        });
                    }
                }
                
                // 显示模态框
                try {
                    $('#editUserModal').modal('show');
                } catch (e) {
                    console.error('显示编辑模态框失败:', e);
                    alert('无法显示编辑用户窗口，请检查页面是否正确加载。');
                }
            }
        });
    });
    
    // 禁用用户
    document.querySelectorAll('.ban-user-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            console.log(`禁用用户: ${userId}`);
            
            if (confirm('确定要禁用此用户吗？')) {
                toggleUserStatus(userId, 'deactivate');
            }
        });
    });
    
    // 启用用户
    document.querySelectorAll('.activate-user-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            console.log(`启用用户: ${userId}`);
            
            if (confirm('确定要启用此用户吗？')) {
                toggleUserStatus(userId, 'activate');
            }
        });
    });
    
    // 删除用户
    document.querySelectorAll('.delete-user-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            console.log(`删除用户: ${userId}`);
            
            if (confirm('警告：此操作不可恢复！确定要删除此用户吗？')) {
                deleteUser(userId);
            }
        });
    });
    
    // 切换用户状态
    async function toggleUserStatus(userId, action) {
        try {
            showLoadingOverlay();
            
            const response = await fetch(`/admin/users/${userId}/status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ action: action })
            });
            
            if (response.ok) {
                const data = await response.json();
                showNotification('success', data.message || '状态已更新');
                // 重新加载页面以显示更新后的状态
                setTimeout(() => window.location.reload(), 1000);
            } else {
                const errorData = await response.json();
                showNotification('error', errorData.error || '更新状态失败');
            }
        } catch (error) {
            console.error('更新用户状态请求失败:', error);
            showNotification('error', '请求失败，请检查网络连接');
        } finally {
            hideLoadingOverlay();
        }
    }
    
    // 删除用户
    async function deleteUser(userId) {
        try {
            showLoadingOverlay();
            
            const response = await fetch(`/admin/users/${userId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                showNotification('success', data.message || '用户已删除');
                // 重新加载页面以移除已删除的用户
                setTimeout(() => window.location.reload(), 1000);
            } else {
                const errorData = await response.json();
                showNotification('error', errorData.error || '删除用户失败');
            }
        } catch (error) {
            console.error('删除用户请求失败:', error);
            showNotification('error', '请求失败，请检查网络连接');
        } finally {
            hideLoadingOverlay();
        }
    }
} 