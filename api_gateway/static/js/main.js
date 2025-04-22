// Biến lưu trữ dữ liệu toàn cục
let products = [];
let orderItems = [];

// Hàm khởi tạo khi trang được tải
document.addEventListener('DOMContentLoaded', function() {
    // Kiểm tra trạng thái dịch vụ
    checkHealth();
    
    // Tải danh sách sản phẩm
    loadProducts();
    
    // Khởi tạo sự kiện
    initEventListeners();
    
    // Cập nhật biểu tượng
    feather.replace();
});

// Khởi tạo các sự kiện
function initEventListeners() {
    // Thêm sản phẩm vào đơn hàng
    document.getElementById('add-item').addEventListener('click', addOrderItem);
    
    // Tạo đơn hàng
    document.getElementById('create-order-form').addEventListener('submit', createOrder);
    
    // Kiểm tra đơn hàng
    document.getElementById('check-order').addEventListener('click', checkOrderStatus);
    
    // Thêm sản phẩm mới
    document.getElementById('submit-product').addEventListener('click', addNewProduct);
    
    // Cập nhật tổng tiền khi số lượng sản phẩm thay đổi
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('product-select') || e.target.classList.contains('product-quantity')) {
            updateTotalAmount();
        }
    });
}

// Kiểm tra trạng thái dịch vụ
function checkHealth() {
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            const healthTable = document.getElementById('health-status');
            let html = '';
            
            // API Gateway
            html += `
                <tr>
                    <td>API Gateway</td>
                    <td><span class="badge ${data.gateway === 'up' ? 'bg-success' : 'bg-danger'}">${data.gateway === 'up' ? 'Hoạt động' : 'Ngừng hoạt động'}</span></td>
                    <td>-</td>
                </tr>
            `;
            
            // Services
            for (const [service, info] of Object.entries(data.services)) {
                html += `
                    <tr>
                        <td>${service.charAt(0).toUpperCase() + service.slice(1)} Service</td>
                        <td><span class="badge ${info.status === 'up' ? 'bg-success' : 'bg-danger'}">${info.status === 'up' ? 'Hoạt động' : 'Ngừng hoạt động'}</span></td>
                        <td>${info.status === 'up' ? (info.details.version || '-') : 'Không thể kết nối'}</td>
                    </tr>
                `;
            }
            
            healthTable.innerHTML = html;
            feather.replace();
        })
        .catch(error => {
            console.error('Lỗi khi kiểm tra trạng thái dịch vụ:', error);
            showAlert('Không thể kiểm tra trạng thái dịch vụ. Vui lòng thử lại sau.', 'danger');
        });
}

// Tải danh sách sản phẩm
function loadProducts() {
    fetch('/api/products')
        .then(response => response.json())
        .then(data => {
            products = data;
            
            // Cập nhật số lượng sản phẩm
            document.getElementById('product-count').textContent = products.length;
            
            // Cập nhật bảng sản phẩm
            const productList = document.getElementById('product-list');
            if (products.length === 0) {
                productList.innerHTML = '<tr><td colspan="5" class="text-center">Không có sản phẩm</td></tr>';
                return;
            }
            
            let html = '';
            products.forEach(product => {
                html += `
                    <tr>
                        <td>${product.id}</td>
                        <td>${product.name}</td>
                        <td>${formatCurrency(product.price)}</td>
                        <td>${product.stock}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary me-1">
                                <i data-feather="eye"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-warning me-1">
                                <i data-feather="edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger">
                                <i data-feather="trash-2"></i>
                            </button>
                        </td>
                    </tr>
                `;
            });
            
            productList.innerHTML = html;
            
            // Cập nhật danh sách sản phẩm trong dropdown
            updateProductDropdowns();
            
            feather.replace();
        })
        .catch(error => {
            console.error('Lỗi khi tải danh sách sản phẩm:', error);
            document.getElementById('product-list').innerHTML = '<tr><td colspan="5" class="text-center text-danger">Lỗi khi tải danh sách sản phẩm</td></tr>';
            showAlert('Không thể tải danh sách sản phẩm. Vui lòng kiểm tra kết nối đến Inventory Service.', 'danger');
        });
}

// Cập nhật danh sách sản phẩm trong dropdown
function updateProductDropdowns() {
    const productSelects = document.querySelectorAll('.product-select');
    
    productSelects.forEach(select => {
        const currentValue = select.value;
        let html = '<option value="">Chọn sản phẩm</option>';
        
        products.forEach(product => {
            html += `<option value="${product.id}" data-price="${product.price}" ${currentValue == product.id ? 'selected' : ''}>${product.name} - ${formatCurrency(product.price)}</option>`;
        });
        
        select.innerHTML = html;
    });
}

// Thêm sản phẩm vào đơn hàng
function addOrderItem() {
    const orderItems = document.getElementById('order-items');
    const newItem = document.createElement('div');
    newItem.className = 'row mb-2';
    newItem.innerHTML = `
        <div class="col-md-6">
            <select class="form-select product-select" required>
                <option value="">Chọn sản phẩm</option>
            </select>
        </div>
        <div class="col-md-4">
            <input type="number" class="form-control product-quantity" placeholder="Số lượng" min="1" value="1" required>
        </div>
        <div class="col-md-2">
            <button type="button" class="btn btn-danger remove-item">Xóa</button>
        </div>
    `;
    
    orderItems.appendChild(newItem);
    
    // Cập nhật danh sách sản phẩm trong dropdown
    updateProductDropdowns();
    
    // Thêm sự kiện cho nút xóa
    newItem.querySelector('.remove-item').addEventListener('click', function() {
        orderItems.removeChild(newItem);
        updateTotalAmount();
    });
    
    feather.replace();
}

// Cập nhật tổng tiền
function updateTotalAmount() {
    let total = 0;
    const items = document.querySelectorAll('#order-items .row');
    
    items.forEach(item => {
        const select = item.querySelector('.product-select');
        const quantity = item.querySelector('.product-quantity').value;
        
        if (select.value) {
            const selectedOption = select.options[select.selectedIndex];
            const price = selectedOption.getAttribute('data-price');
            total += price * quantity;
        }
    });
    
    document.getElementById('total-amount').textContent = formatCurrency(total);
}

// Tạo đơn hàng mới
function createOrder(e) {
    e.preventDefault();
    
    const customerId = document.getElementById('customer_id').value;
    const shippingAddress = document.getElementById('shipping_address').value;
    const paymentMethod = document.getElementById('payment_method').value;
    
    // Lấy thông tin sản phẩm
    const items = [];
    let totalAmount = 0;
    
    document.querySelectorAll('#order-items .row').forEach(item => {
        const productId = item.querySelector('.product-select').value;
        const quantity = parseInt(item.querySelector('.product-quantity').value);
        
        if (productId && quantity > 0) {
            const product = products.find(p => p.id == productId);
            const itemTotal = product.price * quantity;
            
            items.push({
                product_id: productId,
                quantity: quantity,
                price: product.price,
                subtotal: itemTotal
            });
            
            totalAmount += itemTotal;
        }
    });
    
    if (items.length === 0) {
        showAlert('Vui lòng chọn ít nhất một sản phẩm', 'warning');
        return;
    }
    
    // Dữ liệu đơn hàng
    const orderData = {
        customer_id: customerId,
        shipping_address: shippingAddress,
        payment_method: paymentMethod,
        items: items,
        total_amount: totalAmount
    };
    
    // Gửi yêu cầu tạo đơn hàng
    fetch('/api/orders', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(orderData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
        } else {
            showAlert('Đơn hàng đã được tạo thành công!', 'success');
            // Cập nhật số lượng đơn hàng
            document.getElementById('order-count').textContent = parseInt(document.getElementById('order-count').textContent || 0) + 1;
            
            // Hiển thị thông tin đơn hàng
            showOrderDetails(data);
            
            // Xóa form
            document.getElementById('create-order-form').reset();
            document.getElementById('order-items').innerHTML = `
                <div class="row mb-2">
                    <div class="col-md-6">
                        <select class="form-select product-select" required>
                            <option value="">Chọn sản phẩm</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <input type="number" class="form-control product-quantity" placeholder="Số lượng" min="1" value="1" required>
                    </div>
                    <div class="col-md-2">
                        <button type="button" class="btn btn-danger remove-item" disabled>Xóa</button>
                    </div>
                </div>
            `;
            
            // Cập nhật danh sách sản phẩm trong dropdown
            updateProductDropdowns();
            
            // Cập nhật tổng tiền
            document.getElementById('total-amount').textContent = '0 VNĐ';
        }
    })
    .catch(error => {
        console.error('Lỗi khi tạo đơn hàng:', error);
        showAlert('Không thể tạo đơn hàng. Vui lòng thử lại sau.', 'danger');
    });
}

// Kiểm tra trạng thái đơn hàng
function checkOrderStatus() {
    const orderId = document.getElementById('order-id-search').value.trim();
    const paymentId = document.getElementById('payment-id-search').value.trim();
    const shippingId = document.getElementById('shipping-id-search').value.trim();
    
    if (!paymentId && !shippingId) {
        showAlert('Vui lòng nhập Payment ID hoặc Shipping ID', 'warning');
        return;
    }
    
    let paymentPromise = Promise.resolve(null);
    let shippingPromise = Promise.resolve(null);
    
    // Kiểm tra thông tin thanh toán
    if (paymentId) {
        paymentPromise = fetch(`/api/payments/${paymentId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Không tìm thấy thông tin thanh toán với ID: ${paymentId}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error('Lỗi khi tìm thông tin thanh toán:', error);
                showAlert('Không tìm thấy thông tin thanh toán. Vui lòng kiểm tra lại ID.', 'danger');
                return null;
            });
    }
    
    // Kiểm tra thông tin vận chuyển
    if (shippingId) {
        shippingPromise = fetch(`/api/shipping/${shippingId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Không tìm thấy thông tin vận chuyển với ID: ${shippingId}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error('Lỗi khi tìm thông tin vận chuyển:', error);
                showAlert('Không tìm thấy thông tin vận chuyển. Vui lòng kiểm tra lại ID.', 'danger');
                return null;
            });
    }
    
    // Kết hợp kết quả
    Promise.all([paymentPromise, shippingPromise])
        .then(([payment, shipping]) => {
            if (!payment && !shipping) {
                return;
            }
            
            const orderData = {
                order_id: orderId || "N/A",
                payment: payment || {
                    id: "N/A",
                    status: "unknown"
                },
                shipping: shipping || {
                    id: "N/A",
                    status: "unknown"
                },
                status: "Đã tìm thấy thông tin đơn hàng"
            };
            
            showOrderDetails(orderData);
        });
}

// Hiển thị thông tin đơn hàng
function showOrderDetails(order) {
    const orderDetails = document.getElementById('order-details');
    
    let paymentStatusClass = 'bg-secondary';
    if (order.payment.status === 'completed') paymentStatusClass = 'bg-success';
    else if (order.payment.status === 'pending') paymentStatusClass = 'bg-warning';
    else if (order.payment.status === 'failed') paymentStatusClass = 'bg-danger';
    
    let shippingStatusClass = 'bg-secondary';
    if (order.shipping.status === 'delivered') shippingStatusClass = 'bg-success';
    else if (order.shipping.status === 'shipped') shippingStatusClass = 'bg-info';
    else if (order.shipping.status === 'processing') shippingStatusClass = 'bg-warning';
    
    orderDetails.innerHTML = `
        <div class="alert alert-info">
            <h4 class="alert-heading">Đơn Hàng #${order.order_id}</h4>
            <p class="mb-0">${order.status}</p>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-header">Thanh Toán</div>
                    <div class="card-body">
                        <p><strong>ID:</strong> ${order.payment.id}</p>
                        <p><strong>Phương thức:</strong> ${getPaymentMethodName(order.payment.payment_method)}</p>
                        <p><strong>Số tiền:</strong> ${formatCurrency(order.payment.amount)}</p>
                        <p><strong>Trạng thái:</strong> <span class="badge ${paymentStatusClass}">${getPaymentStatusName(order.payment.status)}</span></p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card mb-3">
                    <div class="card-header">Vận Chuyển</div>
                    <div class="card-body">
                        <p><strong>ID:</strong> ${order.shipping.id}</p>
                        <p><strong>Trạng thái:</strong> <span class="badge ${shippingStatusClass}">${getShippingStatusName(order.shipping.status)}</span></p>
                        <p><strong>Ngày dự kiến giao hàng:</strong> ${order.shipping.estimated_delivery || 'Chưa xác định'}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Thêm sản phẩm mới
function addNewProduct() {
    const name = document.getElementById('product-name').value;
    const price = document.getElementById('product-price').value;
    const stock = document.getElementById('product-stock').value;
    const description = document.getElementById('product-description').value;
    
    if (!name || !price || !stock) {
        showAlert('Vui lòng điền đầy đủ thông tin sản phẩm', 'warning');
        return;
    }
    
    const productData = {
        name: name,
        price: parseInt(price),
        stock: parseInt(stock),
        description: description
    };
    
    // Gửi yêu cầu thêm sản phẩm
    fetch('/api/products', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(productData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'danger');
        } else {
            showAlert('Sản phẩm đã được thêm thành công!', 'success');
            // Đóng modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addProductModal'));
            modal.hide();
            
            // Xóa form
            document.getElementById('add-product-form').reset();
            
            // Tải lại danh sách sản phẩm
            loadProducts();
        }
    })
    .catch(error => {
        console.error('Lỗi khi thêm sản phẩm:', error);
        showAlert('Không thể thêm sản phẩm. Vui lòng thử lại sau.', 'danger');
    });
}

// Hiển thị thông báo
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Chèn thông báo vào đầu container
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Tự động đóng thông báo sau 5 giây
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

// Định dạng tiền tệ
function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
}

// Lấy tên phương thức thanh toán
function getPaymentMethodName(method) {
    const methods = {
        'credit_card': 'Thẻ Tín Dụng',
        'bank_transfer': 'Chuyển Khoản',
        'cod': 'Thanh Toán Khi Nhận Hàng'
    };
    return methods[method] || method;
}

// Lấy tên trạng thái thanh toán
function getPaymentStatusName(status) {
    const statuses = {
        'completed': 'Đã thanh toán',
        'pending': 'Đang xử lý',
        'failed': 'Thất bại'
    };
    return statuses[status] || status;
}

// Lấy tên trạng thái vận chuyển
function getShippingStatusName(status) {
    const statuses = {
        'delivered': 'Đã giao hàng',
        'shipped': 'Đang vận chuyển',
        'processing': 'Đang xử lý',
        'cancelled': 'Đã hủy'
    };
    return statuses[status] || status;
}
