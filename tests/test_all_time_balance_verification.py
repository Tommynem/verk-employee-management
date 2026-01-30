"""Verification test for all_time_balance() using real CSV data.

This test imports the actual CSV data from zeiterfassung_mama.csv and verifies
that the all_time_balance() calculation is correct against manually calculated
expected values.
"""

import csv
from datetime import date, time
from decimal import Decimal
from pathlib import Path

import pytest

from source.database.enums import AbsenceType
from source.services.time_calculation import TimeCalculationService
from tests.factories import TimeEntryFactory, UserSettingsFactory


def parse_csv_data(csv_path: Path) -> list[dict]:
    """Parse CSV file and return list of row dictionaries.

    Args:
        csv_path: Path to CSV file

    Returns:
        List of dictionaries with parsed data
    """
    entries = []
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            entries.append(row)
    return entries


def parse_time(time_str: str) -> time | None:
    """Parse time string in HH:MM format.

    Args:
        time_str: Time string (e.g., "07:00") or empty string

    Returns:
        time object or None if empty
    """
    if not time_str or time_str.strip() == "":
        return None
    hour, minute = map(int, time_str.split(":"))
    return time(hour, minute)


def map_absence_type(german_absence: str) -> AbsenceType:
    """Map German absence type to AbsenceType enum.

    Args:
        german_absence: German absence string from CSV

    Returns:
        AbsenceType enum value
    """
    mapping = {
        "Keine": AbsenceType.NONE,
        "Urlaub": AbsenceType.VACATION,
        "Krank": AbsenceType.SICK,
        "Gleitzeit": AbsenceType.FLEX_TIME,
        "Feiertag": AbsenceType.HOLIDAY,
    }
    return mapping.get(german_absence, AbsenceType.NONE)


def csv_to_time_entries(csv_entries: list[dict]) -> list:
    """Convert CSV entries to TimeEntry objects.

    Args:
        csv_entries: List of CSV row dictionaries

    Returns:
        List of TimeEntry objects
    """
    time_entries = []
    for row in csv_entries:
        work_date = date.fromisoformat(row["Datum"])
        start_time = parse_time(row["Startzeit"])
        end_time = parse_time(row["Endzeit"])
        break_minutes = int(row["Pause (Min)"]) if row["Pause (Min)"] else 0
        absence_type = map_absence_type(row["Abwesenheit"])
        notes = row.get("Notizen", "").strip() or None

        entry = TimeEntryFactory.build(
            work_date=work_date,
            start_time=start_time,
            end_time=end_time,
            break_minutes=break_minutes,
            absence_type=absence_type,
            notes=notes,
        )
        time_entries.append(entry)

    return time_entries


@pytest.mark.unit
def test_csv_data_import_and_balance_verification():
    """Verify all_time_balance() calculation using real CSV data.

    This test:
    1. Imports CSV data from zeiterfassung_mama.csv
    2. Converts to TimeEntry objects
    3. Calculates monthly and all-time balances
    4. Prints detailed breakdown for manual verification
    """
    # Get CSV path
    csv_path = Path(__file__).parent.parent / "data-import" / "zeiterfassung_mama.csv"
    assert csv_path.exists(), f"CSV file not found: {csv_path}"

    # Parse CSV
    csv_entries = parse_csv_data(csv_path)
    print(f"\n\nParsed {len(csv_entries)} entries from CSV")

    # Convert to TimeEntry objects
    time_entries = csv_to_time_entries(csv_entries)
    print(f"Created {len(time_entries)} TimeEntry objects")

    # Create UserSettings matching expected configuration
    settings = UserSettingsFactory.build(
        weekly_target_hours=Decimal("32.00"),  # 6.4h/day
        tracking_start_date=date(2025, 7, 1),
        initial_hours_offset=Decimal("0.00"),
    )

    # Create service
    service = TimeCalculationService()

    # Calculate all-time balance
    all_time_balance = service.all_time_balance(time_entries, settings)
    print(f"\n{'='*80}")
    print(f"ALL-TIME BALANCE: {all_time_balance} hours")
    print(f"{'='*80}\n")

    # Calculate monthly breakdown
    print("\nMONTHLY BREAKDOWN")
    print("=" * 80)

    months = [
        (2025, 7, "July"),
        (2025, 8, "August"),
        (2025, 9, "September"),
        (2025, 10, "October"),
        (2025, 11, "November"),
        (2025, 12, "December"),
    ]

    running_balance = Decimal("0.00")

    for year, month, month_name in months:
        # Get entries for this month
        month_entries = [e for e in time_entries if e.work_date.year == year and e.work_date.month == month]

        if not month_entries:
            print(f"\n{month_name} {year}: No entries")
            continue

        # Calculate monthly summary
        summary = service.monthly_summary(time_entries, settings, year, month)

        print(f"\n{month_name} {year}")
        print("-" * 80)
        print(f"  Entries:         {len(month_entries)}")
        print(f"  Actual Hours:    {summary.total_actual:>8}")
        print(f"  Target Hours:    {summary.total_target:>8}")
        print(f"  Period Balance:  {summary.period_balance:>8}")
        print(f"  Carryover In:    {summary.carryover_in:>8}")
        print(f"  Carryover Out:   {summary.carryover_out:>8}")

        # Show breakdown by absence type
        absence_counts = {}
        for entry in month_entries:
            absence_type = entry.absence_type
            absence_counts[absence_type] = absence_counts.get(absence_type, 0) + 1

        print("  Breakdown by type:")
        for absence_type, count in sorted(absence_counts.items()):
            print(f"    {absence_type.value:12s}: {count} days")

        running_balance += summary.period_balance

    print(f"\n{'='*80}")
    print(f"RUNNING BALANCE SUM (manual): {running_balance} hours")
    print(f"ALL-TIME BALANCE (calculated): {all_time_balance} hours")
    print(f"MATCH: {running_balance == all_time_balance}")
    print(f"{'='*80}\n")

    # Assertions
    assert all_time_balance == running_balance, (
        f"all_time_balance() mismatch: " f"expected {running_balance}, got {all_time_balance}"
    )


@pytest.mark.unit
def test_all_time_balance_matches_excel():
    """Verify all_time_balance() calculation against Excel reference values.

    Excel reference from "Zeiterfassung Mama ab 01.07.2025.xlsx":
    - Initial hours offset (July carryover): +24:20 (24.33 hours)
    - Final all-time balance (December): +19:30 (19.5 hours)

    This test verifies that our calculation matches the Excel file.
    """
    # Get CSV path
    csv_path = Path(__file__).parent.parent / "data-import" / "zeiterfassung_mama.csv"
    assert csv_path.exists(), f"CSV file not found: {csv_path}"

    # Parse CSV and convert to TimeEntry objects
    csv_entries = parse_csv_data(csv_path)
    time_entries = csv_to_time_entries(csv_entries)

    # Excel reference: Initial offset is +24:20 (24 hours 20 minutes)
    # 24h 20m = 24 + (20/60) = 24.33 hours (rounded)
    EXCEL_INITIAL_OFFSET = Decimal("24.33")

    # Create UserSettings with Excel initial offset
    settings = UserSettingsFactory.build(
        weekly_target_hours=Decimal("32.00"),  # 6.4h/day
        tracking_start_date=date(2025, 7, 1),
        initial_hours_offset=EXCEL_INITIAL_OFFSET,
    )

    # Create service and calculate all-time balance
    service = TimeCalculationService()
    calculated_balance = service.all_time_balance(time_entries, settings)

    # Excel reference: Final balance is +19:30 (19 hours 30 minutes)
    # 19h 30m = 19 + (30/60) = 19.5 hours
    EXCEL_EXPECTED_BALANCE = Decimal("19.50")

    # Print comparison
    print("\n" + "=" * 80)
    print("EXCEL REFERENCE VERIFICATION")
    print("=" * 80)
    print(f"Excel Initial Offset:        +24:20 ({EXCEL_INITIAL_OFFSET} hours)")
    print(f"Excel Expected Final Balance: +19:30 ({EXCEL_EXPECTED_BALANCE} hours)")
    print(f"Calculated All-Time Balance:  {calculated_balance} hours")
    print(f"Difference:                   {calculated_balance - EXCEL_EXPECTED_BALANCE} hours")
    print(f"Match (±0.2h tolerance):      {abs(calculated_balance - EXCEL_EXPECTED_BALANCE) < Decimal('0.2')}")
    print("=" * 80 + "\n")

    # Print monthly carryover progression for comparison with Excel
    print("\nMONTHLY CARRYOVER PROGRESSION (compare with Excel)")
    print("=" * 80)
    print("Excel Reference:")
    print("  July:      carryover_in=24:20 (24.33h), carryover_out=34:15 (34.25h)")
    print("  August:    carryover_in=34:15 (34.25h), carryover_out=43:45 (43.75h)")
    print("  September: carryover_in=43:45 (43.75h), carryover_out=21:34 (21.57h)")
    print("  October:   carryover_in=21:34 (21.57h), carryover_out=27:41 (27.68h)")
    print("  November:  carryover_in=27:41 (27.68h), carryover_out=17:04 (17.07h)")
    print("  December:  carryover_in=17:04 (17.07h), carryover_out=19:30 (19.50h)")
    print("\nCalculated Values:")

    months = [
        (2025, 7, "July"),
        (2025, 8, "August"),
        (2025, 9, "September"),
        (2025, 10, "October"),
        (2025, 11, "November"),
        (2025, 12, "December"),
    ]

    for year, month, month_name in months:
        summary = service.monthly_summary(time_entries, settings, year, month)
        print(f"  {month_name:9s}: carryover_in={summary.carryover_in:>6}, carryover_out={summary.carryover_out:>6}")

    print("=" * 80 + "\n")

    # Detailed month-by-month comparison
    print("\nDETAILED MONTH-BY-MONTH COMPARISON")
    print("=" * 80)

    excel_monthly_data = {
        "July": {"carryover_in": Decimal("24.33"), "carryover_out": Decimal("34.25")},
        "August": {"carryover_in": Decimal("34.25"), "carryover_out": Decimal("43.75")},
        "September": {"carryover_in": Decimal("43.75"), "carryover_out": Decimal("21.57")},
        "October": {"carryover_in": Decimal("21.57"), "carryover_out": Decimal("27.68")},
        "November": {"carryover_in": Decimal("27.68"), "carryover_out": Decimal("17.07")},
        "December": {"carryover_in": Decimal("17.07"), "carryover_out": Decimal("19.50")},
    }

    for year, month, month_name in months:
        summary = service.monthly_summary(time_entries, settings, year, month)
        excel_data = excel_monthly_data.get(month_name, {})

        print(f"\n{month_name} {year}:")
        print(f"  Calculated: carryover_in={summary.carryover_in:>6}, carryover_out={summary.carryover_out:>6}")
        print(
            f"  Excel:      carryover_in={excel_data.get('carryover_in', 'N/A'):>6}, carryover_out={excel_data.get('carryover_out', 'N/A'):>6}"
        )

        if excel_data:
            diff_in = summary.carryover_in - excel_data["carryover_in"]
            diff_out = summary.carryover_out - excel_data["carryover_out"]
            print(f"  Difference: carryover_in={diff_in:>+6.2f}, carryover_out={diff_out:>+6.2f}")

    print("=" * 80 + "\n")

    # Assert with tolerance for rounding
    tolerance = Decimal("0.2")
    assert abs(calculated_balance - EXCEL_EXPECTED_BALANCE) < tolerance, (
        f"all_time_balance() does not match Excel reference.\n"
        f"Expected: {EXCEL_EXPECTED_BALANCE} hours (±{tolerance})\n"
        f"Got: {calculated_balance} hours\n"
        f"Difference: {calculated_balance - EXCEL_EXPECTED_BALANCE} hours"
    )


@pytest.mark.unit
def test_csv_entry_count_verification():
    """Verify CSV has expected number of entries."""
    csv_path = Path(__file__).parent.parent / "data-import" / "zeiterfassung_mama.csv"
    csv_entries = parse_csv_data(csv_path)

    # CSV has 132 data rows (excluding header, line 134 is empty)
    assert len(csv_entries) == 132, f"Expected 132 entries, got {len(csv_entries)}"


@pytest.mark.unit
def test_csv_date_range_verification():
    """Verify CSV date range spans July-December 2025."""
    csv_path = Path(__file__).parent.parent / "data-import" / "zeiterfassung_mama.csv"
    csv_entries = parse_csv_data(csv_path)

    dates = [date.fromisoformat(row["Datum"]) for row in csv_entries]
    min_date = min(dates)
    max_date = max(dates)

    assert min_date == date(2025, 7, 1), f"Expected start date 2025-07-01, got {min_date}"
    assert max_date == date(2025, 12, 31), f"Expected end date 2025-12-31, got {max_date}"


@pytest.mark.unit
def test_csv_absence_type_mapping():
    """Verify all CSV absence types are mapped correctly."""
    csv_path = Path(__file__).parent.parent / "data-import" / "zeiterfassung_mama.csv"
    csv_entries = parse_csv_data(csv_path)

    absence_types = {row["Abwesenheit"] for row in csv_entries}
    print(f"\nAbsence types found in CSV: {absence_types}")

    # Verify all types can be mapped
    for absence_type in absence_types:
        mapped = map_absence_type(absence_type)
        assert mapped is not None, f"Cannot map absence type: {absence_type}"
        print(f"  {absence_type} -> {mapped.value}")


@pytest.mark.unit
def test_december_detailed_analysis():
    """Analyze December 2025 entries in detail to find discrepancy.

    This test examines December entries to understand why calculated balance
    differs from Excel reference by 6.38 hours.
    """
    # Get CSV path and load data
    csv_path = Path(__file__).parent.parent / "data-import" / "zeiterfassung_mama.csv"
    csv_entries = parse_csv_data(csv_path)
    time_entries = csv_to_time_entries(csv_entries)

    # Settings with Excel initial offset
    settings = UserSettingsFactory.build(
        weekly_target_hours=Decimal("32.00"),
        tracking_start_date=date(2025, 7, 1),
        initial_hours_offset=Decimal("24.33"),
    )

    service = TimeCalculationService()

    # Get December entries
    december_entries = [e for e in time_entries if e.work_date.year == 2025 and e.work_date.month == 12]

    print("\n" + "=" * 80)
    print("DECEMBER 2025 DETAILED ANALYSIS")
    print("=" * 80)
    print(f"Total December entries: {len(december_entries)}")

    # Calculate December summary
    december_summary = service.monthly_summary(time_entries, settings, 2025, 12)

    print("\nDecember Summary:")
    print(f"  Actual Hours:    {december_summary.total_actual}")
    print(f"  Target Hours:    {december_summary.total_target}")
    print(f"  Period Balance:  {december_summary.period_balance}")
    print(f"  Carryover In:    {december_summary.carryover_in}")
    print(f"  Carryover Out:   {december_summary.carryover_out}")

    print("\nExpected from Excel:")
    print("  Carryover In:    17.07 (17:04)")
    print("  Carryover Out:   19.50 (19:30)")
    print("  Expected Period Balance: 19.50 - 17.07 = 2.43")

    print("\nDiscrepancy:")
    print(f"  Calculated Period Balance: {december_summary.period_balance}")
    print("  Expected Period Balance:   2.43")
    print(f"  Difference:                {december_summary.period_balance - Decimal('2.43')}")

    # Analyze each December entry
    print("\n" + "-" * 80)
    print("Day-by-Day Analysis (December 2025):")
    print("-" * 80)

    daily_balances = []
    for entry in sorted(december_entries, key=lambda e: e.work_date):
        balance = service.daily_balance(entry, settings)
        daily_balances.append(balance)

        # Format absence type
        absence_str = entry.absence_type.value if entry.absence_type else "none"

        # Format times
        if entry.start_time and entry.end_time:
            times = f"{entry.start_time.strftime('%H:%M')}-{entry.end_time.strftime('%H:%M')}"
        else:
            times = "no times"

        print(
            f"{entry.work_date.strftime('%Y-%m-%d')} ({entry.work_date.strftime('%a')}): "
            f"{times:11s} | absence={absence_str:10s} | balance={balance:>6}"
        )

    total_december = sum(daily_balances)
    print("-" * 80)
    print(f"Sum of daily balances: {total_december}")
    print(f"Period balance from summary: {december_summary.period_balance}")
    print(f"Match: {total_december == december_summary.period_balance}")
    print("=" * 80 + "\n")


@pytest.mark.unit
def test_manual_calculation_sample():
    """Manually calculate balance for a few sample entries to verify logic.

    This test calculates the expected balance for the first few entries
    to ensure the calculation logic is correct.
    """
    # Settings
    settings = UserSettingsFactory.build(
        weekly_target_hours=Decimal("32.00"),  # 6.4h/day
        tracking_start_date=date(2025, 7, 1),
        initial_hours_offset=Decimal("0.00"),
    )
    service = TimeCalculationService()

    # Sample entries from CSV:
    # 2025-07-01;06:50;17:50;60;Keine;Physio ohne Mittag
    #   actual: 17:50 - 06:50 - 1h = 10h
    #   target: 6.4h (Tuesday)
    #   balance: 10h - 6.4h = +3.6h

    entry1 = TimeEntryFactory.build(
        work_date=date(2025, 7, 1),  # Tuesday
        start_time=time(6, 50),
        end_time=time(17, 50),
        break_minutes=60,
        absence_type=AbsenceType.NONE,
    )
    balance1 = service.daily_balance(entry1, settings)
    print(f"\n2025-07-01 (Tuesday): balance = {balance1}")
    assert balance1 == Decimal("3.60"), f"Expected +3.60, got {balance1}"

    # 2025-07-02;;;0;Gleitzeit;
    #   FLEX_TIME: consumes accumulated hours
    #   actual: 0h, target: 6.4h
    #   balance: 0h - 6.4h = -6.4h

    entry2 = TimeEntryFactory.build(
        work_date=date(2025, 7, 2),  # Wednesday
        start_time=None,
        end_time=None,
        break_minutes=0,
        absence_type=AbsenceType.FLEX_TIME,
    )
    balance2 = service.daily_balance(entry2, settings)
    print(f"2025-07-02 (Gleitzeit): balance = {balance2}")
    assert balance2 == Decimal("-6.40"), f"Expected -6.40, got {balance2}"

    # 2025-07-03;07:00;09:30;0;Keine;Dresden Wasserschaden
    #   actual: 09:30 - 07:00 = 2.5h
    #   target: 6.4h (Thursday)
    #   balance: 2.5h - 6.4h = -3.9h

    entry3 = TimeEntryFactory.build(
        work_date=date(2025, 7, 3),  # Thursday
        start_time=time(7, 0),
        end_time=time(9, 30),
        break_minutes=0,
        absence_type=AbsenceType.NONE,
    )
    balance3 = service.daily_balance(entry3, settings)
    print(f"2025-07-03 (Thursday): balance = {balance3}")
    assert balance3 == Decimal("-3.90"), f"Expected -3.90, got {balance3}"

    # 2025-07-04;;;0;Urlaub;
    #   VACATION: credits full target
    #   actual: 6.4h (credited), target: 6.4h
    #   balance: 0h

    entry4 = TimeEntryFactory.build(
        work_date=date(2025, 7, 4),  # Friday
        start_time=None,
        end_time=None,
        break_minutes=0,
        absence_type=AbsenceType.VACATION,
    )
    balance4 = service.daily_balance(entry4, settings)
    print(f"2025-07-04 (Urlaub): balance = {balance4}")
    assert balance4 == Decimal("0.00"), f"Expected 0.00, got {balance4}"

    # Sum of first 4 days: 3.6 + (-6.4) + (-3.9) + 0 = -6.7
    total = balance1 + balance2 + balance3 + balance4
    print(f"\nSum of first 4 days: {total}")
    assert total == Decimal("-6.70"), f"Expected -6.70, got {total}"

    print("\nManual calculation sample PASSED")
