# Vehicle Routing Problem (VRP) Application

A comprehensive web application for solving complex vehicle routing problems using Google OR-Tools and Google Routes API. This application enables users to upload Excel files containing delivery, pickup, truck, depot, and employee data, then generates optimized routes that minimize total costs while respecting real-world constraints.

## 🎯 Overview

This VRP solver addresses the Capacitated Vehicle Routing Problem with Pickup and Delivery (CVRPPD), incorporating multiple dimensions including:
- **Distance constraints** (vehicle range limitations)
- **Volume and weight capacity** constraints
- **Time windows** (employee work hours)
- **Pickup-delivery pairing** constraints
- **Cost optimization** (fuel + labor costs)

## 🏗️ Architecture & Technical Decisions

### Frontend: Vanilla JavaScript
**Decision Rationale:**
- **Simplicity over complexity**: The frontend requirements are straightforward - file upload, column mapping interface, and basic visualization
- **No framework overhead**: Avoiding the performance and bundle size overhead of React/Vue/Angular for a relatively simple UI
- **Fundamentals focus**: Chosen to solidify core frontend development skills without framework abstractions
- **Rapid prototyping**: Faster initial development without build tools, transpilation, or complex tooling setup

**Key Features:**
- Drag-and-drop Excel file upload with validation
- Dynamic column mapping interface for flexible data structures
- Progressive web app workflow (Upload → Map → Solve → Visualize)
- Responsive design with CSS animations and modern UI patterns

### Backend: Python with Flask
**Decision Rationale:**
- **Rapid iteration**: Python's expressiveness enables quick development and testing of complex VRP algorithms
- **OR-Tools integration**: Google OR-Tools has excellent Python bindings, despite the underlying C++ implementation
- **No performance concerns**: 
  - OR-Tools solver is implemented in C++, so Python wrapper doesn't impact solving performance
  - Single-user application doesn't require high-concurrency server frameworks
  - I/O operations (file processing, API calls) benefit more from Python's ecosystem than raw performance
- **Rich ecosystem**: Pandas for Excel processing, requests for API integration, Flask for lightweight web serving

### Key Technical Components

#### 1. Excel File Processing (`server/services/csv/handle_excel_file.py`)
- **Configurable mapping system**: Dynamic field processors allow flexible Excel column mapping
- **Chunked processing**: Handles large files efficiently using pandas chunking
- **Type safety**: Robust data validation and type conversion with fallback defaults
- **Multi-sheet support**: Processes multiple Excel sheets (deliveries, trucks, depots, pickups, employees)

#### 2. Google Routes API Integration (`server/services/google_routes_api/`)
- **Intelligent caching**: Persistent disk-based cache prevents redundant API calls
- **Rate limiting**: Implements Google's 3000 elements/minute quota with rolling window tracking
- **Batch processing**: Optimizes API usage by batching distance matrix requests
- **Exponential backoff**: Handles API errors and rate limits gracefully
- **Address normalization**: Consistent address handling for reliable caching

#### 3. OR-Tools VRP Solver (`server/services/vrp/`)
**Multi-dimensional optimization:**
- **Cost dimension**: Primary objective combining fuel costs (distance/MPG × gas price) and labor costs (time × hourly rate)
- **Distance dimension**: Enforces vehicle range constraints
- **Volume/Weight dimensions**: Respects truck capacity limits
- **Time dimension**: Handles employee work hour constraints
- **Pickup-delivery constraints**: Ensures proper sequencing of pickup/delivery pairs

**Solver strategies:**
- Multiple first-solution strategies with fallback (PATH_CHEAPEST_ARC, PARALLEL_CHEAPEST_INSERTION, SAVINGS, etc.)
- Guided Local Search metaheuristic for solution improvement
- Configurable time limits for responsive user experience
- Comprehensive logging for debugging and optimization analysis

#### 4. Database Layer (`server/db/`)
- **SQLite for simplicity**: Lightweight, serverless database perfect for single-user applications
- **File caching**: Temporary storage of uploaded Excel files with TTL expiration
- **API response caching**: Persistent storage of Google Routes API responses

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Google Maps API key with Routes API enabled

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd vehicle-routing-problem-app
```

2. **Set up Python environment:**
```bash
cd server
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
# Create .env file in server directory
echo "GOOGLE_MAPS_API_KEY=your_api_key_here" > .env
```

4. **Initialize database:**
```bash
python -c "from server.db.init_db import init_app; from flask import Flask; app = Flask(__name__); init_app(app)"
```

5. **Start the server:**
```bash
python app.py
```

6. **Access the application:**
Open `http://localhost:5000` in your browser

## 📊 Data Format

The application expects Excel files with the following sheets:

### Trucks Sheet
| Column | Description | Example |
|--------|-------------|---------|
| UID | Unique truck identifier | "TRUCK_001" |
| Max Volume | Maximum cargo volume | 1000.0 |
| Max Weight | Maximum cargo weight | 5000.0 |
| Current Location | Starting address | "123 Main St, City, State" |
| End Location | Return address | "123 Main St, City, State" |
| Range | Maximum travel distance | 300.0 |
| MPG | Miles per gallon | 8.5 |

### Deliveries Sheet
| Column | Description | Example |
|--------|-------------|---------|
| UID | Unique delivery identifier | "DEL_001" |
| Current Location | Pickup address | "456 Oak Ave, City, State" |
| Destination | Delivery address | "789 Pine St, City, State" |
| Volume | Package volume | 50.0 |
| Weight | Package weight | 25.0 |

### Pickups Sheet
Same structure as Deliveries sheet.

### Depots Sheet
| Column | Description | Example |
|--------|-------------|---------|
| UID | Unique depot identifier | "DEPOT_001" |
| Location | Depot address | "100 Warehouse Rd, City, State" |

### Employees Sheet
| Column | Description | Example |
|--------|-------------|---------|
| UID | Unique employee identifier | "EMP_001" |
| Hours Available | Work hours available | 8.0 |
| Hourly Pay Rate | Cost per hour | 25.00 |
| Truck UID | Assigned truck | "TRUCK_001" |

## 🔧 Configuration

### Cost Parameters
- **Fuel price**: $3.50/gallon (configurable in `cost_dimension.py`)
- **Vehicle fixed cost**: $1 per vehicle used
- **Penalty for dropped nodes**: $1,000,000 (encourages complete solutions)

### Solver Parameters
- **Time limit**: 30 seconds per solve attempt
- **Metaheuristic**: Guided Local Search
- **Multiple strategy fallback**: 6 different first-solution strategies

### API Limits
- **Google Routes API**: 3000 elements per minute (automatically throttled)
- **Batch size**: 25×25 origins/destinations per request

## 🎯 Use Cases

1. **Last-mile delivery optimization**: E-commerce, food delivery, package services
2. **Service route planning**: Field service, maintenance, healthcare visits
3. **Logistics coordination**: Multi-stop pickup and delivery operations
4. **Fleet management**: Optimizing vehicle utilization and driver schedules

## 🔍 Algorithm Details

The solver implements a sophisticated CVRPPD algorithm:

1. **Problem modeling**: Converts real-world constraints into OR-Tools dimensions and constraints
2. **Distance matrix generation**: Uses Google Routes API for accurate travel times and distances
3. **Multi-objective optimization**: Balances fuel costs, labor costs, and constraint satisfaction
4. **Constraint handling**: Enforces capacity, time, range, and pickup-delivery pairing constraints
5. **Solution refinement**: Applies local search metaheuristics for solution improvement

## 🚧 Future Enhancements

- **Route visualization**: Interactive maps showing optimized routes
- **Real-time tracking**: Integration with GPS tracking systems
- **Advanced constraints**: Time windows, driver preferences, vehicle-customer compatibility
- **Batch processing**: Support for multiple optimization scenarios
- **Export capabilities**: PDF reports, CSV route sheets, API integration

## 📝 Development Notes

### Performance Considerations
- OR-Tools C++ core ensures fast solving despite Python wrapper
- Caching strategies minimize redundant API calls and computations
- Chunked file processing handles large datasets efficiently
- SQLite provides adequate performance for single-user scenarios

### Scalability Paths
- **Multi-user**: Upgrade to PostgreSQL + Redis for session management
- **High-performance**: Consider FastAPI + async processing for concurrent requests
- **Enterprise**: Implement microservices architecture with dedicated solver instances

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google OR-Tools**: Powerful optimization library enabling sophisticated VRP solving
- **Google Routes API**: Accurate real-world distance and time data
- **Flask**: Lightweight and flexible web framework
- **Pandas**: Robust data processing and Excel integration
