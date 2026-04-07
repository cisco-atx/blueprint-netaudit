/**
 * Handles device follow-up modal actions and audit run operations.
 */

$(document).ready(function () {
    const followUpModal = $("#modalOverlay");
    let followUpDevices = [];

    /**
     * Opens the follow-up modal and populates it based on selected devices.
     * @param {Array|string} devices - Device IDs to follow up.
     */
    function openFollowUpModal(devices) {
        followUpDevices = Array.isArray(devices) ? devices : [devices];

        if (followUpDevices.length === 1) {
            const deviceId = followUpDevices[0];
            const row = $(`.row-check[data-id="${deviceId}"]`).closest("tr");

            if (row.length) {
                const actionText = row.find("td:nth-child(4)").text().trim();
                const commentText = row.data("comments") || "";
                $("#userActionSelect").val(actionText);
                $("#userComment").val(commentText);
            } else {
                const actionText = $(".device-infotable tr:has(th:contains('Action Taken')) td").text().trim();
                const commentText = $(".device-infotable tr:has(th:contains('Comments')) td").text().trim();
                $("#userActionSelect").val(actionText);
                $("#userComment").val(commentText);
            }
        } else {
            $("#userActionSelect").val("");
            $("#userComment").val("");
        }

        followUpModal.css("display", "flex");
    }

    /**
     * Closes the follow-up modal and clears device-specific data.
     */
    function closeFollowUpModal() {
        followUpDevices = [];
        followUpModal.css("display", "none");
    }

    /**
     * Initiates the audit process for selected devices and view.
     * @param {Array} devices - Array of device identifiers.
     * @param {string} view - The current view context.
     */

    async function startAuditFlow(devices, view, btn) {
        if (!devices.length) return;

        let originalHtml = null;

        try {
            const deviceConnectorMap = await ensureDeviceConnectors(devices);

            const payload = {
                devices: deviceConnectorMap,
                view
            };

            originalHtml = btn.html();
            btn.prop("disabled", true).html('<span class="material-icons spin">autorenew</span> Running...');

            await $.ajax({
                url: '/netaudit/results/run',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(payload)
            });

            btn.prop("disabled", false).html(originalHtml);
            if (window.loadAuditView && window.currentAuditView) {
                window.loadAuditView(window.currentAuditView);
            }

        } catch (err) {
            console.error(err);
            alert("Failed to start audit");

            // restore button ONLY on failure
            btn.prop("disabled", false).html(originalHtml);
        }
    }

    /**
     * Export audit results for one or more devices
     */
    function exportAuditResults(devices, btn = null) {
        if (!devices.length) return;

        let originalHtml = null;

        if (btn) {
            originalHtml = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="material-icons spin">autorenew</span> Exporting…';
        }

        fetch("/netaudit/results/snap", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ device_ids: devices })
        })
        .then(response => {
            if (!response.ok) throw new Error("Export failed");

            const disposition = response.headers.get("Content-Disposition");
            let filename = "audit_results.zip";

            if (disposition && disposition.includes("filename=")) {
                filename = disposition
                    .split("filename=")[1]
                    .replace(/"/g, "")
                    .trim();
            }

            return response.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        })
        .catch(err => {
            console.error(err);
            alert("Failed to export audit results");
        })
        .finally(() => {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        });
    }

    // Expose functions to global scope
    window.openFollowUpModal = openFollowUpModal;
    window.closeFollowUpModal = closeFollowUpModal;
    window.startAuditFlow = startAuditFlow;
    window.exportAuditResults = exportAuditResults;

    // Modal button handlers
    $("#closeModalBtn").on("click", closeFollowUpModal);

    // Save Follow-Up
    $("#saveBtn").on("click", function () {
        const user_action = $("#userActionSelect").val();
        const user_comments = $("#userComment").val();

        if (!followUpDevices.length) return;

        $.ajax({
            url: '/netaudit/api/results/followup',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ devices: followUpDevices, user_action, user_comments }),
            success: () => {
                closeFollowUpModal();
                if (window.loadAuditView && window.currentAuditView) {
                    window.loadAuditView(window.currentAuditView);
                } else {
                    location.reload();
                }
            },
            error: () => alert("Follow up save failed")
        });

        closeFollowUpModal();
    });
});
