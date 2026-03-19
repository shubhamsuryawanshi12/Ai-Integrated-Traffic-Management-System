from app.models.parking_category import VehicleCategory, CategorySlotConfig
import math

class PricingService:
    @staticmethod
    def calculate_fare(
        category: VehicleCategory,
        config: CategorySlotConfig,
        duration_hours: float,
        is_overnight: bool = False
    ) -> float:
        """
        Calculates the fare based on the category-specific configuration.
        Implements 1st hour premium, hourly rate, overnight flat rate, and daily cap.
        """
        if duration_hours <= 0:
            return 0.0

        # Handle overnight flat rate if Applicable
        if is_overnight and config.overnight_flat is not None:
            base_fare = config.overnight_flat
        else:
            # Handle 1st hour vs remaining
            first_hour_rate = config.price_first_hour if config.price_first_hour is not None else config.price_per_hour
            
            if duration_hours <= 1.0:
                base_fare = first_hour_rate
            else:
                remaining_hours = math.ceil(duration_hours - 1.0)
                base_fare = first_hour_rate + (remaining_hours * config.price_per_hour)

        # Apply daily cap if configured
        if config.daily_cap is not None:
            base_fare = min(base_fare, config.daily_cap)

        # Apply EV charging if Applicable (Simplified: charging for entire duration)
        if config.has_ev_charging and config.ev_charging_per_hour:
            charging_fee = duration_hours * config.ev_charging_per_hour
            base_fare += charging_fee

        return round(base_fare, 2)

    @staticmethod
    def get_tier1_defaults() -> dict:
        """Returns standard recommended pricing for major cities."""
        return {
            "2w":           {"hour": 10, "first": 10,  "cap": 80,  "flat": 30},
            "2w_ev":        {"hour": 10, "first": 10,  "cap": 80,  "flat": 30},
            "4w_compact":   {"hour": 30, "first": 40,  "cap": 250, "flat": 80},
            "4w_midsize":   {"hour": 40, "first": 50,  "cap": 350, "flat": 100},
            "4w_large":     {"hour": 60, "first": 80,  "cap": 500, "flat": 150},
            "4w_xl":        {"hour": 100, "first": 120, "cap": 800, "flat": 200},
            "4w_ev":        {"hour": 50, "first": 60,  "cap": 400, "flat": 120},
        }
