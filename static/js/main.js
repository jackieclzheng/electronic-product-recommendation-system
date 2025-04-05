// 前台JavaScript功能
// filename: static/js/main.js

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    $('[data-toggle="tooltip"]').tooltip();
    
    // 初始化轮播图自动播放
    $('.carousel').carousel({
        interval: 5000
    });
    
    // 自动消失的提示信息
    setTimeout(function() {
        $('.alert-dismissible').alert('close');
    }, 5000);
    
    // 产品详情页评价表单
    if (document.getElementById('reviewModal')) {
        $('#reviewModal').on('show.bs.modal', function (event) {
            var button = $(event.relatedTarget);
            var productId = button.data('product-id');
            var modal = $(this);
            modal.find('#product_id').val(productId);
        });
        
        // 星级评分
        $('.rating-input i').on('click', function() {
            var value = parseInt($(this).data('value'));
            $('#rating').val(value);
            
            // 更新星星显示
            $('.rating-input i').each(function() {
                var star = parseInt($(this).data('value'));
                if (star <= value) {
                    $(this).removeClass('far').addClass('fas');
                } else {
                    $(this).removeClass('fas').addClass('far');
                }
            });
        });
    }
    
    // 产品列表页筛选
    if (document.getElementById('filterForm')) {
        // 价格范围滑块
        var priceSlider = document.getElementById('priceRange');
        if (priceSlider) {
            noUiSlider.create(priceSlider, {
                start: [
                    parseInt(priceSlider.dataset.minPrice || 0),
                    parseInt(priceSlider.dataset.maxPrice || 10000)
                ],
                connect: true,
                step: 100,
                range: {
                    'min': 0,
                    'max': 20000
                },
                format: {
                    to: function (value) {
                        return Math.round(value);
                    },
                    from: function (value) {
                        return Math.round(value);
                    }
                }
            });
            
            // 更新价格显示
            var minPriceInput = document.getElementById('min_price');
            var maxPriceInput = document.getElementById('max_price');
            var priceDisplay = document.getElementById('priceDisplay');
            
            priceSlider.noUiSlider.on('update', function (values, handle) {
                var minPrice = values[0];
                var maxPrice = values[1];
                
                minPriceInput.value = minPrice;
                maxPriceInput.value = maxPrice;
                
                if (priceDisplay) {
                    priceDisplay.textContent = '¥' + minPrice + ' - ¥' + maxPrice;
                }
            });
        }
        
        // 自动提交表单
        $('#filterForm select').on('change', function() {
            $('#filterForm').submit();
        });
    }
    
    // 用户行为记录
    $('.product-card').on('click', function(e) {
        var productId = $(this).data('product-id');
        if (productId) {
            // 记录点击行为
            $.post('/api/record_behavior', {
                product_id: productId,
                behavior_type: 'click'
            });
        }
    });
    
    // 收藏按钮
    $('.btn-favorite').on('click', function(e) {
        e.preventDefault();
        var productId = $(this).data('product-id');
        var btn = $(this);
        
        $.post('/api/toggle_favorite', {
            product_id: productId
        }, function(data) {
            if (data.status === 'success') {
                if (data.action === 'add') {
                    btn.find('i').removeClass('far').addClass('fas');
                    btn.attr('title', '取消收藏').tooltip('dispose').tooltip();
                } else {
                    btn.find('i').removeClass('fas').addClass('far');
                    btn.attr('title', '收藏').tooltip('dispose').tooltip();
                }
            }
        });
    });
    
    // 加入购物车
    $('.btn-add-cart').on('click', function(e) {
        e.preventDefault();
        var productId = $(this).data('product-id');
        
        $.post('/api/add_to_cart', {
            product_id: productId,
            quantity: 1
        }, function(data) {
            if (data.status === 'success') {
                // 显示成功提示
                var toast = $('<div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000">' +
                              '<div class="toast-header bg-success text-white">' +
                              '<strong class="mr-auto">成功</strong>' +
                              '<button type="button" class="ml-2 mb-1 close" data-dismiss="toast" aria-label="Close">' +
                              '<span aria-hidden="true">&times;</span></button>' +
                              '</div>' +
                              '<div class="toast-body">已添加到购物车</div>' +
                              '</div>');
                
                $('.toast-container').append(toast);
                toast.toast('show');
                
                // 更新购物车数量
                $('#cartCount').text(data.cart_count);
            }
        });
    });
    
    // 价格趋势图
    if (document.getElementById('priceTrendChart')) {
        var ctx = document.getElementById('priceTrendChart').getContext('2d');
        var chartData = JSON.parse(document.getElementById('priceTrendData').textContent);
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.dates,
                datasets: [
                    {
                        label: '原价',
                        data: chartData.prices,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 2,
                        pointRadius: 3
                    },
                    {
                        label: '优惠价',
                        data: chartData.discount_prices,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        borderWidth: 2,
                        pointRadius: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '¥' + value;
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ¥' + context.raw;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // 平台价格对比图
    if (document.getElementById('platformCompareChart')) {
        var ctx = document.getElementById('platformCompareChart').getContext('2d');
        var chartData = JSON.parse(document.getElementById('platformCompareData').textContent);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.platforms,
                datasets: [{
                    label: '平均价格',
                    data: chartData.prices,
                    backgroundColor: [
                        '#3498db',
                        '#e74c3c',
                        '#2ecc71',
                        '#f39c12'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '¥' + value;
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return '平均价格: ¥' + context.raw;
                            }
                        }
                    }
                }
            }
        });
    }
});
