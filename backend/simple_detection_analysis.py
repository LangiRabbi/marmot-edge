#!/usr/bin/env python3
"""
Real-time detection analysis - simple version without emoji characters
"""

import asyncio
import sys
from datetime import datetime, timedelta

sys.path.append(".")

async def analyze_workstation(workstation_id: str, seconds: int = 30):
    """Analyze detections for workstation"""

    print(f"\n=== WORKSTATION {workstation_id} ANALYSIS ({seconds}s) ===")

    try:
        from app.database import get_db_session
        from app.models.detection import Detection
        from sqlalchemy import and_, func, desc

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=seconds)

        print(f"Start: {start_time.strftime('%H:%M:%S')}")
        print(f"Monitoring for {seconds} seconds...")
        print("Time     | Persons | Details")
        print("-" * 50)

        results = []
        current_time = start_time

        while current_time < end_time:
            second_start = current_time
            second_end = current_time + timedelta(seconds=1)

            async with get_db_session() as session:
                # Check for detections in this second
                from sqlalchemy import select
                latest_detection = await session.scalar(
                    select(Detection).where(
                        and_(
                            Detection.workstation_id == workstation_id,
                            Detection.created_at >= second_start,
                            Detection.created_at < second_end
                        )
                    ).order_by(Detection.created_at.desc()).limit(1)
                )

            person_count = 0
            details = "No detection"

            if latest_detection:
                person_count = latest_detection.person_count or 0
                frame_num = latest_detection.frame_number or 0
                details = f"Frame #{frame_num}"

            timestamp_str = current_time.strftime("%H:%M:%S")
            print(f"{timestamp_str} | {person_count:7d} | {details}")

            results.append(person_count)

            await asyncio.sleep(1)
            current_time = datetime.utcnow()

            if current_time > start_time + timedelta(seconds=seconds + 5):
                print("WARNING: Analysis timeout")
                break

        # Summary
        total_detections = sum(1 for count in results if count > 0)
        max_persons = max(results) if results else 0
        avg_persons = sum(results) / len(results) if results else 0

        print("-" * 50)
        print(f"SUMMARY for workstation {workstation_id}:")
        print(f"  Detection events: {total_detections}/{seconds}")
        print(f"  Max persons: {max_persons}")
        print(f"  Average persons: {avg_persons:.2f}")
        print(f"  Detection rate: {(total_detections/seconds)*100:.1f}%")

        if total_detections == 0:
            print("  CRITICAL: NO DETECTIONS - YOLOv11 NOT WORKING!")

        return results

    except Exception as e:
        print(f"ERROR: {e}")
        return []

async def main():
    """Run analysis on both workstations"""

    print("REAL-TIME DETECTION ANALYSIS")
    print("Testing YOLOv11 processing on live streams")
    print("=" * 60)

    try:
        # Check database state first
        from app.database import get_db_session
        from app.models.detection import Detection
        from sqlalchemy import func, desc

        async with get_db_session() as session:
            total_detections = await session.scalar(func.count(Detection.id))
            print(f"Total detections in database: {total_detections}")

            # Check last detection
            from sqlalchemy import select
            latest = await session.scalar(
                select(Detection).order_by(desc(Detection.created_at)).limit(1)
            )
            if latest:
                print(f"Latest detection: {latest.created_at} (workstation {latest.workstation_id})")
            else:
                print("No detections found in database")

        # Analyze workstation 8 (Krupowki) for 30 seconds
        results_8 = await analyze_workstation("8", 30)

        # Brief pause
        await asyncio.sleep(2)

        # Analyze workstation 7 (ziemniaki) for 30 seconds
        results_7 = await analyze_workstation("7", 30)

        # Final analysis
        print("\n" + "=" * 60)
        print("FINAL RESULTS:")

        detections_8 = sum(1 for count in results_8 if count > 0)
        detections_7 = sum(1 for count in results_7 if count > 0)

        print(f"Workstation 8 (Krupowki): {detections_8}/30 detections")
        print(f"Workstation 7 (ziemniaki): {detections_7}/30 detections")

        if detections_8 == 0 and detections_7 == 0:
            print("CRITICAL: NO LIVE DETECTIONS ON EITHER WORKSTATION!")
            print("This confirms YOLOv11 is NOT processing live streams.")
            print("Only test broadcasts work via API endpoint.")

        print("Analysis completed.")

    except Exception as e:
        print(f"MAIN ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())