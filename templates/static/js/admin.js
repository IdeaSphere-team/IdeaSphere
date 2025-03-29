/**
 * IdeaSphere 管理后台脚本
 */

document.addEventListener('DOMContentLoaded', function() {
    // 移动设备侧边栏切换
    initSidebarToggle();
    
    // 初始化表单增强功能
    initFormEnhancements();
    
    // 初始化表格功能
    initTableFeatures();
    
    // 初始化工具提示
    initTooltips();
    
    // 初始化确认对话框
    initConfirmDialogs();
    
    // 初始化通知系统
    initNotifications();
});

/**
 * 侧边栏在移动设备上的切换功能
 */
function initSidebarToggle() {
    // 添加汉堡按钮（如果在移动视图中不存在）
    if (!document.querySelector('.sidebar-toggle')) {
        const mainContent = document.querySelector('.admin-main');
        if (mainContent) {
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'sidebar-toggle';
            toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
            mainContent.insertBefore(toggleBtn, mainContent.firstChild);
            
            // 添加汉堡按钮样式
            const style = document.createElement('style');
            style.textContent = `
                .sidebar-toggle {
                    display: none;
                    position: fixed;
                    top: 15px;
                    left: 15px;
                    z-index: 1000;
                    width: 40px;
                    height: 40px;
                    border: none;
                    border-radius: 50%;
                    background: var(--primary);
                    color: white;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                    cursor: pointer;
                    transition: all 0.3s ease;
                }
                
                @media (max-width: 992px) {
                    .sidebar-toggle {
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    
                    .admin-sidebar {
                        transform: translateX(-100%);
                        transition: transform 0.3s ease;
                    }
                    
                    .admin-sidebar.show {
                        transform: translateX(0);
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    // 添加侧边栏切换事件
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.admin-sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // 点击主内容区域时关闭侧边栏
        document.querySelector('.admin-main').addEventListener('click', function(e) {
            if (window.innerWidth <= 992 && sidebar.classList.contains('show') && !e.target.closest('.sidebar-toggle')) {
                sidebar.classList.remove('show');
            }
        });
    }
}

/**
 * 表单增强功能
 */
function initFormEnhancements() {
    // 自定义文件上传显示文件名
    document.querySelectorAll('.custom-file-input').forEach(input => {
        input.addEventListener('change', function() {
            let fileName = this.files[0]?.name || '选择文件';
            let label = this.nextElementSibling;
            if (label) {
                label.textContent = fileName;
            }
        });
    });
    
    // 表单提交前显示加载状态
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
                
                // 10秒后恢复按钮状态（防止无限等待）
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 10000);
            }
        });
    });
}

/**
 * 表格增强功能
 */
function initTableFeatures() {
    // 为数据表格添加行选择功能
    document.querySelectorAll('.table-selectable').forEach(table => {
        const checkAll = table.querySelector('thead .check-all');
        const checkboxes = table.querySelectorAll('tbody .check-row');
        
        if (checkAll) {
            checkAll.addEventListener('change', function() {
                checkboxes.forEach(checkbox => {
                    checkbox.checked = this.checked;
                    toggleRowSelected(checkbox);
                });
                updateBulkActions();
            });
        }
        
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                toggleRowSelected(this);
                if (checkAll) {
                    checkAll.checked = [...checkboxes].every(cb => cb.checked);
                    checkAll.indeterminate = !checkAll.checked && [...checkboxes].some(cb => cb.checked);
                }
                updateBulkActions();
            });
        });
        
        function toggleRowSelected(checkbox) {
            const row = checkbox.closest('tr');
            if (row) {
                if (checkbox.checked) {
                    row.classList.add('table-row-selected');
                } else {
                    row.classList.remove('table-row-selected');
                }
            }
        }
        
        function updateBulkActions() {
            const selectedCount = [...checkboxes].filter(cb => cb.checked).length;
            const bulkActions = document.querySelector('.bulk-actions');
            
            if (bulkActions) {
                const countSpan = bulkActions.querySelector('.selected-count');
                if (countSpan) {
                    countSpan.textContent = selectedCount;
                }
                
                if (selectedCount > 0) {
                    bulkActions.classList.add('show');
                } else {
                    bulkActions.classList.remove('show');
                }
            }
        }
    });
}

/**
 * 工具提示初始化
 */
function initTooltips() {
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = element.getAttribute('data-tooltip');
        
        element.addEventListener('mouseenter', function() {
            document.body.appendChild(tooltip);
            const rect = element.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
            tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)}px`;
            tooltip.style.opacity = '1';
        });
        
        element.addEventListener('mouseleave', function() {
            tooltip.style.opacity = '0';
            setTimeout(() => {
                if (tooltip.parentNode) {
                    tooltip.parentNode.removeChild(tooltip);
                }
            }, 200);
        });
    });
}

/**
 * 确认对话框初始化
 */
function initConfirmDialogs() {
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || '确定要执行此操作吗？';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * 通知系统初始化
 */
function initNotifications() {
    // 让提示消息自动消失
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 500);
        }, 5000);
    });
}

/**
 * 显示或隐藏加载状态
 */
function toggleLoading(show = true) {
    let loadingOverlay = document.getElementById('loadingOverlay');
    
    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loadingOverlay';
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = '<div class="spinner"></div>';
        document.body.appendChild(loadingOverlay);
    }
    
    if (show) {
        loadingOverlay.classList.add('show');
    } else {
        loadingOverlay.classList.remove('show');
    }
}

/**
 * AJAX 请求工具函数
 */
async function ajaxRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    const fetchOptions = { ...defaultOptions, ...options };
    
    try {
        toggleLoading(true);
        const response = await fetch(url, fetchOptions);
        const data = await response.json();
        toggleLoading(false);
        
        return { success: true, data };
    } catch (error) {
        toggleLoading(false);
        console.error('AJAX 请求失败:', error);
        return { success: false, error: error.message };
    }
} 