$(document).ready(function () {

    const viewsPanel = $("#viewsDockPanel");
    const viewFilterInput = $("#viewFilterInput");
    const viewsBtn = $("#viewsBtn");

    if (!$("#resultsDatatable").length) return;

    let table = null;
    let currentView = null;

    const followupBtn = $("#followupBtn");
    const runAuditBtn = $("#runAuditBtn");
    const exportAuditBtn = $("#exportAuditBtn");


function openViewsPanel() {
        viewsPanel.addClass("open");

        // change toggle icon
        viewsBtn.find(".toggle-icon").text("chevron_right");

        // reset search
        viewFilterInput.val("").trigger("keyup");
        viewFilterInput.focus();
    }

      function closeViewsPanel() {
        viewsPanel.removeClass("open");

        // restore icon
        viewsBtn.find(".toggle-icon").text("chevron_left");
    }

    function toggleViewsPanel() {
        viewsPanel.hasClass("open")
            ? closeViewsPanel()
            : openViewsPanel();
    }

    viewsBtn.on("click", function (e) {
        e.stopPropagation();
        toggleViewsPanel();
    });

     $(document).on("click", function (e) {
        if (
            viewsPanel.hasClass("open") &&
            !$(e.target).closest("#viewsDockPanel, #viewsBtn").length
        ) {
            closeViewsPanel();
        }
    });

        viewsPanel.on("click", function (e) {
        e.stopPropagation();
    });


    // filter views
    viewFilterInput.on("keyup", function () {
        const value = $(this).val().toLowerCase();

        $(".dock-item").each(function () {
            const text = $(this).find(".view-name").text().toLowerCase();
            $(this).toggle(text.includes(value));
        });
    });

    function toggleActionBtns() {
        const checked = $(".row-check:checked").length;
        const show = checked > 0 ? "inline-flex" : "none";

        followupBtn.css("display", show);
        runAuditBtn.css("display", show);
        exportAuditBtn.css("display", show);
    }

    $(document).on("change", "#selectAll", function () {
        $(".row-check").prop("checked", this.checked);
        toggleActionBtns();
    });

    $(document).on("change", ".row-check", function () {
        toggleActionBtns();
    });

    function bindColumnFilters() {
        $("#resultsDatatable thead tr:eq(1) th input.col-filter").each(function () {
            const colIndex = $(this).data("col") + 1;

            $(this).on("keyup change clear", function () {
                const value = this.value;

                if (table) {
                    table.column(colIndex).search(value).draw();
                }
            });
        });
    }

    function buildTableHeader(columns) {
        const headerRow = `
            <tr>
                <th><input type="checkbox" id="selectAll"></th>
                ${columns.map(col => `<th>${col}</th>`).join("")}
            </tr>
        `;

        const filterRow = `
            <tr>
                <th></th>
                ${columns.map((col, index) => `
                    <th>
                        <input
                            type="text"
                            class="col-filter"
                            data-col="${index}"
                            placeholder="Filter ${col}"
                        >
                    </th>
                `).join("")}
            </tr>
        `;

        $("#resultsDatatable thead").html(headerRow + filterRow);
    }

    function buildTableBody(rows) {
        const tbodyHtml = rows.map(row => {
            const checkCols = row.checks.map(check => `
                <td class="check-col text-center">
                    ${renderStatusBadge(check)}
                </td>
            `).join("");

            return `
                <tr>
                    <td>
                        <input
                            type="checkbox"
                            class="row-check"
                            data-id="${row.device_id}"
                        >
                    </td>
                    <td>
                        <div class="hostname-cell">
                            <a
                                class="hostname-text"
                                href="/netaudit/results/device/${row.device_id}?view=${encodeURIComponent(currentView || "")}"
                            >
                                ${row.hostname}
                            </a>
                            <div class="last-audit">
                                <span class="material-icons" style="font-size:16px;">schedule</span>
                                <span>${row.last_audit || ""}</span>
                            </div>
                        </div>
                    </td>
                    <td>${renderStatusBadge(row.overall)}</td>
                    <td><div style="white-space: nowrap;">${row.action_taken || ""}</div></td>
                    ${checkCols}
                </tr>
            `;
        }).join("");

        $("#resultsDatatable tbody").html(tbodyHtml);
    }

    function updateViewsButton(viewName) {
        const selectedView = $(`.dock-item[data-view="${viewName}"]`);
        const selectedIcon = selectedView.find(".material-icons:first").text().trim();

        $("#viewsBtn .label").text(viewName);

        if (selectedIcon) {
            $("#viewsBtn .view-icon").text(selectedIcon);
        }

        $(".dock-item").removeClass("active");
        selectedView.addClass("active");
    }

    function renderStatusBadge(status) {
        const item = STATUS_CODES[status] || {
            label: "Unknown",
            icon: "help",
            description: ""
        };

        const className = item.label
            .toLowerCase()
            .replace(/\s+/g, "");

        return `
            <span
                class="badge status-${className}"
                title="${item.description || ""}"
            >
                <span class="material-icons">${item.icon}</span>
                <span>${item.label}</span>
            </span>
        `;
    }

    function showLoadingDataTable() {

        if ($.fn.DataTable.isDataTable("#resultsDatatable")) {
            $("#resultsDatatable").DataTable().destroy();
        }

        table = $("#resultsDatatable").DataTable({
            orderCellsTop: true,
            fixedHeader: true,
            paging: true,
            searching: true,
            info: true,
            autoWidth: true,
            columnDefs: [
                { width: "30px", targets: 0 }
            ]
        });
        bindColumnFilters();
    }

    function rebuildDataTable(columns, rows) {
        if ($.fn.DataTable.isDataTable("#resultsDatatable")) {
            $("#resultsDatatable").DataTable().destroy();
        }

        buildTableHeader(columns);
        buildTableBody(rows);

        table = $("#resultsDatatable").DataTable({
            orderCellsTop: true,
            fixedHeader: true,
            paging: true,
            searching: true,
            info: true,
            autoWidth: true,
            columnDefs: [
                { width: "30px", targets: 0 }
            ]
        });

        bindColumnFilters();
        toggleActionBtns();
    }

    function loadView(viewName) {
        currentView = viewName;
        window.currentAuditView = viewName;

        localStorage.setItem("lastAuditView", viewName);

        showLoadingDataTable();

        $.ajax({
            url: `/netaudit/results/view/${viewName}`,
            method: "GET",
            success: function (response) {
                rebuildDataTable(response.columns, response.rows);
                $("#viewsBtn .label").text(viewName);
                updateViewsButton(viewName);
            },
            error: function () {
                $("#resultsDatatable tbody").html(`
                    <tr>
                        <td colspan="4" class="text-center loading-row">
                            Failed to load data.
                        </td>
                    </tr>
                `);
            }
        });
    }

    $("#viewsMenu").on("click", ".dock-item", function (e) {
        e.preventDefault();
        e.stopPropagation();

        const viewName = $(this).data("view");

        closeViewsPanel();
        loadView(viewName);
    });

    $("#followupBtn").on("click", function () {
        const selected = $(".row-check:checked")
            .map(function () {
                return $(this).data("id");
            })
            .get();

        if (selected.length) {
            window.openFollowUpModal(selected);
        }
    });

    $("#runAuditBtn").on("click", async function () {
        const selected = $(".row-check:checked")
            .map(function () {
                return $(this).data("id");
            })
            .get();

        if (!selected.length) return;

        try {
            await startAuditFlow(selected, currentView, $(this));
            loadView(currentView);
        } catch (error) {
            console.error("Audit failed:", error);
        }
    });

    $("#exportAuditBtn").on("click", function () {
        const selected = $(".row-check:checked")
            .map(function () {
                return $(this).data("id");
            })
            .get();

        window.exportAuditResults(selected, this);
    });

    window.loadAuditView = loadView;

    const savedView = localStorage.getItem("lastAuditView");
    const firstView = $(".dock-item:first").data("view");

    const initialView = savedView || firstView;

    showLoadingDataTable();

    if (initialView) {
        loadView(initialView);
    }
});