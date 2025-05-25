from supabase import create_client, Client
from config import config
from typing import Dict, Any, List
import json

class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        self.sessions_table = "interview_sessions"
        self.reports_table = "evaluation_reports"
    
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new interview session"""
        try:
            # Convert datetime objects to strings
            session_data = self._serialize_data(session_data)
            
            result = self.client.table(self.sessions_table).insert([session_data]).execute()
            
            if hasattr(result, 'data') and result.data:
                return result.data[0]
            else:
                raise Exception("Failed to create session")
                
        except Exception as e:
            print(f"Database error creating session: {str(e)}")
            return session_data  # Return original data as fallback
    
    async def update_session(self, session_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing interview session"""
        try:
            # Convert datetime objects to strings
            session_data = self._serialize_data(session_data)
            
            result = self.client.table(self.sessions_table)\
                .update(session_data)\
                .eq('session_id', session_id)\
                .execute()
            
            if hasattr(result, 'data') and result.data:
                return result.data[0]
            else:
                return session_data
                
        except Exception as e:
            print(f"Database error updating session: {str(e)}")
            return session_data  # Return original data as fallback
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get interview session by ID"""
        try:
            result = self.client.table(self.sessions_table)\
                .select("*")\
                .eq('session_id', session_id)\
                .execute()
            
            if hasattr(result, 'data') and result.data:
                return result.data[0]
            else:
                return None
                
        except Exception as e:
            print(f"Database error getting session: {str(e)}")
            return None
    
    async def save_report(self, session_id: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save evaluation report"""
        try:
            report_record = {
                "session_id": session_id,
                "report_data": json.dumps(report_data),
                "created_at": report_data.get("candidate_info", {}).get("evaluation_date")
            }
            
            result = self.client.table(self.reports_table).insert([report_record]).execute()
            
            if hasattr(result, 'data') and result.data:
                return result.data[0]
            else:
                return report_record
                
        except Exception as e:
            print(f"Database error saving report: {str(e)}")
            return report_record
    
    async def get_report(self, session_id: str) -> Dict[str, Any]:
        """Get evaluation report by session ID"""
        try:
            result = self.client.table(self.reports_table)\
                .select("*")\
                .eq('session_id', session_id)\
                .execute()
            
            if hasattr(result, 'data') and result.data:
                report_json = result.data[0].get('report_data', '{}')
                return json.loads(report_json)
            else:
                return None
                
        except Exception as e:
            print(f"Database error getting report: {str(e)}")
            return None
    
    async def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent interview sessions"""
        try:
            result = self.client.table(self.sessions_table)\
                .select("session_id, created_at, status, candidate_name, role")\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            if hasattr(result, 'data'):
                return result.data
            else:
                return []
                
        except Exception as e:
            print(f"Database error listing sessions: {str(e)}")
            return []
    
    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert complex data types to JSON-serializable format"""
        serialized = {}
        
        for key, value in data.items():
            if hasattr(value, 'isoformat'):  # datetime objects
                serialized[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                serialized[key] = json.dumps(value) if key in ['cv_data', 'questions', 'answers', 'assessment', 'assessment_result', 'final_report'] else value
            else:
                serialized[key] = value
        
        return serialized
    
    async def setup_tables(self):
        """Setup database tables (run once during deployment)"""
        
        # Create sessions table
        sessions_schema = """
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            status VARCHAR(50) DEFAULT 'initialized',
            candidate_name VARCHAR(255),
            candidate_email VARCHAR(255),
            role VARCHAR(255),
            cv_data JSONB,
            questions JSONB,
            current_question_index INTEGER DEFAULT 0,
            answers JSONB,
            assessment JSONB,
            assessment_result JSONB,
            final_report JSONB
        );
        """
        
        # Create reports table
        reports_schema = """
        CREATE TABLE IF NOT EXISTS evaluation_reports (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) REFERENCES interview_sessions(session_id),
            report_data JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        try:
            # Note: Supabase Python client doesn't support direct SQL execution
            # These would need to be run via Supabase dashboard or SQL editor
            print("Database schema setup required via Supabase dashboard:")
            print(sessions_schema)
            print(reports_schema)
            
        except Exception as e:
            print(f"Schema setup error: {str(e)}")