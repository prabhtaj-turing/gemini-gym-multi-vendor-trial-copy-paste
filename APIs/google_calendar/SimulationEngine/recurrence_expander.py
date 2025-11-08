import copy
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple, Set
from .utils import parse_iso_datetime
from .custom_errors import InvalidInputError


class RecurrenceExpander:
    """
    Expands recurring events into individual instances within a given time range.
    Supports RRULE format as specified in RFC 5545, including EXDATE and RDATE.
    """
    
    # Day abbreviations mapping
    DAY_ABBREVIATIONS = {
        'MO': 0,  # Monday
        'TU': 1,  # Tuesday
        'WE': 2,  # Wednesday
        'TH': 3,  # Thursday
        'FR': 4,  # Friday
        'SA': 5,  # Saturday
        'SU': 6,  # Sunday
    }
    
    @classmethod
    def expand_recurring_event(
        cls, 
        event: Dict[str, Any], 
        time_min: Optional[datetime] = None, 
        time_max: Optional[datetime] = None,
        max_instances: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Expands a recurring event into individual instances.
        
        Args:
            event: The recurring event dictionary
            time_min: Minimum time for instances (inclusive)
            time_max: Maximum time for instances (exclusive)
            max_instances: Maximum number of instances to generate
            
        Returns:
            List of event instances
        """
        if not event.get("recurrence"):
            # Not a recurring event, return as single instance
            return [event]
        
        # Get the base event start and end times
        base_start = cls._get_event_start(event)
        base_end = cls._get_event_end(event)
        
        if not base_start or not base_end:
            # Can't expand without valid start/end times
            return [event]
        
        # Parse EXDATE and RDATE entries
        exdates = cls._parse_exdates(event["recurrence"])
        rdates = cls._parse_rdates(event["recurrence"])
        
        instances = []
        
        for rule in event["recurrence"]:
            if not rule.startswith("RRULE:"):
                # Skip non-RRULE entries (EXDATE and RDATE are handled separately)
                continue
            rule_instances = cls._expand_rrule(
                event, rule, base_start, base_end, time_min, time_max, max_instances, exdates
            )
            instances.extend(rule_instances)
        
        # Add RDATE instances
        rdate_instances = cls._create_rdate_instances(event, rdates, base_start, base_end, time_min, time_max)
        instances.extend(rdate_instances)
        
        # Remove duplicates and sort by start time
        unique_instances = cls._deduplicate_instances(instances)
        unique_instances.sort(key=lambda x: cls._get_event_start(x) or datetime.max)
        
        return unique_instances[:max_instances]
    
    @classmethod
    def _parse_exdates(cls, recurrence: List[str]) -> Set[datetime]:
        """
        Parses EXDATE entries from recurrence list.
        
        Args:
            recurrence: List of recurrence rules
            
        Returns:
            Set of excluded dates (datetime objects, some may have time=00:00:00 for date-only exclusions)
        """
        exdates = set()
        
        for rule in recurrence:
            if rule.startswith("EXDATE:"):
                # Extract the date part after EXDATE:
                date_part = rule[7:]  # Remove 'EXDATE:' prefix
                
                # Parse the date
                excluded_dt = cls._parse_date_string(date_part)
                if excluded_dt:
                    exdates.add(excluded_dt)
        
        return exdates
    
    @classmethod
    def _parse_rdates(cls, recurrence: List[str]) -> List[datetime]:
        """
        Parses RDATE entries from recurrence list.
        
        Args:
            recurrence: List of recurrence rules
            
        Returns:
            List of included dates
        """
        rdates = []
        
        for rule in recurrence:
            if rule.startswith("RDATE:"):
                # Extract the date part after RDATE:
                date_part = rule[6:]  # Remove 'RDATE:' prefix
                
                # Parse the date
                included_dt = cls._parse_date_string(date_part)
                if included_dt:
                    rdates.append(included_dt)
        
        return rdates
    
    @classmethod
    def _parse_date_string(cls, date_str: str) -> Optional[datetime]:
        """
        Parses a date string in various formats.
        
        Args:
            date_str: Date string in format YYYYMMDDTHHMMSSZ, YYYYMMDDTHHMMSS, or YYYYMMDD
            
        Returns:
            Parsed datetime or None if invalid
        """
        date_str = date_str.strip()
        
        try:
            if len(date_str) == 8:
                # Format: YYYYMMDD
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                return datetime(year, month, day).replace(tzinfo=timezone.utc)
            elif len(date_str) == 15:
                # Format: YYYYMMDDTHHMMSS
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                hour = int(date_str[9:11])
                minute = int(date_str[11:13])
                second = int(date_str[13:15])
                return datetime(year, month, day, hour, minute, second).replace(tzinfo=timezone.utc)
            elif len(date_str) == 16 and date_str.endswith('Z'):
                # Format: YYYYMMDDTHHMMSSZ
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                hour = int(date_str[9:11])
                minute = int(date_str[11:13])
                second = int(date_str[13:15])
                return datetime(year, month, day, hour, minute, second).replace(tzinfo=timezone.utc)
            else:
                return None
        except (ValueError, IndexError):
            return None
    
    @classmethod
    def _expand_rrule(
        cls,
        event: Dict[str, Any],
        rule: str,
        base_start: datetime,
        base_end: datetime,
        time_min: Optional[datetime],
        time_max: Optional[datetime],
        max_instances: int,
        exdates: Set[datetime]
    ) -> List[Dict[str, Any]]:
        """
        Expands a single RRULE into instances.
        """
        # Parse the RRULE
        rule_dict = cls._parse_rrule(rule)

        if not rule_dict:
            return []
        
        freq = rule_dict.get("FREQ", "DAILY")
        interval = int(rule_dict.get("INTERVAL", "1"))
        count = rule_dict.get("COUNT")
        until = rule_dict.get("UNTIL")
        byday = rule_dict.get("BYDAY")
        bymonth = rule_dict.get("BYMONTH")
        bymonthday = rule_dict.get("BYMONTHDAY")
        byyearday = rule_dict.get("BYYEARDAY")
        byweekno = rule_dict.get("BYWEEKNO")
        byhour = rule_dict.get("BYHOUR")
        byminute = rule_dict.get("BYMINUTE")
        bysecond = rule_dict.get("BYSECOND")
        bysetpos = rule_dict.get("BYSETPOS")
        wkst = rule_dict.get("WKST", "MO")
        
        # Parse until date if provided
        until_dt = None
        if until:
            until_dt = cls._parse_until_date(until)
        
        # Determine end condition
        if count:
            max_occurrences = int(count)
        elif until_dt:
            max_occurrences = 1000  # Large number, will be limited by until date
        else:
            max_occurrences = 100  # Default limit
        
        instances = []
        current_dt = base_start
        occurrence_count = 0
        
        while occurrence_count < max_occurrences and occurrence_count < max_instances:
            # Check if current instance is within time range
            if time_max and current_dt >= time_max:
                break
            if time_min and current_dt < time_min:
                # Skip to next occurrence
                current_dt = cls._get_next_occurrence(
                    current_dt, freq, interval, byday, bymonth, bymonthday, 
                    byyearday, byweekno, byhour, byminute, bysecond, wkst
                )
                continue
            
            # Check if we've reached the until date
            if until_dt and current_dt > until_dt:
                break
            
            # Check if this instance is excluded by EXDATE
            if cls._is_excluded_by_exdate(current_dt, exdates):
                # Skip this instance
                current_dt = cls._get_next_occurrence(
                    current_dt, freq, interval, byday, bymonth, bymonthday, 
                    byyearday, byweekno, byhour, byminute, bysecond, wkst
                )
                occurrence_count += 1
                continue
            
            # Create instance
            instance = cls._create_instance(event, current_dt, base_start, base_end)
            instances.append(instance)
            occurrence_count += 1
            
            # Get next occurrence
            current_dt = cls._get_next_occurrence(
                current_dt, freq, interval, byday, bymonth, bymonthday, 
                byyearday, byweekno, byhour, byminute, bysecond, wkst
            )
            
            # Safety check to prevent infinite loops
            if current_dt <= base_start:
                break

        return instances
    
    @classmethod
    def _create_rdate_instances(
        cls,
        event: Dict[str, Any],
        rdates: List[datetime],
        base_start: datetime,
        base_end: datetime,
        time_min: Optional[datetime],
        time_max: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """
        Creates instances for RDATE entries.
        
        Args:
            event: The base event
            rdates: List of included dates
            base_start: Original start time
            base_end: Original end time
            time_min: Minimum time filter
            time_max: Maximum time filter
            
        Returns:
            List of RDATE instances
        """
        instances = []
        
        for rdate in rdates:
            # Check if RDATE is within time range
            if time_max and rdate >= time_max:
                continue
            if time_min and rdate < time_min:
                continue
            
            # Create instance for this RDATE
            instance = cls._create_instance(event, rdate, base_start, base_end)
            instances.append(instance)
        
        return instances
    
    @classmethod
    def _parse_rrule(cls, rule: str) -> Dict[str, str]:
        """Parses an RRULE string into a dictionary."""
        if not rule.startswith("RRULE:"):
            return {}
        
        rule_part = rule[6:]  # Remove 'RRULE:' prefix
        rule_dict = {}
        
        for part in rule_part.split(';'):
            part = part.strip()
            if not part or '=' not in part:
                continue
            
            key, value = part.split('=', 1)
            rule_dict[key.strip().upper()] = value.strip()
        
        return rule_dict
    
    @classmethod
    def _parse_until_date(cls, until: str) -> Optional[datetime]:
        """Parses an UNTIL date string."""
        # Format: YYYYMMDDTHHMMSSZ or YYYYMMDDTHHMMSS
        if len(until) != 15 and len(until) != 16:
            return None
        
        try:
            year = int(until[:4])
            month = int(until[4:6])
            day = int(until[6:8])
            hour = int(until[9:11])
            minute = int(until[11:13])
            second = int(until[13:15])
            
            return datetime(year, month, day, hour, minute, second).replace(tzinfo=timezone.utc)
        except (ValueError, IndexError):
            return None
    
    @classmethod
    def _get_next_occurrence(
        cls,
        current_dt: datetime,
        freq: str,
        interval: int,
        byday: Optional[str],
        bymonth: Optional[str],
        bymonthday: Optional[str],
        byyearday: Optional[str],
        byweekno: Optional[str],
        byhour: Optional[str],
        byminute: Optional[str],
        bysecond: Optional[str],
        wkst: str
    ) -> datetime:
        """Gets the next occurrence based on frequency and parameters."""
        if freq == "DAILY":
            return current_dt + timedelta(days=interval)
        elif freq == "WEEKLY":
            return current_dt + timedelta(weeks=interval)
        elif freq == "MONTHLY":
            # Simple monthly increment (doesn't handle all edge cases)
            year = current_dt.year
            month = current_dt.month + interval
            while month > 12:
                year += 1
                month -= 12
            try:
                return current_dt.replace(year=year, month=month)
            except ValueError:
                # Handle edge case where day doesn't exist in target month
                return current_dt + timedelta(days=30 * interval)
        elif freq == "YEARLY":
            return current_dt.replace(year=current_dt.year + interval)
        else:
            # For other frequencies, use daily increment as fallback
            return current_dt + timedelta(days=interval)
    
    @classmethod
    def _create_instance(
        cls, 
        event: Dict[str, Any], 
        start_dt: datetime, 
        base_start: datetime, 
        base_end: datetime
    ) -> Dict[str, Any]:
        """Creates an event instance with updated start/end times."""
        # Calculate duration
        duration = base_end - base_start
        
        # Create new instance
        instance = copy.deepcopy(event)
        
        # Remove recurrence field from expanded instances
        # According to Google Calendar API, expanded instances should not have recurrence field
        if "recurrence" in instance:
            del instance["recurrence"]
        
        # Update start time
        if "start" in instance and "dateTime" in instance["start"]:
            instance["start"]["dateTime"] = start_dt.isoformat()
        
        # Update end time
        if "end" in instance and "dateTime" in instance["end"]:
            end_dt = start_dt + duration
            instance["end"]["dateTime"] = end_dt.isoformat()
        
        # Add instance-specific fields
        instance["recurringEventId"] = event.get("id")
        instance["originalStartTime"] = {
            "dateTime": base_start.isoformat()
        }
        
        return instance
    
    @classmethod
    def _get_event_start(cls, event: Dict[str, Any]) -> Optional[datetime]:
        """Gets the start time of an event."""
        if "start" in event and "dateTime" in event["start"]:
            return parse_iso_datetime(event["start"]["dateTime"]).replace(tzinfo=timezone.utc)
        return None
    
    @classmethod
    def _get_event_end(cls, event: Dict[str, Any]) -> Optional[datetime]:
        """Gets the end time of an event."""
        if "end" in event and "dateTime" in event["end"]:
            return parse_iso_datetime(event["end"]["dateTime"]).replace(tzinfo=timezone.utc)
        return None
    
    @classmethod
    def _deduplicate_instances(cls, instances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Removes duplicate instances based on start time."""
        seen = set()
        unique_instances = []
        
        for instance in instances:
            start_dt = cls._get_event_start(instance)
            if start_dt:
                start_key = start_dt.isoformat()
                if start_key not in seen:
                    seen.add(start_key)
                    unique_instances.append(instance)
        
        return unique_instances
    
    @classmethod
    def _is_excluded_by_exdate(cls, current_dt: datetime, exdates: Set[datetime]) -> bool:
        """
        Checks if a datetime is excluded by any EXDATE entry.
        
        Args:
            current_dt: The datetime to check
            exdates: Set of excluded dates
            
        Returns:
            True if the datetime should be excluded
        """
        for exdate in exdates:
            # If EXDATE has time (hour, minute, second), do exact comparison
            if exdate.hour != 0 or exdate.minute != 0 or exdate.second != 0:
                if current_dt == exdate:
                    return True
            else:
                # If EXDATE has no time (date-only), exclude all instances on that date
                if (current_dt.year == exdate.year and 
                    current_dt.month == exdate.month and 
                    current_dt.day == exdate.day):
                    return True
        
        return False


def expand_recurring_events(
    events: List[Dict[str, Any]], 
    time_min: Optional[datetime] = None, 
    time_max: Optional[datetime] = None,
    max_instances_per_event: int = 100
) -> List[Dict[str, Any]]:
    """
    Expands all recurring events in a list into individual instances.
    
    Args:
        events: List of events (some may be recurring)
        time_min: Minimum time for instances (inclusive)
        time_max: Maximum time for instances (exclusive)
        max_instances_per_event: Maximum instances per recurring event
        
    Returns:
        List of events with recurring events expanded into instances
    """
    expanded_events = []
    
    for event in events:
        if event.get("recurrence"):
            # Expand recurring event
            instances = RecurrenceExpander.expand_recurring_event(
                event, time_min, time_max, max_instances_per_event
            )
            expanded_events.extend(instances)
        else:
            # Non-recurring event, add as-is
            expanded_events.append(event)
    
    return expanded_events 