class MapVisualizer {
  constructor() {
    this.map = null;
    this.directionsService = null;
    this.directionsRenderers = [];
    this.markers = [];
    this.paths = [];
    this.colors = [
      "#FF0000", // Red
      "#0000FF", // Blue
      "#008000", // Green
      "#FFA500", // Orange
      "#800080", // Purple
      "#A52A2A", // Brown
      "#000080", // Navy
      "#008B8B", // Dark Cyan
    ];
  }

  initMap() {
    if (!this.map) {
      // Wait for the map element to be available
      const mapElement = document.getElementById("map");
      if (!mapElement) {
        console.error("Map container element not found!");
        return;
      }

      // Ensure map element has dimensions
      mapElement.style.height = "500px";
      mapElement.style.width = "100%";

      // Initialize with a default location (e.g., US center)
      this.map = new google.maps.Map(mapElement, {
        zoom: 4,
        center: { lat: 39.8283, lng: -98.5795 }, // Center of US
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        streetViewControl: false,
      });
      this.directionsService = new google.maps.DirectionsService();
    }

    // Clear existing routes and markers
    this.clearMap();
  }

  clearMap() {
    this.directionsRenderers.forEach((renderer) => renderer.setMap(null));
    this.markers.forEach((marker) => marker.setMap(null));
    this.directionsRenderers = [];
    this.markers = [];
    this.paths.forEach((path) => path.setMap(null));
    this.paths = [];
  }

  async displayRoutes(routes) {
    console.log("Starting displayRoutes with routes:", routes);
    this.initMap();
    const bounds = new google.maps.LatLngBounds();

    for (let i = 0; i < routes.length; i++) {
      const route = routes[i];
      console.log(`Processing route ${i}:`, route);
      const routeColor = this.colors[i % this.colors.length];

      const directionsRenderer = new google.maps.DirectionsRenderer({
        map: this.map,
        suppressMarkers: true,
        polylineOptions: {
          strokeColor: routeColor,
          strokeWeight: 4,
        },
      });
      this.directionsRenderers.push(directionsRenderer);

      const stops = route.stop_details;
      console.log("Stops for this route:", stops);
      if (stops.length < 2) continue;

      // **Create markers for each stop using Promises to handle asynchronous geocoding**
      const geocodePromises = stops.map((stop, stopIndex) => {
        return new Promise((resolve, reject) => {
          const marker = new google.maps.Marker({
            position: null,
            map: this.map,
            label: {
              text: `${stopIndex + 1}`,
              color: "white",
            },
            icon: {
              path: google.maps.SymbolPath.CIRCLE,
              fillColor: routeColor,
              fillOpacity: 1,
              strokeWeight: 1,
              scale: 10,
            },
            title: stop.address,
          });

          const geocoder = new google.maps.Geocoder();
          geocoder.geocode({ address: stop.address }, (results, status) => {
            console.log(
              `Geocoding result for stop ${stopIndex}:`,
              status,
              results
            );
            if (status === "OK") {
              const location = results[0].geometry.location;
              marker.setPosition(location);
              bounds.extend(location);
              this.markers.push(marker);
              resolve();
            } else {
              console.error(
                `Geocoding failed for address: ${stop.address}`,
                status
              );
              resolve(); // Continue even if one geocode fails
            }
          });
        });
      });

      // **Wait for all geocoding operations to complete**
      await Promise.all(geocodePromises);

      // **Adjust map bounds after all markers are placed**
      this.map.fitBounds(bounds);

      // Calculate route
      try {
        const waypoints = stops.slice(1, -1).map((stop) => ({
          location: stop.address,
          stopover: true,
        }));

        console.log("Calculating directions with:", {
          origin: stops[0].address,
          destination: stops[stops.length - 1].address,
          waypoints: waypoints,
        });

        const result = await this.getDirections(
          stops[0].address,
          stops[stops.length - 1].address,
          waypoints
        );

        console.log("Directions result:", result);
        directionsRenderer.setDirections(result);
      } catch (error) {
        console.error(`Error displaying route ${i + 1}:`, error);
      }
    }
  }

  getDirections(origin, destination, waypoints) {
    return new Promise((resolve, reject) => {
      this.directionsService.route(
        {
          origin: origin,
          destination: destination,
          waypoints: waypoints,
          optimizeWaypoints: false,
          travelMode: google.maps.TravelMode.DRIVING,
        },
        (result, status) => {
          if (status === "OK") {
            resolve(result);
          } else {
            reject(new Error(`Directions request failed: ${status}`));
          }
        }
      );
    });
  }

  visualizeRoute(points) {
    if (!points || points.length === 0) {
      console.error("No points provided for visualization");
      return;
    }

    // Clear any existing markers and routes
    this.clearMap();

    // Create markers for each point
    points.forEach((point, index) => {
      const marker = new google.maps.Marker({
        position: { lat: parseFloat(point.lat), lng: parseFloat(point.lng) },
        map: this.map,
        label: (index + 1).toString(),
      });
      this.markers.push(marker);
    });

    // Adjust map bounds to show all points
    const bounds = new google.maps.LatLngBounds();
    points.forEach((point) => {
      bounds.extend({ lat: parseFloat(point.lat), lng: parseFloat(point.lng) });
    });
    this.map.fitBounds(bounds);

    // Create route path
    const path = new google.maps.Polyline({
      path: points.map((point) => ({
        lat: parseFloat(point.lat),
        lng: parseFloat(point.lng),
      })),
      geodesic: true,
      strokeColor: "#FF0000",
      strokeOpacity: 1.0,
      strokeWeight: 2,
      map: this.map,
    });
    this.paths.push(path);
  }
}

export const mapVisualizer = new MapVisualizer();
