USER_ACTIONS = {
    "Action Required": {"icon": "notification_important", "color": "warning"},
    "Remediated": {"icon": "undo", "color": "primary"},
    "Reviewed - OK": {"icon": "thumb_up", "color": "info"},
    "False Positive": {"icon": "check_circle", "color": "success"},
    "Accepted Risk": {"icon": "warning", "color": "danger"},
}

# Status codes for audit checks.
AUDIT_STATUS_CODES = {
    0: {"label": "NOT RUN",
        "icon": "do_not_disturb_on",
        "description": "Check has not executed yet",
        "excel_color": "#D9D9D9",
        },
    1: {"label": "PASS",
        "icon": "check_circle",
        "description": "Check conditions fully satisfied",
        "excel_color": "#C6EFCE",
        },
    2: {"label": "FAIL",
        "icon": "x_circle",
        "description": "Check conditions violated",
        "excel_color": "#FFC7CE",
        },
    3: {"label": "WARN",
        "icon": "warning",
        "description": "Partial compliance, risk detected, or best-practice deviation",
        "excel_color": "#FFEBAB",
        },
    4: {"label": "INFO",
        "icon": "info",
        "description": "Informational check (no pass/fail semantics)",
        "excel_color": "#9ED9EC",
        },
    5: {"label": "ERROR",
        "icon": "error",
        "description": "Execution/parsing error, command failed, unexpected output",
        "excel_color": "#F99D9D",
        },
    6: {"label": "INCONCLUSIVE",
        "icon": "help",
        "description": "Output insufficient or ambiguous",
        "excel_color": "#A7D8E3",
        },
}

# Material icons for different device views.
VIEW_ICONS = [
    "account_tree",
    "globe",
    "wifi",
    "devices",
    "database",
    "storage",
    "cloud",
    "dns",
    "domain"
]