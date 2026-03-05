"""
Database operations for bank segments, cross sections, and correction lines
"""

import json
from typing import List, Dict, Any, Optional, Tuple

from util import db


def create_bank_segment(
    case_id: str,
    segment_id: str,
    segment_name: str,
    region_code: str,
    geometry: Dict[str, Any],
    dem_id: Optional[str] = None,
    bench_id: Optional[str] = None,
    ref_id: Optional[str] = None,
    hydro_segment: Optional[str] = None,
    hydro_year: Optional[str] = None,
    hydro_set: Optional[str] = None,
    protection_level: Optional[str] = None,
    control_level: Optional[str] = None,
    other_params: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Create a bank segment in database
    """
    with db.get_db_cursor() as (conn, cursor):
        geom_json = json.dumps(geometry)

        cursor.execute(
            """
            INSERT INTO bank_segments (
                case_id, segment_id, segment_name, region_code,
                start_point, end_point, geom,
                dem_id, bench_id, ref_id,
                hydro_segment, hydro_year, hydro_set,
                protection_level, control_level, other_params
            ) VALUES (
                %s, %s, %s, %s,
                ST_StartPoint(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)),
                ST_EndPoint(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)),
                ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s::jsonb
            )
            RETURNING id
            """,
            (
                case_id,
                segment_id,
                segment_name,
                region_code,
                geom_json,
                geom_json,
                geom_json,
                dem_id,
                bench_id,
                ref_id,
                hydro_segment,
                hydro_year,
                hydro_set,
                protection_level,
                control_level,
                json.dumps(other_params) if other_params else None,
            ),
        )
        return cursor.fetchone()[0]


def get_bank_segments(case_id: str) -> List[Dict[str, Any]]:
    """
    Get all bank segments for a case
    """
    with db.get_db_cursor(dict_cursor=True) as (conn, cursor):
        cursor.execute(
            """
            SELECT 
                id, case_id, segment_id, segment_name, region_code,
                dem_id, bench_id, ref_id,
                hydro_segment, hydro_year, hydro_set,
                protection_level, control_level, other_params,
                ST_AsGeoJSON(start_point)::jsonb as start_point,
                ST_AsGeoJSON(end_point)::jsonb as end_point,
                ST_AsGeoJSON(geom)::jsonb as geometry,
                created_at, updated_at
            FROM bank_segments
            WHERE case_id = %s
            ORDER BY id
            """,
            (case_id,),
        )
        return cursor.fetchall()


def create_cross_section(
    case_id: str,
    section_id: str,
    section_name: str,
    segment_id_db: int,
    region_code: str,
    segment_index: Optional[int] = None,
    geometry: Dict[str, Any] = None,
    hs: Optional[float] = None,
    hc: Optional[float] = None,
    protection_level: Optional[str] = None,
    control_level: Optional[str] = None,
    water_qs: Optional[str] = None,
    tidal_level: Optional[str] = None,
    current_timepoint: Optional[str] = None,
    comparison_timepoint: Optional[str] = None,
    risk_thresholds: Optional[Dict[str, Any]] = None,
    weights: Optional[Dict[str, Any]] = None,
    other_params: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Create a cross section in database
    """
    with db.get_db_cursor() as (conn, cursor):
        geom_json = json.dumps(geometry) if geometry else None

        cursor.execute(
            """
            INSERT INTO cross_sections (
                case_id, section_id, section_name, segment_id, region_code,
                segment_index,
                start_point, end_point, geom,
                hs, hc, protection_level, control_level,
                water_qs, tidal_level,
                current_timepoint, comparison_timepoint,
                risk_thresholds, weights, other_params
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s,
                ST_StartPoint(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)),
                ST_EndPoint(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)),
                ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
                %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s::jsonb, %s::jsonb, %s::jsonb
            )
            RETURNING id
            """,
            (
                case_id,
                section_id,
                section_name,
                segment_id_db,
                region_code,
                segment_index,
                geom_json,
                geom_json,
                geom_json,
                hs,
                hc,
                protection_level,
                control_level,
                water_qs,
                tidal_level,
                current_timepoint,
                comparison_timepoint,
                json.dumps(risk_thresholds) if risk_thresholds else None,
                json.dumps(weights) if weights else None,
                json.dumps(other_params) if other_params else None,
            ),
        )
        return cursor.fetchone()[0]


def get_cross_sections(
    case_id: str, segment_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get all cross sections for a case
    """
    with db.get_db_cursor(dict_cursor=True) as (conn, cursor):
        if segment_id:
            cursor.execute(
                """
                SELECT 
                    cs.*,
                    bs.segment_name,
                    ST_AsGeoJSON(cs.geom)::jsonb as geometry
                FROM cross_sections cs
                JOIN bank_segments bs ON cs.segment_id = bs.id
                WHERE cs.case_id = %s AND cs.segment_id = %s
                ORDER BY cs.id
                """,
                (case_id, segment_id),
            )
        else:
            cursor.execute(
                """
                SELECT 
                    cs.*,
                    bs.segment_name,
                    ST_AsGeoJSON(cs.geom)::jsonb as geometry
                FROM cross_sections cs
                JOIN bank_segments bs ON cs.segment_id = bs.id
                WHERE cs.case_id = %s
                ORDER BY cs.id
                """,
                (case_id,),
            )
        return cursor.fetchall()


def create_correction_line(
    case_id: str,
    correction_id: str,
    geometry: Dict[str, Any],
    correction_rules: Dict[str, Any],
    description: Optional[str] = None,
) -> int:
    """
    Create a correction line in database
    """
    with db.get_db_cursor() as (conn, cursor):
        geom_json = json.dumps(geometry)

        cursor.execute(
            """
            INSERT INTO correction_lines (
                case_id, correction_id, geom, correction_rules, description
            ) VALUES (
                %s, %s,
                ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
                %s::jsonb, %s
            )
            RETURNING id
            """,
            (
                case_id,
                correction_id,
                geom_json,
                json.dumps(correction_rules),
                description,
            ),
        )
        return cursor.fetchone()[0]


def get_correction_lines(case_id: str) -> List[Dict[str, Any]]:
    """
    Get all correction lines for a case
    """
    with db.get_db_cursor(dict_cursor=True) as (conn, cursor):
        cursor.execute(
            """
            SELECT 
                id, case_id, correction_id, description,
                correction_rules,
                ST_AsGeoJSON(geom)::jsonb as geometry,
                created_at, updated_at
            FROM correction_lines
            WHERE case_id = %s
            ORDER BY id
            """,
            (case_id,),
        )
        return cursor.fetchall()


def get_full_case_data(case_id: str) -> Dict[str, Any]:
    """
    Get all data for a case (segments + sections + corrections)
    """
    return {
        "segments": get_bank_segments(case_id),
        "sections": get_cross_sections(case_id),
        "corrections": get_correction_lines(case_id),
    }


def delete_bank_segment(case_id: str, segment_id: str) -> bool:
    """
    Delete a bank segment
    """
    with db.get_db_cursor() as (conn, cursor):
        cursor.execute(
            """
            DELETE FROM bank_segments
            WHERE case_id = %s AND segment_id = %s
            RETURNING id
            """,
            (case_id, segment_id),
        )
        return cursor.fetchone() is not None


def delete_cross_section(case_id: str, section_id: str) -> bool:
    """
    Delete a cross section
    """
    with db.get_db_cursor() as (conn, cursor):
        cursor.execute(
            """
            DELETE FROM cross_sections
            WHERE case_id = %s AND section_id = %s
            RETURNING id
            """,
            (case_id, section_id),
        )
        return cursor.fetchone() is not None


def delete_correction_line(case_id: str, correction_id: str) -> bool:
    """
    Delete a correction line
    """
    with db.get_db_cursor() as (conn, cursor):
        cursor.execute(
            """
            DELETE FROM correction_lines
            WHERE case_id = %s AND correction_id = %s
            RETURNING id
            """,
            (case_id, correction_id),
        )
        return cursor.fetchone() is not None


def clear_case_data(case_id: str) -> Dict[str, int]:
    """
    Clear all data for a case
    """
    with db.get_db_cursor() as (conn, cursor):
        cursor.execute("DELETE FROM bank_risk_results WHERE case_id = %s", (case_id,))
        results_deleted = cursor.rowcount

        cursor.execute("DELETE FROM correction_lines WHERE case_id = %s", (case_id,))
        corrections_deleted = cursor.rowcount

        cursor.execute("DELETE FROM cross_sections WHERE case_id = %s", (case_id,))
        sections_deleted = cursor.rowcount

        cursor.execute("DELETE FROM bank_segments WHERE case_id = %s", (case_id,))
        segments_deleted = cursor.rowcount

        return {
            "segments": segments_deleted,
            "sections": sections_deleted,
            "corrections": corrections_deleted,
            "results": results_deleted,
        }
