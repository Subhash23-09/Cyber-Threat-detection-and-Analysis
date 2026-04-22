from datetime import datetime, date, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models_v2 import DailyStats, UserBaseline
import math

class AnomalyService:
    """
    Statistical Anomaly Detection Engine
    - Tracks daily usage stats per user/IP
    - Calculates baselines (Mean + StdDev)
    - Detects Z-Score anomalies
    """

    MIN_TRAINING_DAYS = 7  # Warm-up period
    STRICT_Z_SCORE = 3.0   # 99.7% confidence interval

    @staticmethod
    async def update_stats(session: AsyncSession, entity_type: str, entity_val: str, count: int = 1):
        """
        Increment the daily event count for a user or IP.
        """
        today = date.today()
        
        # Check if record exists for today - Use func.date for strict day-level comparison
        stmt = select(DailyStats).where(
            and_(
                func.date(DailyStats.date) == today,
                DailyStats.entity_type == entity_type,
                DailyStats.entity_val == entity_val
            )
        )
        result = await session.execute(stmt)
        stat = result.scalars().first()

        if stat:
            stat.event_count += count
        else:
            stat = DailyStats(
                date=today,
                entity_type=entity_type,
                entity_val=entity_val,
                event_count=count
            )
            session.add(stat)
        
        # We don't commit here to allow batching by the caller, 
        # but if needed we could. For now, assume caller commits.
        return stat

    @staticmethod
    async def get_anomaly_score(session: AsyncSession, entity_type: str, entity_val: str, current_count: int) -> dict:
        """
        Check if the current activity deviates from the baseline.
        Returns: {
            "is_anomaly": bool,
            "z_score": float,
            "baseline_mean": float,
            "description": str
        }
        """
        # Get Baseline
        stmt = select(UserBaseline).where(
            and_(
                UserBaseline.entity_type == entity_type,
                UserBaseline.entity_val == entity_val
            )
        )
        result = await session.execute(stmt)
        baseline = result.scalars().first()

        # Default Response
        response = {
            "is_anomaly": False,
            "z_score": 0.0,
            "baseline_mean": 0.0,
            "description": "No baseline data available (Learning Mode)"
        }

        if not baseline:
            return response

        # Check Warm-up Period (Optional: Check number of DailyStats entries if baseline is empty)
        # Assuming baseline is only created after MIN_TRAINING_DAYS
        # But if we just rely on the baseline object existing:
        if baseline.avg_events_per_day == 0 and baseline.std_dev_events == 0:
             return response

        # Calculate Z-Score
        # Z = (X - Mean) / StdDev
        if baseline.std_dev_events == 0:
            # Avoid division by zero. If std_dev is 0, it means consistency.
            # If current != mean, it's technically infinite Z-score.
            # We treat it as high if difference is significant (> 5 events)
            diff = abs(current_count - baseline.avg_events_per_day)
            response["z_score"] = 10.0 if diff > 5 else 0.0
        else:
            response["z_score"] = (current_count - baseline.avg_events_per_day) / baseline.std_dev_events

        response["baseline_mean"] = baseline.avg_events_per_day
        
        # Threshold Check
        if response["z_score"] > AnomalyService.STRICT_Z_SCORE:
            response["is_anomaly"] = True
            response["description"] = (
                f"Statistical Anomaly Detected: Activity is {response['z_score']:.1f}σ "
                f"above normal (Avg: {baseline.avg_events_per_day:.1f})"
            )
        else:
            response["description"] = "Within normal statistical range"

        return response

    @staticmethod
    async def calculate_baselines(session: AsyncSession):
        """
        Background Job: Recalculate baselines for all users based on DailyStats.
        Should be run once every 24h.
        """
        # Get all unique entities
        # This is a simplified version. Ideally we iterate distinct entities.
        # For now, let's just process everyone who has stats.
        
        # Subquery to count days per entity
        # We need entities with > MIN_TRAINING_DAYS of history
        
        # Step 1: Get list of entities with enough data
        # Note: Implementing pure SQL aggregation for efficiency
        
        # Find entities with >= 7 entries
        # SELECT entity_type, entity_val FROM daily_stats GROUP BY ... HAVING count(*) >= 7
        
        stmt = select(
            DailyStats.entity_type, 
            DailyStats.entity_val, 
            func.count(DailyStats.id).label('days_active'),
            func.avg(DailyStats.event_count).label('avg_count'),
            func.stddev(DailyStats.event_count).label('std_dev')
        ).group_by(
            DailyStats.entity_type, 
            DailyStats.entity_val
        ).having(func.count(DailyStats.id) >= AnomalyService.MIN_TRAINING_DAYS)

        result = await session.execute(stmt)
        rows = result.all()

        count_updates = 0
        for row in rows:
            e_type, e_val, days, avg, std = row
            
            # Update or Create Baseline
            b_stmt = select(UserBaseline).where(
                and_(
                    UserBaseline.entity_type == e_type,
                    UserBaseline.entity_val == e_val
                )
            )
            b_result = await session.execute(b_stmt)
            baseline = b_result.scalars().first()

            if not baseline:
                baseline = UserBaseline(entity_type=e_type, entity_val=e_val)
                session.add(baseline)
            
            baseline.avg_events_per_day = float(avg)
            baseline.std_dev_events = float(std) if std else 0.0
            count_updates += 1
        
        # Commit all changes
        await session.commit()
        return count_updates
