import os
from typing import List, Dict, Optional

from ...students import index_db as index
from ...students import student_db as student


def create_package(data_dir: str, master_key: bytes, student_uuid: str, package_data: dict) -> int:
    """
    Create a new package for a student, update next_invoice in the index,
    and return the new package ID.
    """
    key = index.get_student_db_key_from_dir(data_dir, master_key, student_uuid)
    if not key:
        raise ValueError(f"Student {student_uuid} not found")

    student_db_dir = os.path.join(data_dir, 'students')
    sconn = student.open_student_db(student_db_dir, student_uuid, key)
    try:
        pid = student.add_package(sconn, package_data)
    finally:
        sconn.close()

    # Recalculate invoice for this student
    recalculate_invoice(data_dir, master_key, student_uuid)
    # Update linked students (if invoice grouping is active)
    _recalc_linked_invoices(data_dir, master_key, student_uuid)

    return pid


def update_package(data_dir: str, master_key: bytes, student_uuid: str, package_id: int, updates: dict):
    """Update fields of an existing package and recalc invoices."""
    key = index.get_student_db_key_from_dir(data_dir, master_key, student_uuid)
    if not key:
        raise ValueError(f"Student {student_uuid} not found")

    student_db_dir = os.path.join(data_dir, 'students')
    sconn = student.open_student_db(student_db_dir, student_uuid, key)
    try:
        student.update_package(sconn, package_id, updates)
    finally:
        sconn.close()

    recalculate_invoice(data_dir, master_key, student_uuid)
    _recalc_linked_invoices(data_dir, master_key, student_uuid)


def delete_package(data_dir: str, master_key: bytes, student_uuid: str, package_id: int):
    """Delete a package and its associated meeting times, then recalc."""
    key = index.get_student_db_key_from_dir(data_dir, master_key, student_uuid)
    if not key:
        raise ValueError(f"Student {student_uuid} not found")

    student_db_dir = os.path.join(data_dir, 'students')
    sconn = student.open_student_db(student_db_dir, student_uuid, key)
    try:
        student.delete_package(sconn, package_id)
    finally:
        sconn.close()

    recalculate_invoice(data_dir, master_key, student_uuid)
    _recalc_linked_invoices(data_dir, master_key, student_uuid)


def recalculate_invoice(data_dir: str, master_key: bytes, student_uuid: str) -> int:
    """
    Compute the student's next_invoice from all active packages
    and update the index. Returns the computed amount.
    """
    key = index.get_student_db_key_from_dir(data_dir, master_key, student_uuid)
    if not key:
        return 0

    student_db_dir = os.path.join(data_dir, 'students')
    sconn = student.open_student_db(student_db_dir, student_uuid, key)
    try:
        packages = student.get_packages(sconn)
        total = sum(p['rate'] - p.get('discount_amount', 0)
                    for p in packages if p.get('status') == 'active')
    finally:
        sconn.close()

    # Update index; clear invoice_reference because this student might be primary
    index_conn = index.open_index_db_with_key(data_dir, master_key)
    try:
        index.update_student_summary(index_conn, student_uuid, next_invoice=total, invoice_reference='')
    finally:
        index.close_index_db(index_conn)

    return total


# ------------------------------------------------------------
# Linked‑student invoice grouping (internal helper)
# ------------------------------------------------------------
def _recalc_linked_invoices(data_dir: str, master_key: bytes, changed_uuid: str):
    """
    After a student's packages change, ensure that all linked students
    with invoice_group=True have correct combined invoices.
    The student with the smallest UUID in each group becomes the primary.
    """
    # Recalculate own invoice first
    recalculate_invoice(data_dir, master_key, changed_uuid)

    index_conn = index.open_index_db_with_key(data_dir, master_key)
    try:
        all_students = index.get_all_students(index_conn)
    finally:
        index.close_index_db(index_conn)

    # Find all students who have an invoice_group relationship with changed_uuid
    group_members = {changed_uuid}
    for s in all_students:
        other_uuid = s['uuid']
        if other_uuid == changed_uuid:
            continue
        key = index.get_student_db_key_from_dir(data_dir, master_key, other_uuid)
        if not key:
            continue
        student_db_dir = os.path.join(data_dir, 'students')
        other_conn = student.open_student_db(student_db_dir, other_uuid, key)
        try:
            rels = student.get_relationships(other_conn)
        finally:
            other_conn.close()
        for rel in rels:
            if rel.get('invoice_group') and rel['other_uuid'] == changed_uuid:
                group_members.add(other_uuid)
                break

    if len(group_members) <= 1:
        # No group invoice needed
        return

    # Compute combined invoice for all members
    combined = 0
    for uid in group_members:
        key = index.get_student_db_key_from_dir(data_dir, master_key, uid)
        if not key:
            continue
        student_db_dir = os.path.join(data_dir, 'students')
        sconn = student.open_student_db(student_db_dir, uid, key)
        try:
            packages = student.get_packages(sconn)
            own_total = sum(p['rate'] - p.get('discount_amount', 0)
                            for p in packages if p.get('status') == 'active')
        finally:
            sconn.close()
        combined += own_total

    # Determine primary (smallest uuid)
    primary = min(group_members)
    primary_name = ""
    index_conn = index.open_index_db_with_key(data_dir, master_key)
    try:
        primary_summary = index.get_student_summary(index_conn, primary)
        if primary_summary:
            primary_name = primary_summary['name']
        # Update primary
        index.update_student_summary(index_conn, primary, next_invoice=combined, invoice_reference='')
        # Update others
        for uid in group_members:
            if uid != primary:
                index.update_student_summary(index_conn, uid, next_invoice=0, invoice_reference=primary_name)
    finally:
        index.close_index_db(index_conn)


# Helper to get DB key from index using data_dir and master_key
def get_student_db_key_from_dir(data_dir: str, master_key: bytes, uuid: str) -> Optional[bytes]:
    conn = index.open_index_db_with_key(data_dir, master_key)
    try:
        return index.get_student_db_key(conn, uuid)
    finally:
        index.close_index_db(conn)