/* ==========================================================================
   CodeAlpha Restaurant Management — script.js
   Small helper behaviours for the UI (no framework needed).
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function () {
    // ---- Mobile navbar toggle ----
    const navToggle = document.getElementById("navToggle");
    const navLinks = document.querySelector(".navbar-links");
    if (navToggle && navLinks) {
        navToggle.addEventListener("click", function () {
            navLinks.classList.toggle("open");
        });
    }

    // ---- Auto-dismiss flash messages after 5 seconds ----
    document.querySelectorAll(".flash").forEach(function (flash) {
        setTimeout(function () {
            flash.style.transition = "opacity 0.4s ease";
            flash.style.opacity = "0";
            setTimeout(function () { flash.remove(); }, 400);
        }, 5000);
    });

    // ---- Live order total calculator (used on /order/create) ----
    const orderForm = document.getElementById("orderForm");
    if (orderForm) {
        const totalDisplay = document.getElementById("orderTotalValue");

        function recalcTotal() {
            let total = 0;
            document.querySelectorAll(".order-item-row").forEach(function (row) {
                const checkbox = row.querySelector('input[type="checkbox"]');
                const qtyInput = row.querySelector('input[type="number"]');
                const price = parseFloat(row.dataset.price || "0");

                if (checkbox && checkbox.checked) {
                    const qty = parseInt(qtyInput.value || "0", 10);
                    total += price * qty;
                    qtyInput.disabled = false;
                } else if (qtyInput) {
                    qtyInput.disabled = true;
                }
            });
            if (totalDisplay) {
                totalDisplay.textContent = "₹" + total.toFixed(2);
            }
        }

        orderForm.addEventListener("change", recalcTotal);
        orderForm.addEventListener("input", recalcTotal);
        recalcTotal(); // run once on page load
    }
});
