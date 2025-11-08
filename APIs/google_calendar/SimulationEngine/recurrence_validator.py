import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from .custom_errors import InvalidInputError

class RecurrenceValidator:
    """
    Validates and parses recurrence rules for Google Calendar events.
    Supports RRULE format as specified in RFC 5545, including EXDATE and RDATE.
    """
    
    # Valid frequency values
    VALID_FREQUENCIES = {'MINUTELY', 'HOURLY', 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY'}
    
    # Valid interval values (must be positive integer)
    INTERVAL_PATTERN = r'^[1-9]\d*$'
    
    # Valid count values (must be positive integer)
    COUNT_PATTERN = r'^[1-9]\d*$'
    
    # Valid until date format (YYYYMMDDTHHMMSSZ or YYYYMMDDTHHMMSS)
    UNTIL_PATTERN = r'^(\d{8}T\d{6}Z?)$'
    
    # Valid date formats for EXDATE and RDATE
    DATE_PATTERN = r'^(\d{8}(T\d{6}Z?)?)$'
    
    # Valid byday values
    VALID_BYDAY = {'SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'}
    
    # Valid bymonth values (1-12)
    VALID_BYMONTH = set(range(1, 13))
    
    # Valid bymonthday values (1-31)
    VALID_BYMONTHDAY = set(range(1, 32))

    # Valid bymonthday per bymonth
    VALID_BYMONTHDAY_PER_BYMONTH = {
        1: set(range(1, 32)),
        2: set(range(1, 30)),
        3: set(range(1, 32)),
        4: set(range(1, 31)),
        5: set(range(1, 32)),
        6: set(range(1, 31)),
        7: set(range(1, 32)),
        8: set(range(1, 32)),
        9: set(range(1, 31)),
        10: set(range(1, 32)),
        11: set(range(1, 31)),
        12: set(range(1, 32)),
    }
    
    # Valid byyearday values (1-366)
    VALID_BYYEARDAY = set(range(1, 367))
    
    # Valid byweekno values (1-53)
    VALID_BYWEEKNO = set(range(1, 54))
    
    # Valid byhour values (0-23)
    VALID_BYHOUR = set(range(24))
    
    # Valid byminute values (0-59)
    VALID_BYMINUTE = set(range(60))
    
    # Valid bysecond values (0-59)
    VALID_BYSECOND = set(range(60))
    
    # Valid bysetpos values (1-366 or -366 to -1)
    VALID_BYSETPOS = set(range(1, 367)) | set(range(-366, 0))
    
    @classmethod
    def validate_recurrence_rules(cls, recurrence: List[str]) -> None:
        """
        Validates a list of recurrence rules.
        
        Args:
            recurrence: List of recurrence rule strings
            
        Raises:
            InvalidInputError: If any rule is invalid
        """
        if not isinstance(recurrence, list):
            raise InvalidInputError("Recurrence must be a list of strings")
        
        for i, rule in enumerate(recurrence):
            if not isinstance(rule, str):
                raise InvalidInputError(f"Recurrence rule {i} must be a string")
            
            if not rule.strip():
                raise InvalidInputError(f"Recurrence rule {i} cannot be empty")
            
            cls._validate_single_rule(rule, i)
    
    @classmethod
    def _validate_single_rule(cls, rule: str, rule_index: int) -> None:
        """
        Validates a single recurrence rule.
        
        Args:
            rule: The recurrence rule string
            rule_index: Index of the rule for error reporting
            
        Raises:
            InvalidInputError: If the rule is invalid
        """
        # Check if it's an RRULE
        if rule.startswith('RRULE:'):
            cls._validate_rrule(rule, rule_index)
        # Check if it's an EXDATE
        elif rule.startswith('EXDATE:'):
            cls._validate_exdate(rule, rule_index)
        # Check if it's an RDATE
        elif rule.startswith('RDATE:'):
            cls._validate_rdate(rule, rule_index)
        else:
            raise InvalidInputError(f"Recurrence rule {rule_index} must start with 'RRULE:', 'EXDATE:', or 'RDATE:'")
    
    @classmethod
    def _validate_rrule(cls, rule: str, rule_index: int) -> None:
        """
        Validates an RRULE string.
        
        Args:
            rule: The RRULE string
            rule_index: Index of the rule for error reporting
            
        Raises:
            InvalidInputError: If the rule is invalid
        """
        # Extract the rule part after RRULE:
        rule_part = rule[6:]  # Remove 'RRULE:' prefix
        
        if not rule_part.strip():
            raise InvalidInputError(f"Recurrence rule {rule_index} has no content after 'RRULE:'")
        
        # Parse and validate the rule
        cls._parse_and_validate_rrule(rule_part, rule_index)
    
    @classmethod
    def _validate_exdate(cls, rule: str, rule_index: int) -> None:
        """
        Validates an EXDATE string.
        
        Args:
            rule: The EXDATE string
            rule_index: Index of the rule for error reporting
            
        Raises:
            InvalidInputError: If the rule is invalid
        """
        # Extract the date part after EXDATE:
        date_part = rule[7:].strip()  # Remove 'EXDATE:' prefix
        
        if not date_part.strip():
            raise InvalidInputError(f"EXDATE rule {rule_index} has no content after 'EXDATE:'")
        
        # Validate the date format
        if not re.match(cls.DATE_PATTERN, date_part):
            raise InvalidInputError(
                f"EXDATE rule {rule_index} has invalid date format '{date_part}'. "
                f"Must be in format YYYYMMDD, YYYYMMDDTHHMMSS, or YYYYMMDDTHHMMSSZ"
            )
    
    @classmethod
    def _validate_rdate(cls, rule: str, rule_index: int) -> None:
        """
        Validates an RDATE string.
        
        Args:
            rule: The RDATE string
            rule_index: Index of the rule for error reporting
            
        Raises:
            InvalidInputError: If the rule is invalid
        """
        # Extract the date part after RDATE:
        date_part = rule[6:].strip()  # Remove 'RDATE:' prefix
        
        if not date_part.strip():
            raise InvalidInputError(f"RDATE rule {rule_index} has no content after 'RDATE:'")
        
        # Validate the date format
        if not re.match(cls.DATE_PATTERN, date_part):
            raise InvalidInputError(
                f"RDATE rule {rule_index} has invalid date format '{date_part}'. "
                f"Must be in format YYYYMMDD, YYYYMMDDTHHMMSS, or YYYYMMDDTHHMMSSZ"
            )
    
    @classmethod
    def _parse_and_validate_rrule(cls, rule_part: str, rule_index: int) -> None:
        """
        Parses and validates an RRULE string.
        
        Args:
            rule_part: The rule part after 'RRULE:' prefix
            rule_index: Index of the rule for error reporting
            
        Raises:
            InvalidInputError: If the rule is invalid
        """
        # Split by semicolon
        parts = rule_part.split(';')
        
        if not parts:
            raise InvalidInputError(f"Recurrence rule {rule_index} has no valid parts")
        
        # Parse each part
        rule_dict = {}
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            if '=' not in part:
                raise InvalidInputError(f"Recurrence rule {rule_index} part '{part}' must contain '='")
            
            key, value = part.split('=', 1)
            key = key.strip().upper()
            value = value.strip()
            
            if key in rule_dict:
                raise InvalidInputError(f"Recurrence rule {rule_index} has duplicate key '{key}'")
            
            rule_dict[key] = value
        
        # Validate the parsed rule
        cls._validate_rule_dict(rule_dict, rule_index)
    
    @classmethod
    def _validate_rule_dict(cls, rule_dict: Dict[str, str], rule_index: int) -> None:
        """
        Validates a parsed rule dictionary.
        
        Args:
            rule_dict: Dictionary of rule key-value pairs
            rule_index: Index of the rule for error reporting
            
        Raises:
            InvalidInputError: If the rule is invalid
        """
        # FREQ is required
        if 'FREQ' not in rule_dict:
            raise InvalidInputError(f"Recurrence rule {rule_index} must contain FREQ")
        
        freq = rule_dict['FREQ']
        if freq not in cls.VALID_FREQUENCIES:
            raise InvalidInputError(
                f"Recurrence rule {rule_index} has invalid FREQ '{freq}'. "
                f"Must be one of: {', '.join(sorted(cls.VALID_FREQUENCIES))}"
            )
        
        # Validate INTERVAL
        if 'INTERVAL' in rule_dict:
            interval = rule_dict['INTERVAL']
            if not re.match(cls.INTERVAL_PATTERN, interval):
                raise InvalidInputError(f"Recurrence rule {rule_index} INTERVAL must be a positive integer")
        
        # Validate COUNT
        if 'COUNT' in rule_dict:
            count = rule_dict['COUNT']
            if not re.match(cls.COUNT_PATTERN, count):
                raise InvalidInputError(f"Recurrence rule {rule_index} COUNT must be a positive integer")
        
        # Validate UNTIL
        if 'UNTIL' in rule_dict:
            until = rule_dict['UNTIL']
            if not re.match(cls.UNTIL_PATTERN, until):
                raise InvalidInputError(
                    f"Recurrence rule {rule_index} UNTIL must be in format YYYYMMDDTHHMMSSZ or YYYYMMDDTHHMMSS"
                )
        
        # Validate BYDAY
        if 'BYDAY' in rule_dict:
            cls._validate_byday(rule_dict['BYDAY'], rule_index)
        
        # Validate BYMONTH
        if 'BYMONTH' in rule_dict:
            cls._validate_bymonth(rule_dict['BYMONTH'], rule_index)
        
        # Validate BYMONTHDAY
        if 'BYMONTHDAY' in rule_dict:
            cls._validate_bymonthday(rule_dict['BYMONTHDAY'], rule_index)
        
        # Validate BYMONTH and BYMONTHDAY together
        if 'BYMONTH' in rule_dict and 'BYMONTHDAY' in rule_dict:
            cls._validate_bymonth_and_bymonthday(rule_dict['BYMONTH'], rule_dict['BYMONTHDAY'], rule_index)
        
        # Validate BYYEARDAY
        if 'BYYEARDAY' in rule_dict:
            cls._validate_byyearday(rule_dict['BYYEARDAY'], rule_index)
        
        # Validate BYWEEKNO
        if 'BYWEEKNO' in rule_dict:
            cls._validate_byweekno(rule_dict['BYWEEKNO'], rule_index)
        
        # Validate BYHOUR
        if 'BYHOUR' in rule_dict:
            cls._validate_byhour(rule_dict['BYHOUR'], rule_index)
        
        # Validate BYMINUTE
        if 'BYMINUTE' in rule_dict:
            cls._validate_byminute(rule_dict['BYMINUTE'], rule_index)
        
        # Validate BYSECOND
        if 'BYSECOND' in rule_dict:
            cls._validate_bysecond(rule_dict['BYSECOND'], rule_index)
        
        # Validate BYSETPOS
        if 'BYSETPOS' in rule_dict:
            cls._validate_bysetpos(rule_dict['BYSETPOS'], rule_index)
        
        # Validate WKST (week start)
        if 'WKST' in rule_dict:
            wkst = rule_dict['WKST']
            if wkst not in cls.VALID_BYDAY:
                raise InvalidInputError(
                    f"Recurrence rule {rule_index} has invalid WKST '{wkst}'. "
                    f"Must be one of: {', '.join(sorted(cls.VALID_BYDAY))}"
                )
    
    @classmethod
    def _validate_byday(cls, byday: str, rule_index: int) -> None:
        """Validates BYDAY parameter."""
        days = byday.split(',')
        for day in days:
            day = day.strip()
            if not day:
                continue
            
            # Check for ordinal prefix (e.g., 1SU, -1MO)
            if day[0] in '0123456789-':
                # Has ordinal prefix
                if day.startswith('-'):
                    # Negative ordinal
                    if len(day) < 3:
                        raise InvalidInputError(f"Recurrence rule {rule_index} BYDAY '{day}' has invalid format")
                    ordinal_part = day[1:-2]
                    day_part = day[-2:]
                else:
                    # Positive ordinal
                    if len(day) < 3:
                        raise InvalidInputError(f"Recurrence rule {rule_index} BYDAY '{day}' has invalid format")
                    ordinal_part = day[:-2]
                    day_part = day[-2:]
                
                # Validate ordinal
                try:
                    ordinal = int(ordinal_part)
                    if ordinal == 0 or ordinal < -53 or ordinal > 53:
                        raise InvalidInputError(f"Recurrence rule {rule_index} BYDAY ordinal must be 1-53 or -53 to -1")
                except ValueError:
                    raise InvalidInputError(f"Recurrence rule {rule_index} BYDAY '{day}' has invalid ordinal")
            else:
                # No ordinal prefix
                day_part = day
            
            # Validate day
            if day_part not in cls.VALID_BYDAY:
                raise InvalidInputError(
                    f"Recurrence rule {rule_index} BYDAY '{day}' has invalid day '{day_part}'. "
                    f"Must be one of: {', '.join(sorted(cls.VALID_BYDAY))}"
                )
    
    @classmethod
    def _validate_bymonth(cls, bymonth: str, rule_index: int) -> None:
        """Validates BYMONTH parameter."""
        months = bymonth.split(',')
        for month in months:
            month = month.strip()
            if not month:
                continue
            
            try:
                month_val = int(month)
                if month_val not in cls.VALID_BYMONTH:
                    raise InvalidInputError(f"Recurrence rule {rule_index} BYMONTH must be 1-12")
            except ValueError:
                raise InvalidInputError(f"Recurrence rule {rule_index} BYMONTH '{month}' must be an integer")
    
    @classmethod
    def _validate_bymonthday(cls, bymonthday: str, rule_index: int) -> None:
        """Validates BYMONTHDAY parameter."""
        days = bymonthday.split(',')
        for day in days:
            day = day.strip()
            if not day:
                continue
            
            try:
                day_val = int(day)
                if day_val not in cls.VALID_BYMONTHDAY:
                    raise InvalidInputError(f"Recurrence rule {rule_index} BYMONTHDAY must be 1-31")
            except ValueError:
                raise InvalidInputError(f"Recurrence rule {rule_index} BYMONTHDAY '{day}' must be an integer")

    @classmethod
    def _validate_bymonth_and_bymonthday(cls, bymonth: str, bymonthday: str, rule_index: int) -> None:
        """Validates BYMONTH and BYMONTHDAY together."""
        months = bymonth.split(',')
        days = bymonthday.split(',')
        for month in months:
            month = month.strip()
            if not month:
                continue
            try:
                month_val = int(month)
            except ValueError:
                raise InvalidInputError(f"Recurrence rule {rule_index} BYMONTH '{month}' must be an integer")
            if month_val not in cls.VALID_BYMONTH:
                raise InvalidInputError(f"Recurrence rule {rule_index} BYMONTH must be 1-12")
            for day in days:
                day = day.strip()
                if not day:
                    continue
                try:
                    day_val = int(day)
                except ValueError:
                    raise InvalidInputError(f"Recurrence rule {rule_index} BYMONTHDAY '{day}' must be an integer")
                if day_val not in cls.VALID_BYMONTHDAY:
                    raise InvalidInputError(f"Recurrence rule {rule_index} BYMONTHDAY must be 1-31")
                
                valid_days = cls.VALID_BYMONTHDAY_PER_BYMONTH[month_val]
                if day_val not in valid_days:
                    raise InvalidInputError(f"Recurrence rule {rule_index} BYMONTHDAY must be 1-{max(valid_days)} for month {month_val}")
                
    @classmethod
    def _validate_byyearday(cls, byyearday: str, rule_index: int) -> None:
        """Validates BYYEARDAY parameter."""
        days = byyearday.split(',')
        for day in days:
            day = day.strip()
            if not day:
                continue
            
            try:
                day_val = int(day)
                if day_val not in cls.VALID_BYYEARDAY:
                    raise InvalidInputError(f"Recurrence rule {rule_index} BYYEARDAY must be 1-366")
            except ValueError:
                raise InvalidInputError(f"Recurrence rule {rule_index} BYYEARDAY '{day}' must be an integer")
    
    @classmethod
    def _validate_byweekno(cls, byweekno: str, rule_index: int) -> None:
        """Validates BYWEEKNO parameter."""
        weeks = byweekno.split(',')
        for week in weeks:
            week = week.strip()
            if not week:
                continue
            
            try:
                week_val = int(week)
                if week_val not in cls.VALID_BYWEEKNO:
                    raise InvalidInputError(f"Recurrence rule {rule_index} BYWEEKNO must be 1-53")
            except ValueError:
                raise InvalidInputError(f"Recurrence rule {rule_index} BYWEEKNO '{week}' must be an integer")
    
    @classmethod
    def _validate_byhour(cls, byhour: str, rule_index: int) -> None:
        """Validates BYHOUR parameter."""
        hours = byhour.split(',')
        for hour in hours:
            hour = hour.strip()
            if not hour:
                continue
            
            try:
                hour_val = int(hour)
                if hour_val not in cls.VALID_BYHOUR:
                    raise InvalidInputError(f"Recurrence rule {rule_index} BYHOUR must be 0-23")
            except ValueError:
                raise InvalidInputError(f"Recurrence rule {rule_index} BYHOUR '{hour}' must be an integer")
    
    @classmethod
    def _validate_byminute(cls, byminute: str, rule_index: int) -> None:
        """Validates BYMINUTE parameter."""
        minutes = byminute.split(',')
        for minute in minutes:
            minute = minute.strip()
            if not minute:
                continue
            
            try:
                minute_val = int(minute)
                if minute_val not in cls.VALID_BYMINUTE:
                    raise InvalidInputError(f"Recurrence rule {rule_index} BYMINUTE must be 0-59")
            except ValueError:
                raise InvalidInputError(f"Recurrence rule {rule_index} BYMINUTE '{minute}' must be an integer")
    
    @classmethod
    def _validate_bysecond(cls, bysecond: str, rule_index: int) -> None:
        """Validates BYSECOND parameter."""
        seconds = bysecond.split(',')
        for second in seconds:
            second = second.strip()
            if not second:
                continue
            
            try:
                second_val = int(second)
                if second_val not in cls.VALID_BYSECOND:
                    raise InvalidInputError(f"Recurrence rule {rule_index} BYSECOND must be 0-59")
            except ValueError:
                raise InvalidInputError(f"Recurrence rule {rule_index} BYSECOND '{second}' must be an integer")
    
    @classmethod
    def _validate_bysetpos(cls, bysetpos: str, rule_index: int) -> None:
        """Validates BYSETPOS parameter."""
        positions = bysetpos.split(',')
        for pos in positions:
            pos = pos.strip()
            if not pos:
                continue
            
            try:
                pos_val = int(pos)
                if pos_val not in cls.VALID_BYSETPOS:
                    raise InvalidInputError(f"Recurrence rule {rule_index} BYSETPOS must be 1-366 or -366 to -1")
            except ValueError:
                raise InvalidInputError(f"Recurrence rule {rule_index} BYSETPOS '{pos}' must be an integer")

def validate_recurrence_rules(recurrence: Optional[List[str]]) -> None:
    """
    Validates recurrence rules for an event.
    
    Args:
        recurrence: List of recurrence rule strings or None
        
    Raises:
        InvalidInputError: If any rule is invalid
    """
    if recurrence is not None:
        RecurrenceValidator.validate_recurrence_rules(recurrence) 