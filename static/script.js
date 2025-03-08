document.addEventListener("DOMContentLoaded", function () {
    // Xử lý chọn tất cả bài viết
    const selectAllCheckbox = document.getElementById("select-all");
    const checkboxes = document.querySelectorAll(".post-checkbox");
    const deleteButton = document.getElementById("delete-selected");

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener("change", function () {
            checkboxes.forEach(checkbox => checkbox.checked = selectAllCheckbox.checked);
        });
    }

    // Xử lý xóa nhiều bài viết
    if (deleteButton) {
        deleteButton.addEventListener("click", function () {
            let selectedIds = Array.from(checkboxes)
                .filter(checkbox => checkbox.checked)
                .map(checkbox => checkbox.dataset.id);

            if (selectedIds.length === 0) {
                alert("Vui lòng chọn ít nhất một bài viết để xóa.");
                return;
            }

            fetch("/delete_posts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ post_ids: selectedIds })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                location.reload(); // Refresh trang sau khi xóa thành công
            })
            .catch(error => console.error("Lỗi:", error));
        });
    }

    // Xử lý gửi bài viết mới
    const postForm = document.querySelector("form");
    if (postForm) {
        postForm.addEventListener("submit", function (event) {
            event.preventDefault();
            let formData = new FormData(postForm);
            
            fetch("/dashboard", {
                method: "POST",
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.success) {
                    location.reload(); // Refresh trang sau khi đăng bài thành công
                }
            })
            .catch(error => console.error("Lỗi:", error));
        });
    }
});