"""
supabase_client.py
Supabase connection for storing prediction logs and user activity.
We use this to keep track of predictions made through the app.

Mehmet Tanil Kaplan - T0429362
"""

import os
from datetime import datetime

# supabase credentials
SUPABASE_URL = os.getenv(
    'SUPABASE_URL',
    'https://onvbqyxrgpqnipiavvxv.supabase.co'
)
SUPABASE_KEY = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9udmJxeXhyZ3BxbmlwaWF2dnh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQxNTYxNjksImV4cCI6MjA4OTczMjE2OX0.pYei_3LMHAqhKa3_6vGJVLk81f8LpQQ1f5pEI75pf3k'
)

# lazy init so import never crashes the backend
_supabase = None


def _get_client():
    global _supabase
    if _supabase is None:
        try:
            from supabase import create_client
            _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Warning: could not connect to supabase: {e}")
            return None
    return _supabase


def log_prediction(ticker, baseline_pred, lstm_pred, last_close):
    """Save a prediction record to supabase for tracking."""
    try:
        client = _get_client()
        if not client:
            return None
        record = {
            'ticker': ticker,
            'baseline_prediction': baseline_pred,
            'lstm_prediction': lstm_pred,
            'last_close': last_close,
            'created_at': datetime.utcnow().isoformat()
        }
        result = client.table('prediction_logs').insert(record).execute()
        return result
    except Exception as e:
        # dont crash the app if supabase logging fails
        print(f"Warning: could not log prediction to supabase: {e}")
        return None


def get_prediction_history(ticker=None, limit=50):
    """Fetch recent prediction logs from supabase."""
    try:
        client = _get_client()
        if not client:
            return []
        query = client.table('prediction_logs').select('*').order(
            'created_at', desc=True
        ).limit(limit)

        if ticker:
            query = query.eq('ticker', ticker)

        result = query.execute()
        return result.data
    except Exception as e:
        print(f"Warning: could not fetch from supabase: {e}")
        return []
