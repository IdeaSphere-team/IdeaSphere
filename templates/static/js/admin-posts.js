/**
 * 帖子管理页面脚本
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化各种功能
    initSearch();
    initFilters();
    initSelection();
    initBulkActions();
    initPagination();
    initPostActions();
    initModals();
    initDatepickers();

    // 单个帖子操作
    document.querySelectorAll('.pin-post-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            var postId = this.dataset.postId;
            pinPost(postId, true);
        });
    });
    
    document.querySelectorAll('.unpin-post-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            var postId = this.dataset.postId;
            pinPost(postId, false);
        });
    });
    
    document.querySelectorAll('.delete-post-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            var postId = this.dataset.postId;
            document.getElementById('confirmDelete').dataset.postId = postId;
            new bootstrap.Modal(document.getElementById('deletePostModal')).show();
        });
    });
    
    document.querySelectorAll('.restore-post-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            var postId = this.dataset.postId;
            restorePost(postId);
        });
    });
    
    const confirmDeleteBtn = document.getElementById('confirmDelete');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            var postId = this.dataset.postId;
            var permanent = document.getElementById('permanentDelete').checked;
            deletePost(postId, permanent);
            bootstrap.Modal.getInstance(document.getElementById('deletePostModal')).hide();
        });
    }
    
    // 批量操作
    const selectAllCheckbox = document.getElementById('selectAllPosts');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            document.querySelectorAll('.post-checkbox').forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActions();
        });
    }
    
    document.querySelectorAll('.post-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateBulkActions();
        });
    });
    
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', function() {
            document.getElementById('bulkActionTitle').textContent = '批量删除帖子';
            document.getElementById('bulkActionConfirmMessage').textContent = '确定要删除选中的帖子吗？';
            document.getElementById('bulkPermanentDeleteContainer').style.display = 'block';
            document.getElementById('confirmBulkAction').dataset.action = 'delete';
            new bootstrap.Modal(document.getElementById('bulkActionModal')).show();
        });
    }
    
    const bulkPinBtn = document.getElementById('bulkPinBtn');
    if (bulkPinBtn) {
        bulkPinBtn.addEventListener('click', function() {
            document.getElementById('bulkActionTitle').textContent = '批量置顶帖子';
            document.getElementById('bulkActionConfirmMessage').textContent = '确定要置顶选中的帖子吗？';
            document.getElementById('bulkPermanentDeleteContainer').style.display = 'none';
            document.getElementById('confirmBulkAction').dataset.action = 'pin';
            new bootstrap.Modal(document.getElementById('bulkActionModal')).show();
        });
    }
    
    const bulkCancelBtn = document.getElementById('bulkCancelBtn');
    if (bulkCancelBtn) {
        bulkCancelBtn.addEventListener('click', function() {
            document.querySelectorAll('.post-checkbox, #selectAllPosts').forEach(checkbox => {
                checkbox.checked = false;
            });
            updateBulkActions();
        });
    }
    
    const confirmBulkActionBtn = document.getElementById('confirmBulkAction');
    if (confirmBulkActionBtn) {
        confirmBulkActionBtn.addEventListener('click', function() {
            var action = this.dataset.action;
            var permanent = document.getElementById('bulkPermanentDelete').checked;
            var selectedPosts = [];
            
            document.querySelectorAll('.post-checkbox:checked').forEach(checkbox => {
                var postId = checkbox.closest('tr').dataset.postId;
                selectedPosts.push(postId);
            });
            
            if (action == 'delete') {
                bulkDeletePosts(selectedPosts, permanent);
            } else if (action == 'pin') {
                bulkPinPosts(selectedPosts);
            }
            
            bootstrap.Modal.getInstance(document.getElementById('bulkActionModal')).hide();
        });
    }
    
    // 搜索功能
    const postSearchInput = document.getElementById('postSearch');
    if (postSearchInput) {
        postSearchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                var searchTerm = this.value.trim();
                if (searchTerm) {
                    window.location.href = "/admin/posts?search=" + encodeURIComponent(searchTerm);
                }
            }
        });
    }
    
    // 过滤和排序
    document.querySelectorAll('.dropdown-item[data-filter]').forEach(item => {
        item.addEventListener('click', function() {
            var filter = this.dataset.filter;
            window.location.href = "/admin/posts?filter=" + filter;
        });
    });
    
    document.querySelectorAll('.dropdown-item[data-sort]').forEach(item => {
        item.addEventListener('click', function() {
            var sort = this.dataset.sort;
            window.location.href = "/admin/posts?sort=" + sort;
        });
    });
    
    // 导出数据
    const exportPostsBtn = document.getElementById('exportPostsBtn');
    if (exportPostsBtn) {
        exportPostsBtn.addEventListener('click', function() {
            window.location.href = "/admin/posts?export=true";
        });
    }
});

/**
 * 初始化搜索功能
 */
function initSearch() {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearch');
    
    // 清除搜索
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            searchInput.value = '';
            searchForm.submit();
        });
    }
    
    // 搜索输入框回车提交
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchForm.submit();
            }
        });
    }
    
    // 高级搜索按钮
    const advancedSearchBtn = document.getElementById('advancedSearchBtn');
    if (advancedSearchBtn) {
        advancedSearchBtn.addEventListener('click', function() {
            const advancedSearchModal = new bootstrap.Modal(document.getElementById('advancedSearchModal'));
            advancedSearchModal.show();
        });
    }
    
    // 应用高级搜索
    const applyAdvancedSearchBtn = document.getElementById('applyAdvancedSearch');
    if (applyAdvancedSearchBtn) {
        applyAdvancedSearchBtn.addEventListener('click', function() {
            const form = document.getElementById('advancedSearchForm');
            const formData = new FormData(form);
            const params = new URLSearchParams();
            
            for (const [key, value] of formData.entries()) {
                if (value) {
                    params.append(key, value);
                }
            }
            
            // 添加高级搜索标志
            params.append('advanced', 'true');
            
            // 跳转到带有查询参数的页面
            window.location.href = `${window.location.pathname}?${params.toString()}`;
        });
    }
    
    // 重置高级搜索
    const resetAdvancedSearchBtn = document.getElementById('resetAdvancedSearch');
    if (resetAdvancedSearchBtn) {
        resetAdvancedSearchBtn.addEventListener('click', function() {
            document.getElementById('advancedSearchForm').reset();
        });
    }
}

/**
 * 初始化过滤器功能
 */
function initFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            
            // 自定义筛选
            if (filter === 'custom') {
                const customFilterModal = new bootstrap.Modal(document.getElementById('customFilterModal'));
                customFilterModal.show();
                return;
            }
            
            // 常规筛选
            const params = new URLSearchParams(window.location.search);
            params.set('filter', filter);
            params.delete('page'); // 重置页码
            
            window.location.href = `${window.location.pathname}?${params.toString()}`;
        });
    });
    
    // 应用自定义筛选
    const applyCustomFilterBtn = document.getElementById('applyCustomFilter');
    if (applyCustomFilterBtn) {
        applyCustomFilterBtn.addEventListener('click', function() {
            const form = document.getElementById('customFilterForm');
            const formData = new FormData(form);
            const params = new URLSearchParams(window.location.search);
            
            // 清除之前的过滤参数
            params.delete('filter');
            params.delete('page');
            params.set('filter', 'custom');
            
            for (const [key, value] of formData.entries()) {
                if (value) {
                    // 处理多选复选框
                    if (key.endsWith('[]')) {
                        const cleanKey = key.substring(0, key.length - 2);
                        params.append(cleanKey, value);
                    } else {
                        params.set(key, value);
                    }
                }
            }
            
            window.location.href = `${window.location.pathname}?${params.toString()}`;
        });
    }
}

/**
 * 初始化选择功能
 */
function initSelection() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const postCheckboxes = document.querySelectorAll('.post-checkbox');
    const bulkSelectionControls = document.getElementById('bulkSelectionControls');
    const selectedCountSpan = document.getElementById('selectedCount');
    
    // 全选/取消全选
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            
            postCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            
            updateSelectionCount();
        });
    }
    
    // 单个帖子选择
    postCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectionCount();
            
            // 更新全选框状态
            if (selectAllCheckbox) {
                const allChecked = Array.from(postCheckboxes).every(cb => cb.checked);
                const anyChecked = Array.from(postCheckboxes).some(cb => cb.checked);
                
                selectAllCheckbox.checked = allChecked;
                selectAllCheckbox.indeterminate = anyChecked && !allChecked;
            }
        });
    });
    
    // 更新选择计数
    function updateSelectionCount() {
        const checkedCount = document.querySelectorAll('.post-checkbox:checked').length;
        
        if (selectedCountSpan) {
            selectedCountSpan.textContent = checkedCount;
        }
        
        // 显示/隐藏批量操作控件
        if (bulkSelectionControls) {
            if (checkedCount > 0) {
                bulkSelectionControls.classList.remove('hidden');
            } else {
                bulkSelectionControls.classList.add('hidden');
            }
        }
    }
}

/**
 * 初始化批量操作
 */
function initBulkActions() {
    const bulkActionButtons = document.querySelectorAll('.bulk-action');
    const actionForm = document.getElementById('actionForm');
    
    bulkActionButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.dataset.action;
            
            // 取消选择
            if (action === 'cancel') {
                const postCheckboxes = document.querySelectorAll('.post-checkbox');
                postCheckboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                document.getElementById('selectAll').checked = false;
                document.getElementById('bulkSelectionControls').classList.add('hidden');
                return;
            }
            
            // 获取所有选中的帖子ID
            const selectedPostIds = Array.from(
                document.querySelectorAll('.post-checkbox:checked')
            ).map(checkbox => checkbox.dataset.postId);
            
            if (selectedPostIds.length === 0) {
                showNotification('请至少选择一个帖子', 'error');
                return;
            }
            
            // 根据操作类型执行不同的操作
            switch (action) {
                case 'pin':
                    confirmBulkAction(
                        `确定要${selectedPostIds.length > 1 ? '批量' : ''}置顶选中的 ${selectedPostIds.length} 个帖子吗？`,
                        '置顶操作',
                        () => performBulkAction('pin_posts', selectedPostIds)
                    );
                    break;
                case 'delete':
                    confirmBulkAction(
                        `确定要${selectedPostIds.length > 1 ? '批量' : ''}删除选中的 ${selectedPostIds.length} 个帖子吗？`,
                        '删除操作',
                        () => performBulkAction('delete_posts', selectedPostIds)
                    );
                    break;
            }
        });
    });
    
    // 确认批量操作
    function confirmBulkAction(message, title, callback) {
        if (confirm(message)) {
            callback();
        }
    }
    
    // 执行批量操作
    function performBulkAction(action, postIds) {
        // 显示加载遮罩
        showLoading();
        
        // 准备表单数据
        const formData = new FormData();
        formData.append('action', action);
        postIds.forEach(id => {
            formData.append('post_ids[]', id);
        });
        
        // 添加CSRF令牌
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (csrfToken) {
            formData.append('csrf_token', csrfToken.content);
        }
        
        // 发送AJAX请求
        fetch('/api/admin/posts/bulk', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                showNotification(data.message || '操作成功', 'success');
                
                // 刷新页面以显示更新后的数据
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showNotification(data.message || '操作失败', 'error');
            }
        })
        .catch(error => {
            hideLoading();
            showNotification('发生错误：' + error.message, 'error');
        });
    }
}

/**
 * 初始化分页
 */
function initPagination() {
    const pageButtons = document.querySelectorAll('.page-btn');
    const prevPageBtn = document.getElementById('prevPage');
    const nextPageBtn = document.getElementById('nextPage');
    
    // 页码按钮点击
    pageButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const page = this.dataset.page;
            goToPage(page);
        });
    });
    
    // 上一页按钮
    if (prevPageBtn) {
        prevPageBtn.addEventListener('click', function() {
            if (!this.disabled) {
                const currentPage = parseInt(document.querySelector('.page-btn.active').dataset.page);
                goToPage(currentPage - 1);
            }
        });
    }
    
    // 下一页按钮
    if (nextPageBtn) {
        nextPageBtn.addEventListener('click', function() {
            if (!this.disabled) {
                const currentPage = parseInt(document.querySelector('.page-btn.active').dataset.page);
                goToPage(currentPage + 1);
            }
        });
    }
    
    // 跳转到指定页
    function goToPage(page) {
        const params = new URLSearchParams(window.location.search);
        params.set('page', page);
        
        window.location.href = `${window.location.pathname}?${params.toString()}`;
    }
}

/**
 * 初始化帖子操作
 */
function initPostActions() {
    // 置顶/取消置顶
    const pinButtons = document.querySelectorAll('.pin-post');
    pinButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const postId = this.dataset.postId;
            const action = 'pin_post';
            
            performPostAction(action, postId);
        });
    });
    
    // 删除帖子
    const deleteButtons = document.querySelectorAll('.delete-post');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const postId = this.dataset.postId;
            
            if (confirm('确定要删除此帖子吗？')) {
                const action = 'delete_post';
                performPostAction(action, postId);
            }
        });
    });
    
    // 恢复帖子
    const restoreButtons = document.querySelectorAll('.restore-post');
    restoreButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const postId = this.dataset.postId;
            
            if (confirm('确定要恢复此帖子吗？')) {
                const action = 'restore_post';
                performPostAction(action, postId);
            }
        });
    });
    
    // 永久删除帖子
    const permanentDeleteButtons = document.querySelectorAll('.permanent-delete');
    permanentDeleteButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const postId = this.dataset.postId;
            
            if (confirm('警告：此操作不可逆！确定要永久删除此帖子吗？')) {
                if (confirm('请再次确认，此操作将永久删除帖子及其所有评论，无法恢复！')) {
                    const action = 'permanent_delete_post';
                    performPostAction(action, postId);
                }
            }
        });
    });
    
    // 查看帖子统计
    const postStatsButtons = document.querySelectorAll('.post-stats');
    postStatsButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const postId = this.dataset.postId;
            openPostStatsModal(postId);
        });
    });
    
    // 执行帖子操作
    function performPostAction(action, postId) {
        // 显示加载遮罩
        showLoading();
        
        // 准备表单数据
        const formData = new FormData();
        formData.append('action', action);
        formData.append('post_id', postId);
        
        // 添加CSRF令牌
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (csrfToken) {
            formData.append('csrf_token', csrfToken.content);
        }
        
        // 发送AJAX请求
        fetch('/api/admin/posts/action', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                showNotification(data.message || '操作成功', 'success');
                
                // 刷新页面以显示更新后的数据
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showNotification(data.message || '操作失败', 'error');
            }
        })
        .catch(error => {
            hideLoading();
            showNotification('发生错误：' + error.message, 'error');
        });
    }
    
    // 打开帖子统计模态框
    function openPostStatsModal(postId) {
        const modal = new bootstrap.Modal(document.getElementById('postStatsModal'));
        const modalContent = document.getElementById('postStatsContent');
        
        // 重置内容
        modalContent.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">加载统计数据...</p>
            </div>
        `;
        
        modal.show();
        
        // 加载帖子统计数据
        fetch(`/api/admin/posts/${postId}/stats`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 更新模态框内容
                    updatePostStatsModal(data.post, data.stats);
                } else {
                    modalContent.innerHTML = `
                        <div class="alert alert-danger">
                            加载统计数据失败：${data.message || '未知错误'}
                        </div>
                    `;
                }
            })
            .catch(error => {
                modalContent.innerHTML = `
                    <div class="alert alert-danger">
                        发生错误：${error.message}
                    </div>
                `;
            });
    }
    
    // 更新帖子统计模态框内容
    function updatePostStatsModal(post, stats) {
        const modalContent = document.getElementById('postStatsContent');
        const modalTitle = document.getElementById('postStatsModalLabel');
        
        // 更新模态框标题
        if (modalTitle) {
            modalTitle.textContent = `帖子统计 - ${post.title}`;
        }
        
        // 构建统计内容
        let html = `
            <div class="post-stats-header mb-4">
                <h4 class="post-title">${post.title}</h4>
                <div class="post-meta">
                    <span class="me-3">
                        <i class="fas fa-user me-1"></i>${post.author_name}
                    </span>
                    <span class="me-3">
                        <i class="fas fa-folder me-1"></i>${post.section_name}
                    </span>
                    <span>
                        <i class="fas fa-calendar me-1"></i>${post.created_at}
                    </span>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-4">
                    <div class="card mb-3">
                        <div class="card-body text-center">
                            <h1 class="display-4">${stats.view_count}</h1>
                            <p class="text-muted">浏览量</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card mb-3">
                        <div class="card-body text-center">
                            <h1 class="display-4">${stats.comment_count}</h1>
                            <p class="text-muted">评论数</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card mb-3">
                        <div class="card-body text-center">
                            <h1 class="display-4">${stats.like_count}</h1>
                            <p class="text-muted">点赞数</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card mb-3">
                        <div class="card-header">
                            <h6 class="card-title mb-0">
                                <i class="fas fa-chart-line me-2"></i>浏览趋势
                            </h6>
                        </div>
                        <div class="card-body">
                            <canvas id="viewsChart" height="200"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card mb-3">
                        <div class="card-header">
                            <h6 class="card-title mb-0">
                                <i class="fas fa-chart-line me-2"></i>互动趋势
                            </h6>
                        </div>
                        <div class="card-body">
                            <canvas id="interactionChart" height="200"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card mb-3">
                        <div class="card-header">
                            <h6 class="card-title mb-0">
                                <i class="fas fa-globe me-2"></i>访问来源
                            </h6>
                        </div>
                        <div class="card-body">
                            <canvas id="referrerChart" height="200"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card mb-3">
                        <div class="card-header">
                            <h6 class="card-title mb-0">
                                <i class="fas fa-user me-2"></i>访客设备
                            </h6>
                        </div>
                        <div class="card-body">
                            <canvas id="deviceChart" height="200"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 更新模态框内容
        modalContent.innerHTML = html;
        
        // 初始化图表
        initPostCharts(stats);
    }
    
    // 初始化帖子统计图表
    function initPostCharts(stats) {
        // 浏览趋势图表
        const viewsChartCtx = document.getElementById('viewsChart').getContext('2d');
        new Chart(viewsChartCtx, {
            type: 'line',
            data: {
                labels: stats.view_trend.labels,
                datasets: [{
                    label: '浏览量',
                    data: stats.view_trend.data,
                    backgroundColor: 'rgba(38, 56, 73, 0.1)',
                    borderColor: 'rgb(38, 56, 73)',
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 3,
                    pointBackgroundColor: 'rgb(38, 56, 73)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
        
        // 互动趋势图表
        const interactionChartCtx = document.getElementById('interactionChart').getContext('2d');
        new Chart(interactionChartCtx, {
            type: 'line',
            data: {
                labels: stats.interaction_trend.labels,
                datasets: [
                    {
                        label: '评论',
                        data: stats.interaction_trend.comments,
                        backgroundColor: 'rgba(45, 206, 137, 0.1)',
                        borderColor: 'rgb(45, 206, 137)',
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 3,
                        pointBackgroundColor: 'rgb(45, 206, 137)'
                    },
                    {
                        label: '点赞',
                        data: stats.interaction_trend.likes,
                        backgroundColor: 'rgba(251, 99, 64, 0.1)',
                        borderColor: 'rgb(251, 99, 64)',
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 3,
                        pointBackgroundColor: 'rgb(251, 99, 64)'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
        
        // 访问来源饼图
        const referrerChartCtx = document.getElementById('referrerChart').getContext('2d');
        new Chart(referrerChartCtx, {
            type: 'doughnut',
            data: {
                labels: stats.referrers.labels,
                datasets: [{
                    data: stats.referrers.data,
                    backgroundColor: [
                        'rgb(38, 56, 73)',
                        'rgb(45, 206, 137)',
                        'rgb(251, 99, 64)',
                        'rgb(17, 205, 239)',
                        'rgb(251, 189, 8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
        
        // 设备饼图
        const deviceChartCtx = document.getElementById('deviceChart').getContext('2d');
        new Chart(deviceChartCtx, {
            type: 'doughnut',
            data: {
                labels: stats.devices.labels,
                datasets: [{
                    data: stats.devices.data,
                    backgroundColor: [
                        'rgb(38, 56, 73)',
                        'rgb(45, 206, 137)',
                        'rgb(251, 99, 64)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }
}

/**
 * 初始化模态框
 */
function initModals() {
    // 自定义筛选模态框
    const customFilterBtn = document.getElementById('customFilterBtn');
    if (customFilterBtn) {
        customFilterBtn.addEventListener('click', function() {
            const customFilterModal = new bootstrap.Modal(document.getElementById('customFilterModal'));
            customFilterModal.show();
        });
    }
    
    // 导出帖子统计按钮
    const exportPostStatsBtn = document.getElementById('exportPostStats');
    if (exportPostStatsBtn) {
        exportPostStatsBtn.addEventListener('click', function() {
            const postId = document.querySelector('.post-stats-header h4').dataset.postId;
            window.open(`/api/admin/posts/${postId}/stats/export`, '_blank');
        });
    }
}

/**
 * 初始化日期选择器
 */
function initDatepickers() {
    const datePickerElements = document.querySelectorAll('.datepicker');
    
    datePickerElements.forEach(elem => {
        flatpickr(elem, {
            locale: 'zh',
            dateFormat: 'Y-m-d',
            allowInput: true,
            altInput: true,
            altFormat: 'Y年m月d日',
            disableMobile: true
        });
    });
}

/**
 * 显示通知
 * @param {string} message - 通知消息
 * @param {string} type - 通知类型 (success, error, info)
 */
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    const notificationMessage = notification.querySelector('.notification-message');
    const notificationIcon = notification.querySelector('.notification-icon i');
    
    // 设置通知类型
    notification.className = 'notification';
    notification.classList.add(`notification-${type}`);
    
    // 设置图标
    switch (type) {
        case 'success':
            notificationIcon.className = 'fas fa-check-circle';
            break;
        case 'error':
            notificationIcon.className = 'fas fa-times-circle';
            break;
        case 'info':
            notificationIcon.className = 'fas fa-info-circle';
            break;
    }
    
    // 设置消息
    notificationMessage.textContent = message;
    
    // 显示通知
    notification.classList.add('notification-show');
    
    // 3秒后自动隐藏
    setTimeout(() => {
        hideNotification();
    }, 3000);
    
    // 点击关闭按钮
    const closeButton = notification.querySelector('.notification-close');
    closeButton.addEventListener('click', hideNotification);
    
    // 隐藏通知
    function hideNotification() {
        notification.classList.remove('notification-show');
        notification.classList.add('notification-hide');
    }
}

/**
 * 显示加载中遮罩
 */
function showLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('d-none');
    }
}

/**
 * 隐藏加载中遮罩
 */
function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.add('d-none');
    }
}

/**
 * 更新批量操作界面
 */
function updateBulkActions() {
    var selectedCount = document.querySelectorAll('.post-checkbox:checked').length;
    document.getElementById('selectedCount').textContent = '已选择 ' + selectedCount + ' 个帖子';
    
    if (selectedCount > 0) {
        document.querySelector('.bulk-count').classList.remove('hidden');
        document.querySelector('.bulk-actions').classList.remove('hidden');
    } else {
        document.querySelector('.bulk-count').classList.add('hidden');
        document.querySelector('.bulk-actions').classList.add('hidden');
    }
}

/**
 * 置顶/取消置顶帖子
 */
function pinPost(postId, pinned) {
    fetch('/api/admin/post/pin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            post_id: postId,
            pin: pinned
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('操作失败: ' + data.message);
        }
    });
}

/**
 * 删除帖子
 */
function deletePost(postId, permanent) {
    fetch('/api/admin/post/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            post_id: postId,
            permanent: permanent
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('操作失败: ' + data.message);
        }
    });
}

/**
 * 恢复帖子
 */
function restorePost(postId) {
    fetch('/api/admin/post/restore', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            post_id: postId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('操作失败: ' + data.message);
        }
    });
}

/**
 * 批量删除帖子
 */
function bulkDeletePosts(postIds, permanent) {
    fetch('/api/admin/posts/bulk', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            action: 'delete',
            post_ids: postIds,
            permanent: permanent
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('操作失败: ' + data.message);
        }
    });
}

/**
 * 批量置顶帖子
 */
function bulkPinPosts(postIds) {
    fetch('/api/admin/posts/bulk', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            action: 'pin',
            post_ids: postIds
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('操作失败: ' + data.message);
        }
    });
}

/**
 * 获取CSRF令牌
 */
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
} 