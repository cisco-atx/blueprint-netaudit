/**
 * netaudit.results.device.js
 *
 * This JavaScript file is responsible for handling the interactions and functionalities
 * related to the device results table in the NetAudit application. It initializes the
 * DataTable for displaying device results, manages the opening and closing of modals
 * for viewing raw logs and follow-up actions, and handles the initiation of audit processes
 * and exporting of audit reports for individual devices.
 *
 * Main functionalities include:
 * - Initializing the DataTable with specific configurations.
 * - Handling click events for buttons to open modals and initiate actions.
 * - Managing the user interface elements related to device results.
 */



$(document).ready(function () {
    // Initialize the DataTable for device result table if it exists
    if ($("#deviceResultstable").length) {
        $('#deviceResultstable').DataTable({
            orderCellsTop: true,
            fixedHeader: true,
            paging: false,
            searching: false,
            info: false,
            autoWidth: true,
            columnDefs: [{ width: '300px', targets: 0 }],
        });
    }

    /**
    * Opens logs modal for a specific device when the Raw Logs button is clicked.
    */
    $(document).on("click", "#logsBtn", function () {
        const deviceId = $(this).data("id");
        if (deviceId) {
            $("#logsModalOverlay").css("display", "flex");
        }
    });

    $(document).on("click", "#closeLogsModalBtn", function () {
        $("#logsModalOverlay").css("display", "none");
    });

    /**
     * Opens the Follow-Up modal for a single device when the Follow-Up button is clicked.
     */
    $(document).on("click", "#followupBtn", function () {
        const deviceId = $(this).data("id");
        if (deviceId) {
            window.openFollowUpModal(deviceId);
        }
    });

    /**
     * Disables the Run Audit button, shows a loading indicator, and initiates
     * an audit process for a single device when the Run Audit button is clicked.
     */
    $(document).on("click", "#runAuditBtn", function () {
        const btn = $(this);
        const deviceId = btn.data("id");
        const view = btn.data("view");

        if (deviceId) {
            window.startAuditFlow([deviceId], view, btn);
        }
    });


    /**
     * Exports the audit report for a single device when the Export Audit button is clicked.
     */
    $(document).on("click", "#exportAuditBtn", function () {
        const deviceId = $(this).data("id");
        window.exportAuditResults([deviceId], this);
    });
});