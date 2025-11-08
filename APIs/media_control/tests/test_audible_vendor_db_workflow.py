# Test the workflow of the audible vendor db

import os
import sys
import json
import tempfile
import unittest
import shutil
from datetime import datetime
from typing import Dict, Any
from APIs.common_utils.base_case import BaseTestCaseWithErrorHandler
import media_control
from pathlib import Path
import json
from Scripts.porting import port_media_control
from media_control.SimulationEngine import db
from media_control.SimulationEngine import utils
from media_control.SimulationEngine import models
from media_control.SimulationEngine import custom_errors
from media_control.SimulationEngine import db
from media_control.SimulationEngine import utils
from media_control.SimulationEngine import db_models
from media_control.SimulationEngine import custom_errors



class TestAudibleVendorDBWorkflow(BaseTestCaseWithErrorHandler):
    """Test the workflow of the audible vendor db"""

    def setUp(self):
        """Set up the test environment"""
        super().setUp()
        # clear the db
        db.DB.clear()
        # load the default data
        db.load_default_data()
    
    def _add_audible_vendor_db(self):
        """Add the audible vendor db to the db"""
        media_path = "Scripts/porting/SampleDBs/media_control/vendor_media_control.json"
        raw_path = Path(media_path)
        merged_vendor_db = port_media_control.port_media_control_db(raw_path.read_text())
        db.DB.update(merged_vendor_db)

    
    def test_audible_vendor_db_workflow(self):
        """
        Test the workflow of the audible vendor db with the current media player
        steps
        1. Get the current media player
        2. Check if Audible is present in the media players
        3. If not add vendor db to current db
        4. Check if Audible is present in the media player
        5. Update current media player to Audible
        6. Update state of the current media player
        """

        current_media_player = utils.get_active_media_player()

        db.DB["active_media_player"] = current_media_player["app_name"]

        # Assert the current media player
        self.assertEqual(db.DB["active_media_player"], current_media_player["app_name"])
        self.assertEqual(db.DB["media_players"][current_media_player["app_name"]]["app_name"], current_media_player["app_name"])
        self.assertEqual(db.DB["media_players"][current_media_player["app_name"]]["current_media"]["title"], current_media_player["current_media"]["title"])
        self.assertEqual(db.DB["media_players"][current_media_player["app_name"]]["current_media"]["current_position_seconds"], current_media_player["current_media"]["current_position_seconds"])
        self.assertEqual(db.DB["media_players"][current_media_player["app_name"]]["current_media"]["media_type"], current_media_player["current_media"]["media_type"])
        self.assertEqual(db.DB["media_players"][current_media_player["app_name"]]["current_media"]["rating"], current_media_player["current_media"]["rating"])
        self.assertEqual(db.DB["media_players"][current_media_player["app_name"]]["current_media"]["app_name"], current_media_player["current_media"]["app_name"])


        # 2. Check if Audible is present in the media players
        self.assertFalse("Audible" in db.DB["media_players"])

        # 3. If not add vendor db to current db
        self._add_audible_vendor_db()

        # 4. Check if Audible is present in the media player
        self.assertTrue("Audible" in db.DB["media_players"])

        # 5. Update current media player to Audible 
        utils.set_active_media_player("Audible")

        # 6. Update state of the current media player
        active_media_player = utils.get_active_media_player()
        if active_media_player['playback_state'] == "PAUSED":
            media_control.resume()
        elif active_media_player['playback_state'] == "PLAYING":
            media_control.pause()
        
        # Assert the current media player playback state
        active_media_player = utils.get_active_media_player()
        self.assertEqual(active_media_player['playback_state'], "PLAYING")
        