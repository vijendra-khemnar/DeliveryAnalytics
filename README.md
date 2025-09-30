# Advanced Delivery Root Cause Analytics System

## Overview

This system provides intelligent root cause analysis for delivery failures and delays by aggregating multi-domain data across orders, fleet operations, warehouse activities, external factors, and customer feedback. It enables operations managers to understand WHY deliveries fail, not just WHAT failed.

## 🎯 Business Problem Solved

- **Fragmented Data Analysis**: Eliminates manual investigation across siloed systems
- **Reactive Operations**: Converts reactive problem-solving to proactive insights  
- **Hidden Systemic Issues**: Identifies recurring bottlenecks and patterns
- **Revenue Leakage**: Quantifies impact and provides actionable recommendations

## 🚀 Key Features

### 1. **Multi-Domain Data Integration**
- Orders & Shipment Data (timestamps, delivery status)
- Fleet & Driver Logs (GPS traces, driver notes) 
- Warehouse Data (stockouts, preparation delays)
- Customer Feedback (sentiment analysis, ratings)
- Contextual Data (weather, traffic, events)

### 2. **Intelligent Root Cause Analysis**
- Automatic correlation of events across data domains
- Pattern recognition for systemic issues
- Severity classification and impact quantification
- Time-based trend analysis

### 3. **Natural Language Query Interface**
- Support for business-friendly queries
- No technical knowledge required
- Flexible query interpretation
- Context-aware filtering

### 4. **Actionable Insights & Recommendations**
- Human-readable narrative explanations
- Specific operational recommendations
- Resource allocation suggestions
- Preventive action plans

## 📊 Sample Use Cases Supported

1. **"Why were deliveries delayed in Chennai yesterday?"**
   - Time-specific analysis with city filtering
   - Root cause breakdown with quantified impact

2. **"Why did Client X's orders fail in the past week?"**
   - Client-specific failure analysis
   - Historical trend identification

3. **"Explain the top reasons for delivery failures linked to Warehouse B in August?"**
   - Warehouse-specific operational analysis
   - Monthly performance assessment

4. **"Compare delivery failure causes between Mumbai and Delhi last month?"**
   - Multi-city comparative analysis
   - Performance benchmarking

5. **"What are the likely causes of delivery failures during festival periods?"**
   - Seasonal pattern analysis
   - Event-driven failure prediction

6. **"If we onboard Client Y with 20,000 extra orders, what risks should we expect?"**
   - Predictive capacity analysis
   - Risk mitigation planning

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- CSV data files in the project directory

### Setup Instructions

1. **Clone or download the project files**
   ```bash
   git clone <repository-url>
   cd DeliveryAnalytics
   ```

2. **Install required packages**
   ```bash
   pip install pandas python-dotenv dateparser openai numpy matplotlib seaborn
   ```

3. **Ensure data files are present**
   Required CSV files:
   - `orders.csv` - Primary order data with delivery status
   - `fleet_logs.csv` - Driver and vehicle tracking data
   - `warehouse_logs.csv` - Warehouse operation logs
   - `external_factors.csv` - Traffic, weather, and event data
   - `feedback.csv` - Customer feedback and ratings
   - `warehouses.csv` - Warehouse information
   - `clients.csv` - Client/customer data
   - `drivers.csv` - Driver information

## 🎮 Usage

### Interactive Mode
```bash
python delivery_root_cause_analyzer.py
```

This launches an interactive session where you can:
- Enter natural language queries
- View detailed analysis reports  
- Get actionable recommendations
- Access help and sample queries

### Demo Mode
```bash
python demo_use_cases.py
```

Runs through all the sample use cases automatically to demonstrate system capabilities.

### Programmatic Usage
```python
from delivery_root_cause_analyzer import DeliveryAnalyzer

# Initialize the system
analyzer = DeliveryAnalyzer()

# Process a query
response = analyzer.process_query("Why were deliveries delayed in Mumbai last week?")

# Display results
analyzer.display_results(response)
```

## 📋 Sample Queries

### Root Cause Analysis
- "Why were deliveries delayed in [city] [timeframe]?"
- "What are the top reasons for delivery failures?"
- "Explain delivery issues for [client] in [timeframe]"

### Comparative Analysis  
- "Compare delivery performance between [city1] and [city2]"
- "Compare warehouse efficiency across regions"

### Trend Analysis
- "What warehouse problems occurred in [timeframe]?"
- "Show delivery patterns during festival periods"

### Predictive Analysis
- "What risks should we expect with increased volume?"
- "How should we prepare for peak season?"

## 📊 Data Schema

### Core Data Sources

#### Orders (`orders.csv`)
- `order_id`, `client_id`, `customer_name`
- `city`, `state`, `delivery_address`
- `order_date`, `promised_delivery_date`, `actual_delivery_date`
- `status`, `failure_reason`, `amount`

#### Fleet Logs (`fleet_logs.csv`)  
- `order_id`, `driver_id`, `vehicle_number`
- `route_code`, `gps_delay_notes`
- `departure_time`, `arrival_time`

#### Warehouse Logs (`warehouse_logs.csv`)
- `order_id`, `warehouse_id`
- `picking_start`, `picking_end`, `dispatch_time`
- `notes` (delays, issues)

#### External Factors (`external_factors.csv`)
- `order_id`, `traffic_condition`, `weather_condition`
- `event_type` (festivals, strikes, holidays)

#### Customer Feedback (`feedback.csv`)
- `order_id`, `feedback_text`, `sentiment`, `rating`

## 🎯 Output Format

### Analysis Report Structure
```
📊 DELIVERY ANALYTICS REPORT
================================

🔍 Query: [User's natural language query]
🕐 Analysis Time: [Timestamp]

🎯 Filters Applied:
   • [Applied filters and parameters]

🎯 ROOT CAUSE ANALYSIS
──────────────────────────────
📈 Total Affected Orders: [Number]
💰 Total Lost Revenue: $[Amount]
⏱️  Average Delay: [Days]

🔍 Top Root Causes:
   [Cause]:
      • Failure Count: [Number]
      • Avg Delay: [Days]  
      • Lost Revenue: $[Amount]
      • Critical Cases: [Number]

📅 Worst Performing Days:
   • [Day]: [Failures]

🌍 Most Affected Cities:
   • [City]: [Failures], $[Lost Revenue]

💡 ACTIONABLE RECOMMENDATIONS
──────────────────────────────
1. [Specific recommendation]
2. [Operational improvement]
3. [Resource allocation suggestion]
```

## ⚙️ Configuration

### Environment Variables (`.env`)
```
# Debug mode
DEBUG=false

# OpenAI API (optional - system works without it)
OPENAI_API_KEY=your_key_here

# Processing limits
ROW_LIMIT=100000
MAX_DAYS_RANGE=90
DEFAULT_LIMIT=500
```

## 🔧 System Architecture

### Core Components

1. **Data Loader** - Reads and validates CSV files
2. **Data Integrator** - Joins data across domains  
3. **Feature Engineer** - Creates derived analytics features
4. **NLU Parser** - Interprets natural language queries
5. **Query Executor** - Applies filters and aggregations
6. **Insight Generator** - Creates human-readable explanations
7. **Recommendation Engine** - Generates actionable advice

### Root Cause Categories
- **Traffic Congestion** - Route delays, peak hour issues
- **Weather Disruption** - Rain, fog, extreme conditions  
- **Warehouse Operations** - Picking delays, stock issues
- **Address Issues** - Incorrect/incomplete addresses
- **Stock Unavailability** - Out-of-stock scenarios
- **Vehicle Issues** - Breakdowns, maintenance
- **Customer Returns** - Customer-initiated returns
- **Processing Delays** - Internal operational delays

## 📈 Performance Insights

The system processes:
- ✅ 10,000+ orders with 50+ integrated features
- ✅ Real-time query processing (< 5 seconds)
- ✅ Multi-dimensional analysis and filtering
- ✅ Automated root cause classification
- ✅ Revenue impact quantification

## 🔍 Audit & Logging

All analysis sessions are automatically logged to the `audit/` directory with:
- Query details and parameters
- Analysis results and insights  
- Recommendations generated
- Timestamps and metadata

## 🚀 Future Enhancements

### Planned Features
- **Machine Learning Models** - Predictive failure analysis
- **Real-time Dashboards** - Live monitoring capabilities  
- **API Endpoints** - RESTful API for system integration
- **Advanced NLU** - Enhanced query understanding with OpenAI
- **Alerting System** - Proactive issue notifications
- **Mobile Interface** - Mobile-friendly query interface

### Integration Opportunities
- **ERP Systems** - Direct data pipeline integration
- **BI Tools** - Dashboard embedding capabilities
- **Notification Systems** - Slack/Email alert integration
- **GPS Tracking** - Real-time location data integration

## ❓ Troubleshooting

### Common Issues

1. **"File not found" errors**
   - Ensure all CSV files are in the project directory
   - Check file names match exactly

2. **"Status column missing" warning**
   - This is handled gracefully by the system
   - Indicates merge operations are working correctly

3. **Empty query results**  
   - Check date filters (system defaults to recent data)
   - Verify city/client names match data exactly
   - Use broader time ranges for historical queries

4. **Performance issues**
   - Reduce ROW_LIMIT in .env file
   - Filter by specific date ranges
   - Focus queries on specific cities/clients

### Debug Mode
Set `DEBUG=true` in `.env` for detailed error messages and execution traces.

## 📞 Support

For technical support or feature requests:
1. Check the troubleshooting section
2. Review audit logs in `audit/` directory  
3. Run demo use cases to verify system functionality
4. Examine console output for detailed error information

## 📜 License

This system is provided for demonstration and educational purposes. Ensure compliance with your organization's data privacy and security policies when using with production data.

---

**🚚 Advanced Delivery Root Cause Analytics System - Transform reactive operations into proactive insights!**