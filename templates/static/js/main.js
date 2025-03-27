document.addEventListener('DOMContentLoaded', function() {
    // 初始化轮播图
    if (document.querySelector('.swiper-container')) {
        new Swiper('.swiper-container', {
            loop: true,
            autoplay: {
                delay: 5000,
                disableOnInteraction: false,
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
            }
        });
    }

    // 移动端菜单切换
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }

    // 用户下拉菜单
    const userMenu = document.querySelector('.user-menu');
    const userDropdown = document.querySelector('.user-dropdown');
    
    if (userMenu && userDropdown) {
        userMenu.addEventListener('mouseenter', function() {
            userDropdown.style.opacity = '1';
            userDropdown.style.visibility = 'visible';
            userDropdown.style.transform = 'translateY(0)';
        });
        
        userMenu.addEventListener('mouseleave', function() {
            userDropdown.style.opacity = '0';
            userDropdown.style.visibility = 'hidden';
            userDropdown.style.transform = 'translateY(10px)';
        });
    }

    // 搜索功能
    const searchInput = document.getElementById('searchInput');
    const searchResultsPopup = document.getElementById('searchResultsPopup');
    
    if (searchInput && searchResultsPopup) {
        searchInput.addEventListener('focus', function() {
            // 只在有输入内容时显示结果弹窗
            if (this.value.trim().length > 0) {
                searchResultsPopup.style.display = 'block';
            }
        });
        
        searchInput.addEventListener('blur', function() {
            // 延迟关闭，以便用户可以点击结果
            setTimeout(() => {
                searchResultsPopup.style.display = 'none';
            }, 200);
        });
        
        searchInput.addEventListener('input', function() {
            if (this.value.trim().length > 0) {
                searchResultsPopup.style.display = 'block';
                // 这里可以添加实际的搜索逻辑
            } else {
                searchResultsPopup.style.display = 'none';
            }
        });

        // 搜索图标点击
        const searchIcon = searchInput.nextElementSibling;
        if (searchIcon) {
            searchIcon.addEventListener('click', function() {
                if (searchInput.value.trim().length > 0) {
                    // 执行搜索
                    window.location.href = '/search/' + encodeURIComponent(searchInput.value.trim());
                }
            });
        }

        // 回车键搜索
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && this.value.trim().length > 0) {
                window.location.href = '/search/' + encodeURIComponent(this.value.trim());
            }
        });
    }
}); 