
import os
import json
import time
import threading
import traceback
from datetime import datetime
from typing import Dict, Any, List

import config
import model
from util import db_ops

class TaskRunner:
    """
    Handles the execution of bank risk analysis tasks.
    Connects the Database (Tasks & Sections) with the Model Engine (Risk Level).
    """

    def __init__(self):
        self._running_tasks = {}  # In-memory tracking of running task threads

    def start_task(self, task_id: str):
        """
        Start a background thread to process the task
        """
        if task_id in self._running_tasks:
            return False, "Task is already running"

        task = db_ops.get_task(task_id)
        if not task:
            return False, "Task not found"

        # Update status to running
        db_ops.update_task_status(
            task_id, 
            status="running",
            run_started_at=datetime.now().isoformat()
        )

        # Start execution in a separate thread
        thread = threading.Thread(target=self._execute_task_logic, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        self._running_tasks[task_id] = thread
        return True, "Task started successfully"

    def _execute_task_logic(self, task_id: str):
        """
        The core logic:
        1. Fetch all sections for the task.
        2. preparing input for Risk Level Model.
        3. Call the model.
        4. Wait for results.
        5. Save results to DB.
        """
        try:
            print(f"[{task_id}] Starting execution...")
            
            # 1. Fetch sections
            sections = db_ops.get_sections_by_task(task_id)
            print(f"[{task_id}] Found {len(sections)} sections.")
            
            completed_count = 0
            
            # Process each section
            # TODO: Can be parallelized using ThreadPoolExecutor for better performance
            for section in sections:
                try:
                    self._process_single_section(task_id, section)
                    completed_count += 1
                except Exception as e:
                    print(f"[{task_id}] Error processing section {section.get('section_id')}: {str(e)}")
                    # Continue to next section even if one fails
            
            # Update task status to completed
            db_ops.update_task_status(
                task_id, 
                status="completed",
                run_completed_at=datetime.now().isoformat()
            )
            print(f"[{task_id}] Task completed. Processed {completed_count}/{len(sections)} sections.")

        except Exception as e:
            error_msg = f"Task Execution Failed: {str(e)}"
            print(f"[{task_id}] {error_msg}")
            traceback.print_exc()
            
            db_ops.update_task_status(
                task_id, 
                status="failed",
                error_message=error_msg
            )
        finally:
            # Cleanup
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]

    def _process_single_section(self, task_id: str, section: Dict[str, Any]):
        """
        Run model for a single section and save result
        """
        section_id_db = section['id']
        section_id_str = section['section_id']
        
        # 2. Prepare Input for Risk Level Model
        # Map DB fields to Model JSON structure
        # Note: adjust field names based on actual DB schema and Model requirements
        request_json = {
            "case-id": f"{task_id}_{section_id_str}", # Unique ID for this run
            "dem-id": section.get('bench_id', "NONE"), # Model expects dem-id
            "section-geometry": section.get('section_geometry', {}), # GeoJson
            
            # Basic Params
            "segment": section.get('segment', "Mzs"),
            "year": section.get('current_timepoint', "2023"),
            "set": section.get('set_name', "standard"),
            "water-qs": section.get('water_qs', "5000"),
            "tidal-level": section.get('tidal_level', "3.5"),
            
            # Thresholds
            "risk-threshold": section.get('risk_thresholds', "NONE"),
            
            # Weights (if needed by model)
            "weights": section.get('weights', "NONE"),

            # Other params...
            "protection-level": section.get('protection_level', "NONE"),
            "control-level": section.get('control_level', "NONE"),
            "hs": section.get('hs', "NONE"),
            "hc": section.get('hc', "NONE")
        }
        
        # 3. Call Model (Risk Level)
        # We use the launcher directly to bypass HTTP overhead, or use HTTP if preferred.
        # Here we use the Python API directly for better integration.
        print(f"    -> Running model for section {section_id_str}...")
        
        # Use ModelLauncher to run the model
        # This returns a ModelCaseReference immediately (async)
        risk_launcher = model.launcher.fetch_model_from_API(config.API_MI_RISK_LEVEL)
        mcr = risk_launcher.run(request_json)
        
        # 4. Wait for Result (Polling)
        # Since run() is async, we need to wait for status to be COMPLETE
        max_retries = 60 # 60 seconds timeout
        for _ in range(max_retries):
            status_dict = mcr.get_status() # Should return status dict
            # Check status file content directly or use helper
            # Assuming get_status returns the content of status file
            
            # Check if complete
            if mcr.find_status(config.STATUS_COMPLETE):
                break
            if mcr.find_status(config.STATUS_ERROR):
                raise Exception(f"Model run failed: {mcr.get_simplified_error_log()}")
            
            time.sleep(1)
        else:
            raise Exception("Model run timed out")
            
        # 5. Get Result
        result_data = mcr.get_case_response()
        # Expecting result to contain 'risk-level' and other indicators
        
        risk_level_val = result_data.get('risk-level', 0)
        # Map string risk level to int if necessary
        if isinstance(risk_level_val, str):
            if risk_level_val == "I": risk_level_val = 1
            elif risk_level_val == "II": risk_level_val = 2
            elif risk_level_val == "III": risk_level_val = 3
            elif risk_level_val == "IV": risk_level_val = 4
            else: risk_level_val = 0

        # 6. Save to DB
        db_ops.create_risk_result(
            task_id=db_ops.get_task(task_id)['id'], # Need integer ID for foreign key
            section_id=section_id_db,
            section_name=section.get('section_name'),
            region_code=section.get('region_code'),
            bank_id=section.get('bank_id'),
            risk_level=risk_level_val,
            indicators=result_data, # Store full JSON result
            geometry=section.get('geometry') # Reuse section geometry
        )
        print(f"    -> Result saved for {section_id_str}. Level: {risk_level_val}")

# Global instance
task_runner = TaskRunner()
