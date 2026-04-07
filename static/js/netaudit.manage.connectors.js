/**
 * manage_connectors.js
 * Handles the Connectors management page, including modal interactions,
 * password visibility toggle, and connector save/update functionalities.
 */

$(document).ready(function () {

    // Set global dataset name for the connectors.
    window.datasetName = "connectors";

    /**
     * Opens the "Add Connector" modal by resetting the form and enabling the connector name field.
     */
    $('#openModalBtn').on('click', function () {
        $('#modalForm')[0].reset();
        $('#modalTitle').text('Add Connector');
        $('#connectorName').prop('disabled', false);
        $("#modalOverlay").css("display", "flex");
    });

    /**
     * Closes the modal via cancel or close button.
     */
    $('#closeModalBtn').on('click', function () {
        $("#modalOverlay").css("display", "none");
    });

    /**
     * Opens the "Edit Connector" modal, populating fields with connector details
     * fetched from the server based on the connector key.
     */
    $(document).on('click', '.edit-btn', function () {
        const row = $(this).closest('tr');
        const key = row.find('td:eq(1)').text().trim();

        $.getJSON('/netaudit/api/connectors', function (data) {
            const connector = data[key];
            if (!connector) return;

            $('#connectorName').val(key).prop('disabled', true);
            $('#connectorJumphostIp').val(connector.jumphost_ip || '');
            $('#connectorJumphostUser').val(connector.jumphost_username || '');
            $('#connectorJumphostPassword').val(connector.jumphost_password || '');
            $('#connectorNetUser').val(connector.network_username || '');
            $('#connectorNetPassword').val(connector.network_password || '');

            $('#modalTitle').text('Edit Connector');
            $("#modalOverlay").css("display", "flex");
        });
    });

    /**
     * Saves or updates a connector based on the form input. Sends the data
     * to the server and reloads the page on success, or alerts the user on failure.
     */
    $('#modalForm').on('submit', function (e) {
        e.preventDefault();

        const $keyInput = $('#connectorName');
        const key = $keyInput.val().trim();

        if (!$keyInput.prop('disabled') && window.itemExists(key)) {
            $keyInput[0].setCustomValidity('Connector already exists');
            $keyInput[0].reportValidity();
            return;
        } else {
            $keyInput[0].setCustomValidity('');
        }

        const data = {
            jumphost_ip: $('#connectorJumphostIp').val(),
            jumphost_username: $('#connectorJumphostUser').val(),
            jumphost_password: $('#connectorJumphostPassword').val(),
            network_username: $('#connectorNetUser').val(),
            network_password: $('#connectorNetPassword').val()
        };

        $.ajax({
            url: '/netaudit/api/' + window.datasetName,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ key: key, data: data }),
            success: () => location.reload(),
            error: err => alert("Save failed: " + (err.responseJSON?.error || "Unknown error"))
        });
    });

});