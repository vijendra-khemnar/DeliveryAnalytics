#!/usr/bin/env python3
"""
Demo script for the Delivery Root Cause Analytics System
This script demonstrates all the sample use cases mentioned in the requirements.
"""

from delivery_root_cause_analyzer import DeliveryAnalyzer
import traceback

def demo_sample_use_cases():
    """Demonstrate all the sample use cases"""
    
    print("🚚 DELIVERY ANALYTICS SYSTEM - DEMO")
    print("=" * 80)
    
    # Initialize analyzer
    try:
        analyzer = DeliveryAnalyzer()
        print(f"✅ System initialized with {len(analyzer.integrated_df)} orders\n")
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return
    
    # Sample use cases from requirements
    sample_queries = [
        "Why were deliveries delayed in city Chennai yesterday?",
        "Why did Client orders fail in the past week?", 
        "Explain the top reasons for delivery failures linked to Warehouse in August?",
        "Compare delivery failure causes between Chennai and Mumbai last month?",
        "What are the likely causes of delivery failures during the festival period, and how should we prepare?",
        "If we onboard Client Sunder Ltd with ~20,000 extra monthly orders, what new failure risks should we expect and how do we mitigate them?"
    ]
    
    print("🎯 DEMONSTRATING SAMPLE USE CASES")
    print("=" * 80)
    
    for i, query in enumerate(sample_queries, 1):
        print(f"\n{'='*20} USE CASE {i} {'='*20}")
        print(f"Query: {query}")
        print("-" * 60)
        
        try:
            response = analyzer.process_query(query)
            analyzer.display_results(response)
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            if hasattr(e, '__traceback__'):
                traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("🎉 DEMO COMPLETED - All use cases demonstrated!")
    print("=" * 80)

if __name__ == "__main__":
    demo_sample_use_cases()