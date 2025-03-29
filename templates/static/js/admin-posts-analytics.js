/**
 * 帖子管理分析页面的JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化图表
    initActivityChart();
    initSectionChart();
    
    // 初始化时间周期选择器
    initPeriodSelector();
    
    // 设置当前时间
    updateCurrentTime();
    setInterval(updateCurrentTime, 60000); // 每分钟更新一次
});

/**
 * 初始化活动趋势图表
 */
function initActivityChart() {
    const activityChartElem = document.getElementById('activityChart');
    if (!activityChartElem) return;
    
    const ctx = activityChartElem.getContext('2d');
    
    // 从HTML数据属性中获取图表数据
    const labels = JSON.parse(activityChartElem.dataset.labels || '[]');
    const postsData = JSON.parse(activityChartElem.dataset.posts || '[]');
    const commentsData = JSON.parse(activityChartElem.dataset.comments || '[]');
    const viewsData = JSON.parse(activityChartElem.dataset.views || '[]');
    const likesData = JSON.parse(activityChartElem.dataset.likes || '[]');
    
    // 检查是否有任何数据
    const hasData = postsData.some(val => val > 0) || 
                    commentsData.some(val => val > 0) || 
                    viewsData.some(val => val > 0) || 
                    likesData.some(val => val > 0);
    
    // 如果完全没有数据，显示"暂无数据"提示
    if (!hasData && labels.length > 0) {
        const noDataMessage = document.createElement('div');
        noDataMessage.className = 'no-data-message';
        noDataMessage.innerHTML = '<i class="fas fa-info-circle"></i> 系统刚刚安装，暂无趋势数据，请先添加内容。';
        activityChartElem.parentNode.insertBefore(noDataMessage, activityChartElem);
    }
    
    // 创建图表
    window.activityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '帖子',
                    data: postsData,
                    borderColor: '#5e72e4',
                    backgroundColor: 'rgba(94, 114, 228, 0.1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointBackgroundColor: '#5e72e4',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '评论',
                    data: commentsData,
                    borderColor: '#2dce89',
                    backgroundColor: 'rgba(45, 206, 137, 0.1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointBackgroundColor: '#2dce89',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '浏览',
                    data: viewsData,
                    borderColor: '#fb6340',
                    backgroundColor: 'rgba(251, 99, 64, 0.1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointBackgroundColor: '#fb6340',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '点赞',
                    data: likesData,
                    borderColor: '#ffc107',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointBackgroundColor: '#ffc107',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    min: 0,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

/**
 * 初始化版块分布图表
 */
function initSectionChart() {
    const sectionsChartElem = document.getElementById('sectionsChart');
    if (!sectionsChartElem) return;
    
    const ctx = sectionsChartElem.getContext('2d');
    
    // 从HTML数据属性中获取图表数据
    const labels = JSON.parse(sectionsChartElem.dataset.labels || '[]');
    const data = JSON.parse(sectionsChartElem.dataset.values || '[]');
    
    // 检查是否有任何数据
    const hasData = data.some(val => val > 0);
    
    // 如果完全没有数据，显示"暂无数据"提示
    if (!hasData && labels.length > 0) {
        const noDataMessage = document.createElement('div');
        noDataMessage.className = 'no-data-message';
        noDataMessage.innerHTML = '<i class="fas fa-info-circle"></i> 系统刚刚安装，暂无版块分布数据，请先添加内容。';
        sectionsChartElem.parentNode.insertBefore(noDataMessage, sectionsChartElem);
    }
    
    // 生成颜色
    const backgroundColors = [
        'rgba(94, 114, 228, 0.8)',
        'rgba(45, 206, 137, 0.8)',
        'rgba(251, 99, 64, 0.8)',
        'rgba(255, 193, 7, 0.8)',
        'rgba(17, 205, 239, 0.8)',
        'rgba(133, 80, 255, 0.8)'
    ];
    
    // 确保数据不全为零
    const effectiveData = hasData ? data : [1]; // 如果全为零，使用[1]显示一个占位图表
    const effectiveLabels = hasData ? labels : ['暂无数据'];
    
    // 创建图表
    window.sectionsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: effectiveLabels,
            datasets: [{
                data: effectiveData,
                backgroundColor: backgroundColors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    align: 'start'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (!hasData) return '暂无数据';
                            
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '70%'
        }
    });
}

/**
 * 初始化时间周期选择器
 */
function initPeriodSelector() {
    const periodBtns = document.querySelectorAll('.chart-period-btn');
    if (periodBtns.length === 0) return;
    
    periodBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // 移除所有按钮的active类
            periodBtns.forEach(b => b.classList.remove('active'));
            
            // 添加当前按钮的active类
            this.classList.add('active');
            
            // 获取时间周期
            const period = this.dataset.period;
            
            // 刷新页面，带上时间周期参数
            const url = new URL(window.location.href);
            url.searchParams.set('period', period);
            window.location.href = url.toString();
        });
    });
    
    // 设置当前周期按钮的active类
    const currentPeriod = new URLSearchParams(window.location.search).get('period') || 'week';
    document.querySelector(`.chart-period-btn[data-period="${currentPeriod}"]`)?.classList.add('active');
}

/**
 * 更新当前时间显示
 */
function updateCurrentTime() {
    const timeElem = document.getElementById('current-time');
    if (!timeElem) return;
    
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    timeElem.textContent = `${hours}:${minutes}`;
}

/**
 * 处理年份选择器变更
 */
function handleYearChange(select) {
    const year = select.value;
    const url = new URL(window.location.href);
    
    if (year) {
        url.searchParams.set('year', year);
        // 如果选择了年份，则移除周期参数
        url.searchParams.delete('period');
    } else {
        url.searchParams.delete('year');
        url.searchParams.delete('month');
    }
    
    window.location.href = url.toString();
}

/**
 * 处理月份选择器变更
 */
function handleMonthChange(select) {
    const month = select.value;
    const url = new URL(window.location.href);
    const year = url.searchParams.get('year');
    
    if (!year) {
        // 如果没有年份，则使用当前年份
        const currentYear = new Date().getFullYear();
        url.searchParams.set('year', currentYear);
    }
    
    if (month) {
        url.searchParams.set('month', month);
    } else {
        url.searchParams.delete('month');
    }
    
    window.location.href = url.toString();
}

/**
 * 导出统计数据为CSV
 */
function exportStatsToCSV() {
    const url = new URL(window.location.href);
    const period = url.searchParams.get('period') || 'week';
    const year = url.searchParams.get('year');
    const month = url.searchParams.get('month');
    
    let exportUrl = '/api/admin/posts/stats/export?';
    
    if (year) {
        exportUrl += `year=${year}`;
        if (month) {
            exportUrl += `&month=${month}`;
        }
    } else {
        exportUrl += `period=${period}`;
    }
    
    window.open(exportUrl, '_blank');
} 