#!/usr/bin/env python3
"""
Real-time detection analysis for Krupówki (workstation 8) and ziemniaki (workstation 7)
Analyzes 30 seconds second-by-second to identify detection rate issues
"""

import asyncio
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sqlite3
import json

sys.path.append(".")

async def analyze_workstation_detections(workstation_id: str, duration_seconds: int = 30) -> List[Tuple[datetime, int, str]]:
    """Analyze real-time detections for a specific workstation"""

    results = []
    print(f"\nANALYZING WORKSTATION {workstation_id} - {duration_seconds} SECONDS")
    print("=" * 60)

    try:
        from app.database import get_db_session
        from app.models.detection import Detection
        from sqlalchemy import and_, func

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=duration_seconds)

        print(f"Start: {start_time.strftime('%H:%M:%S')}")
        print(f"End:   {end_time.strftime('%H:%M:%S')}")
        print("\nREAL-TIME DETECTION MONITORING:")
        print("Time     | Persons | Detection Data")
        print("-" * 60)

        # Monitor every second
        current_time = start_time
        while current_time < end_time:

            # Check database for new detections in the last second
            second_start = current_time
            second_end = current_time + timedelta(seconds=1)

            async with get_db_session() as session:
                # Count detections in this second
                detection_count = await session.scalar(
                    func.count(Detection.id).where(
                        and_(
                            Detection.workstation_id == workstation_id,
                            Detection.created_at >= second_start,
                            Detection.created_at < second_end
                        )
                    )
                )

                # Get latest detection with person count
                latest_detection = await session.scalar(
                    session.query(Detection).where(
                        and_(
                            Detection.workstation_id == workstation_id,
                            Detection.created_at >= second_start,
                            Detection.created_at < second_end
                        )
                    ).order_by(Detection.created_at.desc()).limit(1)
                )

            person_count = 0
            detection_info = "No detection"

            if latest_detection:
                person_count = latest_detection.person_count or 0
                frame_num = latest_detection.frame_number or 0
                confidence_data = latest_detection.confidence_scores or {}
                detection_info = f"Frame #{frame_num}, Confidence: {confidence_data}"

            # Log the result
            timestamp_str = current_time.strftime("%H:%M:%S")
            print(f"{timestamp_str} | {person_count:7d} | {detection_info}")

            results.append((current_time, person_count, detection_info))

            # Wait for next second
            await asyncio.sleep(1)
            current_time = datetime.utcnow()

            # Safety check - don't run longer than expected
            if current_time > start_time + timedelta(seconds=duration_seconds + 5):
                print("⚠️ WARNING: Analysis took longer than expected, stopping...")
                break

        # Summary
        total_detections = sum(1 for _, count, _ in results if count > 0)
        max_persons = max((count for _, count, _ in results), default=0)
        avg_persons = sum(count for _, count, _ in results) / len(results) if results else 0

        print("\n" + "=" * 60)
        print(f"📊 WORKSTATION {workstation_id} SUMMARY ({duration_seconds}s):")
        print(f"   🔢 Total detection events: {total_detections}")
        print(f"   👥 Max persons detected: {max_persons}")
        print(f"   📈 Average persons: {avg_persons:.2f}")
        print(f"   📋 Detection rate: {total_detections}/{duration_seconds}s = {(total_detections/duration_seconds)*100:.1f}%")

        if total_detections == 0:
            print("   🚨 CRITICAL: NO DETECTIONS FOUND - YOLOv11 NOT PROCESSING LIVE STREAMS!")
        elif total_detections < duration_seconds * 0.1:  # Less than 10% detection rate
            print("   ⚠️ WARNING: Very low detection rate - possible processing issues")
        else:
            print("   ✅ Detection rate appears normal")

        return results

    except Exception as e:
        print(f"❌ ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()
        return []

async def main():
    """Run comprehensive real-time detection analysis"""

    print("🎯 REAL-TIME DETECTION ANALYSIS")
    print("Testing live YOLOv11 processing on dynamic scenes")
    print("=" * 80)

    try:
        # Test both workstations
        workstations = [
            ("8", "Krupówki (dynamic scene with people)"),
            ("7", "ziemniaki (dynamic scene with potatoes)")
        ]

        all_results = {}

        for workstation_id, description in workstations:
            print(f"\n🏭 WORKSTATION {workstation_id}: {description}")

            results = await analyze_workstation_detections(workstation_id, duration_seconds=30)
            all_results[workstation_id] = results

            # Brief pause between analyses
            await asyncio.sleep(2)

        # Final comparative analysis
        print("\n" + "=" * 80)
        print("🔍 COMPARATIVE ANALYSIS")
        print("=" * 80)

        for workstation_id, results in all_results.items():
            if results:
                detection_events = sum(1 for _, count, _ in results if count > 0)
                max_persons = max((count for _, count, _ in results), default=0)
                print(f"Workstation {workstation_id}: {detection_events}/30 detections, max {max_persons} persons")
            else:
                print(f"Workstation {workstation_id}: Analysis failed")

        # Database state check
        print("\n📊 DATABASE STATE CHECK:")
        from app.database import get_db_session
        from app.models.detection import Detection
        from sqlalchemy import func, desc

        async with get_db_session() as session:
            # Total detections ever
            total_detections = await session.scalar(func.count(Detection.id))
            print(f"   Total detection records: {total_detections}")

            # Last 5 minutes
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            recent_detections = await session.scalar(
                func.count(Detection.id).where(Detection.created_at >= five_minutes_ago)
            )
            print(f"   Detections last 5 minutes: {recent_detections}")

            # Latest detection
            latest = await session.scalar(
                session.query(Detection).order_by(desc(Detection.created_at)).limit(1)
            )
            if latest:
                print(f"   Latest detection: {latest.created_at} (workstation {latest.workstation_id})")
            else:
                print("   No detections found")

        if all(len(results) == 0 or sum(1 for _, count, _ in results if count > 0) == 0 for results in all_results.values()):
            print("\n🚨 CRITICAL FINDING: NO LIVE DETECTIONS ON EITHER WORKSTATION")
            print("   This confirms YOLOv11 is NOT processing live video streams")
            print("   Only test broadcasts work (via /api/v1/websocket/broadcast)")
            print("   Live stream processing pipeline is broken!")

        print("\n✅ Real-time detection analysis completed")

    except Exception as e:
        print(f"❌ ANALYSIS ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())