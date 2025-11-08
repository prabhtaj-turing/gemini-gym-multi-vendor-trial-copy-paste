# Scripts/porting/test_calendar_timezone.py

import json
from Scripts.porting.port_calendar import port_calendar
from Scripts.porting.helpers import is_datetime_of_format, local_to_UTC

class TestCalendarTimezone():

    def test_convert_vendor_to_ported_handles_timezone_success(self):
        """Test that convert_vendor_to_ported handles timezone correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))            
        ported_db, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))

        assert "events" in vendor_db
        for event in vendor_db["events"].values():
            for time_key in ("start", "end"):
                assert time_key in event
                assert ("dateTime" in event[time_key] and "date" not in event[time_key]) or ("date" in event[time_key] and "dateTime" not in event[time_key])
                if "date" in event[time_key]:
                    event[time_key]["dateTime"] = event[time_key]["date"] + "T00:00:00" if time_key == "start" else event[time_key]["date"] + "T23:59:59"
                    del event[time_key]["date"]
                try:
                    local_to_UTC(event[time_key])
                except Exception as e:
                    print(e)
                    assert False
        
        assert message == "Validation successful"
        assert "events" in ported_db
        assert set(ported_db["events"].keys()) == set(vendor_db["events"].keys())
        for event in ported_db["events"].values():
            for time_key in ("start", "end"):
                assert time_key in event
                assert "dateTime" in event[time_key]
                assert "offset" in event[time_key]
                assert "timeZone" in event[time_key]
        
        for cal_ev_id in ported_db["events"].keys():
            vendor_ev = vendor_db["events"][cal_ev_id]
            ported_ev = ported_db["events"][cal_ev_id]
            for time_key in ("start", "end"):
                assert local_to_UTC(vendor_ev[time_key]) == ported_ev[time_key]
    
    def test_convert_vendor_datetime_ISO_8601_UTC_Z_no_timezone_success(self):
        """Test that convert_vendor_to_ported handles ISO 8601 UTC Z format correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"dateTime": "2024-01-01T10:00:00Z"},"end": {"dateTime": "2024-01-01T11:00:00Z"}}}
        ported_db, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        
        assert message == "Validation successful"
        vendor_ev = vendor_db["events"]["cal1:ev1"]
        ported_ev = ported_db["events"]["cal1:ev1"]
        for time_key in ("start", "end"):
            assert local_to_UTC(vendor_ev[time_key]) == ported_ev[time_key]

    def test_convert_vendor_datetime_ISO_8601_UTC_OFFSET_no_timezone_success(self):
        """Test that convert_vendor_to_ported handles ISO 8601 UTC Offset format correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"dateTime": "2024-01-01T10:00:00+03:00"},"end": {"dateTime": "2024-01-01T11:00:00+03:00"}}}
        ported_db, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        
        assert message == "Validation successful"
        vendor_ev = vendor_db["events"]["cal1:ev1"]
        ported_ev = ported_db["events"]["cal1:ev1"]
        for time_key in ("start", "end"):
            assert local_to_UTC(vendor_ev[time_key]) == ported_ev[time_key]

    def test_convert_vendor_datetime_ISO_8601_WITH_TIMEZONE_no_timezone_failure(self):
        """Test that convert_vendor_to_ported handles ISO 8601 WITH TIMEZONE format correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"dateTime": "2024-01-03T10:00:00"},"end": {"dateTime": "2024-01-03T11:00:00"}}}
        _, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        assert message == "Invalid format for event 'cal1:ev1' field 'start': If timeZone is not provided, dateTime must have timezone information."
    
    def test_convert_vendor_datetime_ISO_8601_UTC_Z_with_timezone_success(self):
        """Test that convert_vendor_to_ported handles ISO 8601 UTC Z format with timezone correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"dateTime": "2024-01-01T10:00:00Z", "timeZone": "America/Sao_Paulo"},"end": {"dateTime": "2024-01-01T11:00:00Z", "timeZone": "America/Sao_Paulo"}}}
        ported_db, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        
        assert message == "Validation successful"
        vendor_ev = vendor_db["events"]["cal1:ev1"]
        ported_ev = ported_db["events"]["cal1:ev1"]
        for time_key in ("start", "end"):
            assert local_to_UTC(vendor_ev[time_key]) == ported_ev[time_key]
    
    def test_convert_vendor_datetime_ISO_8601_UTC_OFFSET_with_timezone_success(self):
        """Test that convert_vendor_to_ported handles ISO 8601 UTC Offset format with timezone correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"dateTime": "2024-01-01T10:00:00+03:00", "timeZone": "America/Sao_Paulo"},"end": {"dateTime": "2024-01-01T11:00:00+03:00", "timeZone": "America/Sao_Paulo"}}}
        ported_db, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        
        assert message == "Validation successful"
        vendor_ev = vendor_db["events"]["cal1:ev1"]
        ported_ev = ported_db["events"]["cal1:ev1"]
        for time_key in ("start", "end"):
            assert local_to_UTC(vendor_ev[time_key]) == ported_ev[time_key]
    
    def test_convert_vendor_datetime_ISO_8601_WITH_TIMEZONE_with_timezone_success(self):
        """Test that convert_vendor_to_ported handles ISO 8601 WITH TIMEZONE format with timezone correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"dateTime": "2024-01-01T10:00:00", "timeZone": "America/Sao_Paulo"},"end": {"dateTime": "2024-01-01T11:00:00", "timeZone": "America/Sao_Paulo"}}}
        ported_db, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        
        assert message == "Validation successful"
        vendor_ev = vendor_db["events"]["cal1:ev1"]
        ported_ev = ported_db["events"]["cal1:ev1"]
        for time_key in ("start", "end"):
            assert local_to_UTC(vendor_ev[time_key]) == ported_ev[time_key]
    
    def test_convert_vendor_handles_daylight_saving_time_success(self):
        """Test that convert_vendor_to_ported handles daylight saving time correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"dateTime": "2024-03-09T10:00:00", "timeZone": "America/New_York"},"end": {"dateTime": "2024-03-09T11:00:00", "timeZone": "America/New_York"}},
                               "cal1:ev2": {"start": {"dateTime": "2024-03-11T10:00:00", "timeZone": "America/New_York"},"end": {"dateTime": "2024-03-11T11:00:00", "timeZone": "America/New_York"}}}
        ported_db, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        
        assert message == "Validation successful"
        vendor_ev_before_DST = vendor_db["events"]["cal1:ev1"]
        ported_ev_before_DST = ported_db["events"]["cal1:ev1"]
        vendor_ev_after_DST = vendor_db["events"]["cal1:ev2"]
        ported_ev_after_DST = ported_db["events"]["cal1:ev2"]
        
        for time_key in ("start", "end"):
            assert local_to_UTC(vendor_ev_before_DST[time_key]) == ported_ev_before_DST[time_key]
            assert local_to_UTC(vendor_ev_after_DST[time_key]) == ported_ev_after_DST[time_key]
            assert ported_ev_before_DST[time_key]["offset"] == "-05:00"
            assert ported_ev_after_DST[time_key]["offset"] == "-04:00"
    
    def test_convert_vendor_invalid_datetime_failure(self):
        """Test that convert_vendor_to_ported handles invalid datetime correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"dateTime": "invalid_datetime"},"end": {"dateTime": "invalid_datetime"}}}
        _, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        assert message == "Invalid format for event 'cal1:ev1' field 'start': Invalid dateTime"
    
    def test_convert_vendor_invalid_timezone_failure(self):
        """Test that convert_vendor_to_ported handles invalid timezone correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"dateTime": "2024-01-01T10:00:00", "timeZone": "invalid_timezone"},"end": {"dateTime": "2024-01-01T11:00:00", "timeZone": "invalid_timezone"}}}
        _, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        assert message == "Invalid format for event 'cal1:ev1' field 'start': Invalid timeZone"
    
    def test_convert_vendor_invalid_date_failure(self):
        """Test that convert_vendor_to_ported handles invalid date correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"date": "invalid_date"},"end": {"date": "invalid_date"}}}
        _, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        assert message == "Invalid format for event 'cal1:ev1' field 'start': Invalid dateTime"
    
    def test_convert_vendor_datetime_and_date_failure(self):
        """Test that convert_vendor_to_ported handles invalid datetime and date correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"dateTime": "2024-01-01T10:00:00", "date": "2024-01-01"},"end": {"dateTime": "2024-01-01T11:00:00", "date": "2024-01-01"}}}
        _, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        assert message == "Invalid format for event 'cal1:ev1': 'start' must include only one of 'dateTime' or 'date' for event 'cal1:ev1'"
    
    def test_convert_vendor_no_datetime_no_date_failure(self):
        """Test that convert_vendor_to_ported handles no datetime and no date correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"timeZone": "America/Sao_Paulo"},"end": {"timeZone": "America/Sao_Paulo"}}}
        _, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        assert message == "Invalid format for event 'cal1:ev1': 'start' must include 'dateTime' or 'date' for event 'cal1:ev1'"
    
    def test_convert_vendor_datetime_start_after_end_failure(self):
        """Test that convert_vendor_to_ported handles datetime and date correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        vendor_db["events"] = {"cal1:ev1": {"start": {"dateTime": "2024-01-01T10:00:00Z"},"end": {"dateTime": "2024-01-01T09:00:00Z"}}}
        _, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        assert message == "Event 'cal1:ev1' has end before start"
    
    def test_convert_vendor_inserts_primary_in_first_calendar_if_no_primary_success(self):
        """Test that convert_vendor_to_ported inserts primary in first calendar if no primary."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        cal_1 = {'id': 'cal-1', 'summary': 'Work', 'description': 'Work-related events and meetings.', 'timeZone': 'America/Chicago'}
        cal_2 = {'id': 'cal-2', 'summary': 'Personal', 'description': 'Personal events and reminders.', 'timeZone': 'America/Chicago'}
        vendor_db["calendars"] = {"cal1": cal_1, "cal2": cal_2}
        ported_db, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        assert message == "Validation successful"
        assert ported_db["calendars"]["cal1"]["primary"] == True
        assert ported_db["calendars"]["cal2"]["primary"] == False
    
    def test_convert_vendor_keeps_primary_calendar_if_present_success(self):
        """Test that convert_vendor_to_ported keeps primary calendar correctly."""
        vendor_db = json.load(open("Scripts/porting/SampleDBs/calendar/vendor_calendar.json"))
        cal_1 = {'id': 'cal-1', 'summary': 'Work', 'description': 'Work-related events and meetings.', 'timeZone': 'America/Chicago', 'primary': False}
        cal_2 = {'id': 'cal-2', 'summary': 'Personal', 'description': 'Personal events and reminders.', 'timeZone': 'America/Chicago', 'primary': True}
        vendor_db["calendars"] = {"cal1": cal_1, "cal2": cal_2}
        ported_db, message = port_calendar(json.dumps(vendor_db, ensure_ascii=False))
        assert message == "Validation successful"
        assert ported_db["calendars"]["cal1"]["primary"] == False
        assert ported_db["calendars"]["cal2"]["primary"] == True