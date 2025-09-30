#!/usr/bin/env python3
"""
Advanced Delivery Root Cause Analytics System

This system aggregates multi-domain data (orders, fleet logs, warehouse logs, external factors, 
and customer feedback) to provide intelligent root cause analysis for delivery failures and delays.

Key Features:
- Natural language query processing
- Automated event correlation
- Human-readable insights
- Actionable recommendations
- Support for all sample use cases

Usage: python delivery_root_cause_analyzer.py
"""

import os
import sys
import json
import re
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import dateparser
from dotenv import load_dotenv
import requests
import time

# Load environment variables
load_dotenv()

# Configuration
AUDIT_DIR = Path("./audit")
AUDIT_DIR.mkdir(exist_ok=True)

# Perplexity AI Configuration
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
PERPLEXITY_BASE_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = os.getenv('PERPLEXITY_MODEL', 'sonar')
PERPLEXITY_MAX_TOKENS = int(os.getenv('PERPLEXITY_MAX_TOKENS', '1000'))
PERPLEXITY_TEMPERATURE = float(os.getenv('PERPLEXITY_TEMPERATURE', '0.2'))

# Data file paths
DATA_FILES = {
    'orders': 'orders.csv',
    'fleet_logs': 'fleet_logs.csv',
    'warehouse_logs': 'warehouse_logs.csv',
    'external_factors': 'external_factors.csv',
    'feedback': 'feedback.csv',
    'warehouses': 'warehouses.csv',
    'clients': 'clients.csv',
    'drivers': 'drivers.csv'
}

class DeliveryAnalyzer:
    """Main class for delivery analytics and root cause analysis"""
    
    def __init__(self):
        self.data = {}
        self.integrated_df = None
        # Perplexity integration flag
        self.use_perplexity = bool(PERPLEXITY_API_KEY)
        if self.use_perplexity:
            print("🤖 Perplexity AI integration enabled")
        else:
            print("📋 Using rule-based NLP (Perplexity disabled)")
        self.load_all_data()
        self.create_integrated_dataset()
    
    def load_all_data(self):
        """Load all CSV files into memory"""
        print("Loading data files...")
        for key, filename in DATA_FILES.items():
            filepath = Path(filename)
            if filepath.exists():
                try:
                    self.data[key] = pd.read_csv(filepath)
                    print(f"✓ Loaded {filename}: {len(self.data[key])} records")
                except Exception as e:
                    print(f"✗ Error loading {filename}: {e}")
            else:
                print(f"✗ File not found: {filename}")
    
    def create_integrated_dataset(self):
        """Create an integrated dataset by joining all relevant data"""
        print("\nCreating integrated dataset...")
        
        if 'orders' not in self.data:
            raise ValueError("Orders data is required as the primary dataset")
        
        # Start with orders as the base
        df = self.data['orders'].copy()
        print(f"Base orders columns: {list(df.columns)}")
        
        # Parse dates
        date_columns = ['order_date', 'promised_delivery_date', 'actual_delivery_date', 'created_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Add warehouse information
        if 'warehouses' in self.data:
            # Create warehouse mapping based on city for simplicity
            warehouse_mapping = self.data['warehouses'].groupby('city')['warehouse_id'].first().to_dict()
            df['warehouse_id'] = df['city'].map(warehouse_mapping)
            df = df.merge(
                self.data['warehouses'][['warehouse_id', 'warehouse_name', 'capacity', 'manager_name']],
                on='warehouse_id', how='left'
            )
        
        # Add client information
        if 'clients' in self.data:
            df = df.merge(
                self.data['clients'][['client_id', 'client_name', 'contact_person']],
                on='client_id', how='left'
            )
        
        # Add fleet logs information
        if 'fleet_logs' in self.data:
            fleet_summary = self.data['fleet_logs'].groupby('order_id').agg({
                'driver_id': 'first',
                'vehicle_number': 'first',
                'route_code': 'first',
                'gps_delay_notes': lambda x: ', '.join(filter(lambda y: y and pd.notna(y), x)) if any(pd.notna(x)) else None,
                'departure_time': 'first',
                'arrival_time': 'first'
            }).reset_index()
            
            df = df.merge(fleet_summary, on='order_id', how='left')
        
        # Add driver information
        if 'drivers' in self.data and 'driver_id' in df.columns:
            df = df.merge(
                self.data['drivers'][['driver_id', 'driver_name', 'partner_company', 'status']],
                on='driver_id', how='left'
            )
        
        # Add warehouse logs
        if 'warehouse_logs' in self.data:
            warehouse_summary = self.data['warehouse_logs'].groupby('order_id').agg({
                'picking_start': 'first',
                'picking_end': 'first',
                'dispatch_time': 'first',
                'notes': lambda x: ', '.join(filter(lambda y: y and pd.notna(y), x)) if any(pd.notna(x)) else None
            }).reset_index()
            
            df = df.merge(warehouse_summary, on='order_id', how='left', suffixes=('', '_warehouse'))
        
        # Add external factors
        if 'external_factors' in self.data:
            external_summary = self.data['external_factors'].groupby('order_id').agg({
                'traffic_condition': 'first',
                'weather_condition': 'first',
                'event_type': lambda x: ', '.join(filter(lambda y: y and pd.notna(y), x)) if any(pd.notna(x)) else None
            }).reset_index()
            
            df = df.merge(external_summary, on='order_id', how='left')
        
        # Add customer feedback
        if 'feedback' in self.data:
            feedback_summary = self.data['feedback'].groupby('order_id').agg({
                'feedback_text': lambda x: ' | '.join(x),
                'sentiment': 'first',
                'rating': 'mean'
            }).reset_index()
            
            df = df.merge(feedback_summary, on='order_id', how='left')
        
        # Create derived features for root cause analysis
        self.add_root_cause_features(df)
        
        self.integrated_df = df
        print(f"✓ Integrated dataset created: {len(df)} records with {len(df.columns)} features")
    
    def add_root_cause_features(self, df):
        """Add derived features for root cause analysis"""
        
        # Calculate delivery delay in days
        df['delivery_delay_days'] = (
            (df['actual_delivery_date'] - df['promised_delivery_date']).dt.days
        ).fillna(0)
        
        # Ensure status column exists (check if it was dropped during merges)
        if 'status' not in df.columns:
            print("Warning: 'status' column missing after merges")
            df['status'] = 'Unknown'
        
        # Determine if order was delayed
        df['is_delayed'] = (df['delivery_delay_days'] > 0) | (df['status'].isin(['Failed', 'Returned', 'Pending']))
        
        # Infer primary root causes based on failure_reason (simpler approach)
        df['primary_root_cause'] = 'Other/Unknown'
        
        if 'failure_reason' in df.columns:
            # Map failure reasons to root causes
            df.loc[df['failure_reason'].str.contains('Traffic|congestion', case=False, na=False), 'primary_root_cause'] = 'Traffic Congestion'
            df.loc[df['failure_reason'].str.contains('Weather|disruption', case=False, na=False), 'primary_root_cause'] = 'Weather Disruption'
            df.loc[df['failure_reason'].str.contains('Warehouse|delay', case=False, na=False), 'primary_root_cause'] = 'Warehouse Operations'
            df.loc[df['failure_reason'].str.contains('address|Address', case=False, na=False), 'primary_root_cause'] = 'Address Issues'
            df.loc[df['failure_reason'].str.contains('Stock|stock', case=False, na=False), 'primary_root_cause'] = 'Stock Unavailability'
            df.loc[df['failure_reason'].str.contains('Vehicle|breakdown', case=False, na=False), 'primary_root_cause'] = 'Vehicle Issues'
        
        # For failed orders without specific failure reasons, use status
        df.loc[df['status'] == 'Failed', 'primary_root_cause'] = df.loc[df['status'] == 'Failed', 'failure_reason'].fillna('Unknown Failure')
        df.loc[df['status'] == 'Returned', 'primary_root_cause'] = 'Customer Return'
        df.loc[df['status'] == 'Pending', 'primary_root_cause'] = 'Processing Delay'
        
        # Add severity classification
        df['severity'] = 'Low'
        df.loc[df['delivery_delay_days'] > 2, 'severity'] = 'Medium'
        df.loc[df['delivery_delay_days'] > 5, 'severity'] = 'High'
        df.loc[df['status'] == 'Failed', 'severity'] = 'Critical'
        
        # Add time-based features
        df['order_hour'] = df['order_date'].dt.hour
        df['order_day_of_week'] = df['order_date'].dt.day_name()
        df['order_month'] = df['order_date'].dt.month_name()
    
    def call_perplexity_api(self, prompt, max_retries=3):
        """Make API call to Perplexity with error handling and retries"""
        
        if not self.use_perplexity:
            return None
            
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": PERPLEXITY_MODEL,
            "messages": [
                {
                    "role": "system", 
                    "content": "You are an expert delivery logistics analyst. Provide structured, actionable insights based on data analysis."
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": PERPLEXITY_MAX_TOKENS,
            "temperature": PERPLEXITY_TEMPERATURE
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    PERPLEXITY_BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content']
                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    print(f"⏳ Rate limit hit, waiting {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    print(f"⚠️ Perplexity API error {response.status_code}: {response.text}")
                    return None
                    
            except requests.RequestException as e:
                print(f"⚠️ Perplexity API request failed (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                    
        print("❌ Perplexity API unavailable, falling back to rule-based processing")
        return None
    
    def parse_natural_language_query(self, query):
        """Parse natural language query using Perplexity AI or fallback to rule-based"""
        
        if self.use_perplexity:
            ai_result = self.parse_query_with_perplexity(query)
            if ai_result:
                return ai_result
        
        # Fallback to rule-based parsing
        return self.parse_query_rule_based(query)
    
    def parse_query_with_perplexity(self, query):
        """Use Perplexity AI for advanced natural language understanding"""
        
        # Get available entities from data
        available_cities = []
        available_clients = []
        if self.integrated_df is not None:
            available_cities = self.integrated_df['city'].unique().tolist()[:15]  # Limit for token efficiency
            available_clients = self.integrated_df['client_name'].unique().tolist()[:10]
        
        prompt = f'''Analyze this delivery logistics query and extract structured information:

Query: "{query}"

Available Cities: {available_cities}
Available Clients: {available_clients}

Return ONLY a valid JSON object with:
- intent: one of [explain_causes, compare, predict, rank, analyze_trends]
- entities:
  - cities: list of mentioned cities (from available cities)
  - clients: list of mentioned client names
  - warehouses: list of mentioned warehouses
  - date_filters: object with extracted time references
- analysis_focus: specific aspect to analyze
- confidence: 0-1 score for parsing confidence

Example:
{{
  "intent": "explain_causes",
  "entities": {{
    "cities": ["Mumbai", "Delhi"],
    "clients": ["ClientA"],
    "warehouses": [],
    "date_filters": {{"relative": "last_week"}}
  }},
  "analysis_focus": "delivery delays",
  "confidence": 0.95
}}'''
        
        ai_response = self.call_perplexity_api(prompt)
        
        if ai_response:
            try:
                # Extract JSON from AI response
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    parsed_data = json.loads(json_match.group())
                    
                    # Convert to our internal format
                    return {
                        'intent': parsed_data.get('intent', 'explain_causes'),
                        'cities': parsed_data.get('entities', {}).get('cities', []),
                        'clients': parsed_data.get('entities', {}).get('clients', []),
                        'warehouses': parsed_data.get('entities', {}).get('warehouses', []),
                        'time_references': [parsed_data.get('entities', {}).get('date_filters', {}).get('relative', '')],
                        'original_query': query,
                        'ai_enhanced': True,
                        'confidence': parsed_data.get('confidence', 0.8)
                    }
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"⚠️ Failed to parse Perplexity response: {e}")
        
        return None
    
    def parse_query_rule_based(self, query):
        """Original rule-based parsing method as fallback"""
        query = query.lower().strip()
        
        # Extract time parameters
        time_patterns = {
            'yesterday': datetime.now() - timedelta(days=1),
            'last week': datetime.now() - timedelta(weeks=1),
            'last month': datetime.now() - timedelta(days=30),
            'this month': datetime.now().replace(day=1),
        }
        
        # Extract cities
        cities = ['ahmedabad', 'mumbai', 'delhi', 'bangalore', 'chennai', 'pune', 'surat', 'coimbatore', 'mysuru', 'nagpur']
        mentioned_cities = [city for city in cities if city in query]
        
        # Extract clients (simplified)
        client_pattern = r'client\s+([a-z]+)'
        client_matches = re.findall(client_pattern, query)
        
        # Extract warehouse references
        warehouse_pattern = r'warehouse\s+([a-z]+|\d+)'
        warehouse_matches = re.findall(warehouse_pattern, query)
        
        # Determine intent
        intent = 'unknown'
        if any(word in query for word in ['why', 'explain', 'reasons', 'causes']):
            intent = 'explain_causes'
        elif any(word in query for word in ['compare', 'comparison']):
            intent = 'compare'
        elif any(word in query for word in ['predict', 'forecast', 'expect', 'prepare']):
            intent = 'predict'
        elif any(word in query for word in ['top', 'most', 'highest']):
            intent = 'rank'
        
        return {
            'intent': intent,
            'cities': mentioned_cities,
            'clients': client_matches,
            'warehouses': warehouse_matches,
            'time_references': [k for k, v in time_patterns.items() if k in query],
            'original_query': query
        }
    
    def filter_data(self, filters):
        """Apply filters to the integrated dataset"""
        df = self.integrated_df.copy()
        
        if 'cities' in filters and filters['cities']:
            df = df[df['city'].str.lower().isin([c.lower() for c in filters['cities']])]
        
        if 'date_from' in filters and filters['date_from']:
            df = df[df['order_date'] >= pd.to_datetime(filters['date_from'])]
        
        if 'date_to' in filters and filters['date_to']:
            df = df[df['order_date'] <= pd.to_datetime(filters['date_to'])]
        
        if 'clients' in filters and filters['clients']:
            df = df[df['client_name'].str.lower().str.contains('|'.join(filters['clients']), case=False, na=False)]
        
        if 'warehouses' in filters and filters['warehouses']:
            warehouse_filter = '|'.join(filters['warehouses'])
            df = df[df['warehouse_name'].str.lower().str.contains(warehouse_filter, case=False, na=False)]
        
        return df
    
    def explain_delivery_causes(self, filtered_df, limit=10):
        """Analyze and explain root causes of delivery issues"""
        
        # Focus on problematic deliveries
        problem_df = filtered_df[
            (filtered_df['is_delayed'] == True) | 
            (filtered_df['status'].isin(['Failed', 'Returned']))
        ]
        
        if len(problem_df) == 0:
            return {"message": "No delivery issues found in the specified criteria"}
        
        # Root cause analysis
        cause_analysis = problem_df.groupby('primary_root_cause').agg({
            'order_id': 'count',
            'delivery_delay_days': 'mean',
            'amount': 'sum',
            'rating': 'mean',
            'severity': lambda x: (x == 'Critical').sum()
        }).round(2)
        
        cause_analysis.columns = ['failure_count', 'avg_delay_days', 'lost_revenue', 'avg_rating', 'critical_cases']
        cause_analysis = cause_analysis.sort_values('failure_count', ascending=False).head(limit)
        
        # Additional insights
        insights = {}
        
        # Time-based patterns
        time_patterns = problem_df.groupby(['order_day_of_week'])['order_id'].count().sort_values(ascending=False)
        insights['worst_days'] = time_patterns.head(3).to_dict()
        
        # City-wise impact
        city_impact = problem_df.groupby('city').agg({
            'order_id': 'count',
            'amount': 'sum'
        }).sort_values('order_id', ascending=False).head(5)
        insights['most_affected_cities'] = city_impact.to_dict('index')
        
        # Warehouse performance
        if 'warehouse_name' in problem_df.columns:
            warehouse_performance = problem_df.groupby('warehouse_name')['order_id'].count().sort_values(ascending=False).head(5)
            insights['problematic_warehouses'] = warehouse_performance.to_dict()
        
        return {
            'root_cause_analysis': cause_analysis.to_dict('index'),
            'total_affected_orders': len(problem_df),
            'total_lost_revenue': problem_df['amount'].sum(),
            'average_delay': problem_df['delivery_delay_days'].mean(),
            'insights': insights
        }
    
    def compare_performance(self, filtered_df, comparison_field):
        """Compare delivery performance across different dimensions"""
        
        if comparison_field not in filtered_df.columns:
            return {"error": f"Field '{comparison_field}' not found"}
        
        comparison_stats = filtered_df.groupby(comparison_field).agg({
            'order_id': 'count',
            'is_delayed': lambda x: (x == True).sum(),
            'delivery_delay_days': 'mean',
            'amount': 'sum',
            'rating': 'mean'
        }).round(2)
        
        comparison_stats.columns = ['total_orders', 'delayed_orders', 'avg_delay_days', 'total_revenue', 'avg_rating']
        comparison_stats['delay_rate'] = (comparison_stats['delayed_orders'] / comparison_stats['total_orders'] * 100).round(2)
        
        return comparison_stats.sort_values('delay_rate', ascending=False).to_dict('index')
    
    def generate_recommendations(self, analysis_results):
        """Generate AI-enhanced actionable recommendations with fallback"""
        
        if self.use_perplexity:
            ai_recommendations = self.generate_ai_recommendations(analysis_results)
            if ai_recommendations:
                return ai_recommendations
        
        # Fallback to rule-based recommendations
        return self.generate_rule_based_recommendations(analysis_results)
    
    def generate_ai_recommendations(self, analysis_results):
        """Use Perplexity AI to generate contextual recommendations"""
        
        # Prepare context for AI
        context = {
            'total_failures': analysis_results.get('total_affected_orders', 0),
            'revenue_impact': analysis_results.get('total_lost_revenue', 0),
            'top_causes': list(analysis_results.get('root_cause_analysis', {}).keys())[:5],
            'affected_cities': list(analysis_results.get('insights', {}).get('city_impact', {}).keys())[:5]
        }
        
        prompt = f'''Based on this delivery analytics data, provide 5-7 specific, actionable recommendations:

Context:
- Total Failed Orders: {context['total_failures']}
- Revenue Impact: ${context['revenue_impact']:,.2f}
- Top Root Causes: {context['top_causes']}
- Most Affected Cities: {context['affected_cities']}

Analysis Data (first 1500 chars): {str(analysis_results)[:1500]}

Provide recommendations in this structure:
**IMMEDIATE ACTIONS (0-30 days):**
- [specific action 1]
- [specific action 2]

**SHORT-TERM IMPROVEMENTS (1-3 months):**
- [specific improvement 1]
- [specific improvement 2]

**STRATEGIC INITIATIVES (3-6 months):**
- [strategic initiative 1]
- [strategic initiative 2]

Focus on operational changes, resource allocation, process improvements, and technology investments that directly address the root causes identified.'''
        
        ai_recommendations = self.call_perplexity_api(prompt)
        
        if ai_recommendations:
            return {
                'source': 'perplexity_ai',
                'recommendations': ai_recommendations,
                'confidence': 'high',
                'generated_at': datetime.now().isoformat()
            }
        
        return None
    
    def generate_rule_based_recommendations(self, analysis_results):
        """Original rule-based recommendation generation as fallback"""
        
        recommendations = []
        
        if 'root_cause_analysis' in analysis_results:
            causes = analysis_results['root_cause_analysis']
            
            # Top cause-based recommendations
            if causes:
                top_cause = max(causes.keys(), key=lambda x: causes[x]['failure_count'])
                
                if 'traffic' in top_cause.lower():
                    recommendations.extend([
                        "Optimize delivery routes to avoid peak traffic hours",
                        "Implement real-time traffic monitoring and route adjustment",
                        "Consider alternative delivery time slots during low-traffic periods"
                    ])
                
                elif 'weather' in top_cause.lower():
                    recommendations.extend([
                        "Develop weather contingency plans for deliveries",
                        "Invest in weather-appropriate delivery vehicles",
                        "Implement proactive customer communication during weather events"
                    ])
                
                elif 'warehouse' in top_cause.lower():
                    recommendations.extend([
                        "Review and optimize warehouse picking processes",
                        "Implement better inventory management systems",
                        "Increase staffing during peak periods"
                    ])
                
                elif 'address' in top_cause.lower():
                    recommendations.extend([
                        "Implement address verification at order placement",
                        "Train drivers on GPS navigation and customer communication",
                        "Create a system for updating incorrect addresses"
                    ])
                
                elif 'stock' in top_cause.lower():
                    recommendations.extend([
                        "Improve demand forecasting and inventory planning",
                        "Implement real-time stock visibility across warehouses",
                        "Set up automatic stock replenishment alerts"
                    ])
        
        if 'insights' in analysis_results:
            insights = analysis_results['insights']
            
            # Day-based recommendations
            if 'worst_days' in insights:
                worst_day = max(insights['worst_days'].keys(), key=lambda x: insights['worst_days'][x])
                recommendations.append(f"Focus additional resources on {worst_day}s to handle higher failure rates")
            
            # City-based recommendations
            if 'most_affected_cities' in insights:
                top_city = max(insights['most_affected_cities'].keys(), 
                             key=lambda x: insights['most_affected_cities'][x]['order_id'])
                recommendations.append(f"Prioritize operational improvements in {top_city}")
        
        return recommendations
    
    def generate_executive_summary(self, analysis_results, original_query):
        """Generate executive summary using Perplexity AI"""
        
        if not self.use_perplexity:
            return "Executive summary generation requires Perplexity AI integration."
        
        prompt = f'''Create a concise executive summary for this delivery analytics report:

Original Query: "{original_query}"

Key Findings (first 1500 chars):
{str(analysis_results)[:1500]}

Generate a professional 3-paragraph executive summary covering:

**SITUATION OVERVIEW:**
Current delivery performance and key challenges identified

**ROOT CAUSE ANALYSIS:** 
Primary issues and their quantified business impact

**STRATEGIC RECOMMENDATIONS:**
Top 3 priorities for improvement with expected outcomes

Keep it executive-level (non-technical), action-oriented, and business-focused. Use specific numbers from the data.'''
        
        summary = self.call_perplexity_api(prompt)
        return summary if summary else "Unable to generate executive summary at this time."
    
    def process_query(self, query):
        """Main method to process natural language queries with AI enhancement"""
        
        print(f"\n🔍 Processing query: '{query}'")
        if self.use_perplexity:
            print("🤖 Using Perplexity AI for enhanced processing")
        
        # Parse the query (now AI-enhanced)
        parsed = self.parse_natural_language_query(query)
        print(f"📋 Parsed intent: {parsed['intent']}")
        
        # Show AI enhancement status
        if parsed.get('ai_enhanced'):
            print(f"🎯 AI confidence: {parsed.get('confidence', 0.8):.2f}")
        
        # Apply filters
        filters = {}
        if parsed['cities']:
            filters['cities'] = parsed['cities']
            print(f"🌍 Filtering by cities: {parsed['cities']}")
        
        if parsed['clients']:
            filters['clients'] = parsed['clients']
            print(f"🏢 Filtering by clients: {parsed['clients']}")
        
        if parsed['warehouses']:
            filters['warehouses'] = parsed['warehouses']
            print(f"🏭 Filtering by warehouses: {parsed['warehouses']}")
        
        # Add time filters for recent queries
        if 'yesterday' in query:
            filters['date_from'] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            filters['date_to'] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'last week' in query:
            filters['date_from'] = (datetime.now() - timedelta(weeks=1)).strftime('%Y-%m-%d')
        elif 'last month' in query:
            filters['date_from'] = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Get filtered data
        filtered_df = self.filter_data(filters)
        print(f"📊 Filtered dataset: {len(filtered_df)} records")
        
        # Execute analysis based on intent
        if parsed['intent'] == 'explain_causes':
            results = self.explain_delivery_causes(filtered_df)
        elif parsed['intent'] == 'compare':
            if parsed['cities'] and len(parsed['cities']) > 1:
                results = self.compare_performance(filtered_df, 'city')
            else:
                results = self.compare_performance(filtered_df, 'warehouse_name')
        elif parsed['intent'] == 'rank':
            results = self.explain_delivery_causes(filtered_df, limit=5)
        else:
            # Default to root cause analysis
            results = self.explain_delivery_causes(filtered_df)
        
        # Generate AI-enhanced recommendations
        recommendations = self.generate_recommendations(results)
        
        # Generate executive summary (AI-enhanced)
        executive_summary = None
        if self.use_perplexity:
            executive_summary = self.generate_executive_summary(results, query)
        
        # Create comprehensive response
        response = {
            'query': query,
            'analysis_type': parsed['intent'],
            'filters_applied': filters,
            'results': results,
            'recommendations': recommendations,
            'executive_summary': executive_summary,
            'ai_enhanced': self.use_perplexity,
            'parsing_confidence': parsed.get('confidence', 0.8),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save audit log
        self.save_audit_log(response)
        
        return response
    
    def save_audit_log(self, response):
        """Save analysis to audit log"""
        audit_file = AUDIT_DIR / f"audit_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        with open(audit_file, 'w') as f:
            json.dump(response, f, indent=2, default=str)
    
    def display_results(self, response):
        """Display results in a human-readable format"""
        
        print(f"\n{'='*80}")
        print(f"📊 DELIVERY ANALYTICS REPORT")
        print(f"{'='*80}")
        
        print(f"\n🔍 Query: {response['query']}")
        print(f"🕐 Analysis Time: {response['timestamp']}")
        
        # Show AI enhancement status
        if response.get('ai_enhanced'):
            print(f"🤖 AI-Enhanced Analysis (Confidence: {response.get('parsing_confidence', 0.8):.2f})")
        else:
            print(f"📋 Rule-based Analysis")
        
        if response['filters_applied']:
            print(f"\n🎯 Filters Applied:")
            for key, value in response['filters_applied'].items():
                print(f"   • {key}: {value}")
        
        results = response['results']
        
        if 'root_cause_analysis' in results:
            print(f"\n🎯 ROOT CAUSE ANALYSIS")
            print(f"{'─'*50}")
            
            print(f"📈 Total Affected Orders: {results.get('total_affected_orders', 'N/A')}")
            print(f"💰 Total Lost Revenue: ${results.get('total_lost_revenue', 0):,.2f}")
            print(f"⏱️  Average Delay: {results.get('average_delay', 0):.1f} days")
            
            print(f"\n🔍 Top Root Causes:")
            for cause, data in list(results['root_cause_analysis'].items())[:5]:
                print(f"   {cause}:")
                print(f"      • Failure Count: {data['failure_count']}")
                print(f"      • Avg Delay: {data['avg_delay_days']:.1f} days")
                print(f"      • Lost Revenue: ${data['lost_revenue']:,.2f}")
                print(f"      • Critical Cases: {data['critical_cases']}")
                print()
        
        if 'insights' in results:
            insights = results['insights']
            
            if 'worst_days' in insights:
                print(f"📅 Worst Performing Days:")
                for day, count in list(insights['worst_days'].items())[:3]:
                    print(f"   • {day}: {count} failures")
            
            if 'most_affected_cities' in insights:
                print(f"\n🌍 Most Affected Cities:")
                for city, data in list(insights['most_affected_cities'].items())[:3]:
                    print(f"   • {city}: {data['order_id']} failures, ${data['amount']:,.2f} lost")
        
        # Display executive summary (AI-enhanced)
        if response.get('executive_summary'):
            print(f"\n📋 EXECUTIVE SUMMARY")
            print(f"{'─'*50}")
            print(response['executive_summary'])
        
        # Display recommendations
        if response['recommendations']:
            print(f"\n💡 ACTIONABLE RECOMMENDATIONS")
            print(f"{'─'*50}")
            
            if isinstance(response['recommendations'], dict) and response['recommendations'].get('source') == 'perplexity_ai':
                # AI-generated recommendations
                print("🤖 AI-Generated Recommendations:")
                print(response['recommendations']['recommendations'])
            else:
                # Rule-based recommendations
                for i, rec in enumerate(response['recommendations'][:8], 1):
                    print(f"{i}. {rec}")
        
        print(f"\n{'='*80}\n")

def main():
    """Main interactive loop"""
    
    print("🚚 Advanced Delivery Root Cause Analytics System")
    print("=" * 60)
    print("This system can help you understand delivery failures and delays.")
    print("Try queries like:")
    print("• Why were deliveries delayed in Ahmedabad yesterday?")
    print("• What are the top reasons for delivery failures last week?")
    print("• Compare delivery performance between Mumbai and Delhi")
    print("• Explain delivery issues for Client X in the past month")
    print("\nType 'help' for more examples, 'quit' to exit.")
    print("=" * 60)
    
    try:
        # Initialize the analyzer
        analyzer = DeliveryAnalyzer()
        
        # Sample use cases for demonstration
        sample_queries = [
            "Why were deliveries delayed in Chennai yesterday?",
            "What are the top reasons for delivery failures last week?",
            "Compare delivery performance between Mumbai and Delhi",
            "Explain delivery issues in Coimbatore last month",
            "What warehouse problems occurred in August?",
            "Why did orders fail during the festival period?"
        ]
        
        while True:
            print("\n" + "─" * 60)
            query = input("🔍 Enter your query (or 'help', 'samples', 'quit'): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Thank you for using the Delivery Analytics System!")
                break
            
            elif query.lower() in ['help', 'h']:
                print("\n📚 HELP - Sample Queries You Can Try:")
                print("1. Why were deliveries delayed in [city] [timeframe]?")
                print("2. What are the top reasons for delivery failures?")
                print("3. Compare delivery performance between [city1] and [city2]")
                print("4. Explain delivery issues for [client] in [timeframe]")
                print("5. What warehouse problems occurred in [timeframe]?")
                print("6. Why did orders fail during the festival period?")
                continue
            
            elif query.lower() in ['samples', 'examples', 'demo']:
                print("\n🎯 Running sample queries for demonstration:")
                for i, sample_query in enumerate(sample_queries[:3], 1):
                    print(f"\n{'='*20} SAMPLE {i} {'='*20}")
                    try:
                        response = analyzer.process_query(sample_query)
                        analyzer.display_results(response)
                    except Exception as e:
                        print(f"❌ Error processing sample query: {e}")
                continue
            
            elif not query:
                continue
            
            try:
                # Process the query
                response = analyzer.process_query(query)
                
                # Display results
                analyzer.display_results(response)
                
            except Exception as e:
                print(f"❌ Error processing query: {e}")
                print("Please try rephrasing your query or type 'help' for examples.")
                
                # Print detailed error for debugging
                if os.getenv('DEBUG'):
                    traceback.print_exc()
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ System error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()