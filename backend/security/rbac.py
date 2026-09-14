"""
Role-Based Access Control (RBAC) permission definitions and hierarchy.
Strictly conforms to 07_AUTH_SECURITY.md (Section 7.1) and 04_API_SPEC.md.
"""

from typing import List, Set


# Canonical System Permissions
class Permissions:
    # Investigator base permissions
    CASE_READ = "CASE_READ"
    CASE_UPDATE = "CASE_UPDATE"
    DOCUMENT_READ = "DOCUMENT_READ"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    ENTITY_CREATE = "ENTITY_CREATE"
    ENTITY_READ = "ENTITY_READ"
    ENTITY_WRITE = "ENTITY_WRITE"
    GRAPH_READ = "GRAPH_READ"
    NOTES_WRITE = "NOTES_WRITE"
    TIMELINE_READ = "TIMELINE_READ"

    # Analyst extended permissions
    ANALYSIS_TRIGGER = "ANALYSIS_TRIGGER"
    REVIEW_STAGE = "REVIEW_STAGE"
    QUERY_SAVE = "QUERY_SAVE"
    IMPORT_DATA = "IMPORT_DATA"
    PATTERN_DETECT = "PATTERN_DETECT"

    # Supervisor governance and export permissions
    CASE_CREATE = "CASE_CREATE"
    CASE_ARCHIVE = "CASE_ARCHIVE"
    CASE_ASSIGN_MEMBER = "CASE_ASSIGN_MEMBER"
    DOCUMENT_DELETE = "DOCUMENT_DELETE"
    REVIEW_OVERRIDE = "REVIEW_OVERRIDE"
    AUDIT_READ = "AUDIT_READ"
    EXPORT_REPORT = "EXPORT_REPORT"
    ENTITY_MERGE_APPROVE = "ENTITY_MERGE_APPROVE"


# Canonical System Roles
class SystemRoles:
    INVESTIGATOR = "INVESTIGATOR"
    ANALYST = "ANALYST"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"


# Investigator Permissions Set
INVESTIGATOR_PERMISSIONS: Set[str] = {
    Permissions.CASE_READ,
    Permissions.CASE_UPDATE,
    Permissions.DOCUMENT_READ,
    Permissions.DOCUMENT_UPLOAD,
    Permissions.ENTITY_CREATE,
    Permissions.ENTITY_READ,
    Permissions.ENTITY_WRITE,
    Permissions.GRAPH_READ,
    Permissions.NOTES_WRITE,
    Permissions.TIMELINE_READ,
}

# Analyst Permissions Set: Investigator + Analysis capabilities
ANALYST_PERMISSIONS: Set[str] = INVESTIGATOR_PERMISSIONS | {
    Permissions.ANALYSIS_TRIGGER,
    Permissions.REVIEW_STAGE,
    Permissions.QUERY_SAVE,
    Permissions.IMPORT_DATA,
    Permissions.PATTERN_DETECT,
}

# Supervisor Permissions Set: Analyst + Governance + Override + Audit + Export
SUPERVISOR_PERMISSIONS: Set[str] = ANALYST_PERMISSIONS | {
    Permissions.CASE_CREATE,
    Permissions.CASE_ARCHIVE,
    Permissions.CASE_ASSIGN_MEMBER,
    Permissions.DOCUMENT_DELETE,
    Permissions.REVIEW_OVERRIDE,
    Permissions.AUDIT_READ,
    Permissions.EXPORT_REPORT,
    Permissions.ENTITY_MERGE_APPROVE,
}

# Role-to-Permissions Mapping
ROLE_PERMISSIONS_MAP = {
    SystemRoles.INVESTIGATOR: INVESTIGATOR_PERMISSIONS,
    SystemRoles.ANALYST: ANALYST_PERMISSIONS,
    SystemRoles.SUPERVISOR: SUPERVISOR_PERMISSIONS,
    SystemRoles.ADMIN: SUPERVISOR_PERMISSIONS,  # ADMIN holds supervisor capabilities
}


def get_permissions_for_roles(roles: List[str]) -> Set[str]:
    """
    Aggregates all distinct permissions granted to a given list of role names.
    Roles are normalized to uppercase.
    """
    granted: Set[str] = set()
    for role in roles:
        normalized = role.strip().upper()
        if normalized in ROLE_PERMISSIONS_MAP:
            granted.update(ROLE_PERMISSIONS_MAP[normalized])
    return granted


def has_permission(roles: List[str], required_permission: str) -> bool:
    """
    Evaluates whether the provided roles grant the specified required permission.
    """
    if not required_permission:
        return True
    granted = get_permissions_for_roles(roles)
    return required_permission in granted
